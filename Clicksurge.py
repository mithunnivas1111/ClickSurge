import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

from demo_data import generate_demo_page_data, generate_demo_page_query_data
from analyzers.gsc_analyzer import GSCAnalyzer
from utils.normalizer import normalize_page_df, normalize_query_df
from analyzers.cannibalization import CannibalizationAnalyzer
from analyzers.opportunity import OpportunityAnalyzer
from analyzers.ctr_curve import expected_ctr, ctr_performance_ratio, CTR_CURVE
from analyzers.page_classifier import classify_url, classify_performance, get_page_recommendations
from analyzers.query_analyzer import QueryAnalyzer

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ClickSurge — SEO Growth Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  BRAND THEME
#  Palette  : Deep Ink #0A0C14  ·  Electric Indigo #5046E4  ·  Lime Spark #C8F04A
#  Surface  : Warm white #FAFBFD  ·  Cards #FFFFFF  ·  Border #E4E7F0
#  Fonts    : Outfit (display/headings)  +  Plus Jakarta Sans (body/UI)
#             + Fira Code (mono/URLs)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800;900&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

/* ── ROOT TOKENS ── */
:root {
  --ink:        #0A0C14;
  --ink-soft:   #1C1F2E;
  --indigo:     #5046E4;
  --indigo-lt:  #6B61FF;
  --indigo-dim: rgba(80,70,228,0.12);
  --lime:       #C8F04A;
  --lime-dim:   rgba(200,240,74,0.15);
  --danger:     #F03E3E;
  --danger-dim: rgba(240,62,62,0.1);
  --warn:       #F59F00;
  --warn-dim:   rgba(245,159,0,0.1);
  --success:    #2BB44A;
  --success-dim:rgba(43,180,74,0.1);
  --info:       #3B82F6;
  --info-dim:   rgba(59,130,246,0.1);
  --bg:         #FAFBFD;
  --surface:    #FFFFFF;
  --border:     #E4E7F0;
  --border-dk:  #D1D5E8;
  --muted:      #8590AD;
  --text:       #1C1F2E;
  --text-soft:  #4B526B;
  /* sidebar tokens */
  --sb-bg:      #0A0C14;
  --sb-surface: #12141F;
  --sb-card:    #181B28;
  --sb-border:  #252838;
  --sb-border2: #30344A;
  --sb-muted:   #3E4460;
  --sb-text:    #A8B0CC;
  --sb-bright:  #D8DCF0;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
}
#MainMenu, footer { visibility: hidden; }
header { height: 0; }
[data-testid="collapsedControl"] {
  position: fixed; top: 15px; left: 15px; z-index: 999;
}
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ════════════════════════════════
   SIDEBAR
════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--sb-bg) !important;
  border-right: 1px solid var(--sb-border) !important;
  min-width: 256px !important;
  max-width: 256px !important;
}
[data-testid="stSidebar"] * {
  color: var(--sb-text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}
[data-testid="stSidebar"] .stRadio label {
  font-size: 0.84rem !important;
  padding: 4px 0 !important;
  color: var(--sb-text) !important;
}
[data-testid="stSidebar"] .stButton button {
  background: var(--indigo) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
  font-size: 0.84rem !important;
  padding: 11px 16px !important;
  width: 100% !important;
  transition: background 0.18s, box-shadow 0.18s !important;
  letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: var(--indigo-lt) !important;
  box-shadow: 0 4px 18px rgba(80,70,228,0.35) !important;
}
[data-testid="stSidebar"] .stNumberInput input {
  background: var(--sb-card) !important;
  border: 1px solid var(--sb-border2) !important;
  border-radius: 8px !important;
  color: var(--sb-bright) !important;
  font-size: 0.83rem !important;
}
[data-testid="stSidebar"] hr {
  border-color: var(--sb-border) !important;
  margin: 10px 0 !important;
}

/* ════════════════════════════════
   TOP NAV
════════════════════════════════ */
.cs-nav {
  background: var(--ink);
  border-bottom: 1px solid #1C1F2E;
  height: 54px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 998;
}
.cs-nav-brand { display: flex; align-items: center; gap: 10px; }
.cs-nav-icon {
  width: 30px; height: 30px;
  background: var(--indigo);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; flex-shrink: 0;
}
.cs-nav-name {
  font-family: 'Outfit', sans-serif;
  font-size: 1.12rem; font-weight: 800;
  color: #fff; letter-spacing: -0.3px;
}
.cs-nav-name span { color: var(--lime); }
.cs-nav-right { display: flex; align-items: center; gap: 10px; }
.cs-nav-tag {
  background: #12141F;
  border: 1px solid #252838;
  border-radius: 20px;
  padding: 3px 11px;
  font-size: 0.71rem; font-weight: 600;
  color: #5A6080; letter-spacing: 0.03em;
}
.cs-nav-tag.hi {
  background: var(--indigo-dim);
  border-color: rgba(80,70,228,0.3);
  color: #9B93FF;
}
.cs-nav-ts {
  font-family: 'Fira Code', monospace;
  font-size: 0.71rem; color: #2E3250;
}

/* ════════════════════════════════
   PAGE SHELL
════════════════════════════════ */
.cs-page { padding: 24px 28px; background: var(--bg); }

/* ════════════════════════════════
   PAGE HEADER
════════════════════════════════ */
.cs-ph {
  display: flex; justify-content: space-between;
  align-items: flex-end; margin-bottom: 20px;
}
.cs-ph-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.3rem; font-weight: 700;
  color: var(--ink); letter-spacing: -0.3px;
}
.cs-ph-sub { font-size: 0.78rem; color: var(--muted); margin-top: 3px; }
.cs-health-pill {
  background: #FFF8E1;
  border: 1px solid rgba(245,159,0,0.35);
  border-radius: 10px; padding: 8px 16px;
  font-size: 0.78rem; font-weight: 700;
  color: #8A5C00; white-space: nowrap;
}

/* ════════════════════════════════
   KPI GRID
════════════════════════════════ */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px; margin-bottom: 22px;
}
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px 16px;
  position: relative; overflow: hidden;
  transition: box-shadow 0.2s, transform 0.18s;
}
.kpi-card:hover {
  box-shadow: 0 8px 28px rgba(10,12,20,0.09);
  transform: translateY(-2px);
}
/* bottom colour bar */
.kpi-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 0 0 16px 16px;
}
.kpi-card.orange::after { background: var(--indigo); }
.kpi-card.red::after    { background: var(--danger); }
.kpi-card.amber::after  { background: var(--warn); }
.kpi-card.green::after  { background: var(--success); }
.kpi-card.blue::after   { background: var(--info); }
/* small top-right icon chip */
.kpi-chip {
  position: absolute; top: 14px; right: 14px;
  width: 30px; height: 30px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem;
}
.kpi-card.orange .kpi-chip { background: var(--indigo-dim); }
.kpi-card.red    .kpi-chip { background: var(--danger-dim); }
.kpi-card.amber  .kpi-chip { background: var(--warn-dim); }
.kpi-card.green  .kpi-chip { background: var(--success-dim); }
.kpi-card.blue   .kpi-chip { background: var(--info-dim); }

.kpi-label {
  font-size: 0.66rem; font-weight: 700;
  color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.09em; margin-bottom: 8px;
}
.kpi-value {
  font-family: 'Outfit', sans-serif;
  font-size: 1.9rem; font-weight: 800;
  line-height: 1; margin-bottom: 5px;
}
.kpi-value.orange { color: var(--indigo); }
.kpi-value.red    { color: var(--danger); }
.kpi-value.amber  { color: var(--warn); }
.kpi-value.green  { color: var(--success); }
.kpi-value.blue   { color: var(--info); }
.kpi-delta { font-size: 0.71rem; color: var(--muted); }

/* ════════════════════════════════
   TABS
════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-bottom: 2px solid var(--border) !important;
  border-radius: 14px 14px 0 0 !important;
  padding: 0 16px !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 0.83rem !important; font-weight: 600 !important;
  color: var(--muted) !important;
  padding: 13px 16px !important;
  border-bottom: 2px solid transparent !important;
  margin-bottom: -2px !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--indigo) !important;
  border-bottom-color: var(--indigo) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 14px 14px !important;
  padding: 24px !important;
}

/* ════════════════════════════════
   ISSUE CARDS
════════════════════════════════ */
.issue-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 20px; margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 16px;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.issue-card:hover {
  box-shadow: 0 4px 20px rgba(10,12,20,0.07);
  border-color: var(--border-dk);
}
.issue-rank {
  font-family: 'Outfit', sans-serif;
  font-size: 1rem; font-weight: 800;
  color: #CDD2E8; min-width: 28px; padding-top: 2px;
}
.issue-body { flex: 1; }
.issue-type {
  font-size: 0.66rem; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 4px;
}
.issue-page {
  font-family: 'Fira Code', monospace;
  font-size: 0.78rem; color: var(--info);
  font-weight: 500; margin-bottom: 8px; word-break: break-all;
}
.issue-action {
  font-size: 0.81rem; color: var(--text-soft); line-height: 1.6;
  background: #F5F6FB;
  border-left: 3px solid var(--indigo);
  padding: 8px 12px; border-radius: 0 8px 8px 0;
}
.issue-stats {
  display: flex; flex-direction: column;
  align-items: flex-end; gap: 6px; min-width: 138px;
}
.gain-badge {
  background: var(--lime-dim);
  color: #3A7000;
  border: 1px solid rgba(200,240,74,0.4);
  border-radius: 8px; padding: 6px 12px;
  font-family: 'Outfit', sans-serif;
  font-size: 0.92rem; font-weight: 800; white-space: nowrap;
}
.stat-row { font-size: 0.72rem; color: var(--muted); }
.stat-row span { color: var(--text-soft); font-weight: 600; }

