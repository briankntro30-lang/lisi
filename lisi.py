import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image
from datetime import datetime

st.set_page_config(page_title="Simogramme", layout="wide")

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
# SIDEBAR
# ===================================================
with st.sidebar:

    st.title("Configuration")

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Ajouter machine"):
        new_machine = f"M{len(st.session_state['machines']) + 1}"
        st.session_state["machines"].append(new_machine)

    st.subheader("Offsets")

    offset = {}

    for m in st.session_state["machines"]:
        offset[m] = st.number_input(f"Offset {m}", value=0.0, step=0.5)

    offset["OP"] = st.number_input("Offset Opérateur", value=0.0, step=0.5)

st.title("Simogramme Industriel")
st.markdown("---")

# ===================================================
# TABLEAUX
# ===================================================
dfs = []

for machine in st.session_state["machines"]:

    st.subheader(f"Tableau {machine}")

    df_machine = st.data_editor(
        pd.DataFrame({
            "Etape": [""],
            "Temps": [0.0],
            "TT": [False],
            "TM": [False],
            "TTM": [False],
            "TZ": [False],
            "TF": [False],
        }),
        num_rows="dynamic",
        use_container_width=True,
        key=machine
    )

    df_machine["Sys"] = machine
    dfs.append(df_machine)

edited_df = pd.concat(dfs, ignore_index=True)

# ===================================================
# GENERATION
# ===================================================
if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(18, 7))

    fig.patch.set_facecolor('#f4f6f9')
    ax.set_facecolor('#ffffff')

    machines = st.session_state["machines"]

    # ===================================================
    # 🔥 POSITIONS Y (OPÉRATEUR AU MILIEU)
    # ===================================================
    y_positions = {}
    h = 0.6
    step = 1.5

    y_op = 0  # opérateur toujours au centre

    n = len(machines)

    # distribution équilibrée autour de 0
    for i, m in enumerate(machines):
        if n == 1:
            y_positions[m] = step
        else:
            # alternance haut / bas autour de l’opérateur
            k = (i // 2) + 1
            y_positions[m] = step * k * (1 if i % 2 == 0 else -1)

    # ===================================================
    # CURSEURS
    # ===================================================
    time_cursor = {m: offset[m] for m in machines}
    time_cursor["OP"] = offset["OP"]

    max_x = 0

    total_machine_time = 0
    total_operator_time = 0
    total_wait_time = 0

    COLORS = {
        "TT": "#16a34a",
        "TM": "#2563eb",
        "TTM": "#ea580c",
        "TZ": "#6b7280"
    }

    # ===================================================
    # DESSIN
    # ===================================================
    for i, (_, row) in enumerate(edited_df.iterrows()):

        op = str(row["Etape"])
        temps = float(row["Temps"])
        sys = str(row["Sys"])

        tt = bool(row["TT"])
        tm = bool(row["TM"])
        ttm = bool(row["TTM"])
        tz = bool(row["TZ"])
        tf = bool(row["TF"])

        hatch = "////" if tf else None

        # MACHINE
        if tt:

            start = time_cursor[sys]
            end = start + temps
            time_cursor[sys] = end

            total_machine_time += temps

            ax.add_patch(Rectangle(
                (start, y_positions[sys]),
                temps,
                h,
                facecolor=COLORS["TT"],
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

            max_x = max(max_x, end)

        # OPERATEUR
        elif tm:

            start = time_cursor["OP"]
            end = start + temps
            time_cursor["OP"] = end

            total_operator_time += temps

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TM"],
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

            max_x = max(max_x, end)

        # TRANSFERT
        elif ttm:

            start = max(time_cursor["OP"], time_cursor[sys])
            end = start + temps

            time_cursor["OP"] = end
            time_cursor[sys] = end

            total_operator_time += temps

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                y_positions[sys] - y_op,
                facecolor=COLORS["TTM"],
                edgecolor="black",
                alpha=0.7,
                hatch=hatch
            ))

            max_x = max(max_x, end)

        # ATTENTE
        elif tz:

            start = time_cursor["OP"]
            end = start + temps
            time_cursor["OP"] = end

            total_wait_time += temps

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TZ"],
                edgecolor="black",
                alpha=0.8
            ))

            max_x = max(max_x, end)

        if temps >= 0.5:
            ax.text(start + temps / 2, y_op - 0.35, op,
                    ha="center", fontsize=8, color="black")

    # ===================================================
    # LIGNES
    # ===================================================
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=2)
        ax.text(-0.5, y, m, ha="right", va="center", fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-0.5, y_op, "Opérateur", ha="right", va="center", fontweight="bold")

    ax.set_xlim(0, max_x + 2)
    ax.set_xticks(range(0, int(max_x) + 2, 5))
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_yticks([])

    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()

    st.pyplot(fig)
