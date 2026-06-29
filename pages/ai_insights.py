"""EventLedger AI – AI Insights (native Streamlit)"""

import streamlit as st
from utils.helpers import get_events, get_event_summary
from components.ui import section_header, empty_state
from utils.currency import get_symbol, get_global_currency


def _insights(events, summaries):
    insights = []
    for ev in events:
        s = summaries[ev["id"]]
        name = ev["name"]
        if s["expense_variance"] > 0:
            pct = (s["expense_variance"]/max(s["est_expense"],1))*100
            insights.append(("warning", "⚠️", name, f"Over-budget by {pct:.1f}%",
                f"{name} exceeded its expense budget by ${s['expense_variance']:,.0f}. "
                "Review discretionary spending in high-variance departments."))
        if s["income_variance"] < 0:
            pct = abs(s["income_variance"]/max(s["est_income"],1))*100
            insights.append(("error", "📉", name, f"Revenue {pct:.1f}% below target",
                f"{name} has a ${abs(s['income_variance']):,.0f} income shortfall. "
                "Consider additional ticket channels or sponsor outreach."))
        margin = (s["act_profit"]/max(s["act_income"],1))*100
        if margin >= 20:
            insights.append(("success", "🌟", name, f"Strong margin: {margin:.1f}%",
                f"{name} is performing excellently. This event's model could serve as a future template."))
        if s["budget_accuracy"] >= 90:
            insights.append(("success", "🎯", name, f"Budget accuracy: {s['budget_accuracy']:.1f}%",
                f"Financial planning for {name} was highly accurate within {100-s['budget_accuracy']:.1f}%."))
        if s["budget_accuracy"] < 60 and s["act_expense"] > 0:
            insights.append(("warning", "📊", name, f"Low accuracy: {s['budget_accuracy']:.1f}%",
                f"{name} shows significant variance. Review your estimation methodology."))
    if not insights:
        insights = [("info","💡","General","Start tracking actual finances",
                     "Record income and expenses in the Execution module to unlock AI analysis.")]
    return insights


def show(user):
    st.title("🤖 AI Insights")
    st.caption("Automated financial intelligence & recommendations")
    st.divider()

    events = get_events(user["id"])
    sym = get_symbol()
    if not events:
        empty_state("🤖","No events to analyze","Create events with financial data first."); return

    summaries = {ev["id"]: get_event_summary(ev["id"]) for ev in events}

    # Smart Alerts
    section_header("Smart Alerts","🚨")
    alerts_found = False
    for ev in events:
        s = summaries[ev["id"]]
        if s["est_expense"] > 0:
            util = s["act_expense"]/s["est_expense"]*100
            if util > 90:
                st.error(f"🚨 **{ev['name']}**: Budget utilization at {util:.0f}% — critical")
                alerts_found = True
            elif util > 75:
                st.warning(f"⚠️ **{ev['name']}**: Budget utilization at {util:.0f}% — monitor closely")
                alerts_found = True
        if s["act_income"] > 0 and s["act_profit"] < 0:
            st.error(f"🔴 **{ev['name']}**: Currently at a loss of ${abs(s['act_profit']):,.0f}")
            alerts_found = True
    if not alerts_found:
        st.success("✅ All events are within healthy financial parameters.")

    st.divider()
    section_header("Financial Insights","💡")
    insights = _insights(events, summaries)
    for kind, icon, event, title, body in insights:
        with st.container():
            if kind == "success":
                st.success(f"{icon} **{title}** *({event})*\n\n{body}")
            elif kind == "warning":
                st.warning(f"{icon} **{title}** *({event})*\n\n{body}")
            elif kind == "error":
                st.error(f"{icon} **{title}** *({event})*\n\n{body}")
            else:
                st.info(f"{icon} **{title}** *({event})*\n\n{body}")

    st.divider()
    section_header("Budget Recommendations","🎯")
    recs = [
        ("📋","Zero-Based Budgeting",
         "Start each event budget from scratch. Forces justification of every line item and reduces waste by 15–25%."),
        ("💰","Maintain a Contingency Reserve",
         "Set aside 8–12% of estimated expenses as contingency. Events with this buffer show 40% fewer overruns."),
        ("🤝","Diversify Sponsor Tiers",
         "Aim for 1–2 Platinum, 3–4 Gold, and several Silver/Bronze sponsors rather than one large sponsor."),
        ("📊","Weekly Variance Reviews",
         "Review estimated vs actual variance weekly during execution for early overspending detection."),
        ("🚚","Vendor Contract Caps",
         "Negotiate fixed-fee contracts to eliminate variable cost surprises. Include service penalty clauses."),
    ]
    for icon, title, body in recs:
        with st.expander(f"{icon} {title}"):
            st.write(body)

    st.divider()
    section_header("Financial Forecasting","🔮")
    events_with_data = [e for e in events if summaries[e["id"]]["act_income"] > 0]
    if events_with_data:
        avg_margin = sum(
            summaries[e["id"]]["act_profit"]/max(summaries[e["id"]]["act_income"],1)
            for e in events_with_data
        ) / len(events_with_data)
        avg_inc = sum(summaries[e["id"]]["act_income"] for e in events_with_data) / len(events_with_data)
        f_inc = avg_inc * 1.15
        f_exp = f_inc * (1 - avg_margin)
        f_pft = f_inc - f_exp

        st.markdown(f"**Next Event Forecast** *(based on {len(events_with_data)} events, 15% growth model)*")
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("📈 Projected Revenue",  f"{sym}{f_inc:,.0f}")
        fc2.metric("📤 Projected Expenses", f"{sym}{f_exp:,.0f}")
        fc3.metric("💹 Projected Profit",   f"{sym}{f_pft:,.0f}")
        st.caption(f"Based on avg margin of {avg_margin*100:.1f}% across {len(events_with_data)} events")
    else:
        empty_state("🔮","Record actual income to unlock forecasting")
