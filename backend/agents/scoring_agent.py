"""
ScoringAgent: Reads output from OrchestrationAgent and applies the
high-risk scoring rule:
  - Customer enrolled in loyalty platform >= 8 weeks ago but zero redemptions
"""
import json
import os
from typing import Any

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False


# ── Direct scoring (no Claude) ────────────────────────────────────────────────

def _score_direct(consolidated: dict) -> list[dict]:
    """
    Apply the rule to consolidated data and return high-risk customers.
    Rule: enrolled >= 8 weeks ago AND zero redemptions (redeemed_total == 0 or zero_redemption_flag).
    """
    high_risk = []

    # Score SourceData customers (1000 records with explicit zero_redemption_flag)
    for c in consolidated.get("sd_customers", []):
        weeks = c.get("weeks_since_enrollment", 0)
        zero_flag = c.get("zero_redemption_flag", False)
        redeemed = c.get("redeemed_total", -1)

        if weeks >= 8 and (zero_flag or redeemed == 0):
            risk_score = _compute_risk_score(c)
            high_risk.append({**c, "risk_score": risk_score, "risk_level": _risk_level(risk_score)})

    # Score SourceDataV1 customers (100 detailed records)
    for c in consolidated.get("v1_customers", []):
        redeemed = c.get("redeemed_total", -1)
        enrollment_date = c.get("enrollment_date", "")

        if enrollment_date and redeemed == 0:
            from datetime import datetime, timezone
            try:
                enrolled_dt = datetime.fromisoformat(enrollment_date.replace("Z", "+00:00"))
                weeks = (datetime.now(timezone.utc) - enrolled_dt).total_seconds() / (7 * 24 * 3600)
                if weeks >= 8:
                    risk_score = _compute_risk_score(c)
                    high_risk.append({**c, "weeks_since_enrollment": round(weeks, 1),
                                      "risk_score": risk_score, "risk_level": _risk_level(risk_score)})
            except ValueError:
                pass

    return sorted(high_risk, key=lambda x: x.get("weeks_since_enrollment", 0), reverse=True)


def _compute_risk_score(c: dict) -> int:
    """Higher score = higher churn risk."""
    score = 0
    if c.get("crm_churn_flag"):            score += 3
    if c.get("unsubscribed"):              score += 2
    if (c.get("session_drop_pct") or 0) > 50: score += 2
    if (c.get("unresolved_tickets") or 0) > 0: score += 1
    if c.get("browsing_intent_collapse"):  score += 1
    if (c.get("email_open_rate_pct") or 100) < 10: score += 1
    if (c.get("last_purchase_days_ago") or 0) > 60: score += 1
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
                "Apply the high-risk scoring rule to the consolidated customer data: "
                "customers enrolled >= 8 weeks ago with zero loyalty redemptions. "
                "Returns the list of high-risk customers with their risk score and level."
            ),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_risk_distribution",
            "description": "Get the breakdown of high-risk customers by tier, segment, and risk level.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
    ]


def _handle_tool(name: str, consolidated: dict, high_risk_cache: list) -> str:
    if name == "apply_zero_redemption_rule":
        customers = _score_direct(consolidated)
        high_risk_cache.clear()
        high_risk_cache.extend(customers)
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
        return json.dumps({"total": len(customers), "by_tier": tiers, "by_risk_level": levels})

    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Public entry point ────────────────────────────────────────────────────────

def run(consolidated: dict, api_key: str | None = None) -> dict:
    """
    Run the ScoringAgent on consolidated data.
    Returns: { customers, summary, agent_mode }
    """
    if not api_key or not _anthropic_available:
        customers = _score_direct(consolidated)
        return {
            "customers": customers,
            "summary": (
                f"ScoringAgent identified {len(customers)} high-risk customers. "
                "Rule: enrolled in loyalty program 8+ weeks ago with zero redemptions. "
                f"Risk breakdown — "
                f"Critical: {sum(1 for c in customers if c['risk_level']=='critical')}, "
                f"High: {sum(1 for c in customers if c['risk_level']=='high')}, "
                f"Medium: {sum(1 for c in customers if c['risk_level']=='medium')}."
            ),
            "agent_mode": "direct",
        }

    client = anthropic.Anthropic(api_key=api_key)
    high_risk_cache: list = []
    tools = _make_tools(consolidated)

    messages = [{
        "role": "user",
        "content": (
            "You are the Apex Retail ScoringAgent. "
            "The OrchestrationAgent has consolidated customer data. "
            "Your job is to:\n"
            "1. Apply the zero-redemption scoring rule to identify high-risk customers\n"
            "2. Get the risk distribution breakdown\n"
            "3. Provide a brief analysis and retention recommendations\n"
            "Rule: customers enrolled >= 8 weeks ago with zero loyalty redemptions are HIGH RISK."
        )
    }]

    agent_summary = ""
    for _ in range(10):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    agent_summary = block.text
            break

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": _handle_tool(block.name, consolidated, high_risk_cache),
                    })
            messages.append({"role": "user", "content": results})

    customers = high_risk_cache if high_risk_cache else _score_direct(consolidated)
    return {
        "customers": customers,
        "summary": agent_summary or f"ScoringAgent identified {len(customers)} high-risk customers.",
        "agent_mode": "claude",
    }
