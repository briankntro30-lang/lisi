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
    "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png",
    width=180
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
# DATA (M1/M2 ahora SELECTBOX automático)
# ===================================================

df = pd.DataFrame({
    "Op": ["A", "B"],
    "Temps": [1.2, 2.4],
    "Sys": ["M1", "M2"],
    "TT": [True, False],
    "TM": [False, True],
    "TTM": [False, False],
    "TZ": [False, False],
    "TF": [False, True],
})

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    height=160  # 🔥 más compacto
)

# ===================================================
# BOTÓN
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 4))  # 🔥 más compacto vertical

    # ===================================================
    # ESPACIADO MÁS PEQUEÑO
    # ===================================================
    y_m1 = 1.2
    y_op = 0
    y_m2 = -1.2

    h = 0.3  # 🔥 ALTURA PEDIDA
    debut = 0
    max_x = 0

    toggle_m2 = True

    for i, (_, row) in enumerate(edited_df.iterrows()):

        op = str(row["Op"])
        temps = float(row["Temps"])
        sys = row["Sys"]

        tt = row["TT"]
        tm = row["TM"]
        ttm = row["TTM"]
        tz = row["TZ"]
        tf = row["TF"]

        fin = debut + temps
        max_x = fin

        hatch = "////" if tf else None

        # ===================================================
        # MACHINE
        # ===================================================
        if tt:

            y = y_m1 if sys == "M1" else (y_m1 if toggle_m2 else y_m2)

            if sys == "M2":
                toggle_m2 = not toggle_m2

            ax.add_patch(Rectangle(
                (debut, y),
                temps,
                h,
                facecolor="#2ecc71",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

        # ===================================================
        # OPERADOR
        # ===================================================
        elif tm:
            ax.add_patch(Rectangle(
                (debut, y_op),
                temps,
                h,
                facecolor="#3498db",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

        # ===================================================
        # TTM (entre líneas)
        # ===================================================
        elif ttm:

            y_top = y_m1 if sys == "M1" else y_m2

            ax.add_patch(Rectangle(
                (debut, y_op),
                temps,
                y_top - y_op,
                facecolor="#f39c12",
                edgecolor="black",
                alpha=0.7,
                hatch=hatch
            ))

        # ===================================================
        # PAUSA
        # ===================================================
        elif tz:
            ax.add_patch(Rectangle(
                (debut, y_op),
                temps,
                h,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8
            ))

        # ===================================================
        # TEXTO
        # ===================================================
        if temps >= 0.5:
            y_text = y_op - (0.2 if i % 2 == 0 else 0.45)

            ax.text(
                debut + temps / 2,
                y_text,
                op,
                ha="center",
                fontsize=8
            )

        debut += temps

    # ===================================================
    # LÍNEAS BASE
    # ===================================================
    ax.hlines(y_m1, 0, max_x, color="black", linewidth=2)
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.hlines(y_m2, 0, max_x, color="black", linewidth=2)

    ax.text(-0.5, y_m1, "Machine 1", ha="right", va="center", fontweight="bold")
    ax.text(-0.5, y_m2, "Machine 2", ha="right", va="center", fontweight="bold")
    ax.text(-0.5, y_op, "Opérateur", ha="right", va="center", fontweight="bold")

    # ===================================================
    # CLEAN
    # ===================================================
    ax.set_xlim(0, max_x)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)
