"""presenter_ui.py - the interactive presenter tab (talk, ask, translate)."""
import hashlib

import streamlit as st

from app import presenter
from app.extras import LANGS, detect_language
from app.avatar import render_presenter_avatar


def _init():
    ss = st.session_state
    ss.setdefault("presenter_chat", [])
    # NOTE: presenter_lang always stores the INTERNAL name:
    # "English" | "Hindi" | "Arabic" | "French"
    ss.setdefault("presenter_lang", "English")
    ss.setdefault("presenter_context", "")
    ss.setdefault("last_presenter_audio", None)
    ss.setdefault("last_presenter_reply", "")
    ss.setdefault("presenter_mp3", None)
    ss.setdefault("presenter_autoplay", False)
    # Unique nonce for the mic widget, so a finished recording doesn't
    # trigger "An error has occurred, please try again." on the next rerun.
    ss.setdefault("mic_nonce", 0)


def _render_msg(m):
    with st.chat_message(m["role"]):
        if m.get("content"):
            st.markdown(m["content"])


def _say(role, content, speak_it=False):
    m = {"role": role, "content": content}
    st.session_state.presenter_chat.append(m)
    _render_msg(m)
    if speak_it and role == "assistant" and content:
        lang_now = st.session_state.presenter_lang
        mp3 = presenter.say(content, lang_now)
        st.session_state.presenter_mp3 = mp3
        st.session_state.presenter_autoplay = bool(mp3)
        st.session_state.last_presenter_reply = content
        if not mp3:
            st.warning(f"No audio for **{lang_now}**. Check the terminal for SPEAK ERROR.")


# Display strings the user sees -> internal names the code uses
DISPLAY_TO_INTERNAL = {
    "English": "English",
    "हिन्दी": "Hindi",
    "العربية": "Arabic",
    "Français": "French",
}
INTERNAL_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_INTERNAL.items()}


def render():
    _init()
    ss = st.session_state

    st.subheader("🎤 Presenter bot")
    st.caption("Talk live during your demo — it answers, explains and translates.")

    # ---------- LANGUAGE PICKER FIRST (uses display names, stores internal) ----------
    display_names = list(DISPLAY_TO_INTERNAL.keys())
    current_display = INTERNAL_TO_DISPLAY.get(ss.presenter_lang, "English")

    top_left, top_right = st.columns([2, 1])
    with top_left:
        picked_display = st.selectbox(
            "🌐 Presenter language",
            display_names,
            index=display_names.index(current_display),
            key="presenter_lang_pick",
        )
        ss.presenter_lang = DISPLAY_TO_INTERNAL[picked_display]
    with top_right:
        st.write("")
        st.write("")
        if st.button("🔊 Test voice", use_container_width=True):
            test = {
                "English": "Hello! I can speak English.",
                "Hindi": "नमस्ते! मैं हिन्दी बोल सकती हूँ।",
                "Arabic": "مرحباً! أستطيع التحدث بالعربية.",
                "French": "Bonjour ! Je peux parler français.",
            }[ss.presenter_lang]
            _say("assistant", test, speak_it=True)
            st.rerun()

    # ---------- avatar + controls ----------
    left, right = st.columns([1, 2])
    with left:
        render_presenter_avatar(audio_bytes=ss.presenter_mp3,
                                autoplay=ss.presenter_autoplay)
        ss.presenter_autoplay = False

    with right:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶️ Start", use_container_width=True):
                _say("assistant", presenter.intro(ss.presenter_lang), speak_it=True)
                _say("assistant", presenter.demo_offer(ss.presenter_lang))
        with c2:
            if st.button("📜 Pitch", use_container_width=True):
                for title, body in presenter.beats(ss.presenter_lang):
                    _say("assistant", f"**{title}** — {body}")
        with c3:
            if st.button("🗑️ Clear", use_container_width=True):
                ss.presenter_chat = []
                ss.last_presenter_reply = ""
                ss.presenter_mp3 = None
                st.rerun()

        if ss.last_presenter_reply and st.button("🔊 Listen to last reply"):
            mp3 = presenter.say(ss.last_presenter_reply, ss.presenter_lang)
            if mp3:
                ss.presenter_mp3 = mp3
                ss.presenter_autoplay = True
                st.rerun()
            else:
                st.warning(f"Couldn't make **{ss.presenter_lang}** audio. Check terminal.")

    # ---------- chat history ----------
    for m in ss.presenter_chat:
        _render_msg(m)

    # ---------- voice input ----------
    # The widget key changes after each recording, so Streamlit doesn't keep
    # feeding back the finished audio on the next rerun (that caused the
    # "An error has occurred, please try again." message).
    with st.expander("🎙️ Speak to the presenter", expanded=False):
        audio = st.audio_input(
            "Record your question",
            key=f"presenter_mic_{ss.mic_nonce}",
            label_visibility="collapsed",
        )
        if audio is not None:
            data = audio.getvalue()
            h = hashlib.md5(data).hexdigest()
            if ss.last_presenter_audio != h:
                ss.last_presenter_audio = h
                with st.spinner("Transcribing…"):
                    text, detected = presenter.listen(data, None)
                if not text:
                    st.warning("I couldn't hear that. Try again.")
                else:
                    ss.presenter_lang = detected or ss.presenter_lang
                    _say("user", f"🎤 {text}")
                    # Bump the nonce so the next render starts with a fresh widget
                    ss.mic_nonce += 1
                    _handle_turn(text, ss.presenter_lang, speak_it=True)
                    st.rerun()

    # ---------- typed input ----------
    text = st.chat_input("Ask the presenter, or say 'translate'…", key="presenter_input")
    if text:
        _say("user", text)
        detected = detect_language(text)
        if detected:
            ss.presenter_lang = detected
        _handle_turn(text, ss.presenter_lang, speak_it=True)


def _handle_turn(text, lang, speak_it=False):
    low = text.lower()
    if "translate" in low:
        last = st.session_state.get("last_presenter_reply")
        if not last:
            _say("assistant", "There's nothing to translate yet.")
            return
        target = "English"
        if "hindi" in low:
            target = "Hindi"
        elif "arabic" in low:
            target = "Arabic"
        elif "french" in low:
            target = "French"
        with st.spinner("Translating…"):
            out = presenter.translate(last, target)
        _say("assistant", f"**{target}:** {out}", speak_it=speak_it)
        return

    with st.spinner("Thinking…"):
        reply = presenter.respond(text, lang, st.session_state.get("presenter_context") or "")
    _say("assistant", reply, speak_it=speak_it)