"""EventLedger AI – Analytics (native Streamlit)"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import get_events, get_event_summary
from utils.charts import bar_comparison, donut, waterfall, COLORS, PALETTE, LAYOUT_DEFAULTS
from components.ui import section_header, empty_state
from utils.currency import get_symbol, get_global_currency


def show(user):
    st.title("📈 Analytics")
    st.caption("Cross-event financial performance & trends")
    st.divider()

    events = get_events(user["id"])
    sym = get_symbol()
    if not events:
        empty_state("📈","No events to analyze","Create events to see analytics."); return

    summaries = {ev["id"]: get_event_summary(ev["id"]) for ev in events}
    total_inc = sum(s["act_income"]  for s in summaries.values())
    total_exp = sum(s["act_expense"] for s in summaries.values())
    total_pft = total_inc - total_exp
    avg_acc   = sum(s["budget_accuracy"] for s in summaries.values()) / len(summaries)
    margin    = (total_pft/max(total_inc,1))*100

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("💰 Revenue",    f"{sym}{total_inc:,.0f}")
    c2.metric("📤 Expenses",   f"{sym}{total_exp:,.0f}")
    c3.metric("📈 Profit",     f"{sym}{total_pft:,.0f}")
    c4.metric("💹 Margin",     f"{margin:.1f}%")
    c5.metric("🎯 Avg Accuracy",f"{avg_acc:.1f}%")
    c6.metric("📅 Events",     str(len(events)))
    st.divider()

    ev_names = [e["name"] for e in events]
    col1, col2 = st.columns(2)

    with col1:
        section_header("Revenue vs Expenses","📊")
        fig = bar_comparison(ev_names,
                             [summaries[e["id"]]["est_income"] for e in events],
                             [summaries[e["id"]]["act_income"] for e in events],
                             "Estimated vs Actual Revenue")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with col2:
        section_header("Profit per Event","💹")
        profits = [summaries[e["id"]]["act_profit"] for e in events]
        colors  = [COLORS["success"] if p>=0 else COLORS["danger"] for p in profits]
        fig2 = go.Figure(go.Bar(x=ev_names, y=profits, marker_color=colors,
                                text=[f"${p:,.0f}" for p in profits], textposition="outside"))
        fig2.update_layout(height=300,
                           **{k:v for k,v in LAYOUT_DEFAULTS.items() if k not in ("xaxis","yaxis")},
                           xaxis=dict(tickfont=dict(color="#7b7b9a")),
                           yaxis=dict(gridcolor="#2e2e3e",tickfont=dict(color="#7b7b9a")))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    col3, col4 = st.columns(2)
    with col3:
        section_header("Budget Accuracy","🎯")
        accs = [summaries[e["id"]]["budget_accuracy"] for e in events]
        acc_colors = [COLORS["success"] if a>=75 else (COLORS["warning"] if a>=50 else COLORS["danger"]) for a in accs]
        fig3 = go.Figure(go.Bar(x=ev_names, y=accs, marker_color=acc_colors,
                                text=[f"{a:.1f}%" for a in accs], textposition="outside"))
        fig3.add_hline(y=75, line_color=COLORS["success"], line_dash="dash", annotation_text="Target 75%")
        fig3.update_layout(height=300, yaxis_range=[0,115],
                           **{k:v for k,v in LAYOUT_DEFAULTS.items() if k not in ("xaxis","yaxis")},
                           xaxis=dict(tickfont=dict(color="#7b7b9a")),
                           yaxis=dict(gridcolor="#2e2e3e",tickfont=dict(color="#7b7b9a")))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    with col4:
        section_header("Portfolio Split","🥧")
        if total_inc > 0:
            surplus = max(0, total_inc - total_exp)
            fig4 = donut(["Revenue","Expenses","Net Profit"],[total_inc,total_exp,surplus])
            fig4.update_layout(height=300)
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})

    st.divider()
    section_header("Event Performance Ranking","🏆")
    ranked = sorted(events, key=lambda e: summaries[e["id"]]["act_profit"], reverse=True)
    rows = []
    medals = ["🥇","🥈","🥉"]
    for i, ev in enumerate(ranked):
        s = summaries[ev["id"]]
        margin_e = (s["act_profit"]/max(s["act_income"],1))*100
        rows.append({
            "Rank":    medals[i] if i<3 else str(i+1),
            "Event":   ev["name"],
            "Phase":   ev.get("phase","planning").title(),
            "Revenue": f"${s['act_income']:,.0f}",
            "Expenses":f"${s['act_expense']:,.0f}",
            "Profit":  f"${s['act_profit']:,.0f}",
            "Margin":  f"{margin_e:.1f}%",
            "Accuracy":f"{s['budget_accuracy']:.1f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if len(events) > 1:
        st.divider()
        section_header("Cash Flow Waterfall","💧")
        wf_labels, wf_values = [], []
        for ev in events:
            s = summaries[ev["id"]]
            short = ev["name"][:10]
            wf_labels += [f"{short} Inc", f"{short} Exp"]
            wf_values += [s["act_income"], -s["act_expense"]]
        fig_wf = waterfall(wf_labels, wf_values)
        fig_wf.update_layout(height=350)
        st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar":False})
