import streamlit as st

LOGO_URL = "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg"

def set_style():
    st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }

    h1, h2, h3 {
        color: #1f2937;
        font-weight: 700;
    }

    .stButton>button {
        background-color: #1f2937;
        color: white;
        border-radius: 8px;
        height: 45px;
        font-weight: bold;
    }

    .stButton>button:hover {
        background-color: #374151;
    }
    </style>
    """, unsafe_allow_html=True)
