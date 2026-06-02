import streamlit as st
from datetime import datetime

from Configuration import set_style, LOGO_URL
from login import login_page
from state import init_state
from sidebar import render_sidebar
from tables import render_tables
from simogramme import generate_simogramme
from excel import export_excel

from models import init_db
from repository import save_simogramme, save_operations
from backup import auto_backup

# =========================
# INIT
# =========================

st.set_page_config(page_title="Simogramme", layout="wide")
set_style()
st.image(LOGO_URL, width=250)

init_db()
init_state()

# =========================
# LOGIN
# =========================

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox("Menu", ["Simogramme", "Historique"])

# =========================
# HISTORIQUE
# =========================

if menu == "Historique":
    from repository import get_simogrammes

    st.title("📊 Historique des simogrammes")

    data = get_simogrammes()
    st.dataframe(data)

    st.stop()

# =========================
# APP PRINCIPAL
# =========================

render_sidebar()
dfs = render_tables()

if st.button("Générer le simogramme"):

    fig, kpis = generate_simogramme(dfs, st.session_state)

    st.pyplot(fig)

    export_excel(fig, dfs, st.session_state, kpis)

    # =========================
    # SAVE DB
    # =========================

    meta = {
        "reference": st.session_state.get("reference_piece", ""),
        "machine": ",".join(st.session_state["machines"]),
        "pdc": st.session_state.get("pdc", ""),
        "date": str(datetime.now())
    }

    sim_id = save_simogramme(meta, kpis)
    save_operations(sim_id, dfs[0])

    auto_backup()

    st.success("Simogramme généré + sauvegardé")
