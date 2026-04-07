"""
ScoringAgent: Reads output from OrchestrationAgent and applies the
high-risk scoring rules:
  - Customer enrolled in loyalty platform >= 8 weeks ago but zero redemptions
  - 2 support tickets in 90 days -- 1 unresolved for 6 days
  - Average order value down 34% over 6 months
  - 3 of last 5 orders used discount codes
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from logger import get_logger

log = get_logger("ScoringAgent")

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False


# ── Direct scoring (no Claude) ────────────────────────────────────────────────

def _score_direct(consolidated: dict) -> list[dict]:
    """Apply the scoring rules and return high-risk customers."""
    log.info("Applying scoring rules to consolidated data")
    high_risk = []
    skipped = 0

    # ── SourceData customers (1000 records) ───────────────────────────
    sd_candidates = consolidated.get("sd_customers", [])
    log.info("Scanning %d SourceData customers for rule matches", len(sd_candidates))
    for c in sd_candidates:
        weeks     = c.get("weeks_since_enrollment", 0)
        zero_flag = c.get("zero_redemption_flag", False)
        redeemed  = c.get("redeemed_total", -1)
        if weeks >= 8 and (zero_flag or redeemed == 0):
            risk_score = _compute_risk_score(c)
            high_risk.append({**c, "risk_score": risk_score, "risk_level": _risk_level(risk_score)})
        else:
            skipped += 1

    log.debug("SourceData: %d matched, %d skipped", len(high_risk), skipped)

    # ── SourceDataV1 customers (100 detailed records) ─────────────────
    v1_candidates = consolidated.get("v1_customers", [])
    v1_matched = 0
    log.info("Scanning %d SourceDataV1 customers for rule matches", len(v1_candidates))
    for c in v1_candidates:
        redeemed        = c.get("redeemed_total", -1)
        enrollment_date = c.get("enrollment_date", "")
        if enrollment_date and redeemed == 0:
            try:
                enrolled_dt = datetime.fromisoformat(enrollment_date.replace("Z", "+00:00"))
                weeks = (datetime.now(timezone.utc) - enrolled_dt).total_seconds() / (7 * 24 * 3600)
                if weeks >= 8:
                    risk_score = _compute_risk_score(c)
                    high_risk.append({
                        **c,
                        "weeks_since_enrollment": round(weeks, 1),
                        "risk_score": risk_score,
                        "risk_level": _risk_level(risk_score),
                    })
                    v1_matched += 1
            except ValueError as e:
                log.warning("Could not parse enrollment_date for %s: %s", c.get("customer_id"), e)

    log.debug("SourceDataV1: %d matched", v1_matched)

    result = sorted(high_risk, key=lambda x: x.get("weeks_since_enrollment", 0), reverse=True)
    log.info(
        "Scoring complete — %d high-risk customers identified "
        "(Critical: %d  High: %d  Medium: %d)",
        len(result),
        sum(1 for c in result if c["risk_level"] == "critical"),
        sum(1 for c in result if c["risk_level"] == "high"),
        sum(1 for c in result if c["risk_level"] == "medium"),
    )
    return result


def _compute_risk_score(c: dict) -> int:
    """
    Compute churn risk score from multi-source signals.
    Higher score = higher churn risk.
    """
    score = 0
    if c.get("crm_churn_flag"):                          score += 3  # CRM churn flag
    if c.get("unsubscribed"):                            score += 2  # Email unsubscribed
    if (c.get("session_drop_pct") or 0) > 50:           score += 2  # Web session drop > 50%
    if (c.get("unresolved_tickets") or 0) > 0:          score += 1  # Open support ticket
    if c.get("browsing_intent_collapse"):                score += 1  # GA intent collapse
    if (c.get("email_open_rate_pct") or 100) < 10:      score += 1  # Email open rate < 10%
    if (c.get("last_purchase_days_ago") or 0) > 60:     score += 1  # No purchase in 60+ days
    return score


def _risk_level(score: int) -> str:
    if score >= 6: return "critical"
    if score >= 3: return "high"
    return "medium"


# ── Agent tools ───────────────────────────────────────────────────────────────

def _make_tools(consolidated: dict) -> list[dict]:
    return [
        {
            "name": "apply_zero_redemption_rule",
            "description": (
                "Apply the high-risk scoring rules to the consolidated customer data. "
                "Returns the list of high-risk customers with their risk score and level."
            ),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_risk_distribution",
            "description": "Get the breakdown of high-risk customers by tier and risk level.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
    ]


def _handle_tool(name: str, consolidated: dict, high_risk_cache: list) -> str:
    log.info("Tool called: %s", name)
    if name == "apply_zero_redemption_rule":
        customers = _score_direct(consolidated)
        high_risk_cache.clear()
        high_risk_cache.extend(customers)
        log.info("Tool result: apply_zero_redemption_rule -> %d high-risk customers", len(customers))
        return json.dumps({"count": len(customers), "sample": customers[:3]})

    if name == "get_risk_distribution":
        customers = high_risk_cache if high_risk_cache else _score_direct(consolidated)
        tiers: dict[str, int] = {}
        levels: dict[str, int] = {}
        for c in customers:
            t = c.get("loyalty_tier", "Unknown")
            tiers[t] = tiers.get(t, 0) + 1
            l = c.get("risk_level", "medium")
            levels[l] = levels.get(l, 0) + 1
        result = {"total": len(customers), "by_tier": tiers, "by_risk_level": levels}
        log.info("Tool result: get_risk_distribution -> %s", result)
        return json.dumps(result)

    log.warning("Unknown tool requested: %s", name)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Public entry point ────────────────────────────────────────────────────────

def run(consolidated: dict, api_key: str | None = None) -> dict:
    """Run the ScoringAgent on consolidated data. Returns: { customers, summary, agent_mode }"""
    log.info("=" * 60)
    log.info("ScoringAgent STARTED")
    mode = "Claude AI" if (api_key and _anthropic_available) else "Rule Engine (direct)"
    log.info("Mode: %s | Input: %d v1 + %d sd customers",
             mode,
             len(consolidated.get("v1_customers", [])),
             len(consolidated.get("sd_customers", [])))
    t0 = time.perf_counter()

    if not api_key or not _anthropic_available:
        if not api_key:
            log.warning("ANTHROPIC_API_KEY not set — running in Rule Engine mode")
        customers = _score_direct(consolidated)
        summary = (
            f"ScoringAgent identified {len(customers)} high-risk customers. "
            "Rule: enrolled in loyalty program 8+ weeks ago with zero redemptions. "
            f"Risk breakdown — "
            f"Critical: {sum(1 for c in customers if c['risk_level']=='critical')}, "
            f"High: {sum(1 for c in customers if c['risk_level']=='high')}, "
            f"Medium: {sum(1 for c in customers if c['risk_level']=='medium')}."
        )
        log.info("ScoringAgent COMPLETE in %.2fs", time.perf_counter() - t0)
        log.info("=" * 60)
        return {"customers": customers, "summary": summary, "agent_mode": "direct"}

    # Claude AI agent loop
    log.info("Initialising Claude AI agent loop (model: claude-opus-4-6)")
    client = anthropic.Anthropic(api_key=api_key)
    high_risk_cache: list = []
    tools = _make_tools(consolidated)

    messages = [{
        "role": "user",
        "content": (
            "You are the Apex Retail ScoringAgent. "
            "The OrchestrationAgent has consolidated customer data. "
            "Your job is to:\n"
            "1. Apply the scoring rules to identify high-risk customers\n"
            "2. Get the risk distribution breakdown\n"
            "3. Provide a brief analysis and retention recommendations\n"
            "Rule: customers enrolled >= 8 weeks ago with zero loyalty redemptions are HIGH RISK."
        )
    }]

    agent_summary = ""
    iteration = 0
    for iteration in range(10):
        log.info("Agent iteration %d — sending request to Claude", iteration + 1)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            tools=tools,
            messages=messages,
        )
        log.debug("Response stop_reason: %s | tokens used: %s", response.stop_reason, response.usage)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    agent_summary = block.text
            log.info("Agent reached end_turn after %d iteration(s)", iteration + 1)
            break

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    log.info("Claude requested tool: %s", block.name)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": _handle_tool(block.name, consolidated, high_risk_cache),
                    })
            messages.append({"role": "user", "content": results})

    customers = high_risk_cache if high_risk_cache else _score_direct(consolidated)
    log.info("ScoringAgent COMPLETE in %.2fs (%d iterations)", time.perf_counter() - t0, iteration + 1)
    log.info("=" * 60)
    return {
        "customers": customers,
        "summary": agent_summary or f"ScoringAgent identified {len(customers)} high-risk customers.",
        "agent_mode": "claude",
    }
