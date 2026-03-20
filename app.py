"""
SwishX AI Shorts · Pharma Video Reel Generator
"""

import os
import json
import time
import base64
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as _st
    for _key in ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "ELEVENLABS_API_KEY"]:
        if _key in _st.secrets and not os.environ.get(_key):
            os.environ[_key] = _st.secrets[_key]
except Exception:
    pass

from pipeline import PipelineConfig, run_pipeline
from config_loader import load_topic_map

def _img_b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

BASE_DIR      = Path(__file__).parent
PDFS_DIR      = BASE_DIR / "pdfs"
DEMOS_DIR     = BASE_DIR / "demos"
LOGO_PATH     = BASE_DIR / "assets" / "Swish_X_black_logo_02.png"
COMPANIES_DIR = BASE_DIR / "companies"

# ── Company preset ─────────────────────────────────────────────────────────
_company_param  = st.query_params.get("company", "")
_company_config: dict = {}
if _company_param:
    _cfg_path = COMPANIES_DIR / "companies.json"
    if _cfg_path.exists():
        _all = json.loads(_cfg_path.read_text())
        _company_config = _all.get(_company_param, {})

PRESET_COMPANY_NAME = _company_config.get("name", "")
PRESET_LOGO_PATH    = (
    COMPANIES_DIR / _company_config["logo"]
    if _company_config.get("logo") else None
)

_brand_param  = st.query_params.get("brand", "")
_brand_config = _company_config.get("brands", {}).get(_brand_param, {}) if _brand_param else {}
PRESET_BRAND_NAME = _brand_config.get("name", "")
PRESET_VIDEO_URL  = _brand_config.get("video_url", "") or _company_config.get("video_url", "")

DEMO_VIDEOS = [
    {"file": "AllerDuo_intro.mp4",        "drug": "AllerDuo",    "topic": "Intro",
     "composition": "Bilastine + Montelukast",                    "pdf_thumb": "assets/pdf_thumb_AllerDuo.png",    "pages": 9},
    {"file": "Tibrolin_intro.mp4",         "drug": "Tibrolin",    "topic": "Intro",
     "composition": "Trypsin + Bromelain + Rutoside",             "pdf_thumb": "assets/pdf_thumb_Tibrolin.png",    "pages": 4},
    {"file": "Rexulti_intro.mp4",          "drug": "Rexulti",     "topic": "Intro",
     "composition": "Brexpiprazole",                              "pdf_thumb": "assets/pdf_thumb_Rexulti.png",     "pages": 9},
    {"file": "Subneuro-NT_intro.mp4",      "drug": "Subneuro-NT", "topic": "Intro",
     "composition": "Methylcobalamin + Pregabalin + Nortriptyline","pdf_thumb": "assets/pdf_thumb_Subneuro-NT.png", "pages": 4},
    {"file": "AllerDuo_mechanism.mp4",     "drug": "AllerDuo",    "topic": "Mechanism",
     "composition": "Bilastine + Montelukast",                    "pdf_thumb": "assets/pdf_thumb_AllerDuo.png",    "pages": 9},
    {"file": "AllerDuo_dosage_safety.mp4", "drug": "AllerDuo",    "topic": "Dosage & Safety",
     "composition": "Bilastine + Montelukast",                    "pdf_thumb": "assets/pdf_thumb_AllerDuo.png",    "pages": 9},
]

