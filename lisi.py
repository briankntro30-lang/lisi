import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image
from datetime import datetime

# ===================================================
# CONFIG
# ===================================================

st.set_page_config(page_title="Simogramme", layout="wide")

# ===================================================
# STYLE
# ===================================================

st.markdown("""
<style>

.main {
    background-color: #f4f6f9;
}

h1, h2, h3 {
    color: #1f2937;
    font-weight: 700;
}

.stButton>button {
    background-color: #1f2937;
    color: white;
    border-radius: 8px;
    height: 45px;
    font-weight: bold;
    border: none;
}

.stButton>button:hover {
    background-color: #374151;
}

</style>
""", unsafe_allow_html=True)

# ===================================================
# LOGO
# ===================================================

LOGO_URL = "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0"

st.image(LOGO_URL, width=250)

# ===================================================
# LOGIN
# ===================================================

def login():

    st.markdown("## Connexion - Simogramme")

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        user = st.text_input("Utilisateur")
        pwd = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):

            if user == "admin" and pwd == "1234":
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
# SIDEBAR
# ===================================================

with st.sidebar:

    st.image(LOGO_URL, width=220)

    st.title("Configuration")

    st.markdown("## Informations production")

    reference_piece = st.text_input("Référence pièce")
    eof = st.text_input("EOF")
    pdc = st.text_input("PDC")

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
        st.session_state["machines"].append(f"M{len(st.session_state['machines'])+1}")
        st.rerun()

# ===================================================
# TABLES
# ===================================================

dfs = []

for m in st.session_state["machines"]:

    col_title, col_delete = st.columns([6, 1])

    with col_title:
        st.subheader(f"Tableau {m}")

    with col_delete:

        if m != "M1":
            if st.button("🗑️", key=f"del_{m}"):
                st.session_state["machines"].remove(m)

                if m in st.session_state:
                    del st.session_state[m]

                st.rerun()

    # ===================================================
    # DATA INITIAL
    # ===================================================

    default_df = pd.DataFrame({
        "Etape": [""],
        "Début": [0.0],
        "Durée": [0.0],
        "TT": [False],
        "TM": [False],
        "TTM": [False],
        "TR": [False],
        "TF": [False],
    })

    # ===================================================
    # 🔥 FIX IMPORTANT SESSION STATE
    # ===================================================

    if m not in st.session_state:
        st.session_state[m] = default_df

    df = st.data_editor(
        st.session_state[m],
        num_rows="dynamic",
        key=f"editor_{m}",
        use_container_width=True
    )

    # sauvegarde
    st.session_state[m] = df.copy()

    # ===================================================
    # AUTO CALCUL DÉBUT (CORRIGÉ)
    # ===================================================

    for i in range(1, len(df)):

        prev_end = float(df.loc[i-1, "Début"]) + float(df.loc[i-1, "Durée"])

        if pd.isna(df.loc[i, "Début"]) or df.loc[i, "Début"] == 0:
            df.loc[i, "Début"] = prev_end

    df["Fin"] = df["Début"] + df["Durée"]
    df["Sys"] = m

    dfs.append(df)

edited_df = pd.concat(dfs, ignore_index=True)

# ===================================================
# GENERATE SIMOGRAMME
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(18, 6))

    machines = st.session_state["machines"]

    y_positions = {}
    step = 0.6
    h = 0.22
    y_op = 0

    for i, m in enumerate(machines):
        y_positions[m] = step * ((i // 2) + 1) * (1 if i % 2 == 0 else -1)

    max_x = 0

    total_machine_time = 0
    total_operator_time = 0
    total_wait_time = 0

    COLORS = {
        "TT": "#1f4fff",
        "TM": "#ff8c00",
        "TTM": "#111827",
        "TZ": "#9ca3af"
    }

    def draw_hatch(ax, rect, x, y, w, h, spacing=0.2):

        i = 0
        while i < w + h:

            line, = ax.plot(
                [x + i, x + i - h],
                [y, y + h],
                color="black",
                linewidth=0.6,
                alpha=0.6
            )

            line.set_clip_path(rect)
            i += spacing

    for _, row in edited_df.iterrows():

        op = str(row["Etape"])
        start = float(row["Début"])
        temps = float(row["Durée"])
        end = start + temps
        sys = str(row["Sys"])

        tt = bool(row["TT"])
        tm = bool(row["TM"])
        ttm = bool(row["TTM"])
        tz = bool(row["TR"])
        tf = bool(row["TF"])

        if tt:

            total_machine_time += temps

            rect = Rectangle(
                (start, y_positions[sys]),
                temps,
                h,
                facecolor=COLORS["TT"],
                edgecolor="black"
            )

            ax.add_patch(rect)

            if tf:
                draw_hatch(ax, rect, start, y_positions[sys], temps, h)

            max_x = max(max_x, end)

        elif tm:

            total_operator_time += temps

            rect = Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TM"],
                edgecolor="black"
            )

            ax.add_patch(rect)

            if tf:
                draw_hatch(ax, rect, start, y_op, temps, h)

            max_x = max(max_x, end)

        elif ttm:

            total_operator_time += temps
            total_machine_time += temps

            rect = Rectangle(
                (start, y_op),
                temps,
                y_positions[sys] - y_op,
                facecolor="white",
                edgecolor="black"
            )

            ax.add_patch(rect)

            ax.plot(
                [start, start + temps],
                [y_op, y_positions[sys]],
                color="black"
            )

            if tf:
                draw_hatch(ax, rect, start, y_op, temps, abs(y_positions[sys] - y_op))

            max_x = max(max_x, end)

        elif tz:

            total_wait_time += temps

            rect = Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TZ"],
                edgecolor="black",
                alpha=0.6
            )

            ax.add_patch(rect)

            max_x = max(max_x, end)

        if temps >= 0.5:
            ax.text(start + temps/2, y_op - 0.18, op, ha="center", fontsize=9)

    for m, y in y_positions.items():

        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)

        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")

    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.2)

    plt.tight_layout()

    st.pyplot(fig)

    st.success("Simogramme généré avec succès")
