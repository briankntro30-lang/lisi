import streamlit as st

def render_sidebar():

    with st.sidebar:

        st.title("Configuration")

        st.session_state["reference_piece"] = st.text_input("Référence pièce")
        st.session_state["pdc"] = st.text_input("PDC")

        st.session_state["coef_repo"] = st.number_input(
            "Coefficient rendement", 0.1, 5.0, 1.0, 0.05
        )

        st.session_state["heures_travail"] = st.number_input(
            "Heures / jour", 1.0, 24.0, 7.0, 0.5
        )

        st.session_state["temps_reference_machine"] = st.number_input(
            "Temps référence machine", 0.0, 10000.0, 0.0
        )
