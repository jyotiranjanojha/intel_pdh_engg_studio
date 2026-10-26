# PDH Engineering Studio — unified data engineering lifecycle platform
# Co-authored with CoCo
import os
import streamlit as st

st.set_page_config(
    page_title="PDH Engineering Studio",
    page_icon=":material/hub:",
    layout="wide",
)

class _QuietConnection:
    """Proxy for st.connection: every .query() shows a plain spinner icon instead of
    Streamlit's default "Running `snowflake.query(...)`" text. Everything else passes through."""

    def __init__(self, inner):
        self._inner = inner

    def query(self, sql, *args, **kwargs):
        kwargs.setdefault("show_spinner", " ")
        return self._inner.query(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)


conn = _QuietConnection(st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")))
st.session_state["conn"] = conn

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main page theme */
.stApp {
    background: linear-gradient(180deg, #ffffff 0%, #f4f8fc 100%);
}
section[data-testid="stSidebar"] { width: 240px !important; }
.block-container { padding-top: 1rem !important; }
[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    border-radius: 8px; padding: 12px;
    border: 1px solid rgba(128,128,128,0.15);
}
.stButton > button { border-radius: 6px !important; }
.stSuccess, .stError, .stWarning { border-radius: 8px !important; }
.stTabs [data-baseweb="tab"] { font-size: 13px; }
.intel-header { border-left: 4px solid #0068B5; padding-left: 12px; margin-bottom: 16px; }
h1, h2, h3 { color: #0068b5 !important; }
.stTabs [data-baseweb="tab"] { color: #0068b5; }
.stTabs [aria-selected="true"] { border-bottom-color: #0068b5 !important; }
div[data-testid="stMetric"] label { color: #0068b5 !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #00285a !important; }
button[kind="primary"] {
    background-color: #0068b5 !important;
    border-color: #0068b5 !important;
}
button[kind="primary"]:hover {
    background-color: #004f8a !important;
    border-color: #004f8a !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f4f8fc 0%, #e8f0f8 100%);
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    background: #ffffff !important;
    border: 1px solid #c8dced !important;
    border-radius: 10px !important;
    color: #0068b5 !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(0, 104, 181, 0.06) !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: linear-gradient(90deg, #0068b5 0%, #00aeef 100%) !important;
    border-color: transparent !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(0, 104, 181, 0.3) !important;
    transform: translateX(3px);
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, #0068b5 0%, #00aeef 100%) !important;
    border-color: transparent !important;
    color: #fff !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(0, 104, 181, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

if "welcomed" not in st.session_state:
    st.session_state.welcomed = True
    st.snow()

# ── Unified navigation ───────────────────────────────────────────────────────
page = st.navigation(
    {
        "": [
            st.Page("app_pages/home.py", title="Home", icon=":material/home:"),
        ],
        "Development": [
            st.Page("app_pages/code_generator.py", title="Code Generator", icon=":material/terminal:"),
            st.Page("app_pages/compliance_analyzer.py", title="Compliance Analyzer", icon=":material/verified:"),
        ],
        "Analysis": [
            st.Page("app_pages/impact_simulator.py", title="Change Impact Analyzer", icon=":material/science:"),
            st.Page("app_pages/item_tracer.py", title="Data Journey Explorer", icon=":material/travel_explore:"),
        ],
        "Quality Engineering": [
            st.Page("app_pages/tdd_generator.py", title="TDD Generator", icon=":material/description:"),
            st.Page("app_pages/unit_test_generator.py", title="Unit Test Generator", icon=":material/bug_report:"),
        ],
        "Pipeline Intelligence": [
            st.Page("app_pages/object_flow.py", title="Pipeline Flow", icon=":material/schema:"),
            st.Page("app_pages/drift_monitor.py", title="Rule Drift Monitor", icon=":material/sync_problem:"),
            st.Page("app_pages/dev_tracker.py", title="Dev Completion Tracker", icon=":material/task_alt:"),
        ],
        "Intelligence": [
            st.Page("app_pages/cortex_analyst.py", title="AI Engineering Assistant", icon=":material/psychology:"),
        ],
        "Future Enhancements": [
            st.Page("app_pages/code_reviewer.py", title="Code Reviewer", icon=":material/rate_review:"),
        ],
    },
    position="sidebar",
)

# ── Sidebar branding ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<h2 style="color: #0068b5; margin-bottom: 0;">intel</h2>', unsafe_allow_html=True)
    st.markdown("#### PDH Engineering Studio")
    st.markdown("---")
    st.caption("IF_SUPPLY_CHAIN")
    st.markdown(":green-badge[LIVE] :blue-badge[v4.0]")

page.run()
