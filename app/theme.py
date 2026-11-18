"""Dark presentation theme and the opening decision illustration."""

SITE_CSS='''
:root {--runway-bg:#0d151c;--runway-panel:#14232d;--runway-border:#293e48;--runway-text:#edf4f2;--runway-muted:#a6bac2;--runway-accent:#6aded0}
.stApp {background:var(--runway-bg);color:var(--runway-text)}
.block-container {max-width:1280px;padding-top:3rem;padding-bottom:1.5rem}
[data-testid="stHeader"] {background:rgba(13,21,28,.94);backdrop-filter:blur(14px)}
h1 {color:#edf4f2!important;font-weight:650!important;letter-spacing:-.045em!important;line-height:1.12!important}
h2,h3 {color:#e3eeed!important;letter-spacing:-.025em!important}
[data-testid="stSidebar"] {background:#101d26;border-right:1px solid #263a45}
[data-testid="stSidebar"] h1 {font-size:27px!important;letter-spacing:-.035em!important}
[data-testid="stSidebarContent"]{height:100dvh;overflow:hidden!important;display:flex;flex-direction:column}
[data-testid="stSidebarUserContent"]{flex:1;min-height:0;padding:3.5rem 1.25rem 1rem!important;display:flex;flex-direction:column}
[data-testid="stSidebarUserContent"] > div{height:100%;min-height:0}
.st-key-analyst_shell{position:absolute!important;top:64px;bottom:16px;left:20px;right:20px;width:auto!important;height:auto!important;min-height:0;gap:14px!important}
.st-key-analyst_shell > [data-testid="stLayoutWrapper"]:has(> .st-key-analyst_history){flex:1 1 0!important;min-height:0!important;overflow:hidden}
.st-key-analyst_header{flex:0 0 auto!important;gap:8px!important}
.st-key-analyst_history{flex:1 1 0!important;min-height:0!important;overflow-y:auto!important;overscroll-behavior:contain}
.st-key-analyst_prompt{flex:0 0 auto!important;margin-top:auto}
[data-testid="stChatMessage"] {background:#172933;border:1px solid #2a4049;border-radius:14px}
[data-testid="stCaptionContainer"] {color:#91a9b3}
[data-testid="stMetricValue"] {font-size:1.9rem;letter-spacing:-.035em;color:#ecf5f2}
[data-testid="stMetricLabel"] {font-size:.85rem;color:#abc0c7}
.eyebrow {color:#71d9cd;font:600 11px system-ui;letter-spacing:.17em;margin:0 0 8px}
.step-label {font:600 11px system-ui;letter-spacing:.14em;color:#79a9b1;margin-bottom:16px}
.pill {display:inline-block;padding:6px 11px;border:1px solid #465048;border-radius:20px;background:#282f2b;color:#e3bd85;font:500 11px system-ui;letter-spacing:.02em}
.assistant-note {font:400 14px/1.7 system-ui;color:#9eb6c1}
.small-rule {border:0;border-top:1px solid #293e48;margin:20px 0}
.lead {font:400 19px/1.6 system-ui;color:#b8ced3;max-width:850px;margin:0 0 16px}
.statement {font:500 20px/1.5 system-ui;color:#d2e6e3;max-width:1000px;margin:18px 0}
.insight-card {background:#142a30;border:1px solid #28464c;border-radius:14px;padding:18px 22px;margin:12px 0;font:400 15px/1.65 system-ui;color:#bdd3d6}
.insight-card strong {font-weight:650;color:#e9f5f0}
.reference-strip {display:grid;grid-template-columns:1fr 1.3fr 1fr;gap:12px;background:linear-gradient(120deg,#18322f,#162831);border:1px solid #30504d;border-radius:14px;padding:15px 19px}
.reference-strip strong {display:block;font:600 22px system-ui;color:#d9f0e7;letter-spacing:-.03em}
.reference-strip span {display:block;font:400 12px/1.5 system-ui;color:#9fbbb7;margin-top:4px}
.conclusion-card {background:#14262e;border:1px solid #2a4049;border-radius:15px;padding:21px 23px;min-height:174px;margin-bottom:10px}
.conclusion-card h3 {font:600 19px system-ui;color:#e1f1ec;margin:0 0 13px}
.conclusion-card p {font:400 15px/1.65 system-ui;color:#b1c8ce;margin:0}
[data-baseweb="tab-list"] {gap:9px;border-bottom:1px solid #293d47;margin-bottom:22px}
[data-baseweb="tab"] {font-weight:500;padding:12px 17px;border-radius:9px 9px 0 0;color:#9fb8c2}
[data-baseweb="tab"][aria-selected="true"] {background:#183238;color:#83e5d7}
[data-baseweb="tab"]:hover {color:#d8eee9;background:#162a33}
[data-testid="stForm"] {background:#101e27;border-color:#2a404b;border-radius:16px}
[data-testid="stExpander"] {border-color:#2c414b}
/* Bright actions and selected customer chips need dark ink, including the
   nested Markdown labels that Streamlit otherwise paints white. */
[data-testid="stBaseButton-primary"]:not(:disabled),
[data-testid="stBaseButton-primaryFormSubmit"]:not(:disabled) {background:#6aded0!important;border-color:#6aded0!important;color:#092a2a!important;font-weight:650}
[data-testid="stBaseButton-primary"]:not(:disabled) *,
[data-testid="stBaseButton-primaryFormSubmit"]:not(:disabled) * {color:#092a2a!important;-webkit-text-fill-color:#092a2a!important}
[data-testid="stBaseButton-primary"]:not(:disabled):hover,
[data-testid="stBaseButton-primaryFormSubmit"]:not(:disabled):hover {background:#a0ecdf!important;border-color:#a0ecdf!important}
[data-testid="stMultiSelect"] [data-tag] {background:#6aded0!important;border:1px solid #83e8d9!important;color:#092a2a!important}
[data-testid="stMultiSelect"] [data-tag] span,
[data-testid="stMultiSelect"] [data-tag] button,
[data-testid="stMultiSelect"] [data-tag] svg {color:#092a2a!important;-webkit-text-fill-color:#092a2a!important}
[data-testid="stMultiSelect"] [data-tag] button:hover {background:#092a2a1f!important;border-radius:4px}
[role="listbox"] [role="option"][aria-selected="true"],
[role="listbox"] [role="option"][data-focused],
[role="listbox"] [role="option"][data-hovered] {background:#23464c!important;color:#edf4f2!important}
[role="listbox"] [role="option"] span {color:inherit!important}
[data-testid="stMain"] {--story-offset:60px;scroll-snap-type:none;scroll-padding-top:var(--story-offset);scroll-behavior:smooth}
.st-key-chapter_question,.st-key-chapter_audience,.st-key-chapter_patterns,.st-key-chapter_simulation,.st-key-chapter_answer {min-height:calc(100svh - 60px);height:auto;overflow:visible;padding:1rem 0 1.5rem;border-top:1px solid #293d47}
.st-key-chapter_audience,.st-key-chapter_patterns{gap:8px!important;padding:10px 0 12px}
.st-key-audience_tab [role="tabpanel"] > [data-testid="stVerticalBlock"],.st-key-exposure_tab [role="tabpanel"] > [data-testid="stVerticalBlock"]{gap:5px!important}
.st-key-chapter_audience .story-continue,.st-key-chapter_patterns .story-continue{padding:6px 0;font-size:14px}
.st-key-chapter_audience h1,.st-key-chapter_patterns h1{font-size:2.35rem!important;padding:.15rem 0 .4rem!important}
.st-key-chapter_audience h3,.st-key-chapter_patterns h3{font-size:1.2rem!important;padding:.2rem 0 .35rem!important}
.st-key-chapter_audience .step-label,.st-key-chapter_patterns .step-label{margin-bottom:6px}
.st-key-chapter_audience .insight-card{font-size:14px;line-height:1.5;padding:12px 16px;margin:6px 0}
.st-key-chapter_patterns .conclusion-card{padding:16px 18px;min-height:142px;margin-bottom:4px}
.st-key-chapter_patterns .conclusion-card h3{font-size:17px;margin-bottom:8px}
.st-key-chapter_patterns .conclusion-card p{font-size:14px;line-height:1.5}
.st-key-chapter_patterns .reference-strip{padding:8px 14px}
.st-key-chapter_patterns .reference-strip strong{font-size:18px;line-height:1.2}
.st-key-chapter_patterns{gap:6px!important}
.st-key-chapter_patterns .reference-strip span{font-size:11px;line-height:1.4;margin-top:2px}
.st-key-repetition_chart{gap:4px!important}
.st-key-chapter_question {border-top:0;padding-top:1.5rem}
.story-continue {display:inline-flex;gap:18px;align-items:center;color:#78dfd1!important;text-decoration:none!important;font:500 15px system-ui;padding:12px 0}
.story-continue:hover {color:#b0f1e5!important;text-decoration:underline!important}
h1[id],.step-label[id] {scroll-margin-top:5rem}
.hero-copy {padding:12px 22px 12px 0}
.hero-kicker {display:inline-flex;gap:10px;align-items:center;font:600 11px system-ui;letter-spacing:.14em;color:#9ac1bf;margin:0 0 19px}
.hero-kicker:before {content:'';height:7px;width:7px;border-radius:50%;background:#6aded0;box-shadow:0 0 18px #4fc8b44d}
.hero-title {font:650 clamp(42px,4.1vw,66px)/1.03 system-ui!important;letter-spacing:-.065em!important;color:#f0f5f1!important;margin:0 0 20px!important;padding:0!important}
.hero-title span {color:#79e2cf}
.hero-lead {font:400 18px/1.55 system-ui;color:#b4cbd1;max-width:620px;margin:0 0 22px}
.story-continue.hero-cta {background:#79e2cf;color:#10211f!important;padding:13px 22px;border-radius:30px;font-weight:650;box-shadow:0 8px 30px #00000024;transition:transform .2s,background .2s}
.story-continue.hero-cta:hover {background:#a2eddf;transform:translateY(-2px);text-decoration:none!important}
.brief-card {background:linear-gradient(140deg,#162730,#12212a);border:1px solid #2a414a;border-radius:17px;padding:22px 25px;min-height:170px;margin-top:12px}
.brief-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px;margin-top:14px}
.brief-grid .brief-card {margin-top:0}
.brief-card .card-label {font:600 10px system-ui;letter-spacing:.15em;color:#7fa4ae;margin-bottom:12px}
.brief-card h3 {font:600 20px system-ui;letter-spacing:-.025em;margin:0 0 12px;color:#e9f2ed}
.brief-card p {font:400 15px/1.7 system-ui;color:#aec4cd;margin:0;max-width:620px}
.journey-card {display:grid;grid-template-columns:40px 1fr;gap:14px;padding:21px 0 15px;margin-top:12px;border-top:1px solid #29404a}
.journey-number {height:34px;width:34px;display:flex;align-items:center;justify-content:center;border:1px solid #35564f;border-radius:50%;font:600 12px system-ui;color:#7edbc8;background:#142b29}
.journey-card.phase-two .journey-number {color:#f2be8d;border-color:#634d3f;background:#30281f}
.journey-card h3 {font:600 17px system-ui;margin:2px 0 8px;color:#dcece7}
.journey-card p {font:400 14px/1.7 system-ui;color:#91acb8;margin:0;max-width:550px}
.hero-footer {display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:15px;padding-top:18px;border-top:1px solid #293e48;color:#8ca9b4;font:400 13px/1.6 system-ui}
.hero-footer .scroll-hint {color:#77b8b4;white-space:nowrap;letter-spacing:.08em;font-size:10px}
@media(max-width:900px) {.hero-title{font-size:48px!important}.hero-copy{padding-right:0}.reference-strip{grid-template-columns:1fr 1fr}.hero-footer{align-items:flex-start}.hero-footer .scroll-hint{display:none}}
[class*="st-key-audience_group_"]{position:relative;padding:8px 12px!important;border:1px solid #243d47;border-radius:10px;background:#14232d;margin-bottom:0;transition:background .2s,border-color .2s}
[class*="st-key-audience_group_"] [data-testid="stVerticalBlock"]{gap:4px!important}
[class*="st-key-audience_group_"]:hover{border-color:#6aded0;background:#192f38}
[class*="st-key-repetition_group_"]{position:relative;border-radius:14px;overflow:hidden;gap:0!important}
[class*="st-key-choose_audience_"],[class*="st-key-choose_repetition_"]{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:2}
[class*="st-key-choose_audience_"] > div,[class*="st-key-choose_repetition_"] > div{width:100%!important;height:100%!important}
[class*="st-key-choose_audience_"] button,[class*="st-key-choose_repetition_"] button{width:100%!important;height:100%!important;min-height:0!important;background:transparent!important;border:0!important;border-radius:12px!important;box-shadow:none!important;cursor:pointer}
[class*="st-key-choose_audience_"] button *,[class*="st-key-choose_repetition_"] button *{opacity:0!important}
[class*="st-key-choose_audience_"] button:hover,[class*="st-key-choose_repetition_"] button:hover{background:#6aded00a!important}
[class*="st-key-choose_audience_"] button:focus-visible,[class*="st-key-choose_repetition_"] button:focus-visible{outline:2px solid #6aded0!important;outline-offset:-3px!important}
.group-name{font:600 15px/1.35 system-ui;color:#e0edeb}
.group-mission{font-size:11px;color:#a0b8bd;margin-top:2px;line-height:1.35}
.group-criteria{font-size:13px;color:#d4e4e5;line-height:1.4}
.audience-share{display:flex;align-items:center;gap:12px}.audience-share strong{font-size:22px;line-height:1.15;min-width:46px}
.audience-track{flex:1;height:24px;border-radius:5px;background:#20353f}.audience-track span{display:block;height:100%;border-radius:5px}
.analyst-focus{animation:analyst-glow 3.5s ease-out}
@keyframes analyst-glow{0%,35%{box-shadow:0 0 0 3px #6aded0,0 0 36px #6aded026}100%{box-shadow:none}}
@media(max-width:700px) {.brief-grid{grid-template-columns:1fr;gap:14px}}
@media(prefers-reduced-motion:reduce) {[data-testid="stMain"]{scroll-behavior:auto}.story-continue.hero-cta{transition:none}}
'''

