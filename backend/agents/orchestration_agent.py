"""
OrchestrationAgent: Reads all data from SourceDataV1 and SourceData folders,
consolidates them into one unified source of truth per customer.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from logger import get_logger

log = get_logger("OrchestrationAgent")

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False

ROOT        = Path(__file__).parent.parent.parent
DATA_V1_DIR = ROOT / "SourceDataV1"
DATA_DIR    = ROOT / "SourceData"


# ── Raw loaders ───────────────────────────────────────────────────────────────

def _load(path: Path) -> Any:
    log.debug("Loading file: %s", path.name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_sourcedatav1() -> dict[str, dict]:
    """Load SourceDataV1 (100 detailed customers) keyed by customer_id."""
    log.info("Reading SourceDataV1 — 6 source files")

    yotpo   = {a["customer_id"]: a for a in _load(DATA_V1_DIR / "yotpo_loyalty_mock.json")["yotpo_system"]["loyalty_accounts"]}
    log.debug("  yotpo_loyalty_mock.json    -> %d loyalty accounts", len(yotpo))

    crm     = {c["customer_id"]: c for c in _load(DATA_V1_DIR / "crm_retail_mock.json")["crm_system"]["customers"]}
    log.debug("  crm_retail_mock.json       -> %d CRM records", len(crm))

    klaviyo = {p["customer_id"]: p for p in _load(DATA_V1_DIR / "klaviyo_marketing_mock.json")["klaviyo_system"]["profiles"]}
    log.debug("  klaviyo_marketing_mock.json-> %d email profiles", len(klaviyo))

    shopify_list = _load(DATA_V1_DIR / "shopify_retail_mock.json")["shopify_store"]["customers"]["customers"]
    shopify      = {c["id"]: c for c in shopify_list}
    shopify_by_email = {c["email"]: c for c in shopify.values()}
    log.debug("  shopify_retail_mock.json   -> %d customers", len(shopify))

    raw_tickets = _load(DATA_V1_DIR / "support_system_mock.json")["support_system"]["tickets"]
    support_tickets: dict[str, list] = {}
    for t in raw_tickets:
        support_tickets.setdefault(t["customer_id"], []).append(t)
    log.debug("  support_system_mock.json   -> %d tickets across %d customers", len(raw_tickets), len(support_tickets))

    ga = {u["customer_id"]: u for u in _load(DATA_V1_DIR / "google_analytics_mock.json")["google_analytics"]["user_sessions"]}
    log.debug("  google_analytics_mock.json -> %d user sessions", len(ga))

    unified: dict[str, dict] = {}
    for cid, y in yotpo.items():
        c  = crm.get(cid, {})
        k  = klaviyo.get(cid, {})
        email = y.get("email", c.get("personal_info", {}).get("email", ""))
        sh = shopify_by_email.get(email, {})
        g  = ga.get(cid, {})
        tickets = support_tickets.get(cid, [])
        personal = c.get("personal_info", {})
        account  = c.get("account", {})

        unified[cid] = {
            "customer_id": cid,
            "source": "SourceDataV1",
            "name": f"{personal.get('first_name','')} {personal.get('last_name','')}".strip() or sh.get("first_name", ""),
            "email": email,
            "phone": personal.get("phone", sh.get("phone", "")),
            "loyalty_tier": y.get("tier", ""),
            "enrollment_date": y.get("enrollment_date", ""),
            "points_balance": y.get("points", {}).get("balance", 0),
            "lifetime_earned": y.get("points", {}).get("lifetime_earned", 0),
            "redeemed_total": y.get("points", {}).get("redeemed_total", 0),
            "redemption_count": len(y.get("redemption_history", [])),
            "last_redemption_date": (y.get("redemption_history") or [{}])[-1].get("date"),
            "account_status": account.get("status", ""),
            "loyalty_points_crm": account.get("loyalty_points", 0),
            "preferred_channel": account.get("preferred_channel", ""),
            "email_consent": k.get("email_marketing_consent", {}).get("state", ""),
            "email_segments": k.get("segments", []),
            "notification_count": len(k.get("notification_history", [])),
            "total_orders": sh.get("orders_count", 0),
            "total_spend": float(sh.get("total_spent", 0)),
            "avg_order_value": float(sh.get("average_order_value", 0)),
            "shopify_tags": sh.get("tags", ""),
            "open_tickets": sum(1 for t in tickets if t.get("status") == "Open"),
            "total_tickets": len(tickets),
            "session_count": len(g.get("sessions", [])),
        }

    log.info("SourceDataV1 consolidation complete -> %d unified customer profiles", len(unified))
    return unified


def _read_sourcedata() -> dict[str, dict]:
    """Load SourceData (1000 aggregated signal customers) keyed by customer_id."""
    log.info("Reading SourceData — 6 aggregated signal files")

    def load_list(fname: str) -> dict[str, dict]:
        data = {r["customer_id"]: r for r in _load(DATA_DIR / fname)}
        log.debug("  %-38s -> %d records", fname, len(data))
        return data

    yotpo   = load_list("yotpo_loyalty_1000.json")
    crm     = load_list("salesforce_crm_1000.json")
    klaviyo = load_list("klaviyo_1000.json")
    shopify = load_list("shopify_1000.json")
    ga      = load_list("google_analytics_1000.json")
    zendesk = load_list("zendesk_1000.json")

    unified: dict[str, dict] = {}
    for cid, y in yotpo.items():
        c = crm.get(cid, {})
        k = klaviyo.get(cid, {})
        s = shopify.get(cid, {})
        g = ga.get(cid, {})
        z = zendesk.get(cid, {})
        unified[cid] = {
            "customer_id": cid,
            "source": "SourceData",
            "name": "", "email": "", "phone": "",
            "loyalty_tier": y.get("tier", ""),
            "enrollment_date": y.get("enrolment_date", ""),
            "weeks_since_enrollment": y.get("weeks_since_enrolment", 0),
            "points_accrued": y.get("points_accrued", 0),
            "redeemed_total": y.get("points_redeemed", 0),
            "zero_redemption_flag": y.get("zero_redemption_flag", False),
            "last_redemption_date": y.get("last_redemption_date"),
            "referrals_made": y.get("referrals_made", 0),
            "account_status": c.get("account_status", ""),
            "segment": c.get("segment", ""),
            "engagement_score": c.get("engagement_score"),
            "last_purchase_days_ago": c.get("last_purchase_days_ago"),
            "crm_churn_flag": c.get("crm_churn_flag"),
            "email_open_rate_pct": k.get("open_rate_pct"),
            "emails_sent_90d": k.get("emails_sent_90d"),
            "unsubscribed": k.get("unsubscribed"),
            "total_orders": s.get("total_orders"),
            "total_spend": s.get("total_spend_lifetime"),
            "avg_order_value": s.get("avg_order_value_now"),
            "last_order_date": s.get("last_order_date"),
            "sessions_last_30d": g.get("sessions_last_30d"),
            "session_drop_pct": g.get("session_drop_pct"),
            "browsing_intent_collapse": g.get("browsing_intent_collapse_flag"),
            "unresolved_tickets": z.get("unresolved_tickets"),
            "csat_score": z.get("csat_score"),
        }

    log.info("SourceData consolidation complete -> %d unified customer records", len(unified))
    return unified


# ── Direct consolidation (no Claude) ─────────────────────────────────────────

def consolidate_direct() -> dict:
    """Merge SourceDataV1 + SourceData into one source of truth."""
    log.info("Starting direct consolidation (Rule Engine mode)")
    t0 = time.perf_counter()
    v1 = _read_sourcedatav1()
    sd = _read_sourcedata()
    elapsed = time.perf_counter() - t0
    log.info(
        "Consolidation complete in %.2fs — total %d customers "
        "(%d SourceDataV1 + %d SourceData)",
        elapsed, len(v1) + len(sd), len(v1), len(sd),
    )
    return {
        "v1_customers": list(v1.values()),
        "sd_customers": list(sd.values()),
        "total_customers": len(v1) + len(sd),
        "sources": ["SourceDataV1", "SourceData"],
    }


# ── Agent tools ───────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "load_sourcedatav1",
        "description": "Load and consolidate all 6 files from SourceDataV1 folder (yotpo, crm, shopify, klaviyo, ga, support) into unified customer profiles. Returns 100 detailed customer records.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "load_sourcedata",
        "description": "Load and consolidate all 6 aggregated signal files from SourceData folder. Returns 1000 customer signal records.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _handle_tool(name: str) -> str:
    log.info("Tool called: %s", name)
    if name == "load_sourcedatav1":
        data = _read_sourcedatav1()
        log.info("Tool result: load_sourcedatav1 -> %d records", len(data))
        return json.dumps({"count": len(data), "sample": list(data.values())[:2]})
    if name == "load_sourcedata":
        data = _read_sourcedata()
        log.info("Tool result: load_sourcedata -> %d records", len(data))
        return json.dumps({"count": len(data), "sample": list(data.values())[:2]})
    log.warning("Unknown tool requested: %s", name)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Public entry point ────────────────────────────────────────────────────────

def run(api_key: str | None = None) -> dict:
    """Run the OrchestrationAgent. Returns consolidated data + agent summary."""
    log.info("=" * 60)
    log.info("OrchestrationAgent STARTED")
    mode = "Claude AI" if (api_key and _anthropic_available) else "Rule Engine (direct)"
    log.info("Mode: %s", mode)
    t0 = time.perf_counter()

    consolidated = consolidate_direct()

    if not api_key or not _anthropic_available:
        if not api_key:
            log.warning("ANTHROPIC_API_KEY not set — running in Rule Engine mode")
        summary = (
            f"OrchestrationAgent consolidated {consolidated['total_customers']} customers "
            f"from {len(consolidated['sources'])} data sources "
            f"({len(consolidated['v1_customers'])} detailed SourceDataV1 profiles + "
            f"{len(consolidated['sd_customers'])} SourceData signal records)."
        )
        consolidated["agent_summary"] = summary
        consolidated["agent_mode"] = "direct"
        log.info("OrchestrationAgent COMPLETE in %.2fs", time.perf_counter() - t0)
        log.info("=" * 60)
        return consolidated

    # Claude AI agent loop
    log.info("Initialising Claude AI agent loop (model: claude-opus-4-6)")
    client = anthropic.Anthropic(api_key=api_key)
    messages = [{
        "role": "user",
        "content": (
            "You are the Apex Retail OrchestrationAgent. "
            "Load and consolidate all customer data from the available data sources. "
            "Use the tools to load SourceDataV1 (detailed) and SourceData (aggregated signals). "
            "Then provide a brief summary of what you consolidated and any data quality observations."
        )
    }]

    agent_summary = ""
    iteration = 0
    for iteration in range(8):
        log.info("Agent iteration %d — sending request to Claude", iteration + 1)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            tools=TOOLS,
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
                        "content": _handle_tool(block.name),
                    })
            messages.append({"role": "user", "content": results})

    consolidated["agent_summary"] = agent_summary or (
        f"Consolidated {consolidated['total_customers']} customers from "
        f"{len(consolidated['sources'])} sources."
    )
    consolidated["agent_mode"] = "claude"
    log.info("OrchestrationAgent COMPLETE in %.2fs (%d iterations)", time.perf_counter() - t0, iteration + 1)
    log.info("=" * 60)
    return consolidated
