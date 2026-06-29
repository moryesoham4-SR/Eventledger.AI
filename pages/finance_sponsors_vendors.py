"""EventLedger AI – Global Finance / Sponsors / Vendors (native Streamlit)"""

import streamlit as st
import pandas as pd
from utils.helpers import get_events, get_actual_income, get_actual_expenses, get_sponsors, get_vendors, get_event_summary
from utils.charts import bar_comparison, donut, sponsor_scatter, PALETTE, LAYOUT_DEFAULTS
from components.ui import section_header, empty_state
from utils.currency import get_symbol, get_global_currency
import plotly.graph_objects as go


def show_finance(user):
    st.title("💰 Finance Overview")
    st.caption("Consolidated financials across all events")
    st.divider()
    events = get_events(user["id"])
    sym = get_symbol()
    if not events:
        empty_state("💰","No events found","Create an event first."); return

    all_inc, all_exp = [], []
    for ev in events:
        for r in get_actual_income(ev["id"]):
            r["event_name"] = ev["name"]; all_inc.append(r)
        for r in get_actual_expenses(ev["id"]):
            r["event_name"] = ev["name"]; all_exp.append(r)

    total_inc = sum(r["amount"] for r in all_inc)
    total_exp = sum(r["amount"] for r in all_exp)
    total_pft = total_inc - total_exp
    margin    = (total_pft/max(total_inc,1))*100

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💵 Total Revenue",  f"{sym}{total_inc:,.0f}")
    c2.metric("📤 Total Expenses", f"{sym}{total_exp:,.0f}")
    c3.metric("📈 Net Profit",     f"{sym}{total_pft:,.0f}", delta=f"{'+' if total_pft>=0 else ''}{sym}{abs(total_pft):,.0f}")
    c4.metric("🎯 Profit Margin",  f"{margin:.1f}%")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        section_header("Revenue vs Expenses by Event","📊")
        names = [e["name"] for e in events]
        ev_inc = [sum(r["amount"] for r in all_inc if r["event_name"]==e["name"]) for e in events]
        ev_exp = [sum(r["amount"] for r in all_exp if r["event_name"]==e["name"]) for e in events]
        fig = bar_comparison(names, ev_inc, ev_exp)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    with col2:
        section_header("Income by Category","🥧")
        if all_inc:
            cats = {}
            for r in all_inc: cats[r["category"]] = cats.get(r["category"],0)+r["amount"]
            fig2 = donut(list(cats.keys()), list(cats.values()))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    st.divider()
    section_header("Recent Income (last 20)","💵")
    if all_inc:
        rows = sorted(all_inc, key=lambda x: x.get("created_at",""), reverse=True)[:20]
        df = pd.DataFrame([{"Event":r["event_name"],"Source":r["source"],"Category":r["category"],
                             "Amount":f"{sym}{r['amount']:,.0f}","Date":r.get("received_on","—"),
                             "Mode":r.get("payment_mode","—")} for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        empty_state("💵","No income recorded yet")

    st.divider()
    section_header("Recent Expenses (last 20)","📤")
    if all_exp:
        rows2 = sorted(all_exp, key=lambda x: x.get("created_at",""), reverse=True)[:20]
        df2 = pd.DataFrame([{"Event":r["event_name"],"Category":r["category"],
                              "Description":r.get("description","—"),"Amount":f"{sym}{r['amount']:,.0f}",
                              "Date":r.get("paid_on","—"),"Status":r.get("status","—")} for r in rows2])
        st.dataframe(df2, use_container_width=True, hide_index=True)
    else:
        empty_state("📤","No expenses recorded yet")


def show_sponsors(user):
    sym = get_symbol()
    st.title("🤝 Sponsors")
    st.caption("All sponsors across your events")
    st.divider()
    events = get_events(user["id"])
    if not events:
        empty_state("🤝","No events found"); return

    all_sp = []
    for ev in events:
        for s in get_sponsors(ev["id"]):
            s["event_name"] = ev["name"]; all_sp.append(s)

    if not all_sp:
        empty_state("🤝","No sponsors added yet","Open an event → Execution → Sponsors."); return

    total = sum(s["amount"] for s in all_sp)
    tier_totals = {}
    for s in all_sp: tier_totals[s["tier"]] = tier_totals.get(s["tier"],0)+s["amount"]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🤝 Total Sponsors", str(len(all_sp)))
    c2.metric("💰 Total Funds",    f"{sym}{total:,.0f}")
    c3.metric("⭐ Platinum", str(sum(1 for s in all_sp if s["tier"]=="Platinum")))
    c4.metric("🥇 Gold",     str(sum(1 for s in all_sp if s["tier"]=="Gold")))
    st.divider()

    col1, col2 = st.columns([2,1])
    with col1:
        section_header("Sponsor Contributions","📊")
        fig = sponsor_scatter([s["name"] for s in all_sp],[s["tier"] for s in all_sp],[s["amount"] for s in all_sp])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    with col2:
        section_header("By Tier","🥧")
        if tier_totals:
            fig2 = donut(list(tier_totals.keys()), list(tier_totals.values()))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    st.divider()
    section_header("All Sponsors","📋")
    df = pd.DataFrame([{"Sponsor":s["name"],"Event":s["event_name"],"Tier":s["tier"],
                         "Contact":s.get("contact_name","—"),"Email":s.get("contact_email","—"),
                         "Amount":f"{sym}{s['amount']:,.0f}","Status":s.get("status","confirmed")}
                        for s in sorted(all_sp, key=lambda x: x["amount"], reverse=True)])
    st.dataframe(df, use_container_width=True, hide_index=True)


def show_vendors(user):
    sym = get_symbol()
    st.title("🚚 Vendors")
    st.caption("All vendors across your events")
    st.divider()
    events = get_events(user["id"])
    if not events:
        empty_state("🚚","No events found"); return

    all_vd = []
    for ev in events:
        for v in get_vendors(ev["id"]):
            v["event_name"] = ev["name"]; all_vd.append(v)

    if not all_vd:
        empty_state("🚚","No vendors added yet","Open an event → Execution → Vendors."); return

    total_cv = sum(v["contract_value"] for v in all_vd)
    cat_totals = {}
    for v in all_vd: cat_totals[v["category"]] = cat_totals.get(v["category"],0)+v["contract_value"]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🚚 Total Vendors",    str(len(all_vd)))
    c2.metric("💰 Contract Value",   f"{sym}{total_cv:,.0f}")
    c3.metric("✅ Active",           str(sum(1 for v in all_vd if v.get("status")=="active")))
    c4.metric("🗂️ Categories",      str(len(cat_totals)))
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        section_header("Contract Value by Category","🥧")
        if cat_totals:
            fig = donut(list(cat_totals.keys()), list(cat_totals.values()))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    with col2:
        section_header("Top Vendors by Value","📊")
        top = sorted(all_vd, key=lambda x: x["contract_value"], reverse=True)[:8]
        fig2 = go.Figure(go.Bar(
            x=[v["name"] for v in top], y=[v["contract_value"] for v in top],
            marker_color=PALETTE[:len(top)],
            text=[f"${v['contract_value']:,.0f}" for v in top], textposition="outside",
        ))
        fig2.update_layout(height=300, **{k:v for k,v in LAYOUT_DEFAULTS.items() if k not in ("xaxis","yaxis")},
                           xaxis=dict(tickfont=dict(color="#7b7b9a",size=10)),
                           yaxis=dict(gridcolor="#2e2e3e"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    st.divider()
    section_header("All Vendors","📋")
    df = pd.DataFrame([{"Vendor":v["name"],"Event":v["event_name"],"Category":v["category"],
                         "Contact":v.get("contact_name","—"),"Email":v.get("contact_email","—"),
                         "Contract Value":f"{sym}{v['contract_value']:,.0f}","Status":v.get("status","active")}
                        for v in sorted(all_vd, key=lambda x: x["contract_value"], reverse=True)])
    st.dataframe(df, use_container_width=True, hide_index=True)