def landing_tradeoff():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 365" font-family="system-ui,sans-serif" role="img" aria-label="Illustration of one advertising budget split between repeat exposure and reaching new customers">
    <defs><radialGradient id="glow"><stop stop-color="#214b49"/><stop offset="1" stop-color="#12242d"/></radialGradient><linearGradient id="edge" x2="1" y2="1"><stop stop-color="#36554e"/><stop offset="1" stop-color="#263c48"/></linearGradient></defs>
    <rect x="1" y="1" width="498" height="363" rx="24" fill="url(#glow)" stroke="url(#edge)"/>
    <text x="30" y="35" fill="#85aaa9" font-size="10" font-weight="600" letter-spacing="2">THE ALLOCATION TRADEOFF</text>
    <text x="30" y="67" fill="#e1eeeb" font-size="22" font-weight="600" letter-spacing="-.5">One budget. Two directions.</text>
    <path d="M250 120 C250 160 123 133 123 182 M250 120 C250 160 373 133 373 182" fill="none" stroke="#44636a" stroke-width="1.5" stroke-dasharray="4 5"/>
    <rect x="199" y="91" width="102" height="35" rx="18" fill="#223f40" stroke="#4b7970"/><text x="250" y="113" text-anchor="middle" fill="#a5ead8" font-size="12" font-weight="600">THE NEXT AD</text>
    <circle cx="123" cy="213" r="58" fill="none" stroke="#345b57"/><circle cx="123" cy="213" r="42" fill="none" stroke="#4a8d7d"/><circle cx="123" cy="213" r="25" fill="#276255" stroke="#78d3ad"/>
    <circle cx="123" cy="213" r="5" fill="#b6f2d3"/><circle cx="155" cy="187" r="4" fill="#79d4a7"/><circle cx="65" cy="215" r="4" fill="#79d4a7"/>
    <path d="M332 185 L373 171 L410 199 L398 240 L354 251 L329 217 L373 209 L398 240 M373 171 L373 209 L410 199 M354 251 L373 209 L332 185" fill="none" stroke="#70523d" stroke-width="1.4"/>
    <g fill="#efb078"><circle cx="332" cy="185" r="5"/><circle cx="373" cy="171" r="6"/><circle cx="410" cy="199" r="5"/><circle cx="398" cy="240" r="6"/><circle cx="354" cy="251" r="5"/><circle cx="329" cy="217" r="5"/><circle cx="373" cy="209" r="7"/></g>
    <text x="123" y="304" text-anchor="middle" fill="#c4e9db" font-size="16" font-weight="600">Repeat exposure</text><text x="123" y="326" text-anchor="middle" fill="#7fa99d" font-size="12">Build familiarity</text>
    <text x="373" y="304" text-anchor="middle" fill="#efd4b6" font-size="16" font-weight="600">Wider reach</text><text x="373" y="326" text-anchor="middle" fill="#b3987e" font-size="12">Find new customers</text>
    </svg>'''
