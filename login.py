import streamlit as st

def login_page():

    st.markdown("## Connexion - Simogramme")

    user = st.text_input("Utilisateur")
    pwd = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if user == "admin" and pwd == "1234":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Erreur identifiants")
