import streamlit as st
from configuration import set_style, LOGO_URL

def render_sidebar():

    with st.sidebar:

    st.image(LOGO_URL, width=220)

    st.title("Configuration")

    st.markdown("## Informations production")

    reference_piece = st.text_input("Référence pièce")
    numéro_machine = st.text_input("Numéro de la machine")
    pdc = st.text_input("PDC")
    vitesse_coupe = st.text_input("Vitesse de coupe")
    vitesse_avance = st.text_input("Vitesse d'avance")

    coef_repo = st.number_input(
        "Coefficient rendement",
        min_value=0.1,
        max_value=1.0,
        value=0.85,
        step=0.05
    )

    heures_travail = st.number_input(
        "Heures de travail / jour",
        min_value=1.0,
        max_value=24.0,
        value=7.0,
        step=0.5
    )

    st.markdown("---")

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Ajouter machine"):

        st.session_state["machines"].append(
            f"M{len(st.session_state['machines'])+1}"
        )

        st.rerun()
