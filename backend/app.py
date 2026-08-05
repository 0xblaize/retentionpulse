from __future__ import annotations

import os
import tempfile

import streamlit as st

from retentionpulse.analyzer import AnalysisResult, analyze_video
from retentionpulse.suggestions import generate_repair_suggestions
from retentionpulse.visualization import segment_table, timeline_figure


st.set_page_config(page_title="RetentionPulse AI", page_icon="◒", layout="wide", initial_sidebar_state="collapsed")


PULSE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;600;700&display=swap');
:root { --ink:#edf4ff; --muted:#8e9bb4; --bg:#060914; --panel:rgba(15,24,43,.72); --line:rgba(165,190,255,.16); --cyan:#67e8f9; --lime:#9bef9b; --coral:#ff7d73; --accent:#5E0ED7; }
.stApp { background:radial-gradient(circle at 78% 8%, rgba(65,91,255,.19), transparent 30rem),radial-gradient(circle at 6% 80%, rgba(20,180,194,.12), transparent 28rem),var(--bg); color:var(--ink); font-family:'Space Grotesk',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1260px; padding:2rem 3rem 5rem; }
[data-testid="stSidebar"] { background:#080d1a; border-right:1px solid var(--line); }
[data-testid="stMetric"] { background:linear-gradient(135deg, rgba(24,37,65,.8), rgba(8,14,29,.8)); border:1px solid var(--line); border-radius:22px; padding:1.1rem 1.2rem; box-shadow:0 20px 50px rgba(0,0,0,.18); }
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--ink); }
.stButton > button, .stFormSubmitButton > button { border:1px solid rgba(103,232,249,.5); border-radius:999px; background:linear-gradient(135deg,#8ff5ff,#7acbff); color:#06111c; font-weight:700; padding:.75rem 1.2rem; box-shadow:0 0 32px rgba(103,232,249,.2); }
.stButton > button:hover, .stFormSubmitButton > button:hover { border-color:#fff; transform:translateY(-1px); }
.stTextInput input { background:rgba(9,16,31,.88); color:var(--ink); border:1px solid var(--line); border-radius:14px; }
[data-testid="stFileUploader"] { background:rgba(14,24,44,.62); border:1px dashed rgba(103,232,249,.45); border-radius:20px; padding:1rem; }
.glass { background:linear-gradient(135deg,rgba(18,31,56,.78),rgba(8,13,26,.78)); border:1px solid var(--line); border-radius:26px; padding:1.35rem; box-shadow:0 24px 80px rgba(0,0,0,.2); }
.dashboard-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:1rem 0 2rem; }
.dashboard-head h1 { margin:.35rem 0 0; font-size:2.6rem; letter-spacing:-.06em; }
.section-label { color:var(--muted); font:500 .72rem 'DM Mono',monospace; letter-spacing:.15em; text-transform:uppercase; }
.status-pill { display:inline-flex; gap:.5rem; align-items:center; border:1px solid rgba(155,239,155,.25); color:var(--lime); border-radius:999px; padding:.45rem .75rem; font:500 .72rem 'DM Mono',monospace; }
.status-pill.risk { color:var(--coral); border-color:rgba(255,125,115,.32); }
.repair-card { background:rgba(18,28,49,.75); border:1px solid var(--line); border-radius:18px; padding:1.05rem 1.15rem; margin:.7rem 0; }
.repair-card .priority { color:var(--coral); font:500 .7rem 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
.login-wrap { max-width:460px; margin:13vh auto 0; text-align:center; }
.login-wrap h1 { font-size:3rem; letter-spacing:-.06em; }
.login-wrap p { color:var(--muted); line-height:1.6; }
.demo-note { margin-top:1rem; color:#f6c76b; font:500 .75rem 'DM Mono',monospace; }
.landing-shell { --landing-ink:#000; --landing-accent:#5E0ED7; position:relative; min-height:100svh; margin:-2rem -3rem -5rem; overflow:hidden; isolation:isolate; background:#c9c8c6; color:var(--landing-ink); font-family:Inter,ui-sans-serif,system-ui,sans-serif; text-transform:uppercase; letter-spacing:.12em; }
.landing-video { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; z-index:-3; animation:landingVideoIn 1.2s cubic-bezier(.22,1,.36,1) both; }
.landing-overlay { position:absolute; inset:0; z-index:-2; background:linear-gradient(180deg,rgba(255,255,255,.45),rgba(255,255,255,.18) 45%,rgba(255,255,255,.74)),linear-gradient(90deg,rgba(255,255,255,.18),transparent 55%,rgba(255,255,255,.28)); }
.landing-content { position:relative; z-index:1; min-height:100svh; display:flex; flex-direction:column; padding:1.25rem 1.25rem max(2rem,env(safe-area-inset-bottom)); }
.landing-nav { display:flex; align-items:center; justify-content:space-between; min-height:42px; animation:landingFadeDown .5s cubic-bezier(.22,1,.36,1) both; }
.landing-logo { width:32px; height:32px; border:2px solid var(--landing-accent); border-radius:50%; display:inline-flex; align-items:center; justify-content:center; flex:none; }
.landing-logo:after { content:''; width:10px; height:10px; border-radius:50%; background:var(--landing-accent); }
.landing-nav-links { display:flex; align-items:center; gap:2.25rem; margin-left:auto; margin-right:1.5rem; }
.landing-nav-links span { font-size:14px; font-weight:600; color:#000; letter-spacing:.18em; }
.landing-menu-hint { display:none; }
.landing-hero { flex:1; display:flex; align-items:center; justify-content:flex-end; padding:2rem 0; }
.landing-stats { display:flex; justify-content:flex-end; gap:1.25rem; width:100%; animation:landingFadeUp .6s .24s cubic-bezier(.22,1,.36,1) both; }
.landing-stat { text-align:right; min-width:82px; }
.landing-stat-number { font-size:clamp(1.5rem,5vw,3.5rem); line-height:1; font-weight:600; letter-spacing:-.06em; }
.landing-stat-number i { color:var(--landing-accent); font-size:.5em; font-style:normal; vertical-align:top; }
.landing-stat-label { display:block; margin-top:.45rem; font-size:10px; line-height:1.15; font-weight:600; letter-spacing:.16em; }
.landing-bottom { display:flex; flex-direction:column; gap:1.5rem; animation:landingFadeUp .6s .6s cubic-bezier(.22,1,.36,1) both; }
.landing-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
.landing-tagline,.landing-description { margin:0; font-size:10px; line-height:1.45; font-weight:600; letter-spacing:.16em; }
.landing-tagline { max-width:130px; }
.landing-description { width:120px; flex:none; text-align:left; }
.landing-cta { color:var(--landing-accent); font-size:1rem; font-weight:600; letter-spacing:.12em; white-space:nowrap; }
.landing-cta:after { content:'↗'; margin-left:.35rem; font-size:1.1em; }
.landing-heading { display:flex; flex-direction:column; align-items:flex-end; font-size:clamp(2rem,9vw,9rem); line-height:.88; letter-spacing:-.08em; font-weight:600; }
.landing-heading-word { overflow:hidden; height:.9em; }
.landing-heading-word span { display:block; animation:landingWordUp .7s cubic-bezier(.22,1,.36,1) both; }
.landing-heading-word:nth-child(1) span { animation-delay:.4s; }.landing-heading-word:nth-child(2) span { animation-delay:.54s; }.landing-heading-word:nth-child(3) span { animation-delay:.68s; }
.landing-actions { position:absolute; inset:0; pointer-events:none; z-index:2; }
.landing-actions .stButton { pointer-events:auto; }
.landing-actions .stButton > button { background:transparent; color:var(--landing-accent); border:0; box-shadow:none; padding:0; font:600 1rem Inter,sans-serif; text-transform:uppercase; letter-spacing:.12em; }
.landing-actions .stButton > button:hover { color:#000; transform:none; }
@keyframes landingFadeDown { from { opacity:0; transform:translateY(-20px); } to { opacity:1; transform:translateY(0); } }
@keyframes landingFadeUp { from { opacity:0; transform:translateY(32px); } to { opacity:1; transform:translateY(0); } }
@keyframes landingWordUp { from { transform:translateY(110%); } to { transform:translateY(0); } }
@keyframes landingVideoIn { from { opacity:0; transform:scale(1.05); } to { opacity:1; transform:scale(1); } }
@media (min-width:640px) { .landing-content { padding:1.25rem 2rem max(3rem,env(safe-area-inset-bottom)); }.landing-stats { gap:2rem; }.landing-stat-label { font-size:12px; }.landing-tagline,.landing-description { font-size:12px; }.landing-tagline { max-width:160px; }.landing-description { width:180px; }.landing-cta { font-size:1.25rem; } }
@media (min-width:768px) { .landing-shell { margin:-2rem -3rem -5rem; }.landing-content { padding:1.5rem 3rem max(3rem,env(safe-area-inset-bottom)); }.landing-nav-links { display:flex; }.landing-menu-hint { display:block; width:36px; height:36px; border-radius:50%; background:#000; color:#fff; text-align:center; line-height:36px; font-size:0; }.landing-menu-hint:after { content:'☰'; font-size:16px; }.landing-hero { padding:0; }.landing-stats { gap:2.5rem; }.landing-description { width:280px; text-align:right; }.landing-tagline,.landing-description { font-size:14px; }.landing-cta { font-size:1.5rem; } }
@media (max-width:767px) { .landing-nav-links { display:none; }.landing-menu-hint { display:block; width:36px; height:36px; border-radius:50%; background:#000; color:#fff; text-align:center; line-height:36px; font-size:0; }.landing-menu-hint:after { content:'☰'; font-size:16px; }.landing-row:last-child { align-items:flex-end; }.landing-heading { font-size:clamp(2rem,13vw,5rem); }.landing-stats { gap:1.1rem; }.landing-stat { min-width:70px; }.landing-actions { display:none; } }
@media (prefers-reduced-motion: reduce) { *, *:before, *:after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
</style>
"""


def init_state() -> None:
    defaults = {"route": "landing", "authenticated": False, "analysis_result": None, "suggestions": (), "error": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def go(route: str) -> None:
    st.session_state.route = route
    st.rerun()


def render_brand() -> None:
    st.markdown('<div class="eyebrow">RETENTIONPULSE / VISUAL INTELLIGENCE</div>', unsafe_allow_html=True)


def render_landing() -> None:
    st.markdown(
        """
        <section class="hero">
          <div>
            <div class="eyebrow">A RETENTION X-RAY FOR EVERY FRAME</div>
            <h1>Make every<br><span>second</span> matter.</h1>
            <p>RetentionPulse scans your edit for visual dead air before your audience finds it. See the risk. Fix the moment. Keep the watch.</p>
          </div>
          <div class="scene" aria-label="Animated visual analysis preview">
            <div class="orbit"></div><div class="core"></div><div class="scan-line"></div>
            <div class="scan-card"><small>Attention risk</small><strong>01:42</strong><span style="color:#ff7d73">8.6 sec static shot</span></div>
            <div class="scan-card" style="left:0;right:auto;top:310px"><small>Visual rhythm</small><strong style="color:#9bef9b">72 / 100</strong><span style="color:#8e9bb4">healthy pulse</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([1, 1])
    with left:
        if st.button("Enter the X-Ray →", type="primary", use_container_width=False):
            go("login")
    with right:
        st.markdown('<p class="section-label" style="padding-top:.8rem">Frame-by-frame visual risk detection · private by default · built for editors</p>', unsafe_allow_html=True)


def render_login() -> None:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    render_brand()
    st.markdown("<h1>Unlock your pulse.</h1><p>Passkeys are handled by the Django app for secure workspace access.</p>", unsafe_allow_html=True)
    st.link_button("Open passkey login", "http://127.0.0.1:8000/login/", use_container_width=True)
    st.caption("The Streamlit fallback does not collect passwords or passcodes.")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("← Back to landing"):
        st.session_state.error = None
        go("landing")


def reset_workspace() -> None:
    st.session_state.analysis_result = None
    st.session_state.suggestions = ()
    st.session_state.error = None


def render_dashboard() -> None:
    st.sidebar.markdown('<div class="eyebrow">RETENTIONPULSE</div>', unsafe_allow_html=True)
    st.sidebar.markdown("### Analysis room")
    st.sidebar.caption("Visual retention intelligence for your next edit.")
    if st.sidebar.button("New analysis", use_container_width=True):
        reset_workspace()
        st.rerun()
    if st.sidebar.button("Log out", use_container_width=True):
        reset_workspace()
        st.session_state.authenticated = False
        go("landing")
    render_brand()
    st.markdown('<div class="dashboard-head"><div><h1>Your edit, under the microscope.</h1><div class="section-label">SCAN / VISUAL RHYTHM / LIVE REVIEW</div></div></div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Drop a video into the scan chamber", type=["mp4", "mov", "m4v"], help="Your upload is analyzed temporarily and deleted after processing.")
    if uploaded is not None:
        st.video(uploaded)
        if st.button("Run visual scan →", type="primary"):
            suffix = os.path.splitext(uploaded.name)[1].lower() or ".mp4"
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
                    temporary_file.write(uploaded.getbuffer())
                    temporary_path = temporary_file.name
                with st.spinner("Tracing the pulse through every half-second..."):
                    result = analyze_video(temporary_path)
                st.session_state.analysis_result = result
                st.session_state.suggestions = generate_repair_suggestions(result.static_segments)
                st.session_state.error = None
            except ValueError as error:
                st.session_state.error = str(error)
            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)
            st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error)
    result: AnalysisResult | None = st.session_state.analysis_result
    if result is None:
        st.markdown('<div class="glass" style="margin-top:1rem"><div class="section-label">READY STATE</div><h2>Upload an edit to reveal its visual pulse.</h2><p style="color:#8e9bb4">The scan samples frames every 0.5 seconds and flags visual dead air longer than six seconds. No video is stored.</p></div>', unsafe_allow_html=True)
        return

    risk_seconds = sum(segment.duration for segment in result.static_segments)
    risk_ratio = risk_seconds / result.duration if result.duration else 0
    health = max(0, round((1 - risk_ratio) * 100))
    has_risk = bool(result.static_segments)
    status_class = "risk" if has_risk else ""
    status_text = "Attention risk detected" if has_risk else "Healthy visual rhythm"
    st.markdown(f'<div class="glass"><span class="status-pill {status_class}">● {status_text}</span><h2 style="margin:.8rem 0 .25rem">Your video pulse is {health}/100.</h2><p style="color:#8e9bb4">{("We found moments worth tightening before publish." if has_risk else "No visual dead-air segments crossed the six-second threshold.")}</p></div>', unsafe_allow_html=True)
    metric_one, metric_two, metric_three, metric_four = st.columns(4)
    metric_one.metric("Video length", f"{result.duration:.1f}s")
    metric_two.metric("Risk segments", len(result.static_segments))
    metric_three.metric("Risk time", f"{risk_seconds:.1f}s")
    metric_four.metric("Risk ratio", f"{risk_ratio:.0%}")
    st.markdown('<div class="section-label" style="margin:2rem 0 .6rem">RETENTION PULSE / INTERACTIVE TIMELINE</div>', unsafe_allow_html=True)
    st.plotly_chart(timeline_figure(result), use_container_width=True)

    if has_risk:
        left, right = st.columns([1, 1])
        with left:
            st.markdown('<div class="section-label">FLAGGED MOMENTS</div>', unsafe_allow_html=True)
            st.dataframe(segment_table(result), use_container_width=True, hide_index=True)
        with right:
            st.markdown('<div class="section-label">REPAIR PLAN</div>', unsafe_allow_html=True)
            for suggestion in st.session_state.suggestions:
                st.markdown(f'<div class="repair-card"><div class="priority">{suggestion.priority} PRIORITY · {suggestion.action}</div><div style="margin-top:.45rem">{suggestion.detail}</div></div>', unsafe_allow_html=True)
    else:
        st.success("No visual dead-air segments over 6 seconds were detected.")


def main() -> None:
    init_state()
    st.markdown(PULSE_CSS, unsafe_allow_html=True)
    if not st.session_state.authenticated and st.session_state.route == "dashboard":
        st.session_state.route = "landing"
    if st.session_state.route == "landing":
        render_landing()
    elif st.session_state.route == "login":
        render_login()
    else:
        render_dashboard()


main()
