"""EventLedger AI – Design System CSS"""

CUSTOM_CSS = """
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Design Tokens ── */
:root {
    --primary:     #6366f1;
    --primary-dim: #4f46e5;
    --accent:      #f59e0b;
    --success:     #10b981;
    --danger:      #ef4444;
    --warning:     #f97316;
    --bg:          #0f0f13;
    --surface:     #18181f;
    --surface2:    #22222e;
    --border:      #2e2e3e;
    --text:        #e8e8f0;
    --muted:       #7b7b9a;
    --radius:      12px;
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.main .block-container {
    padding: 1.5rem 2.5rem 3rem 2.5rem;
    max-width: 1400px;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── Page Title ── */
.el-page-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.el-page-sub {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 1.5rem;
}

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--card-accent, var(--primary));
    border-radius: var(--radius) var(--radius) 0 0;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: var(--primary);
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1;
    margin-bottom: 0.35rem;
}
.kpi-delta {
    font-size: 0.8rem;
    font-weight: 500;
}
.kpi-delta.pos { color: var(--success); }
.kpi-delta.neg { color: var(--danger); }
.kpi-icon {
    position: absolute;
    top: 1rem; right: 1.25rem;
    font-size: 1.5rem;
    opacity: 0.3;
}

/* ── Section Header ── */
.el-section {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Cards ── */
.el-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.15s ease;
}
.el-card:hover { border-color: var(--primary); }

/* ── Event Cards ── */
.event-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    position: relative;
    overflow: hidden;
}
.event-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
}
.event-card .ev-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.event-card .ev-venue {
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 0.75rem;
}
.ev-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-planning  { background: rgba(99,102,241,0.15); color: #a5b4fc; }
.badge-execution { background: rgba(245,158,11,0.15); color: #fcd34d; }
.badge-comparison{ background: rgba(16,185,129,0.15); color: #6ee7b7; }
.badge-completed { background: rgba(107,114,128,0.15); color: #9ca3af; }

/* ── Status Pills ── */
.pill {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
}
.pill-green  { background: rgba(16,185,129,0.15); color: #6ee7b7; }
.pill-amber  { background: rgba(245,158,11,0.15); color: #fcd34d; }
.pill-red    { background: rgba(239,68,68,0.15); color: #fca5a5; }
.pill-blue   { background: rgba(99,102,241,0.15); color: #a5b4fc; }

/* ── Tables ── */
.el-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.el-table th {
    background: var(--surface2);
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 0.6rem 0.9rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.el-table td {
    padding: 0.7rem 0.9rem;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}
.el-table tr:last-child td { border-bottom: none; }
.el-table tr:hover td { background: rgba(99,102,241,0.04); }
.el-table .amount {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}
.el-table .total-row td {
    background: var(--surface2);
    font-weight: 600;
    border-top: 2px solid var(--border);
}

/* ── Variance indicators ── */
.var-pos { color: var(--success); }
.var-neg { color: var(--danger); }

/* ── Dept color strip ── */
.dept-strip {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}

/* ── Progress bar ── */
.prog-wrap {
    background: var(--surface2);
    border-radius: 99px;
    height: 6px;
    overflow: hidden;
    margin-top: 4px;
}
.prog-fill {
    height: 100%;
    border-radius: 99px;
    background: var(--primary);
    transition: width 0.4s ease;
}
.prog-fill.warn  { background: var(--warning); }
.prog-fill.danger{ background: var(--danger); }

/* ── AI Insight Card ── */
.ai-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(245,158,11,0.05) 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    position: relative;
}
.ai-card::before {
    content: '🤖';
    position: absolute;
    top: 1rem; right: 1.25rem;
    font-size: 1.25rem;
    opacity: 0.5;
}
.ai-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    color: #a5b4fc;
    margin-bottom: 0.4rem;
}
.ai-body { font-size: 0.85rem; color: var(--muted); line-height: 1.55; }

/* ── Health Score Ring ── */
.health-ring {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
}
.health-score {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
}
.health-label { font-size: 0.8rem; color: var(--muted); }

/* ── Tabs override ── */
button[data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* ── Inputs override ── */
.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}

/* ── Buttons override ── */
.stButton button {
    background: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover {
    background: var(--primary-dim) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.4) !important;
}
.stButton.secondary button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Plotly charts ── */
.js-plotly-plot .plotly { background: transparent !important; }

/* ── Sponsor Tier Colors ── */
.tier-platinum { color: #e5e7eb; }
.tier-gold     { color: #fbbf24; }
.tier-silver   { color: #9ca3af; }
.tier-bronze   { color: #b45309; }

/* ── Logo / Brand ── */
.brand-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.2rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.brand-logo span.accent { color: var(--primary); }

/* ── Sidebar Nav ── */
.nav-section {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.25rem 0 0.4rem 0.5rem;
}

/* ── Empty State ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    color: var(--muted);
    text-align: center;
    border: 1px dashed var(--border);
    border-radius: var(--radius);
}
.empty-state .icon { font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.5; }
.empty-state .msg  { font-size: 0.9rem; }

/* ── Timeline ── */
.timeline {
    position: relative;
    padding-left: 1.5rem;
}
.timeline::before {
    content: '';
    position: absolute;
    left: 6px; top: 8px; bottom: 8px;
    width: 2px;
    background: var(--border);
}
.tl-item {
    position: relative;
    padding: 0 0 1rem 1rem;
    font-size: 0.85rem;
}
.tl-item::before {
    content: '';
    position: absolute;
    left: -0.85rem; top: 4px;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--primary);
    border: 2px solid var(--bg);
}
</style>
"""
