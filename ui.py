import streamlit as st

from app.core import record, due, mistake_map
from app.engine import analyse, make_twin, check_twin
from app.llm import extract, explain_with_llm, explain_solution, answer_question

st.title("Mistake-to-Mastery")
user = st.sidebar.text_input("Your name", "student1")

if "chat" not in st.session_state:
    st.session_state.chat = []

for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)


def say(role, msg):
    st.session_state.chat.append((role, msg))
    with st.chat_message(role):
        st.markdown(msg)


prompt = st.chat_input(
    "Ask a question, or send your working (type it or upload a photo).",
    accept_file=True, file_type=["png", "jpg", "jpeg"],
)

if prompt:
    text = prompt.text or ""
    img = prompt.files[0].getvalue() if prompt.files else None
    mime = prompt.files[0].type if prompt.files else "image/png"

    st.session_state.chat.append(("user", text or "📷 (photo)"))
    with st.chat_message("user"):
        if text:
            st.markdown(text)
        if img:
            st.image(img, width=300)

    with st.spinner("Reading your message..."):
        ex = extract(text, img, mime)
    with st.expander("What I read (check it is right!)"):
        st.json(ex.model_dump())

    try:
        result = analyse(ex)
    except Exception:
        result = None
        say("assistant", "I couldn't read the maths there. If I misread your photo, "
                         "type the problem and I'll try again.")

    if result:
        status = result["status"]
        if status == "correct":
            say("assistant", "All correct! ✅")
        elif status == "solved":
            with st.spinner("Working it out..."):
                say("assistant", explain_solution(result["question"], result["answer"]))
        elif status == "unsupported":
            with st.spinner("Thinking..."):
                reply = answer_question(text, img, mime)
            say("assistant", reply + "\n\n*⚠️ Not verified by software: I only verify "
                                     "algebra, derivatives and integrals so far.*")
        else:
            with st.spinner("Writing a hint..."):
                hint = explain_with_llm(result["prev"], result["wrong"], result["tag"])
            say("assistant",
                f"**Verified mistake:** `{result['tag']}`\n\n"
                f"Your line: `{result['wrong']}`\n\n{hint}")
            record(user, result["tag"], correct=False)
            st.session_state["twin"] = {
                "subject": result["subject"], "tag": result["tag"],
                "problem": make_twin(result["subject"], result["tag"]),
            }

tw = st.session_state.get("twin")
if tw:
    task = {"algebra": "Solve step by step", "derivative": "Differentiate",
            "integral": "Integrate"}[tw["subject"]]
    st.subheader("Try a similar one")
    st.write(task + ":")
    st.code(tw["problem"])
    ans = st.text_area("Your working (algebra) or final answer (calculus)", key="twin_ans")
    if st.button("Check twin"):
        try:
            ok = check_twin(tw["subject"], tw["problem"], ans)
        except Exception:
            st.error("I couldn't read your answer.")
            st.stop()
        record(user, tw["tag"], correct=ok)
        if ok:
            st.success("Fixed it! That was likely a slip, or you've now got it.")
        else:
            st.warning("Same trouble. We'll review this again later.")

st.sidebar.header("Mistake map")
for tag, errors, box in mistake_map(user):
    st.sidebar.write(f"{tag}: {errors} errors, mastery level {box}")
st.sidebar.write("Due for review:", due(user))