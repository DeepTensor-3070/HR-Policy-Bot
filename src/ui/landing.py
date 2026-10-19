import streamlit as st


def render_landing():
    st.title("🛡️ HR Policy Assistant")
    st.subheader("Your AI-powered HR policy assistant")

    st.markdown("""
    Get answers from approved company HR policies.

    - 🏖️ Leave and attendance
    - 🏠 Work-from-home policies
    - 💰 Reimbursements and benefits
    - 📋 HR procedures
    - 📄 Policy documents
    """)

    st.info("Enter your Groq API key in the sidebar to get started.")