"""Loads and parses data from SourceData folder (1000-record aggregated signals)."""
import json
from pathlib import Path
from typing import Any

# SourceData has the aggregated signal data with zero_redemption_flag
DATA_DIR = Path(__file__).parent.parent / "SourceData"


def _load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _index_by(records: list[dict], key: str) -> dict[str, dict]:
    return {r[key]: r for r in records if key in r}


def get_high_risk_customers() -> list[dict]:
    """
    Rule: Enrolled in loyalty platform >= 8 weeks ago AND zero redemptions
    (zero_redemption_flag=True AND weeks_since_enrolment >= 8).
    Returns enriched records cross-referenced from all 6 source files.
    """
    loyalty = _load_json("yotpo_loyalty_1000.json")
    crm = _index_by(_load_json("salesforce_crm_1000.json"), "customer_id")
    klaviyo = _index_by(_load_json("klaviyo_1000.json"), "customer_id")
    shopify = _index_by(_load_json("shopify_1000.json"), "customer_id")
    ga = _index_by(_load_json("google_analytics_1000.json"), "customer_id")
    zendesk = _index_by(_load_json("zendesk_1000.json"), "customer_id")

    high_risk = []
    for rec in loyalty:
        cid = rec.get("customer_id")
        weeks = rec.get("weeks_since_enrolment", 0)
        zero_flag = rec.get("zero_redemption_flag", False)

        if not (zero_flag and weeks >= 8):
            continue

        c = crm.get(cid, {})
        k = klaviyo.get(cid, {})
        s = shopify.get(cid, {})
        g = ga.get(cid, {})
        z = zendesk.get(cid, {})

        high_risk.append({
            "customer_id": cid,
            "loyalty_tier": rec.get("tier", ""),
            "enrollment_date": rec.get("enrolment_date", ""),
            "weeks_enrolled": weeks,
            "points_accrued": rec.get("points_accrued", 0),
            "points_redeemed": rec.get("points_redeemed", 0),
            "last_redemption_date": rec.get("last_redemption_date"),
            "risk_reason": "Enrolled 8+ weeks ago with zero loyalty redemptions",

            # CRM signals
            "account_status": c.get("account_status", ""),
            "segment": c.get("segment", ""),
            "engagement_score": c.get("engagement_score"),
            "last_purchase_days_ago": c.get("last_purchase_days_ago"),
            "crm_churn_flag": c.get("crm_churn_flag"),

            # Email signals
            "email_open_rate_pct": k.get("open_rate_pct"),
            "emails_sent_90d": k.get("emails_sent_90d"),
            "unsubscribed": k.get("unsubscribed"),

            # Purchase signals
            "total_orders": s.get("total_orders"),
            "total_spend_lifetime": s.get("total_spend_lifetime"),
            "avg_order_value": s.get("avg_order_value_now"),
            "last_order_date": s.get("last_order_date"),

            # Web signals
            "sessions_last_30d": g.get("sessions_last_30d"),
            "session_drop_pct": g.get("session_drop_pct"),
            "browsing_intent_collapse": g.get("browsing_intent_collapse_flag"),

            # Support signals
            "unresolved_tickets": z.get("unresolved_tickets"),
            "csat_score": z.get("csat_score"),
        })

    return sorted(high_risk, key=lambda x: x["weeks_enrolled"], reverse=True)


def get_loyalty_summary() -> dict:
    """Summary statistics for the loyalty program."""
    loyalty = _load_json("yotpo_loyalty_1000.json")
    total = len(loyalty)
    zero_redeem = sum(1 for r in loyalty if r.get("zero_redemption_flag"))
    high_risk = sum(1 for r in loyalty if r.get("zero_redemption_flag") and r.get("weeks_since_enrolment", 0) >= 8)
    tiers: dict[str, int] = {}
    for r in loyalty:
        t = r.get("tier", "Unknown")
        tiers[t] = tiers.get(t, 0) + 1
    return {
        "total_accounts": total,
        "zero_redemption_customers": zero_redeem,
        "high_risk_customers": high_risk,
        "tier_breakdown": tiers,
    }
