
"""
HR documents tab — browse the policy documents in src/hr_docs.py.
"""

import streamlit as st

from src.hr_docs import HR_DOCUMENTS


def render_docs_tab():
    st.subheader("📄 HR Policy Knowledge Base")

    st.caption(
        "These are the policy documents used to build the FAISS index."
    )

    if not HR_DOCUMENTS:
        st.warning("No HR policy documents are configured.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Policy documents", len(HR_DOCUMENTS))

    with col2:
        total_chars = sum(
            len(doc.get("content", ""))
            for doc in HR_DOCUMENTS
        )
        st.metric("Total policy characters", f"{total_chars:,}")

    st.divider()

    titles = [
        doc.get("title", f"Policy {i + 1}")
        for i, doc in enumerate(HR_DOCUMENTS)
    ]

    selected_title = st.selectbox(
        "Select a policy",
        options=titles,
        key="hr_document_selector",
    )

    selected = next(
        doc for doc in HR_DOCUMENTS
        if doc.get("title") == selected_title
    )

    st.markdown(f"### {selected['title']}")

    with st.container(border=True):
        st.text_area(
            "Policy content",
            value=selected.get("content", ""),
            height=450,
            disabled=True,
            key="hr_document_content",
        )

    st.caption(
        "The displayed text comes from src/hr_docs.py. "
        "Rebuild the FAISS index after changing policy content."
    )
