import streamlit as st
import pandas as pd
from datetime import datetime

from configuration import set_style, LOGO_URL
from login import login_page
from state import init_state
from sidebar import render_sidebar
from tables import render_tables
from simogramme import generate_simogramme
from excel import export_excel

from models import init_db
from backup import auto_backup

import repository
st.write("REPOSITORY IMPORT OK")

# ===================================================
# INIT
# ===================================================

st.set_page_config(
    page_title="Simogramme",
    layout="wide"
)

set_style()

st.image(LOGO_URL, width=250)

init_db()
init_state()

# ===================================================
# LOGIN
# ===================================================

if not st.session_state.get("logged_in", False):
    login_page()
    st.stop()

# ===================================================
# MENU
# ===================================================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Simogramme",
        "Historique"
    ]
)

# ===================================================
# HISTORIQUE
# ===================================================

if menu == "Historique":

    st.title("📊 Historique des simogrammes")

    data = get_simogrammes()

    if len(data) > 0:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Aucun simogramme enregistré.")

    st.stop()

# ===================================================
# APPLICATION PRINCIPALE
# ===================================================

render_sidebar()

dfs = render_tables()

# ===================================================
# GENERATION SIMOGRAMME
# ===================================================

if st.button("Générer le simogramme"):

    # -----------------------------------------------
    # Vérification
    # -----------------------------------------------

    if not dfs:
        st.error("Aucune donnée disponible.")
        st.stop()

    # -----------------------------------------------
    # Fusion de tous les tableaux machines
    # -----------------------------------------------

    edited_df = pd.concat(
        dfs,
        ignore_index=True
    )

    if edited_df.empty:
        st.error("Le tableau est vide.")
        st.stop()

    # -----------------------------------------------
    # Génération graphique + KPI
    # -----------------------------------------------

    fig, kpis = generate_simogramme(
        edited_df,
        st.session_state
    )

    st.pyplot(fig)

    # -----------------------------------------------
    # Export Excel
    # -----------------------------------------------

    export_excel(
        fig,
        edited_df,
        st.session_state,
        kpis
    )

    # -----------------------------------------------
    # Sauvegarde base SQLite
    # -----------------------------------------------

    meta = {
        "reference": st.session_state.get(
            "reference_piece",
            ""
        ),

        "machine": ",".join(
            st.session_state.get(
                "machines",
                []
            )
        ),

        "pdc": st.session_state.get(
            "pdc",
            ""
        ),

        "date": str(datetime.now())
    }

    try:

        sim_id = save_simogramme(
            meta,
            kpis
        )

        save_operations(
            sim_id,
            edited_df
        )

        auto_backup()

        st.success(
            "✅ Simogramme généré et sauvegardé"
        )

    except Exception as e:

        st.error(
            f"Erreur sauvegarde base : {e}"
        )