/* ════════════════════════════════
   BADGES
════════════════════════════════ */
.badge {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 9px; border-radius: 20px;
  font-size: 0.67rem; font-weight: 700; letter-spacing: 0.04em;
}
.badge-high   { background: var(--danger-dim);  color: #C0000C; border: 1px solid rgba(240,62,62,0.25); }
.badge-medium { background: var(--warn-dim);    color: #8A5C00; border: 1px solid rgba(245,159,0,0.25); }
.badge-low    { background: var(--success-dim); color: #1A6B2E; border: 1px solid rgba(43,180,74,0.25); }

/* ════════════════════════════════
   WINNER CARDS
════════════════════════════════ */
.winner-card {
  background: #F4FFF7;
  border: 1px solid rgba(43,180,74,0.25);
  border-left: 4px solid var(--success);
  border-radius: 14px;
  padding: 18px 20px; margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 16px;
}
.winner-badge {
  background: var(--success-dim); color: #1A6B2E;
  border: 1px solid rgba(43,180,74,0.3);
  border-radius: 8px; padding: 6px 12px;
  font-family: 'Outfit', sans-serif;
  font-size: 0.9rem; font-weight: 800; white-space: nowrap;
}

/* ════════════════════════════════
   DECLINING CARDS
════════════════════════════════ */
.declining-card {
  background: var(--surface);
  border: 1px solid rgba(240,62,62,0.2);
  border-left: 4px solid var(--danger);
  border-radius: 14px;
  padding: 18px 20px; margin-bottom: 10px;
}

/* ════════════════════════════════
   CANNIBALIZATION CARDS
════════════════════════════════ */
.cannib-card {
  background: #FFFDF0;
  border: 1px solid rgba(245,159,0,0.25);
  border-left: 4px solid var(--warn);
  border-radius: 14px;
  padding: 18px 20px; margin-bottom: 12px;
}
.cannib-query {
  font-family: 'Outfit', sans-serif;
  font-size: 1rem; font-weight: 700;
  color: var(--ink); margin-bottom: 4px;
}
.cannib-meta { font-size: 0.76rem; color: var(--muted); margin-bottom: 12px; }
.cannib-action {
  font-size: 0.81rem; color: var(--text-soft);
  background: var(--warn-dim); border-radius: 8px;
  padding: 10px 14px; line-height: 1.6;
}

/* ════════════════════════════════
   CARD / CARD TITLE
════════════════════════════════ */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 24px; margin-bottom: 16px;
}
.card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 0.96rem; font-weight: 700;
  color: var(--ink); margin-bottom: 16px;
}

/* ════════════════════════════════
   WELCOME HERO
════════════════════════════════ */
.welcome-hero {
  background: linear-gradient(140deg, #0A0C14 0%, #10142A 55%, #151A30 100%);
  border-radius: 18px; padding: 48px 56px; margin-bottom: 24px;
  position: relative; overflow: hidden;
  border: 1px solid #252838;
}
.welcome-hero::before {
  content: '';
  position: absolute; top: -80px; right: -80px;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(80,70,228,0.18) 0%, transparent 70%);
  border-radius: 50%;
}
.welcome-hero::after {
  content: '⚡'; position: absolute; right: 52px; top: 50%;
  transform: translateY(-50%); font-size: 9rem; opacity: 0.05;
}
.welcome-hero-label {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.15em;
  text-transform: uppercase; color: var(--lime);
  margin-bottom: 14px;
}
.welcome-title {
  font-family: 'Outfit', sans-serif;
  font-size: 2.25rem; font-weight: 800;
  color: #EEF0FF; letter-spacing: -0.5px;
  line-height: 1.2; margin-bottom: 14px;
}
.welcome-title span { color: var(--lime); }
.welcome-sub { font-size: 0.94rem; color: #4E5470; max-width: 520px; line-height: 1.65; }

.feature-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 14px; margin-bottom: 24px;
}
.feature-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 22px;
  transition: box-shadow 0.2s, transform 0.2s;
}
.feature-card:hover {
  box-shadow: 0 6px 22px rgba(10,12,20,0.08);
  transform: translateY(-2px);
}
.feature-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; margin-bottom: 13px;
}
.feature-icon.orange { background: var(--indigo-dim); }
.feature-icon.blue   { background: var(--info-dim); }
.feature-icon.green  { background: var(--success-dim); }
.feature-name {
  font-family: 'Outfit', sans-serif;
  font-size: 0.93rem; font-weight: 700;
  color: var(--ink); margin-bottom: 5px;
}
.feature-desc { font-size: 0.8rem; color: var(--muted); line-height: 1.55; }

/* ════════════════════════════════
   DATA TABLE
════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 12px !important; overflow: hidden !important;
}

/* ════════════════════════════════
   DOWNLOAD BUTTON
════════════════════════════════ */
.stDownloadButton button {
  background: var(--indigo) !important;
  color: #fff !important; border: none !important;
  border-radius: 9px !important; font-weight: 700 !important;
  transition: background 0.18s, box-shadow 0.18s !important;
}
.stDownloadButton button:hover {
  background: var(--indigo-lt) !important;
  box-shadow: 0 4px 14px rgba(80,70,228,0.3) !important;
}

/* ════════════════════════════════
   METRICS
════════════════════════════════ */
div[data-testid="metric-container"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px; padding: 16px !important;
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
  font-size: 0.74rem !important; color: var(--muted) !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'Outfit', sans-serif !important;
  font-size: 1.4rem !important; color: var(--ink) !important;
}

/* ════════════════════════════════
   EXPANDERS
════════════════════════════════ */
div[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  background: var(--surface) !important;
}

/* ════════════════════════════════
   MOBILE RESPONSIVENESS
════════════════════════════════ */

