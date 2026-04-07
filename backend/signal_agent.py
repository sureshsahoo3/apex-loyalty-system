"""
Signal Agent: Uses Claude AI to analyze loyalty data and identify high-risk customers.
Falls back to direct rule-based analysis if ANTHROPIC_API_KEY is not set.
"""
import json
import os
from data_loader import get_high_risk_customers, get_loyalty_summary

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False


TOOLS = [
    {
        "name": "get_high_risk_customers",
        "description": (
            "Retrieve customers enrolled in the loyalty platform 8+ weeks ago "
            "with zero redemptions. Returns enriched customer records including "
            "name, email, tier, enrollment date, points balance, and risk reason."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_loyalty_summary",
        "description": "Get summary statistics about the loyalty program including total accounts, average points, tier breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def _handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_high_risk_customers":
        customers = get_high_risk_customers()
        return json.dumps({"count": len(customers), "customers": customers})

    if tool_name == "get_loyalty_summary":
        return json.dumps(get_loyalty_summary())

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_signal_agent() -> dict:
    """
    Run the signal agent. Uses Claude if API key is available, else direct analysis.
    Returns: { customers: [...], summary: "...", agent_mode: "claude"|"direct" }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key or not _anthropic_available:
        # Direct rule-based analysis
        customers = get_high_risk_customers()
        return {
            "customers": customers,
            "summary": (
                f"Signal Agent identified {len(customers)} high-risk customer(s). "
                "Rule applied: Enrolled in loyalty platform ≥ 8 weeks ago with zero redemptions. "
                "These customers have accumulated loyalty points but never redeemed any rewards, "
                "indicating low engagement and churn risk."
            ),
            "agent_mode": "direct",
        }

    # Claude-powered agent loop
    client = anthropic.Anthropic(api_key=api_key)
    messages = [
        {
            "role": "user",
            "content": (
                "You are the Apex Retail Signal Agent. Your job is to identify high-risk customers "
                "in the loyalty program. Use the available tools to:\n"
                "1. Get the loyalty program summary\n"
                "2. Identify all high-risk customers (enrolled 8+ weeks ago, zero redemptions)\n"
                "3. Provide a brief analysis of why these customers are at risk and what patterns you notice.\n"
                "Return your findings in a structured way."
            ),
        }
    ]

    final_customers = []
    summary_text = ""

    for _ in range(10):  # max iterations
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract text summary from final response
            for block in response.content:
                if hasattr(block, "text"):
                    summary_text = block.text
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                    # Cache high-risk customers from tool call
                    if block.name == "get_high_risk_customers":
                        parsed = json.loads(result)
                        final_customers = parsed.get("customers", [])

            messages.append({"role": "user", "content": tool_results})

    # Fallback if agent didn't call the tool
    if not final_customers:
        final_customers = get_high_risk_customers()

    return {
        "customers": final_customers,
        "summary": summary_text or (
            f"Signal Agent identified {len(final_customers)} high-risk customer(s) "
            "with zero redemptions after 8+ weeks of loyalty enrollment."
        ),
        "agent_mode": "claude",
    }
