"""Plotly chart builders with EventLedger design tokens."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

COLORS = {
    "primary":  "#6366f1",
    "accent":   "#f59e0b",
    "success":  "#10b981",
    "danger":   "#ef4444",
    "warning":  "#f97316",
    "muted":    "#7b7b9a",
    "bg":       "#0f0f13",
    "surface":  "#18181f",
    "surface2": "#22222e",
    "border":   "#2e2e3e",
    "text":     "#e8e8f0",
}

PALETTE = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
           "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#14b8a6"]

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(
        bgcolor="rgba(24,24,31,0.8)",
        bordercolor=COLORS["border"],
        borderwidth=1,
        font=dict(size=11),
    ),
    xaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"],
               tickfont=dict(color=COLORS["muted"], size=11)),
    yaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"],
               tickfont=dict(color=COLORS["muted"], size=11)),
)


def _apply(fig):
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig


# ── Income vs Expense Bar ──────────────────────────────────────────────────

def bar_comparison(categories, estimated, actual, title="Budget vs Actual"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Estimated", x=categories, y=estimated,
        marker_color=COLORS["primary"], opacity=0.8,
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name="Actual", x=categories, y=actual,
        marker_color=COLORS["accent"], opacity=0.9,
        marker_line_width=0,
    ))
    fig.update_layout(barmode="group", title=dict(text=title, font=dict(size=13, color=COLORS["text"])))
    return _apply(fig)


# ── Donut ──────────────────────────────────────────────────────────────────

def donut(labels, values, title=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.6,
        marker=dict(colors=PALETTE, line=dict(width=0)),
        textfont=dict(color="white", size=11),
        hovertemplate="%{label}: <b>%{value:,.0f}</b> (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=COLORS["text"])),
        showlegend=True,
        **{k: v for k, v in LAYOUT_DEFAULTS.items() if k not in ("xaxis", "yaxis")},
    )
    return fig


# ── Line Chart ────────────────────────────────────────────────────────────

def line_chart(x, y_series: dict, title=""):
    fig = go.Figure()
    for i, (name, y) in enumerate(y_series.items()):
        fig.add_trace(go.Scatter(
            x=x, y=y, name=name, mode="lines+markers",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
            marker=dict(size=6),
        ))
    fig.update_layout(title=dict(text=title, font=dict(size=13, color=COLORS["text"])))
    return _apply(fig)


# ── Waterfall ─────────────────────────────────────────────────────────────

def waterfall(labels, values, title="Financial Waterfall"):
    measures = ["relative"] * len(labels)
    fig = go.Figure(go.Waterfall(
        name="", measure=measures, x=labels, y=values,
        connector=dict(line=dict(color=COLORS["border"], dash="dot")),
        increasing=dict(marker_color=COLORS["success"]),
        decreasing=dict(marker_color=COLORS["danger"]),
        totals=dict(marker_color=COLORS["primary"]),
        texttemplate="%{y:,.0f}",
        textposition="outside",
        textfont=dict(color=COLORS["text"]),
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=13, color=COLORS["text"])))
    return _apply(fig)


# ── Department Horizontal Bar ──────────────────────────────────────────────

def dept_bar(dept_names, est_vals, act_vals, colors=None):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Estimated", y=dept_names, x=est_vals, orientation="h",
        marker_color=COLORS["primary"], opacity=0.7, marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name="Actual", y=dept_names, x=act_vals, orientation="h",
        marker_color=COLORS["accent"], opacity=0.9, marker_line_width=0,
    ))
    fig.update_layout(barmode="group", height=max(250, len(dept_names) * 60))
    return _apply(fig)


# ── Gauge / Health Score ──────────────────────────────────────────────────

def health_gauge(score: float):
    color = COLORS["success"] if score >= 75 else (COLORS["warning"] if score >= 50 else COLORS["danger"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="%", font=dict(size=36, color=COLORS["text"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=COLORS["muted"],
                      tickfont=dict(color=COLORS["muted"])),
            bar=dict(color=color, thickness=0.3),
            bgcolor=COLORS["surface2"],
            borderwidth=0,
            steps=[
                dict(range=[0, 50], color="rgba(239,68,68,0.1)"),
                dict(range=[50, 75], color="rgba(249,115,22,0.1)"),
                dict(range=[75, 100], color="rgba(16,185,129,0.1)"),
            ],
            threshold=dict(line=dict(color=color, width=3), thickness=0.75, value=score),
        ),
    ))
    fig.update_layout(
        height=220, margin=dict(l=30, r=30, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
    )
    return fig


# ── Scatter: Sponsor tiers ────────────────────────────────────────────────

def sponsor_scatter(names, tiers, amounts):
    tier_colors = {"Platinum": "#e5e7eb", "Gold": "#fbbf24",
                   "Silver": "#9ca3af", "Bronze": "#b45309"}
    colors = [tier_colors.get(t, COLORS["primary"]) for t in tiers]
    fig = go.Figure(go.Bar(
        x=names, y=amounts,
        marker_color=colors,
        text=[f"${a:,.0f}" for a in amounts],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=10),
    ))
    fig.update_layout(title=dict(text="Sponsor Contributions", font=dict(size=13)))
    return _apply(fig)
