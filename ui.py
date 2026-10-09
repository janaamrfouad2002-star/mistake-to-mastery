import hashlib

import streamlit as st

from app.core import record, due, mistake_map
from app.engine import analyse, make_twin, check_twin
from app.extras import (LANGS, AUTO, CODE, T, GESTURE_REPLY, detect_language,
                        normalize_digits, transcribe, recognise_gesture, speak)
from app.llm import (extract, explain_with_llm, explain_solution, answer_question,
                     simplify, translate_text)
from app.presenter_ui import render as render_presenter

st.set_page_config(page_title="Mistake-to-Mastery", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# ============================================================
# ANIMATED GLOBAL STYLING
# ============================================================
st.markdown("""
<style>
:root {
  --brand:#6366f1;
  --brand2:#a855f7;
  --brand3:#ec4899;
  --ink:#0f172a;
  --muted:#64748b;
  --line:#e2e8f0;
  --ok:#10b981;
  --warn:#f59e0b;
}

html, body, [class*="css"] {
  font-family: "Inter", -apple-system, "Segoe UI", Roboto, sans-serif;
  color: var(--ink);
}

.block-container { padding-top: 1.2rem !important; padding-bottom: 2.5rem !important; }

/* ---------- Floating background orbs ---------- */
.bg-orbs {
  position: fixed; inset: 0; overflow: hidden;
  z-index: 0; pointer-events: none;
}
.bg-orbs span {
  position: absolute; border-radius: 50%;
  filter: blur(60px); opacity: 0.45;
  animation: float 18s ease-in-out infinite;
}
.bg-orbs .o1 { width:280px; height:280px; background:#a5b4fc; top:-60px; left:-40px; animation-delay:0s; }
.bg-orbs .o2 { width:340px; height:340px; background:#f0abfc; top:40%; right:-80px; animation-delay:-6s; }
.bg-orbs .o3 { width:260px; height:260px; background:#fbcfe8; bottom:-80px; left:20%; animation-delay:-12s; }
.bg-orbs .o4 { width:220px; height:220px; background:#c7d2fe; top:15%; left:45%; animation-delay:-3s; }
@keyframes float {
  0%,100% { transform: translate(0,0) scale(1); }
  33%     { transform: translate(30px,-20px) scale(1.05); }
  66%     { transform: translate(-25px,25px) scale(.95); }
}

/* ---------- Animated gradient hero ---------- */
.hero {
  position: relative;
  border-radius: 24px;
  padding: 34px 38px 30px;
  margin-bottom: 24px;
  color: #fff;
  background: linear-gradient(-45deg, #6366f1, #a855f7, #ec4899, #6366f1);
  background-size: 300% 300%;
  animation: heroShift 14s ease infinite;
  box-shadow: 0 25px 60px -25px rgba(99,102,241,.6);
  overflow: hidden;
  z-index: 2;
}
.hero::after {
  content:""; position:absolute; inset:0;
  background:
    radial-gradient(circle at 15% 20%, rgba(255,255,255,.30), transparent 40%),
    radial-gradient(circle at 85% 80%, rgba(255,255,255,.20), transparent 45%);
  pointer-events: none;
}
@keyframes heroShift {
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
.hero h1 {
  font-size: 2.2rem; margin: 0 0 8px 0; font-weight: 800;
  letter-spacing: -0.02em; position: relative; z-index: 2;
}
.hero p {
  margin: 0 0 14px 0; font-size: 1.05rem; opacity: .96;
  position: relative; z-index: 2;
  min-height: 1.5em;
}

.hero .stat-row {
  display: flex; gap: 14px; flex-wrap: wrap; margin-top: 12px;
  position: relative; z-index: 2;
}
.hero .stat {
  flex: 1; min-width: 130px;
  background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 14px;
  padding: 10px 14px;
  backdrop-filter: blur(8px);
}
.hero .stat .label { font-size: .74rem; letter-spacing: .08em; text-transform: uppercase; opacity: .85; }
.hero .stat .value { font-weight: 800; font-size: 1.3rem; margin-top: 2px; }

.hero .chips { margin-top: 14px; display:flex; flex-wrap:wrap; gap:8px;
               position: relative; z-index: 2; }
.hero .chip {
  background: rgba(255,255,255,.18);
  border: 1px solid rgba(255,255,255,.38);
  padding: 5px 13px; border-radius: 999px;
  font-size: .82rem; backdrop-filter: blur(6px);
  transition: transform .15s ease;
}
.hero .chip:hover { transform: translateY(-2px); }

/* ---------- Tabs as pills with shimmer ---------- */
button[data-baseweb="tab"] {
  font-weight: 700; font-size: 1rem;
  padding: 10px 20px; border-radius: 999px;
  position: relative; overflow: hidden;
  transition: all .18s ease;
}
button[data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(90deg, var(--brand), var(--brand2));
  color: #fff !important;
  box-shadow: 0 10px 24px -12px rgba(99,102,241,.9);
}
button[data-baseweb="tab"][aria-selected="true"] * { color:#fff !important; }
button[data-baseweb="tab"][aria-selected="true"]::after {
  content:""; position:absolute; inset:0;
  background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,.35) 50%, transparent 70%);
  transform: translateX(-100%);
  animation: shimmer 3.2s ease-in-out infinite;
}
@keyframes shimmer {
  0%, 60%  { transform: translateX(-100%); }
  100%     { transform: translateX(100%); }
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[data-baseweb="tab-list"] { gap: 8px; }

/* ---------- Buttons with hover lift + click ripple ---------- */
div.stButton > button {
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  font-weight: 600;
  padding: 9px 16px;
  color: var(--ink);
  transition: all .16s ease;
  position: relative; overflow: hidden;
  box-shadow: 0 1px 2px rgba(15,23,42,.05);
}
div.stButton > button::before {
  content:""; position:absolute; left:-100%; top:0; width:100%; height:100%;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,.10), transparent);
  transition: left .5s ease;
}
div.stButton > button:hover::before { left: 100%; }
div.stButton > button:hover {
  border-color: var(--brand); color: var(--brand);
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -12px rgba(99,102,241,.55);
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, var(--brand), var(--brand2));
  color: #fff; border: none;
}
div.stButton > button[kind="primary"]:hover { filter: brightness(1.08); }

/* ---------- Chat bubbles fade-in ---------- */
[data-testid="stChatMessage"] {
  border-radius: 16px;
  border: 1px solid var(--line);
  padding: 10px 14px;
  background: #ffffff;
  box-shadow: 0 4px 14px -10px rgba(15,23,42,.15);
  margin-bottom: 8px;
  animation: fadeUp .35s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Cards ---------- */
.card {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 18px 20px;
  box-shadow: 0 10px 30px -22px rgba(15,23,42,.3);
  position: relative; z-index: 2;
  transition: transform .18s ease, box-shadow .18s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 40px -22px rgba(99,102,241,.5);
}
.muted { color: var(--muted); font-size: .9rem; }

/* ---------- Section header ---------- */
.section-title {
  font-weight: 800; font-size: 1.05rem; color: var(--ink);
  margin: 10px 0 8px;
  display: flex; align-items: center; gap: 8px;
  position: relative; z-index: 2;
}
.section-title::before {
  content:""; width: 6px; height: 20px; border-radius: 4px;
  background: linear-gradient(180deg,var(--brand),var(--brand2));
  animation: barPulse 2.4s ease-in-out infinite;
}
@keyframes barPulse {
  0%,100% { transform: scaleY(1); opacity: 1; }
  50%     { transform: scaleY(.7); opacity: .75; }
}

/* ---------- Pulse ring on example buttons ---------- */
@keyframes pulseRing {
  0%   { box-shadow: 0 0 0 0 rgba(168,85,247,.45); }
  70%  { box-shadow: 0 0 0 12px rgba(168,85,247,0); }
  100% { box-shadow: 0 0 0 0 rgba(168,85,247,0); }
}
div.stButton > button[kind="secondary"]:first-child {
  animation: pulseRing 2.4s ease-out infinite;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#f5f6ff 0%, #ffffff 100%);
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-weight: 800; }

/* ---------- Progress ring ---------- */
.ring-stat {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 10px;
}
.ring-svg { width: 46px; height: 46px; flex-shrink: 0; }
.ring-svg circle {
  fill: none; stroke-width: 5; transform: rotate(-90deg); transform-origin: 50% 50%;
}
.ring-svg .bg { stroke: #e5e7eb; }
.ring-svg .fg {
  stroke: url(#grad); stroke-linecap: round;
  transition: stroke-dashoffset .9s ease;
}
.ring-meta { font-size: .86rem; color: var(--ink); }
.ring-meta .lbl { color: var(--muted); font-size: .76rem; }

/* ---------- Skeleton loader ---------- */
.skel {
  height: 12px; border-radius: 6px;
  background: linear-gradient(90deg,#eef2ff 25%, #e0e7ff 37%, #eef2ff 63%);
  background-size: 400% 100%;
  animation: skel 1.4s ease-in-out infinite;
  margin: 6px 0;
}
@keyframes skel { 0%{background-position:100% 0} 100%{background-position:0 0} }

/* ---------- Inputs / alerts / code ---------- */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div { border-radius: 10px !important; }
[data-testid="stAlert"] { border-radius: 14px !important; border: 1px solid var(--line) !important; }
code { font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; font-size: 0.95rem; }
.stCodeBlock, pre { border-radius: 12px !important; }
details { border-radius: 12px !important; border: 1px solid var(--line) !important; background: #fff !important; }
.stSpinner > div { border-top-color: var(--brand) !important; }
</style>

<!-- floating background orbs -->
<div class="bg-orbs" aria-hidden="true">
  <span class="o1"></span><span class="o2"></span>
  <span class="o3"></span><span class="o4"></span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
ss = st.session_state
ss.setdefault("chat", [])
ss.setdefault("ui_lang", "English")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="section-title">🌐 Language</div>', unsafe_allow_html=True)
    choice = st.selectbox("Language", [AUTO] + list(LANGS), label_visibility="collapsed")
    if choice != AUTO:
        ss.ui_lang = LANGS[choice][0]

start_lang = ss.ui_lang
lang = ss.ui_lang
t = T[lang]

with st.sidebar:
    st.markdown('<div class="section-title">👤 Profile</div>', unsafe_allow_html=True)
    user = st.text_input(t["name"], "student1", label_visibility="collapsed")

if lang == "Arabic":
    st.markdown("<style>[data-testid='stChatMessage']{direction:rtl;text-align:right}</style>",
                unsafe_allow_html=True)

# ============================================================
# HERO with animated counter + typing tagline
# ============================================================
st.markdown(f"""
<div class="hero">
  <h1>🎓 Mistake-to-Mastery</h1>
  <p class="typed" id="tagline"></p>
  <div class="stat-row">
    <div class="stat"><div class="label">Mistakes verified</div><div class="value" id="c1">0</div></div>
    <div class="stat"><div class="label">Languages</div><div class="value" id="c2">0</div></div>
    <div class="stat"><div class="label">Subjects</div><div class="value" id="c3">0</div></div>
  </div>
  <div class="chips">
    <span class="chip">🧠 Verified mistakes</span>
    <span class="chip">🗣️ Any language</span>
    <span class="chip">📷 · 🎤 · ✍️</span>
    <span class="chip">🔁 Twin practice</span>
  </div>
</div>
<script>
(function() {{
  const tagline = {t["tagline"]!r};
  const el = document.getElementById("tagline");
  let i = 0;
  function type() {{
    if (i <= tagline.length) {{
      el.textContent = tagline.slice(0, i);
      i++;
      setTimeout(type, 28);
    }}
  }}
  type();

  function count(id, target, dur=1200) {{
    const e = document.getElementById(id);
    const t0 = performance.now();
    function step(now) {{
      const p = Math.min(1, (now - t0) / dur);
      e.textContent = Math.floor(p * target);
      if (p < 1) requestAnimationFrame(step);
    }}
    requestAnimationFrame(step);
  }}
  count("c1", 400);
  count("c2", 4);
  count("c3", 5);
}})();
</script>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def friendly(tag: str) -> str:
    base = tag.replace("_", " ").capitalize()
    return base if lang == "English" else translate_text(base, lang)


def render(m):
    if m["role"] == "read":
        with st.expander(t["read"]):
            st.json(m["content"])
    else:
        with st.chat_message(m["role"]):
            if m.get("content"):
                st.markdown(m["content"])
            if m.get("img"):
                st.image(m["img"], width=300)


def say(role, content, img=None):
    m = {"role": role, "content": content, "img": img}
    ss.chat.append(m)
    render(m)


def thinking_skeleton(label="Thinking"):
    st.markdown(f"""
    <div class="card" style="max-width:420px">
      <div class="muted" style="margin-bottom:8px">{label}…</div>
      <div class="skel" style="width:90%"></div>
      <div class="skel" style="width:75%"></div>
      <div class="skel" style="width:60%"></div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# TABS
# ============================================================
tab_learn, tab_present = st.tabs(["📚  Learn", "🎤  Present"])

with tab_present:
    render_presenter()

with tab_learn:

    for m in ss.chat:
        render(m)

    if not ss.chat:
        st.markdown(f'<div class="card">{t["welcome"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title" style="margin-top:18px">{t["try"]}</div>',
                    unsafe_allow_html=True)
        cols = st.columns(2)
        for i, example in enumerate(t["examples"]):
            if cols[i % 2].button(example.replace("\n", " / "),
                                  key=f"ex{i}", use_container_width=True):
                ss["queued"] = example

    # ---------- camera gestures ----------
    with st.sidebar:
        st.markdown('<div class="section-title">🎛️ Inputs</div>', unsafe_allow_html=True)

        def on_gesture(name: str):
            if name == "Thumb_Down":
                last = next((m["content"] for m in reversed(ss.chat)
                             if m["role"] == "assistant" and m.get("content")), None)
                if last:
                    with st.spinner("..."):
                        again = simplify(last, lang)
                    say("assistant", again or t["sorry"])
                return
            reply = GESTURE_REPLY[lang].get(name)
            if reply:
                say("assistant", reply)

        shot = st.camera_input(t["cam"])
        if shot is not None:
            data = shot.getvalue()
            h = hashlib.md5(data).hexdigest()
            if ss.get("last_shot") != h:
                ss["last_shot"] = h
                gestures, err = recognise_gesture(data)
                if err:
                    st.warning(err)
                elif not gestures:
                    st.info(t["no_gesture"])
                else:
                    name, score = gestures[0]
                    st.success(f"{name} ({score:.0%})" if score else name)
                    on_gesture(name)

        voice_text, voice_lang = None, None
        ss.setdefault("learn_mic_nonce", 0)
        audio = st.audio_input(t["mic"], key=f"learn_mic_{ss.learn_mic_nonce}")
        if audio is not None:
            data = audio.getvalue()
            h = hashlib.md5(data).hexdigest()
            if ss.get("last_audio") != h:
                ss["last_audio"] = h
                with st.spinner("..."):
                    voice_text, voice_lang = transcribe(data, None if choice == AUTO else CODE[lang])
                ss.learn_mic_nonce += 1
                if not voice_text:
                    st.warning(t["cant_hear"])
                    voice_text = None

    # ---------- main input ----------
    prompt = st.chat_input(t["placeholder"], accept_file=True, file_type=["png", "jpg", "jpeg"])
    queued = ss.pop("queued", None)

    text, img, mime, go, from_voice = "", None, "image/png", False, False
    if prompt:
        text = prompt.text or ""
        if prompt.files:
            img = prompt.files[0].getvalue()
            mime = prompt.files[0].type
        go = True
    elif queued:
        text, go = queued, True
    elif voice_text:
        text, go, from_voice = voice_text, True, True

    if go:
        text = normalize_digits(text)
        if choice == AUTO:
            detected = voice_lang if from_voice and voice_lang else detect_language(text)
            if detected:
                ss.ui_lang = detected
        lang = ss.ui_lang
        t = T[lang]

        say("user", ("🎤 " if from_voice else "") + (text or "📷"), img)

        with st.spinner("..."):
            ex = extract(text, img, mime)
        ss.chat.append({"role": "read", "content": ex.model_dump()})
        render(ss.chat[-1])

        try:
            result = analyse(ex)
        except Exception as e:
            print("ANALYSE ERROR:", repr(e), ex.model_dump())
            result = None
            say("assistant", t["cant_read"])

        if result:
            status = result["status"]
            if status == "correct":
                say("assistant", "✅ " + t["correct"])
            elif status == "solved":
                with st.spinner("..."):
                    reply = explain_solution(result["question"], result["answer"], lang, t["answer"])
                say("assistant", reply)
            elif status == "unsupported":
                with st.spinner("..."):
                    reply = answer_question(text, img, mime, lang) or t["sorry"]
                say("assistant", reply)
            else:
                with st.spinner("..."):
                    hint = explain_with_llm(result["prev"], result["wrong"], result["tag"], lang) or ""
                say("assistant",
                    f"**{t['mistake']}:** `{friendly(result['tag'])}`\n\n"
                    f"{t['your_line']}: `{result['wrong']}`\n\n{hint}")
                record(user, result["tag"], correct=False)
                ss["twin"] = {"subject": result["subject"], "tag": result["tag"],
                              "problem": make_twin(result["subject"], result["tag"])}

        if lang != start_lang:
            st.rerun()

    # ---------- read aloud ----------
    last_reply = next((m["content"] for m in reversed(ss.chat)
                       if m["role"] == "assistant" and m.get("content")), None)
    if last_reply and st.button("🔊 " + t["read_aloud"]):
        mp3 = speak(last_reply, CODE[lang])
        if mp3:
            st.audio(mp3, format="audio/mp3", autoplay=True)
        else:
            st.warning(t["no_audio"])

    # ---------- practice problem ----------
    tw = ss.get("twin")
    if tw:
        st.markdown('<div class="section-title">🧩 ' + t["try_similar"] + '</div>',
                    unsafe_allow_html=True)
        task, label = t["tasks"].get(tw["subject"], ("Solve", "Your answer"))
        st.markdown(f'<div class="card"><b>{task}</b><br>'
                    f'<code style="font-size:1rem">{tw["problem"]}</code></div>',
                    unsafe_allow_html=True)
        ans = st.text_area(label, key="twin_ans")
        if st.button("✅ " + t["check_btn"], type="primary"):
            try:
                ok = check_twin(tw["subject"], tw["problem"], normalize_digits(ans))
            except Exception:
                st.error(t["cant_read_twin"])
                st.stop()
            record(user, tw["tag"], correct=ok)
            if ok:
                st.success(t["fixed"])
                st.balloons()
            else:
                st.warning(t["same"])

    # ---------- sidebar: mistake map with progress rings ----------
    with st.sidebar:
        st.markdown('<div class="section-title">🗺️ ' + t["map"] + '</div>',
                    unsafe_allow_html=True)
        rows = mistake_map(user)
        if not rows:
            st.caption(t["none"])
        for tag, errors, box in rows:
            pct = min(box, 4) / 4
            circ = 2 * 3.14159 * 18
            off = circ * (1 - pct)
            st.markdown(f"""
            <div class="ring-stat">
              <svg class="ring-svg" viewBox="0 0 44 44">
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#6366f1"/>
                    <stop offset="100%" stop-color="#a855f7"/>
                  </linearGradient>
                </defs>
                <circle class="bg" cx="22" cy="22" r="18"/>
                <circle class="fg" cx="22" cy="22" r="18"
                        stroke-dasharray="{circ:.1f}"
                        stroke-dashoffset="{off:.1f}"/>
              </svg>
              <div class="ring-meta">
                <div>{friendly(tag)}</div>
                <div class="lbl">{errors} {t['errors']} · {t['level']} {box}/4</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        due_tags = due(user)
        if due_tags:
            st.info(f"🔔 {t['due']}: " + ", ".join(friendly(x) for x in due_tags))
        if st.button("🗑️ " + t["clear"], use_container_width=True):
            ss.chat = []
            ss.pop("twin", None)
            st.rerun()