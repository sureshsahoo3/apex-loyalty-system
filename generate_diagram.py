"""Generate architecture diagram for Apex Loyalty AI Agent Retention Solution."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(18, 11))
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis("off")
fig.patch.set_facecolor("#0d0f1a")
ax.set_facecolor("#0d0f1a")

# ── Colour palette ──────────────────────────────────────────────────
C_BG      = "#0d0f1a"
C_CARD    = "#12152a"
C_BORDER  = "#1e2440"
C_INDIGO  = "#6366f1"
C_INDIGO2 = "#818cf8"
C_GREEN   = "#22c55e"
C_AMBER   = "#f59e0b"
C_RED     = "#ef4444"
C_ORANGE  = "#fb923c"
C_BLUE    = "#38bdf8"
C_TEXT    = "#e2e8f0"
C_MUTED   = "#64748b"
C_BORDER2 = "#252b45"

def card(x, y, w, h, color=C_CARD, border=C_BORDER, radius=0.25, lw=1.5):
    rect = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=border, linewidth=lw, zorder=2)
    ax.add_patch(rect)

def label(x, y, text, size=9, color=C_TEXT, weight="normal", ha="center", va="center"):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=5, fontfamily="monospace")

def arrow(x1, y1, x2, y2, color=C_MUTED, lw=1.5, style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color,
                        lw=lw, connectionstyle="arc3,rad=0.0"),
        zorder=4)

def section_header(x, y, w, text, color=C_INDIGO):
    card(x, y, w, 0.45, color=color, border=color, radius=0.15, lw=0)
    label(x + w/2, y + 0.22, text, size=8, color="#fff", weight="bold")

# ══════════════════════════════════════════════════════════════════════
# Title
# ══════════════════════════════════════════════════════════════════════
ax.text(9, 10.55, "Apex Retail — AI Agent Retention Solution",
        fontsize=16, color=C_TEXT, fontweight="bold", ha="center", va="center",
        fontfamily="sans-serif", zorder=5)
ax.text(9, 10.15, "Architecture Diagram",
        fontsize=11, color=C_MUTED, ha="center", va="center", zorder=5)

# ══════════════════════════════════════════════════════════════════════
# Layer 1 — Data Sources
# ══════════════════════════════════════════════════════════════════════
section_header(0.5, 8.55, 7.5, "  DATA SOURCES  (SourceDataV1 + SourceData)", color="#1e3a5f")
card(0.5, 6.8, 7.5, 1.65, border="#1e3a5f", radius=0.2)

files_v1 = [
    ("yotpo_loyalty_mock.json",     "Loyalty / Redemptions",   C_BLUE),
    ("crm_retail_mock.json",        "CRM / Customers",         C_GREEN),
    ("shopify_retail_mock.json",    "Shopify / Orders",        C_AMBER),
    ("klaviyo_marketing_mock.json", "Klaviyo / Email",         C_ORANGE),
    ("google_analytics_mock.json",  "GA / Sessions",           C_RED),
    ("support_system_mock.json",    "Support / Tickets",       C_INDIGO2),
]
col_w = 1.15
for i, (fname, desc, col) in enumerate(files_v1):
    cx = 0.65 + i * col_w
    card(cx, 7.0, 1.05, 1.2, color="#0d1a2e", border=col, radius=0.15, lw=1.2)
    ax.text(cx + 0.525, 7.8, "V1", fontsize=6.5, color=col, ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(cx + 0.525, 7.55, fname.replace("_mock","").replace(".json",""),
            fontsize=6, color="#94a3b8", ha="center", va="center", zorder=5)
    ax.text(cx + 0.525, 7.25, desc, fontsize=6.5, color=C_TEXT, ha="center", va="center",
            fontweight="bold", zorder=5)

# SourceData label
ax.text(8.2, 7.5, "SourceData\n(1000 records)", fontsize=7.5, color=C_MUTED,
        ha="center", va="center", zorder=5)

# ══════════════════════════════════════════════════════════════════════
# Layer 2 — OrchestrationAgent
# ══════════════════════════════════════════════════════════════════════
section_header(0.5, 5.75, 7.5, "  ORCHESTRATION AGENT  (Python + Claude AI)", color="#1a2a1a")
card(0.5, 4.25, 7.5, 1.4, border="#22c55e", radius=0.2, lw=1.5)

card(0.75, 4.4, 3.0, 1.05, color="#0d1a0d", border="#22c55e", radius=0.15, lw=1)
label(2.25, 5.1, "orchestration_agent.py", size=8, color=C_GREEN, weight="bold")
label(2.25, 4.83, "Reads all 6 files from SourceDataV1", size=7, color=C_MUTED)
label(2.25, 4.63, "Consolidates into unified customer view", size=7, color=C_MUTED)

card(4.0, 4.4, 1.7, 1.05, color="#0a0a1a", border=C_INDIGO, radius=0.15, lw=1)
label(4.85, 5.1, "Claude AI", size=8, color=C_INDIGO2, weight="bold")
label(4.85, 4.83, "Tool: load_sourcedatav1", size=6.5, color=C_MUTED)
label(4.85, 4.63, "Tool: load_sourcedata", size=6.5, color=C_MUTED)

card(5.9, 4.4, 1.9, 1.05, color="#1a150a", border=C_AMBER, radius=0.15, lw=1)
label(6.85, 5.1, "Output", size=8, color=C_AMBER, weight="bold")
label(6.85, 4.83, "1,100 unified", size=7, color=C_MUTED)
label(6.85, 4.63, "customer records", size=7, color=C_MUTED)

# ══════════════════════════════════════════════════════════════════════
# Layer 3 — ScoringAgent
# ══════════════════════════════════════════════════════════════════════
section_header(0.5, 2.9, 7.5, "  SCORING AGENT  (Python + Claude AI)", color="#2a1a0a")
card(0.5, 1.4, 7.5, 1.4, border=C_ORANGE, radius=0.2, lw=1.5)

card(0.75, 1.55, 3.0, 1.05, color="#1a0d00", border=C_ORANGE, radius=0.15, lw=1)
label(2.25, 2.25, "scoring_agent.py", size=8, color=C_ORANGE, weight="bold")
label(2.25, 1.98, "Rule: enrolled 8+ weeks + zero redemptions", size=6.8, color=C_MUTED)
label(2.25, 1.78, "Computes risk_score per customer", size=7, color=C_MUTED)

card(4.0, 1.55, 1.7, 1.05, color="#0a0a1a", border=C_INDIGO, radius=0.15, lw=1)
label(4.85, 2.25, "Claude AI", size=8, color=C_INDIGO2, weight="bold")
label(4.85, 1.98, "Tool: apply_rule", size=6.5, color=C_MUTED)
label(4.85, 1.78, "Tool: get_distribution", size=6.5, color=C_MUTED)

card(5.9, 1.55, 1.9, 1.05, color="#1a0d00", border=C_RED, radius=0.15, lw=1)
label(6.85, 2.25, "255 High-Risk", size=8, color=C_RED, weight="bold")
label(6.85, 1.98, "Critical: 52", size=6.5, color="#f87171")
label(6.85, 1.78, "High: 119  Med: 84", size=6.5, color=C_MUTED)

# ══════════════════════════════════════════════════════════════════════
# Layer 4 — FastAPI Backend
# ══════════════════════════════════════════════════════════════════════
card(9.0, 6.5, 4.0, 3.3, color=C_CARD, border=C_INDIGO, radius=0.25, lw=1.8)
section_header(9.0, 9.35, 4.0, "  FASTAPI BACKEND  :8080", color=C_INDIGO)

card(9.2, 8.55, 3.6, 0.65, color="#0d0f20", border=C_BORDER2, radius=0.12, lw=1)
label(11.0, 8.88, "GET /health", size=8, color=C_GREEN, weight="bold")

card(9.2, 7.75, 3.6, 0.65, color="#0d0f20", border=C_INDIGO2, radius=0.12, lw=1)
label(11.0, 8.08, "GET /api/high-risk-customers", size=8, color=C_INDIGO2, weight="bold")
label(11.0, 7.88, "Runs full 2-agent pipeline", size=6.5, color=C_MUTED)

card(9.2, 6.65, 3.6, 0.95, color="#0d0f20", border=C_BORDER2, radius=0.12, lw=1)
label(11.0, 7.2, "CORS: localhost:4200", size=7, color=C_MUTED)
label(11.0, 6.97, "python-dotenv  •  ANTHROPIC_API_KEY", size=6.5, color=C_MUTED)
label(11.0, 6.77, ".env  →  Claude AI mode", size=6.5, color=C_AMBER)

# ══════════════════════════════════════════════════════════════════════
# Layer 5 — Angular UI
# ══════════════════════════════════════════════════════════════════════
card(14.0, 6.5, 3.6, 3.3, color=C_CARD, border="#e11d48", radius=0.25, lw=1.8)
section_header(14.0, 9.35, 3.6, "  ANGULAR UI  :4200", color="#be123c")

card(14.15, 8.55, 3.3, 0.65, color="#1a0a12", border="#e11d48", radius=0.12, lw=1)
label(15.8, 8.88, "High-Risk Customer Table", size=8, color="#fb7185", weight="bold")

card(14.15, 7.75, 3.3, 0.65, color="#1a0a12", border="#be123c", radius=0.12, lw=1)
label(15.8, 8.08, "Filter by Tier / Risk Level", size=7.5, color=C_MUTED)
label(15.8, 7.88, "Sortable columns + Search", size=7.5, color=C_MUTED)

card(14.15, 6.65, 3.3, 0.95, color="#1a0a12", border="#7f1d1d", radius=0.12, lw=1)
label(15.8, 7.22, "Agent Pipeline Status", size=7.5, color=C_MUTED)
label(15.8, 6.99, "OrchestrationAgent summary", size=6.5, color=C_MUTED)
label(15.8, 6.79, "ScoringAgent summary", size=6.5, color=C_MUTED)

# ══════════════════════════════════════════════════════════════════════
# Rule box (right side)
# ══════════════════════════════════════════════════════════════════════
card(9.0, 1.2, 8.6, 5.1, color="#100d1a", border=C_INDIGO, radius=0.2, lw=1.2)
section_header(9.0, 5.85, 8.6, "  SCORING RULE  &  RISK MODEL", color="#3730a3")

label(13.3, 5.35, "High-Risk Condition", size=9, color=C_TEXT, weight="bold")
card(9.2, 4.8, 8.2, 0.45, color="#0d0a20", border=C_INDIGO2, radius=0.1, lw=1)
label(13.3, 5.03, "enrollment_date >= 8 weeks ago  AND  points_redeemed == 0", size=8.5, color=C_INDIGO2, weight="bold")

label(13.3, 4.45, "Risk Score Signals", size=9, color=C_TEXT, weight="bold")

signals = [
    ("crm_churn_flag = True",       "+3", C_RED),
    ("unsubscribed = True",          "+2", C_ORANGE),
    ("session_drop_pct > 50%",      "+2", C_AMBER),
    ("unresolved_tickets > 0",      "+1", C_ORANGE),
    ("browsing_intent_collapse",    "+1", C_AMBER),
    ("email_open_rate < 10%",       "+1", C_MUTED),
    ("last_purchase > 60 days ago", "+1", C_MUTED),
]
cols = [(9.2, 12.1), (12.3, 15.2), (15.4, 17.8)]
for i, (sig, pts, col) in enumerate(signals):
    ci = i % 3
    row = i // 3
    cx0, cx1 = cols[ci]
    cy = 4.05 - row * 0.52
    card(cx0, cy - 0.2, cx1 - cx0 - 0.1, 0.38, color="#0a0810", border=col, radius=0.08, lw=1)
    ax.text(cx0 + 0.12, cy + 0.0, sig, fontsize=7, color=C_MUTED, va="center", zorder=5, fontfamily="monospace")
    ax.text(cx1 - 0.22, cy + 0.0, pts, fontsize=8, color=col, va="center", ha="right", fontweight="bold", zorder=5)

label(13.3, 2.4, "Risk Levels", size=9, color=C_TEXT, weight="bold")
lvls = [("score >= 6", "Critical", C_RED, 9.2), ("score >= 3", "High", C_ORANGE, 11.5), ("score < 3", "Medium", "#facc15", 13.8)]
for expr, name, col, bx in lvls:
    card(bx, 1.9, 2.1, 0.42, color="#0a0810", border=col, radius=0.1, lw=1.2)
    label(bx + 1.05, 2.11, f"{name}  ({expr})", size=7.5, color=col, weight="bold")

# ══════════════════════════════════════════════════════════════════════
# Arrows between layers
# ══════════════════════════════════════════════════════════════════════
# Data → OrchestrationAgent
arrow(4.25, 6.8, 4.25, 5.65, color=C_BLUE, lw=2)
ax.text(4.65, 6.25, "reads all\n6 files", fontsize=6.5, color=C_MUTED, ha="left", va="center", zorder=5)

# OrchestrationAgent → ScoringAgent
arrow(4.25, 4.25, 4.25, 2.8, color=C_AMBER, lw=2)
ax.text(4.65, 3.55, "unified\ndata", fontsize=6.5, color=C_MUTED, ha="left", va="center", zorder=5)

# ScoringAgent → FastAPI
arrow(8.0, 2.3, 9.0, 7.8, color=C_INDIGO2, lw=1.8)
ax.text(8.3, 5.0, "results", fontsize=6.5, color=C_MUTED, ha="left", va="center", zorder=5)

# FastAPI → Angular
arrow(13.0, 7.8, 14.0, 7.8, color=C_GREEN, lw=2)
ax.text(13.2, 8.05, "JSON API", fontsize=7, color=C_GREEN, ha="center", va="center", zorder=5)

# ══════════════════════════════════════════════════════════════════════
# Legend — Agent mode
# ══════════════════════════════════════════════════════════════════════
card(0.5, 0.15, 8.0, 1.05, color="#0a0a1a", border=C_INDIGO, radius=0.15, lw=1)
label(1.5, 0.9, "Agent Mode:", size=8, color=C_TEXT, weight="bold", ha="left")
card(2.5, 0.72, 2.8, 0.35, color="#0d0f20", border=C_GREEN, radius=0.08)
label(3.9, 0.9, "ANTHROPIC_API_KEY set  ->  Claude AI (tool-use loop)", size=7.5, color=C_GREEN)
card(2.5, 0.3, 2.8, 0.35, color="#0d0f20", border=C_AMBER, radius=0.08)
label(3.9, 0.48, "No API key             ->  Direct rule-based engine", size=7.5, color=C_AMBER)

card(9.0, 0.15, 8.6, 1.05, color="#0a0a1a", border=C_BORDER, radius=0.15, lw=1)
label(9.2, 0.9, "Tech Stack:", size=8, color=C_TEXT, weight="bold", ha="left")
stack = [("Python 3.13", C_BLUE), ("FastAPI", C_GREEN), ("Anthropic SDK", C_INDIGO2),
         ("Angular 21", "#e11d48"), ("TypeScript", C_BLUE)]
for i, (name, col) in enumerate(stack):
    card(9.2 + i * 1.65, 0.3, 1.5, 0.45, color="#0d0f20", border=col, radius=0.08)
    label(9.2 + i * 1.65 + 0.75, 0.52, name, size=7, color=col, weight="bold")

plt.tight_layout(pad=0)
out = "architecture_diagram.png"
plt.savefig(out, dpi=220, bbox_inches="tight", facecolor=C_BG, edgecolor="none")
print(f"Saved: {out}")
