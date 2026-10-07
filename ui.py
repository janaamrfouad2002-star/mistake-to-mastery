import streamlit as st
from app.core import (first_wrong_step, diagnose, make_problem, record,
                      due, mistake_map)
from app.llm import explain_with_llm


def lines(text):
    return [s.strip() for s in text.splitlines() if s.strip()]


st.title("Mistake-to-Mastery")
user = st.text_input("Your name", "student1")
st.write("Type your working, one equation per line.")
text = st.text_area("Your steps", "2x + 3 = 11\n2x = 14\nx = 7")

if st.button("Check"):
    steps = lines(text)
    try:
        i = first_wrong_step(steps)
    except Exception:
        st.error("I couldn't read one of the lines. Use the form `2x + 3 = 11`.")
        st.stop()
    if i is None:
        st.success("All steps are valid.")
        st.session_state.pop("twin", None)
    else:
        tag = diagnose(steps[i - 1], steps[i])
        st.error(f"First wrong step: line {i + 1}: `{steps[i]}`")
        st.info(f"Diagnosis (verified by SymPy): {tag}")
        with st.spinner("Writing a hint..."):
            st.write(explain_with_llm(steps[i - 1], steps[i], tag))
        record(user, tag, correct=False)
        st.session_state["twin"] = make_problem(tag)
        st.session_state["tag"] = tag

if "twin" in st.session_state:
    st.subheader("Try a similar one")
    st.code(st.session_state["twin"])
    ans = st.text_area("Your steps for the new problem", key="twin_ans")
    if st.button("Check twin"):
        steps = [st.session_state["twin"]] + lines(ans)
        if len(steps) < 2:
            st.warning("Write at least one step first.")
        else:
            try:
                ok = first_wrong_step(steps) is None
            except Exception:
                st.error("I couldn't read one of the lines.")
                st.stop()
            record(user, st.session_state["tag"], correct=ok)
            if ok:
                st.success("Fixed it! That was likely a slip, or you've now got it.")
            else:
                st.warning("Same trouble. Let's review this again later.")

st.sidebar.header("Mistake map")
for tag, errors, box in mistake_map(user):
    st.sidebar.write(f"{tag}: {errors} errors, mastery level {box}")
st.sidebar.write("Due for review:", due(user))