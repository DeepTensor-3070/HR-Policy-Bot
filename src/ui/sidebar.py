import sys
import streamlit as st

from src.config import (
    GROQ_MODELS,
    GUARD_MODEL_DEFAULT,
    CHAT_MODEL_DEFAULT,
)


def render_sidebar() -> tuple[str, str, str]:
    with st.sidebar:
        st.title("🛡️ HR Policy Assistant")
        st.caption("NeMo Guardrails + FAISS RAG")
        st.divider()

        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            key="sidebar_groq_key",
        )

        models = list(GROQ_MODELS.keys())

        if not models:
            st.error("Configure available Groq models in src/config.py")
            st.stop()

        guard_index = (
            models.index(GUARD_MODEL_DEFAULT)
            if GUARD_MODEL_DEFAULT in models else 0
        )
        chat_index = (
            models.index(CHAT_MODEL_DEFAULT)
            if CHAT_MODEL_DEFAULT in models else 0
        )

        guard_model = st.selectbox(
            "Guard model",
            models,
            index=guard_index,
            format_func=lambda m: GROQ_MODELS[m],
            key="guard_model_selector",
        )

        chat_model = st.selectbox(
            "Chat model",
            models,
            index=chat_index,
            format_func=lambda m: GROQ_MODELS[m],
            key="chat_model_selector",
        )

        st.divider()
        st.caption(f"Python {sys.version.split()[0]}")

    return groq_key.strip(), guard_model, chat_model