# EventLedger AI

**Event Financial Lifecycle Management Platform**

---

## Quick Start (Windows)

### Step 1 — Install Python
Download and install **Python 3.10+** from https://python.org  
✅ **Important:** During installation, check **"Add Python to PATH"**

### Step 2 — Install dependencies
Double-click **`setup.bat`**  
*(Only needed once)*

### Step 3 — Run the app
Double-click **`run.bat`**  
Then open your browser at **http://localhost:8501**

---

## Manual Run (Command Prompt / PowerShell)

```bat
cd "C:\Users\Soham\Pictures\SMT CHM\Projects\eventledger.AI\eventledger"
pip install -r requirements.txt
streamlit run app.py
```

---

## Demo Login
| Field    | Value                    |
|----------|--------------------------|
| Email    | demo@eventledger.ai      |
| Password | demo123                  |

---

## Project Structure

```
eventledger/
│
├── app.py                   ← Main entry point (run this)
├── requirements.txt         ← Python dependencies
├── run.bat                  ← Windows quick-start
├── setup.bat                ← Windows first-time setup
│
├── database/
│   └── schema.py            ← SQLite schema + demo data
│
├── utils/
│   ├── helpers.py           ← All DB read/write functions
│   ├── styles.py            ← CSS design system
│   ├── charts.py            ← Plotly chart builders
│   └── export_engine.py     ← PDF (ReportLab) + Excel (OpenPyXL)
│
├── components/
│   └── ui.py                ← Sidebar, KPI cards, shared widgets
│
└── pages/
    ├── auth.py                      ← Login & registration
    ├── dashboard.py                 ← Portfolio overview
    ├── events.py                    ← Event list & create
    ├── event_detail.py              ← Full lifecycle tabs
    ├── finance_sponsors_vendors.py  ← Global finance views
    ├── analytics.py                 ← Cross-event analytics
    ├── ai_insights.py               ← AI alerts & forecasting
    └── reports_archive_settings.py ← Reports + PDF/Excel export
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `'streamlit' is not recognized` | Run `setup.bat` first, or `pip install streamlit` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Browser doesn't open | Manually visit http://localhost:8501 |
| Port 8501 in use | Edit `run.bat`, change `--server.port 8501` to `8502` |
| Blank white screen | Hard refresh browser: `Ctrl + Shift + R` |

---

## Phases Implemented
- ✅ Phase 1 – Foundation (Auth, Dashboard, Events, Departments)
- ✅ Phase 2 – Planning (Estimated Budget, Income, Expenses)
- ✅ Phase 3 – Execution (Actual Income, Expenses, Sponsors, Vendors)
- ✅ Phase 4 – Comparison (Variance Analysis, Health Score)
- ✅ Phase 5 – Analytics (Charts, KPIs, Rankings)
- ✅ Phase 6 – Reports (PDF & Excel Export, 7 report types)
- ✅ Phase 7 – AI Insights (Alerts, Recommendations, Forecasting)
- ✅ Phase 8 – Administration (Archive, Settings, Password Change)
