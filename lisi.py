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
        mot_de_passe = st.text_input("Mot de passe", type="password")

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
# DATA
# ===================================================

df = pd.DataFrame({
    "Numéro": [1, 2],
    "Mode opératoire": ["A", "B"],
    "Temps (s)": [1.2, 2.4],

    "TT (Machine)": [True, False],
    "TM (Humain)": [False, True],
    "TTM (Machine+Humain)": [False, False],
    "TZ (Pause)": [False, False],

    "Tf (Temps frequentiel)": [False, True],
})

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)

# ===================================================
# BUTTON
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 5))

    y_machine = 2
    y_operateur = 0
    hauteur = 0.6

    debut = 0
    max_x = 0

    # ===================================================
    # SIMOGRAMME
    # ===================================================

    for i, row in enumerate(edited_df.iterrows()):

        _, row = row

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

        hatch_style = "////" if tf else None

        # ===================================================
        # MACHINE
        # ===================================================

        if tt:
            ax.add_patch(Rectangle(
                (debut, y_machine),
                temps,
                hauteur,
                facecolor="#2ecc71",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch_style
            ))

        # ===================================================
        # HUMAIN
        # ===================================================

        elif tm:
            ax.add_patch(Rectangle(
                (debut, y_operateur),
                temps,
                hauteur,
                facecolor="#3498db",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch_style
            ))

        # ===================================================
        # MACHINE + HUMAIN
        # ===================================================

        elif ttm:
            ax.add_patch(Rectangle(
                (debut, y_operateur),
                temps,
                y_machine - y_operateur,
                facecolor="#f39c12",
                edgecolor="black",
                alpha=0.7,
                hatch=hatch_style
            ))

        # ===================================================
        # PAUSE
        # ===================================================

        elif tz:
            ax.add_patch(Rectangle(
                (debut, y_operateur),
                temps,
                hauteur,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8
            ))

        # ===================================================
        # TEXTE OPERATION (ANTI-ENCIMADO)
        # ===================================================

        if temps >= 0.5:

            y_text = (y_operateur - 0.35
                      if i % 2 == 0
                      else y_operateur - 0.75)

            ax.text(
                debut + temps / 2,
                y_text,
                operation,
                ha="center",
                fontsize=10,
                fontweight="bold"
            )

        debut += temps

    # ===================================================
    # LINES BASE
    # ===================================================

    ax.hlines(y_machine 1, 0, max_x, color="black", linewidth=2)
    ax.hlines(y_operateur, 0, max_x, color="black", linewidth=2)
    ax.hlines(y_machine 2, 0, max_x, color="black", linewidth=2)

    # ===================================================
    # LABELS LEFT
    # ===================================================

    ax.text(
        -1.2,
        y_machine + hauteur / 2,
        "Machine",
        fontsize=13,
        fontweight="bold",
        va="center",
        ha="right"
    )

    ax.text(
        -1.2,
        y_operateur + hauteur / 2,
        "Opérateur",
        fontsize=13,
        fontweight="bold",
        va="center",
        ha="right"
    )

    # ===================================================
    # AXE X CLEAN
    # ===================================================

    ax.set_xlim(0, max_x)
    ax.set_xticks([])  # ❌ no 1 2 3 4
    ax.set_xlabel("")

    # ===================================================
    # CLEAN STYLE
    # ===================================================

    ax.set_ylim(-1.2, 3.5)
    ax.set_yticks([])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    plt.tight_layout()

    st.pyplot(fig)
