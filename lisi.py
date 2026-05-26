import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ===================================================
# PARAMÈTRES GLOBAUX
# ===================================================

st.set_page_config(
    page_title="Simogramme",
    layout="wide"
)

st.image(
    "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0",
    width=250
)

# ===================================================
# LOGIN
# ===================================================

def login():

    st.title("Connexion - Simogramme")

    col1, col2 = st.columns(2)

    with col1:
        utilisateur = st.text_input("Utilisateur")

    with col2:
        mot_de_passe = st.text_input(
            "Mot de passe",
            type="password"
        )

    if st.button("Se connecter"):

        if utilisateur == "admin" and mot_de_passe == "1234":
            st.session_state["logged_in"] = True
            st.rerun()

        else:
            st.error("Identifiants incorrects")


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ===================================================
# HEADER
# ===================================================

st.title("Simogramme")

st.markdown("---")

# ===================================================
# TABLEAU
# ===================================================

df = pd.DataFrame({
    "Numéro": [1, 2],
    "Mode opératoire": ["A", "B"],
    "Temps (s)": [1.2, 2.4],

    "TT (Machine)": [True, False],
    "TM (Humain)": [False, True],
    "TTM (Machine+Humain)": [False, False],
    "TZ (Pause)": [False, False],

    # Modificateur fréquentiel
    "Tf (Temps frequentiel)": [False, True],
})

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)

# ===================================================
# BOUTON
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 6))

    # ===================================================
    # POSITIONS
    # ===================================================

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

            tt = bool(row["TT (Machine)"])
            tm = bool(row["TM (Humain)"])
            ttm = bool(row["TTM (Machine+Humain)"])
            tz = bool(row["TZ (Pause)"])

            tf = bool(row["Tf (Temps frequentiel)"])

        except:
            continue

        fin = debut + temps
        max_x = fin

        # ===================================================
        # STYLE TF
        # ===================================================

        hatch_style = "////" if tf else None

        # ===================================================
        # TT → MACHINE
        # ===================================================

        if tt:

            rect = Rectangle(
                (debut, y_machine),
                temps,
                hauteur,

                facecolor="#2ecc71",
                edgecolor="black",
                alpha=0.85,

                hatch=hatch_style
            )

            ax.add_patch(rect)

        # ===================================================
        # TM → HUMAIN
        # ===================================================

        elif tm:

            rect = Rectangle(
                (debut, y_operateur),
                temps,
                hauteur,

                facecolor="#3498db",
                edgecolor="black",
                alpha=0.85,

                hatch=hatch_style
            )

            ax.add_patch(rect)

        # ===================================================
        # TTM → MACHINE + HUMAIN
        # SOLO ENTRE LAS DOS LÍNEAS
        # ===================================================

        elif ttm:

            rect = Rectangle(
                (debut, y_operateur),
                temps,
                y_machine - y_operateur,

                facecolor="#f39c12",
                edgecolor="black",
                alpha=0.6,

                hatch=hatch_style
            )

            ax.add_patch(rect)

        # ===================================================
        # TZ → PAUSE
        # ===================================================

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

        # ===================================================
        # TEMPS CUMULÉ
        # ===================================================

        debut += temps

    # ===================================================
    # LIGNES BASE
    # ===================================================

    ax.hlines(
        y_machine,
        0,
        max_x + 1,

        color="black",
        linewidth=2
    )

    ax.hlines(
        y_operateur,
        0,
        max_x + 1,

        color="black",
        linewidth=2
    )

    ax.text(
        -0.8,
        y_machine + 0.2,
        "Machine",
        fontsize=12,
        fontweight="bold"
    )

    ax.text(
        -0.8,
        y_operateur + 0.2,
        "Opérateur",
        fontsize=12,
        fontweight="bold"
    )

    # ===================================================
    # ÉCHELLE TEMPS
    # ===================================================

    ax.set_xlim(0, max_x + 1)

    ax.set_xticks(
        range(0, int(max_x) + 2, 1)
    )

    ax.grid(
        True,
        axis="x",
        linestyle="--",
        alpha=0.4
    )

    ax.set_xlabel(
        "Temps (secondes)",
        fontsize=12
    )

    # ===================================================
    # STYLE FINAL
    # ===================================================

    ax.set_ylim(-1, 4)

    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    # ===================================================
    # AFFICHAGE
    # ===================================================

    st.pyplot(fig)
