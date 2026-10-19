
"""
HR Policy Assistant — Streamlit entry point.
Backend logic lives in src/.
"""

import sys
import traceback

import streamlit as st


st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🛡️",
    layout="wide",
)

try:
    from src.rag import build_vectorstore
    from src.ui.sidebar import render_sidebar
    from src.ui.landing import render_landing
    from src.ui.tab_chat import render_chat_tab
    from src.ui.tab_docs import render_docs_tab

except Exception:
    st.title("🛑 Application Startup Error")
    st.error("A required module or dependency failed to load.")

    with st.expander("Error details", expanded=True):
        st.code(traceback.format_exc(), language="python")

    st.caption(f"Python: {sys.version}")
    st.stop()


# Sidebar configuration.
groq_key, guard_model, chat_model = render_sidebar()


# Show landing page until the API key is provided.
if not groq_key:
    render_landing()
    st.stop()


# Build the vector store using the existing cached RAG function.
try:
    with st.spinner("Preparing the HR policy knowledge base..."):
        vectorstore = build_vectorstore()

except Exception:
    st.error("Failed to build the HR policy vector store.")

    with st.expander("Error details", expanded=True):
        st.code(traceback.format_exc(), language="python")

    st.stop()


# Main application.
st.title("🛡️ HR Policy Assistant")
st.caption("Acme Corp · Groq · NeMo Guardrails · FAISS RAG")

tab_chat, tab_docs = st.tabs([
    "💬 Assistant",
    "📄 HR Policy Documents",
])

with tab_chat:
    render_chat_tab(
        vectorstore,
        groq_key,
        guard_model,
        chat_model,
    )

with tab_docs:
    render_docs_tab()
