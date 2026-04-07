"""High-level architecture diagram — Apex Loyalty AI Agent Retention Solution."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(16, 8))
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis("off")
fig.patch.set_facecolor("#0d0f1a")

# ── Helpers ──────────────────────────────────────────────────────────
def card(x, y, w, h, fc="#12152a", ec="#1e2440", lw=2, r=0.25):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))

def t(x, y, s, sz=10, c="#e2e8f0", w="normal", ha="center", va="center"):
    ax.text(x, y, s, fontsize=sz, color=c, fontweight=w, ha=ha, va=va, zorder=5)

def arrow(x1, y1, x2, y2, col="#4b5563", lw=2.5, label="", label_y_off=0.3):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, mutation_scale=20),
        zorder=4)
    if label:
        t((x1+x2)/2, (y1+y2)/2 + label_y_off, label, sz=8, c=col)

# ── Colours ───────────────────────────────────────────────────────────
BG     = "#0d0f1a"
BLUE   = "#38bdf8"
GREEN  = "#22c55e"
AMBER  = "#f59e0b"
INDIGO = "#6366f1"
PINK   = "#e11d48"
RED    = "#ef4444"
MUTED  = "#64748b"
WHITE  = "#ffffff"

# ════════════════════════════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════════════════════════════
t(8, 7.62, "Apex Retail — AI Agent Retention Solution", sz=16, c=WHITE, w="bold")
t(8, 7.25, "High-Level Architecture", sz=10, c=MUTED)

# ════════════════════════════════════════════════════════════════════
# FIVE COMPONENT BOXES
# Each: width=2.4, height=4.0, top y=6.8, label strip + body
# Centres at x = 1.5, 4.3, 7.1, 9.9, 12.7 ... gap of 0.5
# ════════════════════════════════════════════════════════════════════
BW, BH = 2.4, 4.2
BY = 1.7

boxes = [
    # cx,   title,             color,  body lines
    (1.50,  "Data Sources",    BLUE,   ["SourceDataV1", "6 files / 100 customers", "", "SourceData", "6 files / 1,000 customers", "", "JSON mock data"]),
    (4.30,  "Orchestration",   GREEN,  ["OrchestrationAgent", "(Python)", "", "Reads all source files", "Merges into one", "unified dataset", "1,100 customers"]),
    (7.10,  "Scoring",         AMBER,  ["ScoringAgent", "(Python + Claude AI)", "", "Rule: 8+ wks enrolled", "zero redemptions", "= HIGH RISK", "255 customers flagged"]),
    (9.90,  "API Layer",       INDIGO, ["FastAPI", "(Python)", "", "GET /health", "GET /api/high-risk-customers", "", "localhost : 8080"]),
    (12.70, "UI",              PINK,   ["Angular", "(TypeScript)", "", "High-risk table", "Tier / Risk filters", "Sortable columns", "localhost : 4200"]),
]

for cx, title, col, lines in boxes:
    bx = cx - BW/2
    # card
    card(bx, BY, BW, BH, fc=col + "15", ec=col, lw=2.5, r=0.3)
    # header strip
    card(bx, BY + BH - 0.55, BW, 0.55, fc=col + "40", ec=col, lw=0, r=0.25)
    t(cx, BY + BH - 0.27, title, sz=10, c=WHITE, w="bold")
    # body lines
    line_h = 0.38
    start_y = BY + BH - 0.9
    for i, line in enumerate(lines):
        if line == "":
            continue
        lc = col if i == 0 else ("#94a3b8" if not line.startswith("(") else MUTED)
        t(cx, start_y - i * line_h, line, sz=8, c=lc)

# ════════════════════════════════════════════════════════════════════
# ARROWS
# ════════════════════════════════════════════════════════════════════
ay = BY + BH / 2
gap = 0.14

arrow(1.50 + BW/2 + gap, ay, 4.30 - BW/2 - gap, ay, col=BLUE,   label="reads all files")
arrow(4.30 + BW/2 + gap, ay, 7.10 - BW/2 - gap, ay, col=GREEN,  label="unified data")
arrow(7.10 + BW/2 + gap, ay, 9.90 - BW/2 - gap, ay, col=AMBER,  label="scored results")
arrow(9.90 + BW/2 + gap, ay, 12.70 - BW/2 - gap, ay, col=INDIGO, label="JSON response")

# ════════════════════════════════════════════════════════════════════
# OUTPUT BADGE on Scoring box
# ════════════════════════════════════════════════════════════════════
card(7.10 - 1.0, BY + 0.08, 2.0, 0.5, fc="#3b0f0f", ec=RED, lw=1.5, r=0.15)
t(7.10, BY + 0.33, "255 High-Risk Customers", sz=8, c="#f87171", w="bold")

# ════════════════════════════════════════════════════════════════════
# BOTTOM RULE BAR
# ════════════════════════════════════════════════════════════════════
card(1.5, 0.12, 13.0, 0.52, fc="#0a0810", ec=INDIGO, lw=1.5, r=0.15)
t(8.0, 0.38, "Scoring Rule:   enrollment_date >= 8 weeks ago   AND   points_redeemed == 0   =>   HIGH RISK", sz=9, c="#94a3b8")

# ════════════════════════════════════════════════════════════════════
# AGENT MODE NOTE (top-right corner)
# ════════════════════════════════════════════════════════════════════
card(13.2, 6.7, 2.6, 0.85, fc="#0a0810", ec=INDIGO, lw=1.2, r=0.15)
t(14.5, 7.33, "Agent Mode", sz=8, c="#c7d2fe", w="bold")
t(14.5, 7.1,  "Claude AI  (if API key set)", sz=7.5, c=GREEN)
t(14.5, 6.9,  "Rule Engine (fallback)", sz=7.5, c=AMBER)

plt.tight_layout(pad=0.2)
out = "architecture_diagram_simple.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor=BG, edgecolor="none")
print(f"Saved: {out}")
