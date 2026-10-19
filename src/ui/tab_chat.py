
"""
Chat tab — uses the existing guarded HR pipeline.
"""

import streamlit as st

from src.pipeline import run_pipeline


def render_chat_tab(vectorstore, groq_key, guard_model, chat_model):
    st.subheader("💬 HR Policy Assistant")
    st.caption("Answers are based on the Acme Corp HR policy knowledge base.")

    if "hr_chat_history" not in st.session_state:
        st.session_state.hr_chat_history = []

    # Display conversation history.
    for item in st.session_state.hr_chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

            if item.get("sources"):
                with st.expander("📚 Retrieved policy excerpts"):
                    for source in item["sources"]:
                        st.markdown(f"**{source['source']}**")
                        st.caption(f"Relevance score: {source['score']}")
                        st.write(source["content"])

            if item.get("trace"):
                with st.expander("🔍 Execution trace"):
                    st.json(item["trace"])

    # Chat input.
    question = st.chat_input(
        "Ask about leave, benefits, remote work, or HR policies...",
        key="hr_question_input",
    )

    if not question:
        return

    # Display the new question.
    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.hr_chat_history.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("assistant"):
        try:
            with st.spinner("Checking guardrails and searching HR policies..."):
                reply, trace = run_pipeline(
                    message=question,
                    groq_key=groq_key,
                    guard_model=guard_model,
                    chat_model=chat_model,
                    vectorstore=vectorstore,
                )

            if not isinstance(reply, str):
                reply = str(reply)

            st.markdown(reply)

            # Sources are returned by the existing RAG pipeline.
            retrieval = trace.get("retrieval", {})
            sources = retrieval.get("chunks", [])

            if sources:
                with st.expander("📚 Retrieved policy excerpts"):
                    for source in sources:
                        st.markdown(
                            f"**{source.get('source', 'HR policy')}**"
                        )
                        st.caption(
                            f"Relevance score: {source.get('score', 'N/A')}"
                        )
                        st.write(source.get("content", ""))

            # Show timing and guardrail diagnostics.
            with st.expander("🔍 Execution trace"):
                st.json(trace)

            # Save the completed answer.
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": reply,
                "sources": sources,
                "trace": trace,
            })

        except Exception:
            st.error("The HR assistant could not process your question.")
            st.exception(Exception("Check the pipeline logs and configuration."))

    if st.button("Clear conversation", key="clear_hr_conversation"):
        st.session_state.hr_chat_history = []
        st.rerun()