TOPIC_COLORS = {
    "Intro":           "#fd4816",
    "Mechanism":       "#7c3aed",
    "Dosage & Safety": "#059669",
    "Indications":     "#2563eb",
    "Interactions":    "#d97706",
    "Side Effects":    "#db2777",
}

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwishX AI Shorts: Pharma Video Reels",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── Hide Streamlit chrome ── */
section[data-testid="stSidebar"]  { display: none !important; }
div[data-testid="stToolbar"]      { display: none !important; }
div[data-testid="stDecoration"]   { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
#MainMenu, footer, header         { visibility: hidden !important; }

/* ── Global ── */
html, body,
.stApp,
.stApp > div,
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="stVerticalBlock"] {
    background-color: #ffffff !important;
    font-family: 'Figtree', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

div[data-testid="stMainBlockContainer"] {
    max-width: 1160px;
    padding: 0 2.5rem 6rem;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
label, input, select, textarea, button {
    font-family: 'Figtree', sans-serif !important;
}

::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: #fff; }
::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 2px; }

/* ── Load animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
.reveal         { animation: fadeUp 0.65s cubic-bezier(0.16,1,0.3,1) both; }
.reveal-delay-1 { animation-delay: 0.1s; }
.reveal-delay-2 { animation-delay: 0.2s; }
.reveal-delay-3 { animation-delay: 0.3s; }

/* ── Hero ── */
.hero-section {
    padding: 3rem 0 3.5rem;
}
.hero-eyebrow {
    display: inline-block;
    width: fit-content;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    color: #fd4816;
    background: rgba(253,72,22,0.07);
    border: 1px solid rgba(253,72,22,0.3);
    border-radius: 999px;
    padding: 5px 14px;
    margin-bottom: 24px;
    display: block;
}
.hero-title {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -2px;
    color: #111111;
    margin: 0 0 22px;
}
.hero-title .accent { color: #fd4816; }
.hero-sub {
    font-size: 16px;
    font-weight: 400;
    color: #555555;
    line-height: 1.75;
    margin: 0 0 36px;
    max-width: 480px;
}
.hero-cta-row {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}
.btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fd4816;
    color: #fff !important;
    padding: 13px 26px;
    border-radius: 8px;
    font-family: 'Figtree', sans-serif;
    font-size: 14px;
    font-weight: 700;
    text-decoration: none !important;
    transition: background 0.2s ease;
    letter-spacing: 0.1px;
    border: none;
    cursor: pointer;
}
.btn-primary:hover { background: #e03d12; }
.btn-ghost {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #444444 !important;
    font-family: 'Figtree', sans-serif;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none !important;
    transition: color 0.2s ease;
    letter-spacing: 0.1px;
}
.btn-ghost:hover { color: #fd4816 !important; }
.btn-ghost svg { transition: transform 0.2s ease; }
.btn-ghost:hover svg { transform: translateY(3px); }
.magic-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-top: 18px;
    padding: 7px 14px;
    background: rgba(253,72,22,0.06);
    border: 1px solid rgba(253,72,22,0.2);
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    color: #fd4816;
    letter-spacing: 0.2px;
}

/* ── Phone mockup ── */
.phone-wrap {
    display: flex;
    justify-content: center;
    padding-top: 3rem;
}
.phone-mockup {
    width: 352px;
    background: #0d0d0d;
    border-radius: 36px;
    padding: 10px 8px;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.06) inset,
        0 40px 100px rgba(0,0,0,0.18),
        0 8px 24px rgba(0,0,0,0.12);
}
.phone-screen {
    border-radius: 28px;
    overflow: hidden;
    position: relative;
    aspect-ratio: 1080 / 1540;
    background: #0d0d0d;
}
.phone-screen--empty {
    display: flex;
    align-items: center;
    justify-content: center;
}
.phone-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.phone-placeholder span {
    font-family: 'Figtree', sans-serif;
    font-size: 11px;
    color: rgba(255,255,255,0.35);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Divider ── */
.rule { border: none; border-top: 1px solid rgba(0,0,0,0.08); margin: 0; }

/* ── Section header ── */
.s-eyebrow {
    display: inline-block;
    width: fit-content;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    color: #fd4816;
    background: rgba(253,72,22,0.07);
    border: 1px solid rgba(253,72,22,0.3);
    border-radius: 999px;
    padding: 5px 14px;
    margin-bottom: 16px;
    display: block;
}
.s-title {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #111111;
    margin: 0 0 8px;
    line-height: 1.15;
}
.s-sub {
    font-size: 15px;
    font-weight: 400;
    color: #666666;
    line-height: 1.7;
    margin: 0 0 2.5rem;
    max-width: 540px;
}

/* ── Value prop cards ── */
.vp-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 14px;
    overflow: hidden;
}
.vp-card {
    background: #ffffff;
    padding: 32px 28px;
}
.vp-num {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    color: #fd4816;
    text-transform: uppercase;
    margin-bottom: 20px;
    display: block;
}
.vp-title {
    font-size: 20px;
    font-weight: 700;
    color: #111111;
    margin: 0 0 10px;
    line-height: 1.3;
    letter-spacing: -0.3px;
}
.vp-desc {
    font-size: 13.5px;
    font-weight: 400;
    color: #666666;
    line-height: 1.7;
    margin: 0;
}
.vp-icon {
    display: block;
    margin-bottom: 20px;
}
.vp-icon svg {
    width: 48px;
    height: 48px;
    display: block;
}
.vp-logo {
    height: 36px;
    max-width: 140px;
    margin-bottom: 20px;
    display: block;
    object-fit: contain;
}

/* ── Section spacing ── */
.section-gap { height: 5rem; }
.section-gap-sm { height: 2.5rem; }

/* ── Form ── */
.form-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    color: #fd4816;
    margin-bottom: 10px;
    margin-top: 4px;
    display: block;
}
div[data-baseweb="select"] > div {
    background: #f9f9f9 !important;
    border-color: rgba(0,0,0,0.1) !important;
    color: #333 !important;
    border-radius: 8px !important;
    font-family: 'Figtree', sans-serif !important;
}
div[data-baseweb="select"] svg { fill: #999 !important; }
textarea {
    background: #f9f9f9 !important;
    border-color: rgba(0,0,0,0.1) !important;
    color: #444 !important;
    border-radius: 8px !important;
    font-family: 'Figtree', sans-serif !important;
}
div[data-testid="stFileUploader"] > div {
    background: #f9f9f9 !important;
    border: 1px dashed rgba(0,0,0,0.15) !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploader"] p { color: #aaa !important; font-family: 'Figtree', sans-serif !important; }
.stRadio > div { gap: 1.2rem !important; }
.stRadio label p { color: #444 !important; font-size: 14px !important; font-family: 'Figtree', sans-serif !important; }
.stCheckbox label p { color: #444 !important; font-family: 'Figtree', sans-serif !important; }

/* ── Buttons ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: #fd4816 !important;
    color: #fff !important;
    border: none !important;
    font-family: 'Figtree', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 14px 32px !important;
    border-radius: 8px !important;
    letter-spacing: 0.1px !important;
    transition: background 0.2s ease !important;
    box-shadow: none !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover   { background: #e03d12 !important; transform: none !important; }
div[data-testid="stButton"] > button[kind="primary"]:disabled { opacity: 0.35 !important; }

div[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    color: #fd4816 !important;
    border: 1.5px solid #fd4816 !important;
    border-radius: 8px !important;
    font-family: 'Figtree', sans-serif !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover { background: rgba(253,72,22,0.05) !important; }

div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    color: #444 !important;
    border: 1.5px solid rgba(0,0,0,0.15) !important;
    border-radius: 8px !important;
    font-family: 'Figtree', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: #fd4816 !important;
    color: #fd4816 !important;
}

/* ── Progress ── */
div[data-testid="stProgress"] > div > div { background: #fd4816 !important; }
div[data-testid="stProgress"] > div       { background: #f0f0f0 !important; }
.p-step         { font-family: 'Figtree', sans-serif; font-size: 13px; padding: 4px 0; }
.p-step.waiting { color: #d0d0d0; }
.p-step.active  { color: #fd4816; animation: stepPulse 1.8s ease-in-out infinite; }
.p-step.done    { color: #16a34a; }
@keyframes stepPulse { 0%,100% { opacity:1; } 50% { opacity:.4; } }
.spin-dot { display:inline-block; animation: spinPulse 2s ease-in-out infinite; }
@keyframes spinPulse { 0%,100% { transform:scale(1); opacity:1; } 50% { transform:scale(1.15); opacity:.65; } }

/* ── Video skeleton ── */
.video-skeleton {
    background: #f9f9f9;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px;
    padding: 3rem 1.5rem;
    text-align: center;
    min-height: 320px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: skeletonPulse 2.5s ease-in-out infinite;
}
.video-skeleton .sk-text { font-family: 'Figtree', sans-serif; font-size: 14px; color: #aaa; margin-top: 1rem; }
@keyframes skeletonPulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }

/* ── Demo video cards ── */
video { border-radius: 10px; }
.vid-label {
    font-family: 'Figtree', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: #222;
    margin-bottom: 6px;
}
.t-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Figtree', sans-serif;
    letter-spacing: 0.2px;
}
.demo-pdf-img {
    width: 68px;
    height: 86px;
    object-fit: cover;
    object-position: top;
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 4px;
}
.demo-arrow { color: #fd4816; font-weight: 700; font-size: 1rem; }

/* ── Misc ── */
div[data-testid="stAlert"]              { border-radius: 8px !important; font-family: 'Figtree', sans-serif !important; }
div[data-testid="stExpander"]          { background: #f9f9f9 !important; border: 1px solid rgba(0,0,0,0.08) !important; border-radius: 10px !important; }
div[data-testid="stExpander"] summary  { font-family: 'Figtree', sans-serif !important; font-weight: 600 !important; color: #222 !important; }
div[data-testid="stToast"]             { top: 1rem !important; bottom: auto !important; }
video::-webkit-media-controls-download-button { display: none !important; }
video::-webkit-media-controls-enclosure { overflow: hidden !important; }
video::-webkit-media-controls-panel { width: calc(100% + 30px) !important; }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    div[data-testid="stMainBlockContainer"] {
        padding: 0 1rem 4rem !important;
    }
    /* Stack hero columns */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        min-width: 100% !important;
        width: 100% !important;
    }
    .hero-section { padding: 1.5rem 0 2rem; }
    .hero-title { font-size: 2rem !important; letter-spacing: -1px; }
    .s-title { font-size: 1.5rem !important; }
    /* VP cards: single column on mobile */
    .vp-grid {
        grid-template-columns: 1fr !important;
    }
    /* Demo reels: single column */
    div[data-testid="stHorizontalBlock"]:has(.demo-pdf-img) > div[data-testid="stColumn"] {
        min-width: 100% !important;
    }
    .hero-sub { max-width: 100% !important; font-size: 15px; }
    .s-sub { max-width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════



# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════

hero_left, hero_right = st.columns([2.8, 2], gap="large")

with hero_left:
    st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)

    if PRESET_COMPANY_NAME:
        _eyebrow = f"SEMAGLUTIDE LAUNCH &nbsp;·&nbsp; {PRESET_COMPANY_NAME.upper()}" + (f" &nbsp;·&nbsp; {PRESET_BRAND_NAME.upper()}" if PRESET_BRAND_NAME else "")
        _title   = f"35 companies.<br>Same molecule.<br><span class='accent'>{PRESET_COMPANY_NAME} needs<br>to be first.</span>"
        _sub     = (
            f"Semaglutide patent expires in a few days. Doctors will prescribe the first "
            f"brand that reaches them with a clear, compelling story, "
            f"not the one that sends a 5-page PDF. "
            f"We've built {PRESET_COMPANY_NAME}'s launch content. "
            f"<strong>Generate your branded MagicReel&#8482; in minutes and push it to HCPs, distributors, and retailers on Day 1.</strong>"
        )
    else:
        _eyebrow = "PHARMA CONTENT, REIMAGINED"
        _title   = "From 40-page dossier<br>to 60-second reel.<br><span class='accent'>In minutes.</span>"
        _sub     = (
            "Turn any drug PDF into a clinically verified product intro reel "
            "your field team can WhatsApp to any doctor on launch day. "
            "No agency. No four-week wait. No excuses."
        )

    st.markdown(f"""
    <div class="hero-section reveal">
        <span class="hero-eyebrow">{_eyebrow}</span>
        <div class="hero-title">{_title}</div>
        <p class="hero-sub">{_sub}</p>
        <div class="hero-cta-row">
            <a href="#generate" class="btn-primary">Get Your MagicReel&#8482; for Free &nbsp;↓</a>
        </div>
        <div class="magic-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="flex-shrink:0;">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#fd4816" stroke="#fd4816" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
            SwishX AI MagicReel&#8482;
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    if PRESET_VIDEO_URL:
        _is_mp4 = PRESET_VIDEO_URL.endswith(".mp4") or "cloudinary.com" in PRESET_VIDEO_URL
        _video_tag = (
            f'<video controls playsinline style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;border-radius:12px;"><source src="{PRESET_VIDEO_URL}" type="video/mp4"></video>'
            if _is_mp4 else
            f'<iframe src="{PRESET_VIDEO_URL}" frameborder="0" allow="autoplay; fullscreen" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;"></iframe>'
        )
        components.html(f"""
        <style>
            body {{ margin:0; background:transparent; display:flex; justify-content:center; padding-top:5rem; }}
            .vw {{ position:relative; width:265px; height:470px; border-radius:12px; overflow:hidden; flex-shrink:0; background:#000; }}
        </style>
        <div class="vw">{_video_tag}</div>
        """, height=570)
    else:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# VALUE PROPS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="reveal">
<span class="s-eyebrow">Why SwishX</span>
<div class="s-title">The fastest path from dossier to doctor.</div>
<p class="s-sub">One platform to create, personalise, and distribute product content across your entire launch ecosystem, on Day 1, not Day 30.</p>
</div>
""", unsafe_allow_html=True)

_upload_svg    = (COMPANIES_DIR / "upload.svg").read_text()
_reach_svg     = (COMPANIES_DIR / "reach-doctor.svg").read_text()

if PRESET_LOGO_PATH and PRESET_LOGO_PATH.exists():
    _ext = PRESET_LOGO_PATH.suffix.lower().lstrip(".")
    _mime = "image/svg+xml" if _ext == "svg" else ("image/jpeg" if _ext in ("jpg", "jpeg") else f"image/{_ext}")
    _logo_b64_vp = base64.b64encode(PRESET_LOGO_PATH.read_bytes()).decode()
    _card3_icon = f'<img class="vp-logo" src="data:{_mime};base64,{_logo_b64_vp}" alt="{PRESET_COMPANY_NAME}" />'
else:
    _card3_icon = f'<span class="vp-icon">{(COMPANIES_DIR / "fall-back.svg").read_text()}</span>'

st.markdown(f"""
<div class="vp-grid">
    <div class="vp-card reveal">
        <span class="vp-icon">{_upload_svg}</span>
        <span class="vp-num">01</span>
        <div class="vp-title">Upload your dossier. Get a MagicReel&#8482; in minutes.</div>
        <p class="vp-desc">Your product PDF becomes a clinically verified, narrated video: MOA, trial data, dosing, safety. Ready to share before your competitor finishes their agency brief.</p>
    </div>
    <div class="vp-card reveal reveal-delay-1">
        <span class="vp-icon">{_reach_svg}</span>
        <span class="vp-num">02</span>
        <div class="vp-title">Reach doctors, distributors and retailers. All at once.</div>
        <p class="vp-desc">Push the reel through our Marketing Hub: WhatsApp-first, segmented by specialty, geography and channel tier. AI-optimised send times. UCPMP-compliant workflows.</p>
    </div>
    <div class="vp-card reveal reveal-delay-2">
        {_card3_icon}
        <span class="vp-num">03</span>
        <div class="vp-title">MagicReel&#8482; Branded with your Logo. Launch ready NOW.</div>
        <p class="vp-desc">Your brand name, your logo, your messaging, generated from your own dossier. The brands that show up first with a compelling story own doctor mindshare. Everyone else plays catch-up.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
st.markdown('<hr class="rule">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GENERATE YOUR REEL
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-gap" id="generate"></div>', unsafe_allow_html=True)

_display_name = PRESET_BRAND_NAME if PRESET_BRAND_NAME else PRESET_COMPANY_NAME
if PRESET_COMPANY_NAME:
    st.markdown(f'<div class="reveal"><span class="s-eyebrow" style="text-transform:none">Generate your MagicReel&#8482;</span><div class="s-title">{_display_name}\'s Launch Success Starts Here</div><p class="s-sub"><strong>Upload your product dossier or pick a sample. Your branded, narrated MagicReel&#8482; is ready in under 5 minutes.</strong></p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="reveal"><span class="s-eyebrow" style="text-transform:none">Generate your MagicReel&#8482;</span><div class="s-title">Generate a MagicReel&#8482; from any drug dossier.</div><p class="s-sub"><strong>Upload any pharma PDF. Your clinically verified, narrated MagicReel&#8482; is ready in under 5 minutes.</strong></p></div>', unsafe_allow_html=True)

if "generating" not in st.session_state:
    st.session_state.generating = False
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None

if st.session_state.generating:
    gen_start = st.session_state.get("gen_start_time", 0)
    if time.time() - gen_start > 600:
        st.session_state.generating = False

is_generating = st.session_state.generating

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<span class="form-label">① Choose a PDF</span>', unsafe_allow_html=True)
    existing_pdfs = (
        sorted(PDFS_DIR.glob("*.pdf")) + sorted(PDFS_DIR.glob("*.PDF"))
        if PDFS_DIR.exists() else []
    )
    pdf_source = st.radio(
        "source", ["Upload new", "Use a sample"],
        horizontal=True, label_visibility="collapsed",
        disabled=is_generating,
    )
    pdf_path = None
    if pdf_source == "Upload new":
        uploaded = st.file_uploader("pdf", type=["pdf"], label_visibility="collapsed", disabled=is_generating)
        if uploaded:
            PDFS_DIR.mkdir(exist_ok=True)
            save_path = PDFS_DIR / uploaded.name
            save_path.write_bytes(uploaded.getbuffer())
            pdf_path = str(save_path)
            st.success(f"✓ {uploaded.name}")
    else:
        if existing_pdfs:
            selected = st.selectbox(
                "sample", existing_pdfs,
                format_func=lambda p: p.stem,
                label_visibility="collapsed",
                disabled=is_generating,
            )
            pdf_path = str(selected)
        else:
            st.info("No sample PDFs available")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    st.markdown('<span class="form-label">② Focus (optional)</span>', unsafe_allow_html=True)
    guidance = st.text_area(
        "focus", label_visibility="collapsed",
        placeholder="e.g. Emphasise cardiovascular benefits for cardiologists",
        height=80,
        disabled=is_generating,
    )
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    st.markdown('<span class="form-label">③ Company Logo</span>', unsafe_allow_html=True)
    company_logo_path = ""
    if PRESET_LOGO_PATH and PRESET_LOGO_PATH.exists():
        _ext  = PRESET_LOGO_PATH.suffix.lower().lstrip(".")
        _mime = "image/svg+xml" if _ext == "svg" else ("image/jpeg" if _ext in ("jpg", "jpeg") else f"image/{_ext}")
        _b64  = base64.b64encode(PRESET_LOGO_PATH.read_bytes()).decode()
        st.markdown(f'<img src="data:{_mime};base64,{_b64}" style="height:48px;max-width:200px;object-fit:contain;display:block;margin-bottom:4px;" alt="{PRESET_COMPANY_NAME}">', unsafe_allow_html=True)
        company_logo_path = str(PRESET_LOGO_PATH)
    else:
        company_logo_file = st.file_uploader(
            "logo", type=["png", "jpg", "jpeg"],
            label_visibility="collapsed", disabled=is_generating,
        )
        if company_logo_file:
            logo_save = BASE_DIR / "output" / f"company_logo_{company_logo_file.name}"
            logo_save.parent.mkdir(parents=True, exist_ok=True)
            logo_save.write_bytes(company_logo_file.getbuffer())
            company_logo_path = str(logo_save)

with right:
    st.markdown('<span class="form-label">④ Configure</span>', unsafe_allow_html=True)
    profile = st.selectbox(
        "Audience",
        ["sales_executive", "stockist", "retailer", "doctor", "all"],
        format_func=lambda x: {
            "sales_executive": "Sales Executive / MR",
            "stockist":        "Stockist",
            "retailer":        "Retailer / Chemist",
            "doctor":          "Doctor / HCP",
            "all":             "All Profiles",
        }[x],
        disabled=is_generating,
    )
    topic_entries = load_topic_map(profile)
    topic_keys    = [t["key"] for t in topic_entries]
    topic_labels  = {t["key"]: t["label"] for t in topic_entries}
    topic = st.selectbox(
        "Topic", topic_keys,
        format_func=lambda x: topic_labels.get(x, x),
        key=f"topic_{profile}",
        disabled=is_generating,
    )
    voice_map = {
        "Gaurav: Professional, Calm":     "gaurav",
        "Suyash: Calm Explainer":         "suyash",
        "Sridhar: Natural, Professional": "sridhar",
        "Ruhaan: Clear, Cheerful":        "ruhaan",
        "Ishaan: Warm E-Learning":        "ishaan",
    }
    voice = voice_map[st.selectbox("Voice", list(voice_map.keys()), disabled=is_generating)]
    language_label = st.radio("Language", ["English", "Hindi"], horizontal=True, disabled=is_generating)
    language = "hi" if language_label == "Hindi" else "en"
    include_quiz = st.checkbox(
        "Include quiz + gamification", value=True, disabled=is_generating,
        help="Adds an interactive quiz and a points-based engagement layer to your MagicReel™. Doctors and MRs earn scores as they watch, proven to boost completion rates and recall.",
    )
    mode = "demo" if include_quiz else "production"

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
generate = st.button(
    "Generating…" if is_generating else "Get Your MagicReel™ for Free",
    type="primary",
    disabled=is_generating,
    use_container_width=True,
)
if not is_generating and st.session_state.pipeline_result is None:
    st.markdown('<p style="text-align:center; font-size:13px; color:#999; margin-top:8px; font-family:\'Figtree\',sans-serif;">See more examples below.</p>', unsafe_allow_html=True)

if generate and not is_generating:
    st.session_state.generating = True
    st.session_state.gen_start_time = time.time()
    st.session_state.pipeline_config = dict(
        pdf_path=pdf_path,
        profile=profile,
        topic=topic,
        voice=voice,
        tts="elevenlabs",
        mode=mode,
        guidance=guidance,
        language=language,
        company_logo_path=company_logo_path,
    )
    st.rerun()

if is_generating:
    config = PipelineConfig(**st.session_state.pipeline_config)

    TOTAL_ESTIMATE = 330
    STEP_META = {
        "extract":   ("Reading your PDF",          "Extracting all text, drug names, and data from the document…"),
        "analyze":   ("Understanding the content",  "Mapping indications, mechanism, dosage, and safety data…"),
        "script":    ("Writing the script",         "Crafting a narrative tailored to your audience and topic…"),
        "media":     ("Bringing it to life",        "Generating visuals for each scene and recording the voiceover…"),
        "stitch":    ("Assembling the video",       "Combining scenes, transitions, audio, and branding…"),
        "subtitles": ("Final touches",              "Adding subtitles and polishing the reel…"),
    }
    STEP_ORDER = list(STEP_META.keys())

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    out_left, out_right = st.columns([1.2, 1], gap="large")

    with out_left:
        video_area = st.empty()
        video_area.markdown("""
        <div class="video-skeleton">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24" style="color:#ddd;">
            <rect x="2" y="4" width="20" height="16" rx="3" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 9l5 3-5 3V9z" fill="currentColor"/>
          </svg>
          <div class="sk-text">Your reel is being crafted…</div>
        </div>
        """, unsafe_allow_html=True)
        download_area = st.empty()

    with out_right:
        status_box   = st.empty()
        progress_bar = st.progress(0)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        scol1, scol2 = st.columns(2)
        step_ui = {}
        for j, key in enumerate(STEP_ORDER):
            col = scol1 if j < 3 else scol2
            with col:
                step_ui[key] = st.empty()
                step_ui[key].markdown(
                    f'<div class="p-step waiting">· {STEP_META[key][0]}</div>',
                    unsafe_allow_html=True,
                )

    run_start  = time.time()
    cur_step   = [None]
    step_start = [time.time()]

    def _ft(s):
        s = max(0, int(s))
        return f"{s}s" if s < 60 else f"{s // 60}m {s % 60:02d}s"

    def _render_status(step, pct, message=""):
        meta      = STEP_META.get(step, (step, ""))
        label     = meta[0]
        desc      = message if message else meta[1]
        elapsed   = time.time() - run_start
        remaining = max(0, TOTAL_ESTIMATE - elapsed)
        pct_i     = int(min(pct, 1.0) * 100)
        status_box.markdown(f"""
        <div style="background:#fafafa; border:1px solid rgba(0,0,0,0.08); border-left:3px solid #fd4816;
                    border-radius:10px; padding:1.1rem 1.3rem; margin-bottom:.3rem; font-family:'Figtree',sans-serif;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:.5rem;">
            <div>
              <div style="font-weight:700; font-size:15px; color:#111; margin-bottom:5px;">
                <span class="spin-dot">⏳</span>&nbsp; {label}
              </div>
              <div style="font-size:13px; color:#777; max-width:460px; line-height:1.6;">{desc}</div>
            </div>
            <div style="text-align:right; flex-shrink:0;">
              <div style="font-weight:800; font-size:1.2rem; color:#fd4816;">{pct_i}%</div>
              <div style="font-size:11px; color:#aaa; margin-top:2px;">{_ft(elapsed)} elapsed</div>
              <div style="font-size:11px; color:#aaa; margin-top:1px;">~{_ft(remaining)} remaining</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    def on_progress(step, message, pct):
        if cur_step[0] and cur_step[0] != step and cur_step[0] in step_ui:
            el  = time.time() - step_start[0]
            lbl = STEP_META.get(cur_step[0], (cur_step[0],))[0]
            step_ui[cur_step[0]].markdown(
                f'<div class="p-step done">✓ {lbl} <span style="color:#ccc;font-size:11px">({_ft(el)})</span></div>',
                unsafe_allow_html=True,
            )
        if cur_step[0] != step:
            step_start[0] = time.time()
        cur_step[0] = step
        progress_bar.progress(min(pct, 1.0))
        if step in step_ui:
            step_ui[step].markdown(
                f'<div class="p-step active">⟳ {STEP_META.get(step, (step,))[0]}</div>',
                unsafe_allow_html=True,
            )
        _render_status(step, pct, message)

    result = run_pipeline(config, on_progress=on_progress)

    if cur_step[0] and cur_step[0] in step_ui:
        el  = time.time() - step_start[0]
        lbl = STEP_META.get(cur_step[0], (cur_step[0],))[0]
        step_ui[cur_step[0]].markdown(
            f'<div class="p-step done">✓ {lbl} <span style="color:#ccc;font-size:11px">({_ft(el)})</span></div>',
            unsafe_allow_html=True,
        )
    progress_bar.progress(1.0)
    total = time.time() - run_start

    status_box.markdown(f"""
    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:3px solid #16a34a;
                border-radius:10px; padding:1.1rem 1.3rem; margin-bottom:.3rem; font-family:'Figtree',sans-serif;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:.5rem;">
        <div>
          <div style="font-weight:700; font-size:15px; color:#16a34a; margin-bottom:3px;">✓ &nbsp;Your reel is ready</div>
          <div style="font-size:13px; color:#999;">Generated in {_ft(total)}</div>
        </div>
        <div style="font-weight:800; font-size:1.2rem; color:#16a34a;">100%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.generating = False
    st.session_state.pipeline_result = result
    st.rerun()

elif st.session_state.pipeline_result is not None:
    result = st.session_state.pipeline_result
    if result.get("error"):
        st.error(f"Something went wrong: {result['error']}")
        if st.button("Try Again", use_container_width=True):
            st.session_state.pipeline_result = None
            st.rerun()
    elif result.get("video_path") and os.path.exists(result["video_path"]):
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        _pad_l, out_left, _gap, out_right, _pad_r = st.columns([0.5, 1, 0.3, 1.2, 0.5], gap="small")
        with out_left:
            st.video(result["video_path"])
            st.download_button(
                "Download MP4",
                data=Path(result["video_path"]).read_bytes(),
                file_name=Path(result["video_path"]).name,
                mime="video/mp4",
            )
        with out_right:
            st.markdown("""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:3px solid #16a34a;
                        border-radius:10px; padding:1.1rem 1.3rem; font-family:'Figtree',sans-serif;">
              <div style="font-weight:700; font-size:15px; color:#16a34a; margin-bottom:3px;">✓ &nbsp;Your reel is ready</div>
              <div style="font-size:13px; color:#999; line-height:1.6;">
                Download this reel before generating another. It will be replaced.
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
            if st.button("Generate Another Reel", use_container_width=True):
                st.session_state.pipeline_result = None
                st.rerun()
    else:
        st.error("Generation completed but no video was produced.")
        if st.button("Try Again", use_container_width=True):
            st.session_state.pipeline_result = None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DEMO REELS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-gap-sm" id="demo-reels"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="reveal">
<span class="s-eyebrow" style="text-transform:none">Explore Real Life MagicReel&#8482; Outcomes 👇🏻</span>
<div class="s-title">Dossier in. MagicReel&#8482; out.</div>
<p class="s-sub">Sample MagicReels&#8482; generated entirely from product PDFs: narrated, clinically verified, ready to share. No agency involved.</p>
</div>
""", unsafe_allow_html=True)

for row_start in range(0, len(DEMO_VIDEOS), 3):
    row_demos = DEMO_VIDEOS[row_start:row_start + 3]
    all_cols  = st.columns([1, 0.3, 1, 0.3, 1], gap="small")
    demo_cols = [all_cols[0], all_cols[2], all_cols[4]]
    for i, demo in enumerate(row_demos):
        video_path = DEMOS_DIR / demo["file"]
        thumb_path = BASE_DIR / demo.get("pdf_thumb", "")
        if not video_path.exists():
            continue
        topic_color = TOPIC_COLORS.get(demo["topic"], "#fd4816")
        with demo_cols[i]:
            st.markdown(f"""
            <div style="margin-bottom:10px;">
              <span class="vid-label">{demo["drug"]}</span>&nbsp;
              <span class="t-badge" style="background:{topic_color}12; color:{topic_color}; border:1px solid {topic_color}28; font-size:10px;">{demo["topic"]}</span>
            </div>
            """, unsafe_allow_html=True)
            if thumb_path.exists():
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                  <img src="data:image/png;base64,{_img_b64(thumb_path)}" class="demo-pdf-img">
                  <span class="demo-arrow">→</span>
                </div>
                """, unsafe_allow_html=True)
            st.video(str(video_path))
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

