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
# DATA (CLEAN + SAFE COLUMN NAMES)
# ===================================================

df = pd.DataFrame({
    "Num": [1, 2, 3],
    "Operation": ["A", "B", "C"],
    "Time_s": [1.2, 2.4, 1.8],

    # IMPORTANT: resource for dynamic lanes
    "Resource": ["Machine 1", "Operator", "Machine 2"],

    "TT": [True, False, True],
    "TM": [False, True, False],
    "TTM": [False, False, False],
    "TZ": [False, False, False],
    "TF": [False, True, False],
})

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)

# ===================================================
# GENERATE BUTTON
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 6))

    height = 0.6
    start = 0
    max_x = 0

    # ===================================================
    # DYNAMIC LAYOUT (RESOURCES -> Y POSITIONS)
    # ===================================================

    resources = list(edited_df["Resource"].dropna().unique())
    y_positions = {res: -i * 2 for i, res in enumerate(resources)}

    # ===================================================
    # DRAW
    # ===================================================

    for i, row in edited_df.iterrows():

        try:
            operation = str(row["Operation"])
            time = float(row["Time_s"])
            resource = str(row["Resource"])

            tt = bool(row["TT"])
            tm = bool(row["TM"])
            ttm = bool(row["TTM"])
            tz = bool(row["TZ"])
            tf = bool(row["TF"])

        except:
            continue

        end = start + time
        max_x = max(max_x, end)

        y_base = y_positions.get(resource, 0)

        hatch = "////" if tf else None

        # ===================================================
        # COLOR LOGIC
        # ===================================================

        if tt:
            color = "#2ecc71"
        elif tm:
            color = "#3498db"
        elif ttm:
            color = "#f39c12"
        elif tz:
            color = "gray"
        else:
            color = "#95a5a6"

        # ===================================================
        # RECTANGLE
        # ===================================================

        ax.add_patch(Rectangle(
            (start, y_base),
            time,
            height,
            facecolor=color,
            edgecolor="black",
            alpha=0.9,
            hatch=hatch
        ))

        # ===================================================
        # LABEL (ANTI OVERLAP SIMPLE)
        # ===================================================

        if time >= 0.5:
            y_text = y_base - 0.4 if i % 2 == 0 else y_base - 0.8

            ax.text(
                start + time / 2,
                y_text,
                operation,
                ha="center",
                fontsize=10,
                fontweight="bold"
            )

        start += time

    # ===================================================
    # BASE LINES + LABELS
    # ===================================================

    for res, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=2)

        ax.text(
            -1.2,
            y + height / 2,
            res,
            fontsize=13,
            fontweight="bold",
            va="center",
            ha="right"
        )

    # ===================================================
    # CLEAN AXIS
    # ===================================================

    ax.set_xlim(0, max_x)
    ax.set_xticks([])
    ax.set_yticks([])

    ax.set_ylim(min(y_positions.values()) - 1, 3)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    plt.tight_layout()
    st.pyplot(fig)
