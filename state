import streamlit as st

def init_state():

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if "qc_controls" not in st.session_state:
        st.session_state["qc_controls"] = [
            {"nom": "QC1", "temps": 0.0, "frequence": 10}
        ]
