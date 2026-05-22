import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# Parametres globales
st.set_page_config(page_title="Simogramme", layout="wide")

st.image(
    "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0",
    width=250)

# LOGIN
def login():
    st.title("Connexion - Simogramme")

    col1, col2 = st.columns(2)

    with col1:
        utilisateur = st.text_input("Utilisateur")

    with col2:
        mot_de_passe = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if utilisateur == "admin" and mot_de_passe == "1234":
            st.session_state["logged_in"] = True
        else:
            st.error("Identifiants incorrects")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()


# HEADER
st.title("Simogramme")

st.markdown("---")


# TABLEAU
df = pd.DataFrame({
    "Numéro": [1],
    "Mode opératoire": [A],
    "Temps (ms)": [1.2],
    "TT (Machine)": [False, False],
    "TM (Humain)": [False, False],
    "TTM (Machine+Humain)": [False, False],
    "TZ (Pause)": [False, False],
    "Tf (Temps frequentiel)": [False, False],
})

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)


# BOUTON
if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 6))

    # niveles
    y_machine = 2
    y_operateur = 0
    hauteur = 0.6

    max_x = 0
    debut = 0

    # ===================================================
    # SIMOGRAMME
    # ===================================================
    for _, row in edited_df.iterrows():

        try:
            operation = str(row["Mode opératoire"])
            temps = float(row["Temps (s)"])

            tt = row["TT (Machine)"]
            tm = row["TM (Humain)"]
            ttm = row["TTM (Machine+Humain)"]
            tz = row["TZ (Pause)"]

        except:
            continue

        fin = debut + temps
        max_x = fin

        # =========================
        # TT → MACHINE
        # =========================
        if tt:

            rect = Rectangle(
                (debut, y_machine),
                temps,
                hauteur,
                facecolor="#2ecc71",
                edgecolor="black",
                alpha=0.85
            )
            ax.add_patch(rect)

        # =========================
        # TM → HUMAIN
        # =========================
        elif tm:

            rect = Rectangle(
                (debut, y_operateur),
                temps,
                hauteur,
                facecolor="#3498db",
                edgecolor="black",
                alpha=0.85
            )
            ax.add_patch(rect)

        # =========================
        # TTM → MACHINE + HUMAIN (TOCA EXACTO LAS DOS LINEAS)
        # =========================
        elif ttm:

            rect = Rectangle(
                (debut, y_operateur),
                temps,
                (y_machine - y_operateur),
                facecolor="#f39c12",
                edgecolor="black",
                alpha=0.6
            )
            ax.add_patch(rect)

        # =========================
        # TZ → PAUSE
        # =========================
        elif tz:

            rect = Rectangle(
                (debut, y_operateur),
                temps,
                hauteur,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8
            )
            ax.add_patch(rect)

        # TEXTO
        ax.text(
            debut + temps / 2,
            y_machine + 0.8,
            operation,
            ha="center",
            fontsize=10
        )

        debut += temps

    # ===================================================
    # LIGNES BASE
    # ===================================================
    ax.hlines(y_machine, 0, max_x + 1, color="black", linewidth=2)
    ax.hlines(y_operateur, 0, max_x + 1, color="black", linewidth=2)

    ax.text(-8, y_machine, "Machine", fontsize=12)
    ax.text(-8, y_operateur, "Opérateur", fontsize=12)

    # ===================================================
    # ESCALA DE TEMPS (SEGUNDOS)
    # ===================================================
    ax.set_xlim(0, max_x + 1)

    ax.set_xticks(range(0, int(max_x) + 2, 1))
    ax.set_xticklabels(range(0, int(max_x) + 2, 1))

    ax.grid(True, axis="x", linestyle="--", alpha=0.4)

    ax.set_xlabel("Temps (secondes)")

    # ===================================================
    # ESTILO FINAL
    # ===================================================
    ax.set_ylim(-1, 4)
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    st.pyplot(fig)