/* Tablet: ≤ 900px */
@media (max-width: 900px) {
  .cs-page { padding: 16px 14px; }

  .kpi-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .kpi-value { font-size: 1.5rem; }

  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .cs-ph {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .welcome-hero { padding: 32px 28px; }
  .welcome-title { font-size: 1.75rem; }
  .welcome-hero::after { display: none; }

  .issue-card { gap: 10px; }
  .issue-stats { min-width: 110px; }

  .cs-nav { padding: 0 14px; }
  .cs-nav-ts { display: none; }
}

/* Mobile: ≤ 600px */
@media (max-width: 600px) {
  .cs-page { padding: 12px 10px; }

  /* Nav */
  .cs-nav { padding: 0 10px; height: 48px; }
  .cs-nav-name { font-size: 0.95rem; }
  .cs-nav-tag:not(.hi) { display: none; }

  /* KPI grid: 2 columns on small screens */
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-bottom: 14px;
  }
  .kpi-card { padding: 12px 14px 10px; border-radius: 12px; }
  .kpi-chip { width: 24px; height: 24px; font-size: 0.75rem; top: 10px; right: 10px; }
  .kpi-value { font-size: 1.3rem; }
  .kpi-label { font-size: 0.6rem; }
  .kpi-delta { font-size: 0.65rem; }

  /* Welcome hero */
  .welcome-hero { padding: 24px 18px; border-radius: 12px; }
  .welcome-title { font-size: 1.4rem; }
  .welcome-sub { font-size: 0.82rem; }
  .welcome-hero::before { display: none; }
  .welcome-hero::after { display: none; }

  /* Feature grid: single column */
  .feature-grid { grid-template-columns: 1fr; gap: 10px; }
  .feature-card { padding: 16px; }

  /* Issue cards: stack vertically */
  .issue-card {
    flex-direction: column;
    gap: 12px;
    padding: 14px 14px;
  }
  .issue-stats {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    min-width: unset;
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }
  .gain-badge { font-size: 0.82rem; padding: 4px 10px; }
  .issue-rank { min-width: unset; }
  .issue-page { font-size: 0.72rem; }
  .issue-action { font-size: 0.78rem; }

  /* Cannibalization cards */
  .cannib-card { padding: 14px; }
  .cannib-query { font-size: 0.88rem; }

  /* Tabs: smaller text, scrollable */
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    padding: 0 8px !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: 0.75rem !important;
    padding: 10px 10px !important;
    white-space: nowrap !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    padding: 14px !important;
  }

  /* Page header */
  .cs-ph { gap: 8px; }
  .cs-ph-title { font-size: 1.05rem; }
  .cs-health-pill { font-size: 0.72rem; padding: 6px 10px; }

  /* Metrics */
  div[data-testid="metric-container"] { padding: 10px !important; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
  }

  /* Winner / declining cards */
  .winner-card, .declining-card {
    flex-direction: column;
    gap: 10px;
    padding: 14px;
  }

  /* Sidebar collapsed control more visible on mobile */
  [data-testid="collapsedControl"] {
    top: 10px; left: 10px;
  }

  /* Block container breathing room */
  .block-container { padding: 0 !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key in ['page_df', 'query_df']:
    if key not in st.session_state:
        st.session_state[key] = None

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR  —  card-based layout, dark ink theme
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── BRAND HEADER ────────────────────────────────────────────
    st.markdown("""
    <div style="padding:20px 16px 16px;border-bottom:1px solid #1C1F2E;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">
        <div style="width:28px;height:28px;background:#5046E4;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:0.85rem;flex-shrink:0;">⚡</div>
        <div style="font-family:'Outfit',sans-serif;font-size:1.12rem;font-weight:800;color:#EEF0FF;letter-spacing:-0.3px;">
          Click<span style="color:#C8F04A;">Surge</span>
        </div>
      </div>
      <div style="font-size:0.65rem;color:#252838;letter-spacing:0.11em;text-transform:uppercase;margin-left:38px;">SEO Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    # ── DATA SOURCE CARD ────────────────────────────────────────
    st.markdown("""
    <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px 6px;margin-bottom:10px;">
      <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:9px;">Data Source</div>
    """, unsafe_allow_html=True)
    data_mode = st.radio("", ["🎲 Demo Data", "📂 Upload CSV"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    if data_mode == "🎲 Demo Data":
        # ── DEMO CONFIG CARD ────────────────────────────────────
        st.markdown("""
        <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px 8px;margin-bottom:10px;">
          <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:4px;">Demo Configuration</div>
          <div style="font-size:0.74rem;color:#30344A;line-height:1.55;margin-bottom:10px;">Generate a realistic e-commerce SEO dataset instantly.</div>
        """, unsafe_allow_html=True)
        num_pages = st.slider("Pages to generate", 20, 1000, 100, step=50)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("⚡  Generate Demo Data", use_container_width=True):
            st.session_state.page_df  = generate_demo_page_data(num_pages)
            st.session_state.query_df = generate_demo_page_query_data()
            st.success(f"✅ {num_pages} pages ready!")
    else:
        # ── HOW-TO CARD ─────────────────────────────────────────
        st.markdown("""
        <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px;margin-bottom:10px;">
          <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:8px;">How to Export from GSC</div>
          <div style="font-size:0.74rem;color:#30344A;line-height:1.75;">
            1. Open <b style="color:#5A6080;">Search Console</b><br>
            2. Performance → Search results<br>
            3. <b style="color:#5A6080;">Pages</b> tab → Export CSV<br>
            4. <b style="color:#5A6080;">Queries</b> tab → Export CSV
          </div>
          <div style="background:#0A0C14;border:1px solid #1C1F2E;border-radius:8px;padding:8px 10px;margin-top:10px;">
            <div style="font-size:0.58rem;font-weight:600;color:#252838;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px;">Auto-detected columns</div>
            <div style="font-family:'Fira Code',monospace;font-size:0.69rem;color:#5046E4;line-height:1.65;">Top pages · Clicks<br>Impressions · CTR · Position</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── UPLOAD CARD ─────────────────────────────────────────
        st.markdown("""
        <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px 6px;margin-bottom:10px;">
          <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:10px;">Upload GSC Exports</div>
        """, unsafe_allow_html=True)
        page_file  = st.file_uploader("📄 Pages CSV  (required)", type="csv", key="pu")
        query_file = st.file_uploader("📄 Queries CSV  (optional)", type="csv", key="qu")
        st.markdown("</div>", unsafe_allow_html=True)

        if page_file:
            try:
                raw_page = pd.read_csv(page_file)
                st.session_state.page_df = normalize_page_df(raw_page)
                if query_file:
                    try:
                        raw_query = pd.read_csv(query_file)
                        st.session_state.query_df = normalize_query_df(raw_query)
                        st.success(f"✅ {len(st.session_state.page_df):,} pages + {len(st.session_state.query_df):,} queries loaded!")
                    except Exception as qe:
                        st.session_state.query_df = None
                        st.warning(f"Pages loaded OK but Queries had an issue: {qe}")
                else:
                    st.session_state.query_df = None
                    st.success(f"✅ {len(st.session_state.page_df):,} pages loaded!")
            except ValueError as e:
                st.error(f"❌ Column error: {e}")
                st.info("Export from GSC → Performance → Pages → Export CSV")
            except Exception as e:
                st.error(f"❌ Could not read file: {e}")

    st.markdown("---")

    # ── DETECTION SETTINGS CARD ─────────────────────────────────
    st.markdown("""
    <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px 6px;margin-bottom:10px;">
      <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:10px;">Detection Settings</div>
    """, unsafe_allow_html=True)
    min_impressions    = st.number_input("Min Impressions",           100, 5000,  500)
    low_ctr_threshold  = st.slider("Low CTR Ratio Threshold",    0.20, 0.80, 0.55, 0.05, format="%.2f",
                                   help="Flag pages where actual CTR < X × expected CTR")
    high_imp_threshold = st.number_input("High Impression Threshold", 500, 20000, 3000)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── DATASET STATS CARD (only when data loaded) ───────────────
    if st.session_state.page_df is not None:
        df_ = st.session_state.page_df
        st.markdown("---")
        st.markdown(f"""
        <div style="background:#12141F;border:1px solid #1C1F2E;border-radius:12px;padding:13px 14px;">
          <div style="font-size:0.6rem;font-weight:700;color:#252838;text-transform:uppercase;letter-spacing:0.13em;margin-bottom:10px;">Current Dataset</div>
          <div style="display:flex;flex-direction:column;">
            <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1C1F2E;">
              <span style="font-size:0.76rem;color:#30344A;">Pages</span>
              <span style="font-family:'Fira Code',monospace;font-size:0.79rem;color:#A8B0CC;font-weight:500;">{len(df_):,}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1C1F2E;">
              <span style="font-size:0.76rem;color:#30344A;">Impressions</span>
              <span style="font-family:'Fira Code',monospace;font-size:0.79rem;color:#A8B0CC;font-weight:500;">{int(df_['impressions'].sum()):,}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1C1F2E;">
              <span style="font-size:0.76rem;color:#30344A;">Clicks</span>
              <span style="font-family:'Fira Code',monospace;font-size:0.79rem;color:#A8B0CC;font-weight:500;">{int(df_['clicks'].sum()):,}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1C1F2E;">
              <span style="font-size:0.76rem;color:#30344A;">Avg position</span>
              <span style="font-family:'Fira Code',monospace;font-size:0.79rem;color:#A8B0CC;font-weight:500;">#{df_['position'].mean():.1f}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;">
              <span style="font-size:0.76rem;color:#30344A;">Avg CTR</span>
              <span style="font-family:'Fira Code',monospace;font-size:0.79rem;color:#C8F04A;font-weight:600;">{df_['ctr'].mean():.2%}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── FOOTER ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.62rem;color:#1C1F2E;text-align:center;padding-bottom:6px;letter-spacing:0.07em;">'
        'CLICKSURGE v2.0 · SEO INTELLIGENCE</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────────
now = datetime.now().strftime("%b %d, %Y  %H:%M")
st.markdown(f"""
<div class="cs-nav">
  <div class="cs-nav-brand">
    <div class="cs-nav-icon">⚡</div>
    <div class="cs-nav-name">Click<span>Surge</span></div>
  </div>
  <div class="cs-nav-right">
    <span class="cs-nav-ts">{now}</span>
    <span class="cs-nav-tag">SEO Intelligence</span>
    <span class="cs-nav-tag hi">v2.0</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONTENT
# ─────────────────────────────────────────────
page_df  = st.session_state.page_df
query_df = st.session_state.query_df

st.markdown('<div class="cs-page">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# WELCOME
# ─────────────────────────────────────────────
if page_df is None:
    st.markdown("""
    <div class="welcome-hero">
        <div class="welcome-hero-label">Google Search Console Analytics</div>
        <div class="welcome-title">Find your hidden<br><span>SEO growth levers</span></div>
        <div class="welcome-sub">
            ClickSurge automatically detects low CTR pages, keyword cannibalization,
            declining pages, and untapped ranking opportunities — then tells you exactly what to fix.
        </div>
    </div>
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon orange">🔍</div>
            <div class="feature-name">Issue Detection</div>
            <div class="feature-desc">Position-aware CTR analysis using Google's real CTR benchmark curve. Every issue is detected relative to expected performance.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon blue">⭐</div>
            <div class="feature-name">CTR Winners</div>
            <div class="feature-desc">Identifies your star pages that beat the industry benchmark — so you can learn what's working and replicate it across your site.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon green">⚡</div>
            <div class="feature-name">Actionable Fixes</div>
            <div class="feature-desc">Every issue has a specific recommended action based on both the issue type AND page type (product, blog, category, sale).</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Select **Demo Data** in the sidebar and click **Generate Demo Data** to get started.")

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
else:
    config = {
        'min_impressions':           min_impressions,
        'low_ctr_threshold':         low_ctr_threshold,
        'low_ctr_ratio':             low_ctr_threshold,
        'high_impression_threshold': high_imp_threshold,
        'cannibalization_threshold': 2,
        'output_folder':             'reports',
    }

    with st.spinner("Analyzing SEO data..."):
        gsc_analyzer    = GSCAnalyzer(config)
        cannib_analyzer = CannibalizationAnalyzer(config)
        opp_analyzer    = OpportunityAnalyzer(config)

        issues          = gsc_analyzer.analyze_all(page_df)
        cannibalization = cannib_analyzer.find_cannibalization(query_df) if query_df is not None else pd.DataFrame()
        opportunities   = opp_analyzer.create_opportunity_report(issues, cannibalization)
        stats           = opp_analyzer.get_summary_stats(opportunities)

        # CTR Winners — pages beating industry benchmark
        ctr_winners = pd.DataFrame()
        if not page_df.empty:
            wdf = page_df.copy()
            wdf['expected_ctr'] = wdf['position'].apply(expected_ctr)
            wdf['ctr_ratio']    = wdf.apply(lambda r: ctr_performance_ratio(r['ctr'], r['position']), axis=1)
            wdf['ctr_advantage']= ((wdf['ctr'] - wdf['expected_ctr']) * wdf['impressions']).round(0).astype(int)
            ctr_winners = wdf[
                (wdf['ctr_ratio'] >= 1.25) &
                (wdf['impressions'] >= high_imp_threshold)
            ].sort_values('ctr_advantage', ascending=False).head(20)

        # Declining pages — CTR far below expected + decent impressions
        declining_pages = pd.DataFrame()
        if not page_df.empty:
            ddf = page_df.copy()
            ddf['expected_ctr'] = ddf['position'].apply(expected_ctr)
            ddf['ctr_ratio']    = ddf.apply(lambda r: ctr_performance_ratio(r['ctr'], r['position']), axis=1)
            ddf['lost_clicks']  = ((ddf['expected_ctr'] - ddf['ctr']) * ddf['impressions']).clip(lower=0).round(0).astype(int)
            declining_pages = ddf[
                (ddf['ctr_ratio'] <= 0.40) &
                (ddf['impressions'] >= high_imp_threshold)
            ].sort_values('lost_clicks', ascending=False).head(30)

    # ── PAGE HEADER + SITE HEALTH ──
    now = datetime.now().strftime("%b %d, %Y · %H:%M")
    critical_count = len(opportunities[opportunities['priority'] == 'High']) if not opportunities.empty else 0

    st.markdown(f"""
    <div class="cs-ph">
        <div>
            <div class="cs-ph-title">Site Overview</div>
            <div class="cs-ph-sub">Last analyzed: {now} &nbsp;·&nbsp; {len(page_df)} pages scanned</div>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="text-align:right;">
                <div style="font-size:0.63rem;font-weight:700;color:#8590AD;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">SITE HEALTH</div>
                <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:#F03E3E;line-height:1;">{critical_count}</div>
                <div style="font-size:0.7rem;color:#F03E3E;font-weight:600;">Critical</div>
            </div>
            <div class="cs-health-pill">⚡ {stats['total_opportunities']} issues found</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ──
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card orange">
            <div class="kpi-chip">📄</div>
            <div class="kpi-label">Pages Analyzed</div>
            <div class="kpi-value orange">{len(page_df):,}</div>
            <div class="kpi-delta">Total pages scanned</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-chip">🚨</div>
            <div class="kpi-label">High Priority</div>
            <div class="kpi-value red">{stats['high_priority']}</div>
            <div class="kpi-delta">Fix immediately</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-chip">⚠️</div>
            <div class="kpi-label">Medium Priority</div>
            <div class="kpi-value amber">{stats['medium_priority']}</div>
            <div class="kpi-delta">Fix within 30 days</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-chip">📈</div>
            <div class="kpi-label">Est. Monthly Gain</div>
            <div class="kpi-value green">+{int(stats['total_estimated_gain']):,}</div>
            <div class="kpi-delta">Clicks if all fixed</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-chip">⭐</div>
            <div class="kpi-label">CTR Winners</div>
            <div class="kpi-value blue">{len(ctr_winners)}</div>
            <div class="kpi-delta">Pages to replicate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "⚡  Quick Wins",
        "📋  All Issues",
        "⭐  CTR Winners",
        "🔎  Page Explorer",
        "📊  Analytics",
        "⚠️  Cannibalization",
        "📉  Declining Pages",
        "🔍  Query Intel",
    ])

    # ════════════════════════════════════════
    # TAB 1 — QUICK WINS
    # ════════════════════════════════════════
    with tab1:
        quick_wins = opp_analyzer.get_quick_wins(opportunities, limit=10)

        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
            <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;color:#1C1F2E;">
                ⚡ Top Growth Opportunities
            </div>
            <div style="font-size:0.76rem;color:#8590AD;">Ranked by opportunity score · position-aware CTR analysis</div>
        </div>
        """, unsafe_allow_html=True)

        if quick_wins.empty:
            st.success("✅ No major issues found — your site is performing well!")
        else:
            for i, (_, win) in enumerate(quick_wins.iterrows(), 1):
                priority  = win.get('priority', 'Low')
                badge_cls = {'High':'badge-high','Medium':'badge-medium','Low':'badge-low'}.get(priority,'badge-low')
                badge_dot = {'High':'🔴','Medium':'🟡','Low':'🟢'}.get(priority,'⚪')
                imp       = int(win.get('impressions', 0))
                ctr       = float(win.get('ctr', 0))
                exp_ctr   = float(win.get('expected_ctr', expected_ctr(win.get('position', 10))))
                pos       = float(win.get('position', 0))
                gain      = int(win.get('estimated_gain', 0))
                page      = win.get('page', 'N/A')
                itype     = win.get('type', 'Issue')
                action    = win.get('action', 'N/A')
                url_type  = win.get('url_type', classify_url(page))

                st.markdown(f"""
                <div class="issue-card">
                    <div class="issue-rank">#{i}</div>
                    <div class="issue-body">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                            <div class="issue-type">{itype}</div>
                            <span class="badge {badge_cls}">{badge_dot} {priority.upper()}</span>
                            <span style="font-size:0.67rem;color:#8590AD;background:#F4F5FA;border-radius:5px;padding:2px 7px;font-weight:600;">{url_type}</span>
                        </div>
                        <div class="issue-page">🔗 {page}</div>
                        <div class="issue-action">{action}</div>
                    </div>
                    <div class="issue-stats">
                        <div class="gain-badge">+{gain:,} clicks/mo</div>
                        <div class="stat-row">Impressions: <span>{imp:,}</span></div>
                        <div class="stat-row">CTR: <span>{ctr:.2%}</span> vs <span>{exp_ctr:.2%}</span> exp.</div>
                        <div class="stat-row">Position: <span>#{pos:.1f}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ════════════════════════════════════════
    # TAB 2 — ALL ISSUES
    # ════════════════════════════════════════
    with tab2:
        st.markdown('<div class="card-title">📋 All Detected Issues</div>', unsafe_allow_html=True)

        if not opportunities.empty:
            fa, fb, fc, fd = st.columns([2, 3, 2, 2])
            with fa:
                priority_filter = st.multiselect("🔴 Priority", ["High","Medium","Low"],
                    default=["High","Medium","Low"], key="t2_priority")
            with fb:
                type_opts = opportunities["type"].unique().tolist()
                type_filter = st.multiselect("🏷️ Issue Type", type_opts, default=type_opts, key="t2_type")
            with fc:
                sort_by = st.selectbox("↕️ Sort by",
                    ["estimated_gain","impressions","position","ctr","clicks"], key="t2_sort")
            with fd:
                sort_dir = st.radio("Order", ["Desc ↓","Asc ↑"], horizontal=True, key="t2_dir")

            fb2a, fb2b, fb2c = st.columns(3)
            with fb2a:
                min_imp_f = st.number_input("Min Impressions", 0, 100000, 0, step=500, key="t2_imp")
            with fb2b:
                max_pos_f = st.slider("Max Position", 1.0, 50.0, 50.0, 0.5, key="t2_pos")
            with fb2c:
                max_ctr_f = st.slider("Max CTR", 0.0, 1.0, 1.0, 0.01, format="%.2f", key="t2_ctr")

            url_search = st.text_input("🔍 Search URL / Keyword",
                placeholder="e.g. nike, /blog/, running-shoes", key="t2_url")

            asc = (sort_dir == "Asc ↑")
            fil = opportunities.copy()
            if priority_filter: fil = fil[fil["priority"].isin(priority_filter)]
            if type_filter:     fil = fil[fil["type"].isin(type_filter)]
            if min_imp_f > 0:   fil = fil[fil["impressions"] >= min_imp_f]
            if max_pos_f < 50:  fil = fil[fil["position"] <= max_pos_f]
            if max_ctr_f < 1.0: fil = fil[fil["ctr"] <= max_ctr_f]
            if url_search:      fil = fil[fil["page"].str.contains(url_search, case=False, na=False)]
            if sort_by in fil.columns:
                fil = fil.sort_values(sort_by, ascending=asc)

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric("Showing",       f"{len(fil)} issues")
            sm2.metric("High Priority", len(fil[fil["priority"]=="High"]))
            sm3.metric("Est. Gain",     f"+{int(fil['estimated_gain'].sum()):,} clicks")
            sm4.metric("Avg Position",  f"{fil['position'].mean():.1f}" if not fil.empty else "—")
            st.markdown("<br>", unsafe_allow_html=True)

            display_cols = [c for c in
                ["rank","page","type","priority","url_type","impressions","clicks","ctr","position","estimated_gain","action"]
                if c in fil.columns]

            st.dataframe(
                fil[display_cols].style.format({
                    "ctr":"{:.2%}","impressions":"{:,.0f}",
                    "clicks":"{:,.0f}","estimated_gain":"{:,.0f}","position":"{:.1f}",
                }),
                use_container_width=True, height=520,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            dl1, dl2 = st.columns(2)
            with dl1:
                cbuf = io.StringIO()
                fil[display_cols].to_csv(cbuf, index=False)
                st.download_button("⬇️ Export Filtered Issues CSV", data=cbuf.getvalue(),
                    file_name=f"issues_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True)
            with dl2:
                abuf = io.StringIO()
                opportunities[display_cols].to_csv(abuf, index=False)
                st.download_button("⬇️ Export All Issues CSV", data=abuf.getvalue(),
                    file_name=f"issues_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True)

    # ════════════════════════════════════════
    # TAB 3 — CTR WINNERS
    # ════════════════════════════════════════
    with tab3:
        st.markdown('<div class="card-title">⭐ CTR Winners — Pages Beating the Industry Benchmark</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.83rem;color:#8590AD;margin-bottom:20px;">'
            'These pages have a CTR significantly <strong>above</strong> what is expected for their position. '
            'Study them — their titles, meta descriptions, and schema markup are working. '
            'Replicate what makes them successful across your weaker pages.</div>',
            unsafe_allow_html=True
        )

        if ctr_winners.empty:
            st.info("No CTR Winners detected. Try lowering the High Impression Threshold in the sidebar.")
        else:
            wm1, wm2, wm3, wm4 = st.columns(4)
            wm1.metric("⭐ Star Pages",         len(ctr_winners))
            wm2.metric("Avg CTR Ratio",          f"{ctr_winners['ctr_ratio'].mean():.1%} of benchmark")
            wm3.metric("Extra Clicks Generated", f"+{int(ctr_winners['ctr_advantage'].sum()):,}/mo")
            wm4.metric("Avg Position",           f"#{ctr_winners['position'].mean():.1f}")
            st.markdown("<br>", unsafe_allow_html=True)

            for i, (_, row) in enumerate(ctr_winners.iterrows(), 1):
                page        = row['page']
                pos         = row['position']
                ctr         = row['ctr']
                exp         = row['expected_ctr']
                ratio       = row['ctr_ratio']
                advantage   = int(row['ctr_advantage'])
                imp         = int(row['impressions'])
                clk         = int(row['clicks'])
                url_type    = classify_url(page)
                pct_above   = (ratio - 1) * 100

                st.markdown(f"""
                <div class="winner-card">
                    <div class="issue-rank" style="color:#2BB44A;">#{i}</div>
                    <div class="issue-body">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                            <div class="issue-type" style="color:#2BB44A;">CTR WINNER</div>
                            <span style="font-size:0.67rem;background:rgba(43,180,74,0.1);color:#1A6B2E;border:1px solid rgba(43,180,74,0.3);border-radius:12px;padding:2px 8px;font-weight:700;">
                                +{pct_above:.0f}% above benchmark
                            </span>
                            <span style="font-size:0.67rem;color:#8590AD;background:#F4F5FA;border-radius:5px;padding:2px 7px;font-weight:600;">{url_type}</span>
                        </div>
                        <div class="issue-page">🔗 {page}</div>
                        <div style="font-size:0.82rem;color:#2E3550;line-height:1.6;background:#F4FFF7;border-left:3px solid #2BB44A;padding:8px 12px;border-radius:0 8px 8px 0;">
                            <strong>Why it works:</strong> Position #{pos:.1f} normally gets {exp:.1%} CTR — this page gets {ctr:.1%}.
                            Study the title tag and meta description. Apply the same formula to your low CTR pages at similar positions.
                            {f"As a {url_type} page, likely uses {'review schema / star ratings' if url_type=='product' else 'FAQ schema / rich snippets' if url_type=='blog' else 'strong category keywords'}." }
                        </div>
                    </div>
                    <div class="issue-stats">
                        <div class="winner-badge">+{advantage:,} bonus clicks/mo</div>
                        <div class="stat-row">CTR: <span>{ctr:.2%}</span></div>
                        <div class="stat-row">Expected: <span>{exp:.2%}</span></div>
                        <div class="stat-row">Impressions: <span>{imp:,}</span></div>
                        <div class="stat-row">Clicks: <span>{clk:,}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            wex = io.StringIO()
            ctr_winners[['page','position','ctr','expected_ctr','ctr_ratio','ctr_advantage','impressions','clicks']].to_csv(wex, index=False)
            st.download_button("⬇️ Export CTR Winners CSV", data=wex.getvalue(),
                file_name=f"ctr_winners_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv", use_container_width=True)

    # ════════════════════════════════════════
    # TAB 4 — PAGE EXPLORER
    # ════════════════════════════════════════
    with tab4:
        st.markdown('<div class="card-title">🔎 Page Explorer — Browse All Pages</div>', unsafe_allow_html=True)

        pe1, pe2, pe3 = st.columns([4, 2, 2])
        with pe1:
            pe_search = st.text_input("🔍 Search URL", placeholder="e.g. nike, /blog/, /product/", key="pe_url")
        with pe2:
            pe_sort = st.selectbox("Sort by", ["impressions","clicks","ctr","position"], key="pe_sort")
        with pe3:
            pe_dir = st.radio("Order", ["Desc ↓","Asc ↑"], horizontal=True, key="pe_dir")

        if "page_type" in page_df.columns:
            ptypes  = sorted(page_df["page_type"].unique().tolist())
            pe_type = st.multiselect("Page Type", ptypes, default=ptypes, key="pe_ptype")
        else:
            pe_type = []

        sr1, sr2, sr3, sr4 = st.columns(4)
        with sr1:
            imp_range = st.slider("Impressions",
                int(page_df["impressions"].min()), int(page_df["impressions"].max()),
                (int(page_df["impressions"].min()), int(page_df["impressions"].max())), key="pe_imp")
        with sr2:
            pos_range = st.slider("Position", 1.0, 50.0, (1.0, 50.0), 0.5, key="pe_pos")
        with sr3:
            ctr_range = st.slider("CTR (%)", 0.0, 100.0, (0.0, 100.0), 0.5, key="pe_ctr")
        with sr4:
            clk_range = st.slider("Clicks",
                int(page_df["clicks"].min()), int(page_df["clicks"].max()),
                (int(page_df["clicks"].min()), int(page_df["clicks"].max())), key="pe_clk")

        pe_df = page_df.copy()
        if pe_search:
            pe_df = pe_df[pe_df["page"].str.contains(pe_search, case=False, na=False)]
        if pe_type and "page_type" in pe_df.columns:
            pe_df = pe_df[pe_df["page_type"].isin(pe_type)]
        pe_df = pe_df[
            (pe_df["impressions"] >= imp_range[0]) & (pe_df["impressions"] <= imp_range[1]) &
            (pe_df["position"]    >= pos_range[0]) & (pe_df["position"]    <= pos_range[1]) &
            (pe_df["ctr"]         >= ctr_range[0]/100) & (pe_df["ctr"]     <= ctr_range[1]/100) &
            (pe_df["clicks"]      >= clk_range[0]) & (pe_df["clicks"]      <= clk_range[1])
        ]
        pe_df = pe_df.sort_values(pe_sort, ascending=(pe_dir=="Asc ↑")).reset_index(drop=True)
        pe_df.index = pe_df.index + 1

        pm1, pm2, pm3, pm4, pm5 = st.columns(5)
        pm1.metric("Pages Shown",       f"{len(pe_df):,}")
        pm2.metric("Total Impressions",  f"{int(pe_df['impressions'].sum()):,}" if not pe_df.empty else "—")
        pm3.metric("Total Clicks",       f"{int(pe_df['clicks'].sum()):,}" if not pe_df.empty else "—")
        pm4.metric("Avg CTR",            f"{pe_df['ctr'].mean():.2%}" if not pe_df.empty else "—")
        pm5.metric("Avg Position",       f"{pe_df['position'].mean():.1f}" if not pe_df.empty else "—")
        st.markdown("<br>", unsafe_allow_html=True)

        def flag_page(row):
            pos = row["position"]; ctr = row["ctr"]; imp = row["impressions"]
            exp = expected_ctr(pos)
            ratio = ctr / exp if exp > 0 else 1
            flags = []
            if ratio >= 1.25 and imp >= high_imp_threshold:     flags.append("⭐ CTR Winner")
            elif ratio < 0.40 and imp >= high_imp_threshold:    flags.append("🔴 Low CTR")
            elif 8 <= pos <= 12 and imp >= high_imp_threshold:  flags.append("🟡 Low Hanging")
            elif row["clicks"] <= 5 and imp >= 2000:            flags.append("⚠️ Zero Clicks")
            elif 10 < pos <= 15 and imp >= high_imp_threshold:  flags.append("📌 Page 2 Trap")
            return " ".join(flags) if flags else "✅ Normal"

        if not pe_df.empty:
            pe_show = pe_df.copy()
            pe_show["exp_ctr"]   = pe_show["position"].apply(expected_ctr)
            pe_show["Status"]    = pe_show.apply(flag_page, axis=1)
            pe_show["CTR"]       = pe_show["ctr"].apply(lambda x: f"{x:.2%}")
            pe_show["Exp. CTR"]  = pe_show["exp_ctr"].apply(lambda x: f"{x:.2%}")
            pe_show["Position"]  = pe_show["position"].apply(lambda x: f"#{x:.1f}")
            pe_show["Impr."]     = pe_show["impressions"].apply(lambda x: f"{x:,}")
            pe_show["Clicks"]    = pe_show["clicks"].apply(lambda x: f"{x:,}")

            cols = {"page":"Page URL","Impr.":"Impressions","Clicks":"Clicks",
                    "CTR":"CTR","Exp. CTR":"Expected CTR","Position":"Position","Status":"Status"}
            if "page_type" in pe_show.columns:
                cols["page_type"] = "Page Type"

            st.markdown(
                f'<div style="font-size:0.77rem;color:#8590AD;margin-bottom:10px;">'
                f'Showing <strong style="color:#1C1F2E">{len(pe_df):,}</strong> of '
                f'<strong style="color:#1C1F2E">{len(page_df):,}</strong> total pages</div>',
                unsafe_allow_html=True
            )
            st.dataframe(pe_show[[c for c in cols.keys() if c in pe_show.columns]].rename(columns=cols),
                use_container_width=True, height=580)

            st.markdown("<br>", unsafe_allow_html=True)
            ex1, ex2 = st.columns(2)
            with ex1:
                pe_csv = io.StringIO(); pe_df.to_csv(pe_csv, index=False)
                st.download_button("⬇️ Export Filtered Pages CSV", data=pe_csv.getvalue(),
                    file_name=f"pages_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True)
            with ex2:
                all_csv = io.StringIO(); page_df.to_csv(all_csv, index=False)
                st.download_button("⬇️ Export All Pages CSV", data=all_csv.getvalue(),
                    file_name=f"all_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True)

    # ════════════════════════════════════════
    # TAB 5 — ANALYTICS
    # ════════════════════════════════════════
    with tab5:
        PLOT_BG = PAPER_BG = "#ffffff"
        GRID_CLR = "#F0F1F8"; FONT_CLR = "#8590AD"; ACCENT = "#5046E4"

        def base_layout(title=""):
            return dict(
                paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                font=dict(family="Plus Jakarta Sans, sans-serif", color=FONT_CLR, size=12),
                title=dict(text=title, font=dict(family="Outfit,sans-serif", size=14, color="#1C1F2E"), x=0),
                margin=dict(l=20, r=20, t=44, b=20),
                xaxis=dict(gridcolor=GRID_CLR, linecolor="#E4E7F0", showline=True, tickfont=dict(size=11)),
                yaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, showline=False, tickfont=dict(size=11)),
            )

        # Row 1
        r1a, r1b = st.columns(2)
        with r1a:
            bins   = [0,3,6,10,15,20,100]
            labels = ["#1–3","#4–6","#7–10","#11–15","#16–20","21+"]
            pf = page_df.copy()
            pf["pos_bucket"] = pd.cut(pf["position"], bins=bins, labels=labels, right=True)

            fig1 = go.Figure()
            bucket_stats = pf.groupby("pos_bucket", observed=True).agg(
                actual_ctr=("ctr","mean"), pages=("page","count")).reset_index()
            bucket_stats["actual_pct"]   = (bucket_stats["actual_ctr"] * 100).round(2)
            bucket_stats["bucket_str"]   = bucket_stats["pos_bucket"].astype(str)

            midpoints = {
                "#1–3": expected_ctr(2)*100, "#4–6": expected_ctr(5)*100,
                "#7–10": expected_ctr(8.5)*100, "#11–15": expected_ctr(13)*100,
                "#16–20": expected_ctr(18)*100, "21+": 0.2
            }
            bucket_stats["expected_pct"] = bucket_stats["bucket_str"].map(midpoints)

            fig1.add_trace(go.Bar(
                x=bucket_stats["bucket_str"], y=bucket_stats["expected_pct"],
                name="Expected (Industry)", marker_color="#E4E7F0", marker_line_width=0, width=0.4,
                text=[f"{v:.1f}%" for v in bucket_stats["expected_pct"]],
                textposition="outside", textfont=dict(size=10, color="#8590AD"),
            ))
            fig1.add_trace(go.Bar(
                x=bucket_stats["bucket_str"], y=bucket_stats["actual_pct"],
                name="Your Site", marker_color=ACCENT, marker_line_width=0, width=0.4,
                text=[f"{v:.1f}%" for v in bucket_stats["actual_pct"]],
                textposition="outside", textfont=dict(size=11, color="#1C1F2E"),
            ))
            fig1.update_layout(**base_layout("Actual vs Expected CTR by Position"),
                yaxis_ticksuffix="%", barmode="group",
                legend=dict(orientation="h", y=-0.18, x=0, xanchor="left"))
            st.plotly_chart(fig1, use_container_width=True)

        with r1b:
            if not opportunities.empty:
                tc = opportunities["type"].value_counts().reset_index()
                tc.columns = ["Issue Type","Count"]
                colors_map = {"Low CTR":ACCENT,"Low Hanging Fruit":"#3B82F6",
                              "Page 2 Trap":"#F59F00","Zero Clicks":"#8B5CF6",
                              "Keyword Cannibalization":"#EC4899"}
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=tc["Issue Type"], y=tc["Count"], text=tc["Count"],
                    textposition="outside", textfont=dict(size=12, color="#1C1F2E"),
                    marker_color=[colors_map.get(t,"#8590AD") for t in tc["Issue Type"]],
                    marker_line_width=0, width=0.55,
                ))
                fig2.update_layout(**base_layout("Issues Found by Type"), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

        # Row 2
        r2a, r2b = st.columns(2)
        with r2a:
            if not opportunities.empty:
                pc = opportunities["priority"].value_counts()
                priority_order  = [p for p in ["High","Medium","Low"] if p in pc.index]
                priority_colors = {"High":"#F03E3E","Medium":"#F59F00","Low":"#2BB44A"}
                fig3 = go.Figure(data=[go.Pie(
                    labels=priority_order,
                    values=[pc[p] for p in priority_order],
                    hole=0.65,
                    marker=dict(colors=[priority_colors[p] for p in priority_order],
                                line=dict(color="#ffffff", width=3)),
                    textinfo="label+percent", textfont_size=12, direction="clockwise", sort=False,
                )])
                fig3.add_annotation(
                    text=f"<b>{stats['total_opportunities']}</b><br>Issues",
                    x=0.5, y=0.5, font_size=16, showarrow=False,
                    font=dict(family="Outfit, sans-serif", color="#1C1F2E")
                )
                fig3.update_layout(
                    paper_bgcolor=PAPER_BG,
                    font=dict(family="Plus Jakarta Sans, sans-serif", color=FONT_CLR),
                    title=dict(text="Priority Breakdown", font=dict(family="Outfit,sans-serif", size=14, color="#1C1F2E"), x=0),
                    margin=dict(l=20,r=20,t=44,b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0.5, xanchor="center"),
                )
                st.plotly_chart(fig3, use_container_width=True)

        with r2b:
            if not opportunities.empty:
                top_pages = (opportunities.groupby("page")["estimated_gain"]
                    .sum().sort_values(ascending=True).tail(8).reset_index())
                top_pages["label"] = top_pages["page"].apply(lambda x: ("…"+x[-32:]) if len(x)>35 else x)
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(
                    y=top_pages["label"], x=top_pages["estimated_gain"], orientation="h",
                    text=[f"+{v:,}" for v in top_pages["estimated_gain"]],
                    textposition="outside", textfont=dict(size=11, color="#1C1F2E"),
                    marker=dict(color=top_pages["estimated_gain"],
                                colorscale=[[0,"#C8F04A"],[1,ACCENT]], line=dict(width=0)),
                    width=0.65,
                ))
                fig4.update_layout(**base_layout("Top Pages by Estimated Gain"), showlegend=False,
                    xaxis_title="Estimated clicks/month")
                fig4.update_yaxes(tickfont=dict(size=10), categoryorder="total ascending")
                st.plotly_chart(fig4, use_container_width=True)

        # Row 3
        r3a, r3b = st.columns(2)
        with r3a:
            fig5 = go.Figure()
            fig5.add_trace(go.Histogram(
                x=page_df["impressions"], nbinsx=30,
                marker_color="#3B82F6", marker_line_color="#ffffff", marker_line_width=1, opacity=0.85,
            ))
            fig5.update_layout(**base_layout("Impressions Distribution"),
                bargap=0.08, showlegend=False,
                xaxis_title="Monthly Impressions", yaxis_title="Number of Pages")
            st.plotly_chart(fig5, use_container_width=True)

        with r3b:
            sample_df = page_df.nlargest(80, "impressions").copy()
            sample_df["expected_ctr"] = sample_df["position"].apply(expected_ctr)
            sample_df["ctr_ratio"]    = sample_df.apply(lambda r: ctr_performance_ratio(r["ctr"], r["position"]), axis=1)
            fig6 = go.Figure()
            colors_scatter = sample_df["ctr_ratio"].apply(
                lambda r: "#2BB44A" if r >= 1.2 else ("#F03E3E" if r < 0.5 else "#F59F00"))
            fig6.add_trace(go.Scatter(
                x=sample_df["position"], y=sample_df["ctr"],
                mode="markers",
                marker=dict(size=sample_df["impressions"]/sample_df["impressions"].max()*30+6,
                            color=list(colors_scatter), opacity=0.75,
                            line=dict(width=1.5, color="#ffffff")),
                hovertemplate="<b>%{customdata}</b><br>Pos: %{x:.1f} | CTR: %{y:.1%}<extra></extra>",
                customdata=sample_df["page"].apply(lambda x: x[-40:]),
            ))
            pos_range_vals = sorted(sample_df["position"].unique())
            exp_line = [expected_ctr(p) for p in pos_range_vals]
            fig6.add_trace(go.Scatter(
                x=pos_range_vals, y=exp_line, mode="lines", name="Expected CTR",
                line=dict(color="#3B82F6", width=2, dash="dash"),
            ))
            fig6.update_layout(
                **base_layout("CTR vs Position — Green=Winner, Amber=OK, Red=Low"),
                legend=dict(orientation="h", y=-0.18))
            fig6.update_yaxes(tickformat=".1%")
            st.plotly_chart(fig6, use_container_width=True)

        # Row 4 — CTR Benchmark + Opportunity by URL type
        st.markdown("---")
        bench_a, bench_b = st.columns(2)

        with bench_a:
            bins2   = [0,1,2,3,4,5,6,7,8,9,10,12,15,20,100]
            labels2 = ["1","2","3","4","5","6","7","8","9","10","11-12","13-15","16-20","21+"]
            import pandas as _pd
            pf2 = page_df.copy()
            pf2["pos_bucket"] = _pd.cut(pf2["position"], bins=bins2, labels=labels2, right=True)
            actual_by_pos = pf2.groupby("pos_bucket", observed=True)["ctr"].mean().reset_index()
            actual_by_pos.columns = ["Position","Actual CTR"]
            bench_data = [{"Position": str(p), "Expected CTR": v} for p, v in CTR_CURVE.items() if p <= 15]
            bench_df   = _pd.DataFrame(bench_data)
            merged     = actual_by_pos.merge(bench_df, on="Position", how="left").dropna()

            fig_bench = go.Figure()
            fig_bench.add_trace(go.Scatter(
                x=merged["Position"], y=(merged["Expected CTR"]*100).round(2),
                mode="lines+markers", name="Expected (Industry)",
                line=dict(color="#3B82F6", width=2, dash="dash"), marker=dict(size=7, color="#3B82F6"),
            ))
            fig_bench.add_trace(go.Scatter(
                x=merged["Position"], y=(merged["Actual CTR"]*100).round(2),
                mode="lines+markers", name="Your Site",
                line=dict(color=ACCENT, width=2.5), marker=dict(size=8, color=ACCENT),
                fill="tonexty", fillcolor="rgba(80,70,228,0.08)",
            ))
            fig_bench.update_layout(**base_layout("CTR Benchmark: Your Site vs Industry Average"),
                yaxis_ticksuffix="%", legend=dict(orientation="h", y=-0.18))
            st.plotly_chart(fig_bench, use_container_width=True)

        with bench_b:
            if not opportunities.empty and "url_type" in opportunities.columns:
                url_perf = opportunities.groupby("url_type").agg(
                    pages=("page","count"), total_gain=("estimated_gain","sum"),
                ).reset_index().sort_values("total_gain", ascending=False)
                fig_url = px.bar(url_perf, x="url_type", y="total_gain",
                    text="total_gain", color="total_gain",
                    color_continuous_scale=["#C8F04A", ACCENT], template="plotly_white",
                    labels={"url_type":"Page Type","total_gain":"Total Gain (clicks/mo)"})
                fig_url.update_traces(texttemplate="+%{text:,}", textposition="outside",
                    marker_line_width=0, width=0.6)
                fig_url.update_coloraxes(showscale=False)
                fig_url.update_layout(**base_layout("Opportunity by URL Type"), showlegend=False)
                st.plotly_chart(fig_url, use_container_width=True)

        # Audit snapshot
        from utils.storage import get_trend_data, save_audit_snapshot
        trend = get_trend_data()
        hcol1, hcol2 = st.columns([4,1])
        with hcol2:
            if st.button("💾 Save Audit Snapshot", use_container_width=True):
                save_audit_snapshot(stats, label=f"Audit {datetime.now().strftime('%b %d %H:%M')}")
                st.success("Snapshot saved!")
        if len(trend) >= 2:
            with hcol1:
                tr_df = pd.DataFrame(trend)
                fig_t = go.Figure()
                fig_t.add_trace(go.Scatter(
                    x=tr_df["label"], y=tr_df["total_issues"], mode="lines+markers+text",
                    name="Total Issues", text=tr_df["total_issues"], textposition="top center",
                    line=dict(color=ACCENT, width=2), marker=dict(size=8, color=ACCENT),
                ))
                fig_t.add_trace(go.Scatter(
                    x=tr_df["label"], y=tr_df["high_priority"], mode="lines+markers",
                    name="High Priority", line=dict(color="#F03E3E", width=2, dash="dot"),
                    marker=dict(size=7, color="#F03E3E"),
                ))
                fig_t.update_layout(**base_layout("Issue Trend Over Time"),
                    legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig_t, use_container_width=True)

    # ════════════════════════════════════════
    # TAB 6 — CANNIBALIZATION
    # ════════════════════════════════════════
    with tab6:
        st.markdown('<div class="card-title">⚠️ Keyword Cannibalization</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.83rem;color:#8590AD;margin-bottom:20px;">'
            'Multiple pages competing for the same keyword — splitting impressions and clicks. '
            'Consolidate weaker pages into the dominant page.</div>',
            unsafe_allow_html=True
        )

        if cannibalization.empty:
            if query_df is None:
                st.warning("⚠️ No page-query data. Use Demo Mode (includes query data) or upload a page-query CSV.")
            else:
                st.success("✅ No cannibalization detected!")
        else:
            total_recoverable = int(cannibalization["estimated_gain"].sum())
            st.markdown(
                f'<div style="background:#FFFDF0;border:1px solid rgba(245,159,0,0.3);border-radius:10px;'
                f'padding:12px 16px;margin-bottom:20px;font-size:0.85rem;color:#6B4500;">'
                f'⚠️ <strong>{len(cannibalization)} keywords</strong> have competing pages. '
                f'Consolidating could recover <strong>+{total_recoverable:,} clicks/month</strong>.'
                f'</div>',
                unsafe_allow_html=True
            )

            for _, row in cannibalization.iterrows():
                query      = row["query"]
                page_count = int(row["competing_pages"])
                total_imp  = int(row["total_query_impressions"])
                priority   = row["priority"]
                est_gain   = int(row["estimated_gain"])
                action     = row["action"]
                wasted     = int(row.get("wasted_clicks", 0))
                border_col = "#F03E3E" if priority == "High" else "#F59F00"

                st.markdown(f"""
                <div class="cannib-card" style="border-left-color:{border_col};">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;">
                        <div class="cannib-query">"{query}"</div>
                        <div class="gain-badge" style="font-size:0.78rem;padding:4px 10px;">+{est_gain:,} clicks/mo recoverable</div>
                    </div>
                    <div class="cannib-meta">{page_count} competing pages · {total_imp:,} total impressions · {wasted:,} clicks wasted</div>
                    <div class="cannib-action">{action}</div>
                </div>
                """, unsafe_allow_html=True)

                if "_raw_group" in cannibalization.columns and isinstance(row.get("_raw_group"), list):
                    raw = pd.DataFrame(row["_raw_group"])
                    disp_cols = [c for c in ["page","impressions","clicks","position","ctr"] if c in raw.columns]
                    disp = raw[disp_cols].copy()
                    if "ctr" in disp.columns:         disp["ctr"]         = disp["ctr"].apply(lambda x: f"{x:.2%}")
                    if "position" in disp.columns:    disp["position"]    = disp["position"].apply(lambda x: f"#{x:.1f}")
                    if "impressions" in disp.columns: disp["impressions"] = disp["impressions"].apply(lambda x: f"{int(x):,}")
                    st.dataframe(disp.rename(columns={"page":"Page","impressions":"Impressions",
                        "clicks":"Clicks","position":"Position","ctr":"CTR"}),
                        use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    # TAB 7 — DECLINING PAGES
    # ════════════════════════════════════════
    with tab7:
        st.markdown('<div class="card-title">📉 Declining Pages — CTR Far Below Position Benchmark</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.83rem;color:#8590AD;margin-bottom:20px;">'
            'Pages where actual CTR is critically below the expected benchmark for their position. '
            'These pages are hemorrhaging clicks — their title tags or meta descriptions are likely broken, '
            'outdated, or misaligned with search intent.</div>',
            unsafe_allow_html=True
        )

        if declining_pages.empty:
            st.success("✅ No severely declining pages detected!")
        else:
            dm1, dm2, dm3, dm4 = st.columns(4)
            dm1.metric("Declining Pages",    len(declining_pages))
            dm2.metric("Total Clicks Lost",  f"-{int(declining_pages['lost_clicks'].sum()):,}/mo")
            dm3.metric("Avg CTR Ratio",      f"{declining_pages['ctr_ratio'].mean():.0%} of benchmark")
            dm4.metric("Avg Position",       f"#{declining_pages['position'].mean():.1f}")
            st.markdown("<br>", unsafe_allow_html=True)

            dc1, dc2 = st.columns([3,2])
            with dc1:
                dec_search = st.text_input("🔍 Filter by URL", placeholder="e.g. /product/, nike", key="dec_search")
            with dc2:
                dec_sort = st.selectbox("Sort by", ["lost_clicks","impressions","ctr_ratio","position"], key="dec_sort")

            d_df = declining_pages.copy()
            if dec_search:
                d_df = d_df[d_df["page"].str.contains(dec_search, case=False, na=False)]
            d_df = d_df.sort_values(dec_sort, ascending=(dec_sort=="ctr_ratio")).reset_index(drop=True)

            for i, (_, row) in enumerate(d_df.head(25).iterrows(), 1):
                page      = row["page"]
                pos       = row["position"]
                ctr       = row["ctr"]
                exp       = row["expected_ctr"]
                ratio     = row["ctr_ratio"]
                lost      = int(row["lost_clicks"])
                imp       = int(row["impressions"])
                url_type  = classify_url(page)
                pct_below = (1 - ratio) * 100

                st.markdown(f"""
                <div class="declining-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                                <span style="font-size:0.67rem;font-weight:700;color:#F03E3E;text-transform:uppercase;letter-spacing:0.09em;">DECLINING CTR</span>
                                <span style="font-size:0.67rem;background:rgba(240,62,62,0.1);color:#C0000C;border:1px solid rgba(240,62,62,0.25);border-radius:12px;padding:2px 8px;font-weight:700;">
                                    {pct_below:.0f}% below benchmark
                                </span>
                                <span style="font-size:0.67rem;color:#8590AD;background:#F4F5FA;border-radius:5px;padding:2px 7px;font-weight:600;">{url_type}</span>
                            </div>
                            <div style="font-family:'Fira Code',monospace;font-size:0.78rem;color:#3B82F6;font-weight:500;word-break:break-all;">🔗 {page}</div>
                        </div>
                        <div style="text-align:right;min-width:126px;">
                            <div style="background:rgba(240,62,62,0.1);color:#C0000C;border:1px solid rgba(240,62,62,0.25);border-radius:8px;padding:6px 12px;font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:800;">
                                -{lost:,} clicks/mo
                            </div>
                        </div>
                    </div>
                    <div style="font-size:0.82rem;color:#3A4260;background:rgba(240,62,62,0.05);border-left:3px solid #F03E3E;padding:8px 12px;border-radius:0 8px 8px 0;line-height:1.6;">
                        Position #{pos:.1f} should get {exp:.1%} CTR — this page only gets {ctr:.1%} ({ratio:.0%} of benchmark).
                        {imp:,} impressions/month are wasted.
                        <strong>Action:</strong> Audit the title tag for relevance and click-worthiness.
                        {'Add review schema markup.' if url_type=='product' else 'Add FAQ schema or listicle format.' if url_type=='blog' else 'Ensure title matches category intent.'}
                        Compare to top-ranking competitors for this query.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            dec_csv = io.StringIO()
            d_df[["page","position","ctr","expected_ctr","ctr_ratio","lost_clicks","impressions","clicks"]].to_csv(dec_csv, index=False)
            st.download_button("⬇️ Export Declining Pages CSV", data=dec_csv.getvalue(),
                file_name=f"declining_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv", use_container_width=True)

    # ════════════════════════════════════════
    # TAB 8 — QUERY INTEL
    # ════════════════════════════════════════
    with tab8:
        st.markdown('<div class="card-title">🔍 Query Intel — Search Query Analysis + Page Matching</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.83rem;color:#8590AD;margin-bottom:20px;">'
            'Analyses your GSC query data independently and matches every search query to its most likely '
            'serving page — giving you a combined view of query-level and page-level performance. '
            'Ideal for spotting queries where the page is ranking but the title/meta is failing to convert impressions into clicks.</div>',
            unsafe_allow_html=True
        )

        if query_df is None:
            st.warning("⚠️ No Queries CSV uploaded. Upload your GSC Queries export using the sidebar to enable this tab.")
            st.info("In GSC → Performance → Search results → **Queries tab** → Export CSV")
        else:
            # Run the query analyzer
            with st.spinner("Analysing queries and matching to pages..."):
                q_analyzer   = QueryAnalyzer(config)
                q_combined   = q_analyzer.analyze(query_df, page_df)
                q_issues     = q_analyzer.get_query_issues(q_combined)
                q_gap        = q_analyzer.get_gap_analysis(q_combined)
                q_stats      = q_analyzer.get_summary_stats(q_combined)

            # ── KPI row ──────────────────────────────────────────────────────
            qk1, qk2, qk3, qk4, qk5 = st.columns(5)
            qk1.metric("Total Queries",    f"{q_stats['total_queries']:,}")
            qk2.metric("Matched to Pages", f"{q_stats['matched_queries']:,}",
                       delta=f"{q_stats['matched_queries']/max(q_stats['total_queries'],1):.0%} match rate")
            qk3.metric("Query Issues",     f"{q_stats['total_issues']}")
            qk4.metric("High Priority",    f"{q_stats['high_priority']}")
            qk5.metric("Est. Opp. Clicks", f"+{q_stats['total_opp_clicks']:,}/mo")
            st.markdown("<br>", unsafe_allow_html=True)

            # ── SUB-TABS ─────────────────────────────────────────────────────
            qt1, qt2, qt3 = st.tabs([
                "🚨  Query Issues",
                "⚡  Gap Analysis",
                "🔗  Combined Table",
            ])

            # ── QUERY ISSUES ─────────────────────────────────────────────────
            with qt1:
                st.markdown("""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
                    <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#1C1F2E;">Query-Level Issues</div>
                    <div style="font-size:0.75rem;color:#8590AD;">Queries with below-benchmark CTR for their position</div>
                </div>
                """, unsafe_allow_html=True)

                if q_issues.empty:
                    st.success("✅ No significant query issues found.")
                else:
                    # Filter bar
                    qf1, qf2, qf3 = st.columns([3, 2, 2])
                    with qf1:
                        qi_search = st.text_input("🔍 Filter queries", placeholder="e.g. accessories, crash guard", key="qi_search")
                    with qf2:
                        qi_issue_filter = st.multiselect("Issue type",
                            q_issues['q_issue'].unique().tolist(),
                            default=q_issues['q_issue'].unique().tolist(), key="qi_type")
                    with qf3:
                        qi_pri = st.multiselect("Priority", ["High","Medium","Low"],
                            default=["High","Medium","Low"], key="qi_pri")

                    qi_df = q_issues.copy()
                    if qi_search:
                        qi_df = qi_df[qi_df['query'].str.contains(qi_search, case=False, na=False)]
                    if qi_issue_filter:
                        qi_df = qi_df[qi_df['q_issue'].isin(qi_issue_filter)]
                    if qi_pri:
                        qi_df = qi_df[qi_df['q_priority'].isin(qi_pri)]

                    st.markdown(f'<div style="font-size:0.76rem;color:#8590AD;margin-bottom:12px;">Showing <b style="color:#1C1F2E">{len(qi_df)}</b> issues</div>', unsafe_allow_html=True)

                    for i, (_, row) in enumerate(qi_df.head(30).iterrows(), 1):
                        query      = row['query']
                        issue      = row['q_issue']
                        priority   = row['q_priority']
                        imp        = int(row['q_impressions'])
                        clk        = int(row['q_clicks'])
                        ctr        = float(row['q_ctr'])
                        exp_ctr    = float(row['q_expected_ctr'])
                        pos        = float(row['q_position'])
                        opp        = int(row['q_opportunity_clicks'])
                        action     = row['q_action']
                        page       = row.get('matched_page') or '—'
                        page_ctr   = row.get('page_ctr')
                        page_pos   = row.get('page_position')
                        ratio      = float(row['q_ctr_ratio'])

                        badge_cls  = {'High':'badge-high','Medium':'badge-medium','Low':'badge-low'}.get(priority,'badge-low')
                        badge_dot  = {'High':'🔴','Medium':'🟡','Low':'🟢'}.get(priority,'⚪')
                        issue_col  = {'Low CTR Query':'#5046E4','Low Hanging Query':'#F59F00',
                                      'Zero Click Query':'#F03E3E','Page 2 Query':'#8B5CF6'}.get(issue,'#8590AD')

                        page_info = ''
                        if page != '—' and page_ctr is not None:
                            ctr_delta = ctr - page_ctr
                            delta_str = f"+{ctr_delta:.1%}" if ctr_delta >= 0 else f"{ctr_delta:.1%}"
                            page_info = f"""
                            <div style="margin-top:10px;padding:9px 12px;background:#F8F9FF;border:1px solid #E4E7F0;border-radius:8px;">
                                <div style="font-size:0.65rem;font-weight:700;color:#8590AD;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:5px;">Matched Page</div>
                                <div style="font-family:'Fira Code',monospace;font-size:0.74rem;color:#3B82F6;word-break:break-all;margin-bottom:6px;">🔗 {page}</div>
                                <div style="display:flex;gap:16px;font-size:0.72rem;color:#8590AD;">
                                    <span>Page CTR: <b style="color:#1C1F2E">{page_ctr:.2%}</b></span>
                                    <span>Query CTR: <b style="color:#1C1F2E">{ctr:.2%}</b></span>
                                    <span>Page pos: <b style="color:#1C1F2E">#{page_pos:.1f}</b></span>
                                    <span>CTR delta: <b style="color:{'#2BB44A' if ctr_delta>=0 else '#F03E3E'}">{delta_str}</b></span>
                                </div>
                            </div>"""

                        st.markdown(f"""
                        <div class="issue-card">
                            <div class="issue-rank">#{i}</div>
                            <div class="issue-body">
                                <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;">
                                    <span style="font-size:0.66rem;font-weight:700;color:{issue_col};text-transform:uppercase;letter-spacing:0.09em;">{issue}</span>
                                    <span class="badge {badge_cls}">{badge_dot} {priority.upper()}</span>
                                </div>
                                <div style="font-family:'Outfit',sans-serif;font-size:0.95rem;font-weight:700;color:#1C1F2E;margin-bottom:8px;">"{query}"</div>
                                <div class="issue-action">{action}</div>
                                {page_info}
                            </div>
                            <div class="issue-stats">
                                <div class="gain-badge">+{opp:,} clicks/mo</div>
                                <div class="stat-row">Impressions: <span>{imp:,}</span></div>
                                <div class="stat-row">CTR: <span>{ctr:.2%}</span> vs <span>{exp_ctr:.2%}</span> exp.</div>
                                <div class="stat-row">Position: <span>#{pos:.1f}</span></div>
                                <div class="stat-row">CTR ratio: <span>{ratio:.0%}</span> of benchmark</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    qi_csv = io.StringIO()
                    qi_df.to_csv(qi_csv, index=False)
                    st.download_button("⬇️ Export Query Issues CSV", data=qi_csv.getvalue(),
                        file_name=f"query_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv", use_container_width=True)

            # ── GAP ANALYSIS ────────────────────────────────────────────────
            with qt2:
                st.markdown("""
                <div style="background:#F5F6FF;border:1px solid rgba(80,70,228,0.15);border-radius:12px;padding:14px 18px;margin-bottom:20px;">
                    <div style="font-family:'Outfit',sans-serif;font-size:0.95rem;font-weight:700;color:#1C1F2E;margin-bottom:4px;">⚡ What is Gap Analysis?</div>
                    <div style="font-size:0.81rem;color:#4B526B;line-height:1.6;">
                        These are queries where Google is already ranking your page in <b>the top 10</b>, but the CTR is significantly
                        below the benchmark — meaning searchers see your result but don't click it.
                        This is the highest-ROI fix in SEO: <b>rewrite the title tag and meta description</b> for these exact queries.
                        No new content needed. No link building. Just better copy.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if q_gap.empty:
                    st.success("✅ No significant CTR gaps detected in top-10 queries.")
                else:
                    gp1, gp2, gp3 = st.columns(3)
                    gp1.metric("Gap Queries",        len(q_gap))
                    gp2.metric("Total Clicks Lost",  f"-{int(q_gap['q_opportunity_clicks'].sum()):,}/mo")
                    gp3.metric("Avg CTR vs Benchmark", f"{q_gap['q_ctr_ratio'].mean():.0%}")
                    st.markdown("<br>", unsafe_allow_html=True)

                    for i, (_, row) in enumerate(q_gap.head(25).iterrows(), 1):
                        query    = row['query']
                        pos      = float(row['q_position'])
                        ctr      = float(row['q_ctr'])
                        exp_ctr  = float(row['q_expected_ctr'])
                        ratio    = float(row['q_ctr_ratio'])
                        opp      = int(row['q_opportunity_clicks'])
                        imp      = int(row['q_impressions'])
                        page     = row.get('matched_page') or '—'
                        page_ctr = row.get('page_ctr')
                        pct_below = (1 - ratio) * 100

                        page_line = ''
                        if page != '—':
                            page_line = f'<div style="font-family:\'Fira Code\',monospace;font-size:0.74rem;color:#3B82F6;margin-top:5px;word-break:break-all;">→ Page: {page}</div>'
                            if page_ctr is not None:
                                page_line += f'<div style="font-size:0.72rem;color:#8590AD;margin-top:3px;">Page-level CTR: <b style="color:#1C1F2E">{page_ctr:.2%}</b> · Query CTR: <b style="color:#1C1F2E">{ctr:.2%}</b></div>'

                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E4E7F0;border-left:4px solid #5046E4;
                             border-radius:14px;padding:16px 20px;margin-bottom:10px;
                             display:flex;align-items:flex-start;gap:16px;">
                            <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:800;color:#CDD2E8;min-width:28px;">#{i}</div>
                            <div style="flex:1;">
                                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                                    <span style="font-size:0.66rem;font-weight:700;color:#5046E4;text-transform:uppercase;letter-spacing:0.09em;">CTR GAP</span>
                                    <span style="font-size:0.68rem;background:rgba(80,70,228,0.1);color:#3730A3;
                                          border:1px solid rgba(80,70,228,0.25);border-radius:12px;padding:2px 8px;font-weight:700;">
                                        {pct_below:.0f}% below benchmark
                                    </span>
                                    <span style="font-size:0.68rem;color:#8590AD;background:#F4F5FA;border-radius:5px;padding:2px 7px;font-weight:600;">pos #{pos:.1f}</span>
                                </div>
                                <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#1C1F2E;margin-bottom:6px;">"{query}"</div>
                                <div style="font-size:0.81rem;color:#4B526B;background:#F5F6FF;border-left:3px solid #5046E4;
                                     padding:8px 12px;border-radius:0 8px 8px 0;line-height:1.6;">
                                    Ranking #{pos:.1f} — should get <b>{exp_ctr:.1%}</b> CTR but only getting <b>{ctr:.1%}</b>.
                                    Rewrite the title tag to directly answer this query intent.
                                    Add the exact phrase "<b>{query}</b>" to your title tag and meta description.
                                    Check if a competitor's snippet is stealing clicks with schema markup.
                                </div>
                                {page_line}
                            </div>
                            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;min-width:138px;">
                                <div class="gain-badge">+{opp:,} clicks/mo</div>
                                <div class="stat-row">Impressions: <span>{imp:,}</span></div>
                                <div class="stat-row">CTR ratio: <span>{ratio:.0%}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    gap_csv = io.StringIO()
                    q_gap.to_csv(gap_csv, index=False)
                    st.download_button("⬇️ Export Gap Analysis CSV", data=gap_csv.getvalue(),
                        file_name=f"query_gap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv", use_container_width=True)

            # ── COMBINED TABLE ───────────────────────────────────────────────
            with qt3:
                st.markdown("""
                <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#1C1F2E;margin-bottom:6px;">🔗 Queries × Pages — Combined View</div>
                <div style="font-size:0.81rem;color:#8590AD;margin-bottom:18px;">
                    Every query matched to its most likely serving page using URL keyword analysis.
                    Use this to audit which page is ranking for each query and whether it is the right one.
                </div>
                """, unsafe_allow_html=True)

                ct1, ct2 = st.columns([3, 2])
                with ct1:
                    ct_search = st.text_input("🔍 Search query or page", placeholder="e.g. crash guard, /collections/", key="ct_search")
                with ct2:
                    ct_filter = st.selectbox("Show", ["All queries", "Issues only", "Matched only", "Unmatched only"], key="ct_filter")

                ct_df = q_combined.copy()
                if ct_search:
                    ct_df = ct_df[
                        ct_df['query'].str.contains(ct_search, case=False, na=False) |
                        ct_df['matched_page'].fillna('').str.contains(ct_search, case=False, na=False)
                    ]
                if ct_filter == "Issues only":
                    ct_df = ct_df[ct_df['q_issue'].notna()]
                elif ct_filter == "Matched only":
                    ct_df = ct_df[ct_df['matched_page'].notna()]
                elif ct_filter == "Unmatched only":
                    ct_df = ct_df[ct_df['matched_page'].isna()]

                cm1, cm2, cm3, cm4 = st.columns(4)
                cm1.metric("Queries shown",   f"{len(ct_df):,}")
                cm2.metric("Matched",         f"{ct_df['matched_page'].notna().sum():,}")
                cm3.metric("With issues",     f"{ct_df['q_issue'].notna().sum()}")
                cm4.metric("Total opp clicks",f"+{int(ct_df['q_opportunity_clicks'].sum()):,}/mo")
                st.markdown("<br>", unsafe_allow_html=True)

                display_ct = ct_df[[c for c in [
                    'query', 'q_impressions', 'q_clicks', 'q_ctr', 'q_position',
                    'q_expected_ctr', 'q_ctr_ratio', 'q_opportunity_clicks',
                    'q_issue', 'q_priority', 'matched_page', 'page_ctr', 'page_position'
                ] if c in ct_df.columns]].copy()

                fmt = {}
                for col in ['q_ctr','q_expected_ctr','page_ctr']:
                    if col in display_ct.columns: fmt[col] = "{:.2%}"
                for col in ['q_ctr_ratio']:
                    if col in display_ct.columns: fmt[col] = "{:.0%}"
                for col in ['q_impressions','q_clicks','q_opportunity_clicks']:
                    if col in display_ct.columns: fmt[col] = "{:,.0f}"
                for col in ['q_position','page_position']:
                    if col in display_ct.columns: fmt[col] = "{:.1f}"

                st.dataframe(
                    display_ct.style.format(fmt, na_rep="—"),
                    use_container_width=True, height=540,
                )
                st.markdown("<br>", unsafe_allow_html=True)
                full_csv = io.StringIO()
                ct_df.to_csv(full_csv, index=False)
                st.download_button("⬇️ Export Combined Table CSV", data=full_csv.getvalue(),
                    file_name=f"queries_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)