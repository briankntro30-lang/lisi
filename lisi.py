import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image
from datetime import datetime

# ===================================================
# CONFIG PAGE
# ===================================================

st.set_page_config(page_title="Simogramme", layout="wide")

# ===================================================
# STYLE INDUSTRIEL
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
    color: white;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #d1d5db;
}

div[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #d1d5db;
    padding: 15px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ===================================================
# LOGO
# ===================================================

st.image(
    "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0",
    width=250
)

# ===================================================
# LOGIN (FIXED - CLEAN)
# ===================================================

def login():

    st.markdown("## Connexion - Simogramme")

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        with st.container():

            utilisateur = st.text_input("Utilisateur")
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
# SIDEBAR (START WITH ONLY M1)
# ===================================================

with st.sidebar:

    st.title("Configuration")
    st.markdown("---")

    # 🔥 START WITH ONLY ONE MACHINE
    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Ajouter machine"):
        new_machine = f"M{len(st.session_state['machines']) + 1}"
        st.session_state["machines"].append(new_machine)

    st.markdown("---")

    st.subheader("Offsets")

    offset = {}

    for m in st.session_state["machines"]:
        offset[m] = st.number_input(f"Offset {m}", value=0.0, step=0.5)

    offset["OP"] = st.number_input("Offset Opérateur", value=0.0, step=0.5)

# ===================================================
# TITRE
# ===================================================

st.title("Simogramme")
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

    fig, ax = plt.subplots(figsize=(18, 6))

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    machines = st.session_state["machines"]

    # ===================================================
    # POSITIONS Y (OPERATOR CENTER)
    # ===================================================

    y_positions = {}
    step = 1.2
    h = 0.25   # 🔥 MÁS FINO COMO EN TU IMAGEN

    y_op = 0

    n = len(machines)

    for i, m in enumerate(machines):

        if n == 1:
            y_positions[m] = step

        else:
            if i % 2 == 0:
                y_positions[m] = step * ((i // 2) + 1)
            else:
                y_positions[m] = -step * ((i // 2) + 1)

    # ===================================================
    # CURSORS
    # ===================================================

    time_cursor = {m: offset[m] for m in machines}
    time_cursor["OP"] = offset["OP"]

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

    # ===================================================
    # DRAW
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

        hatch = "///" if tf else None

        # ================= MACHINE =================

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
                linewidth=1,
                alpha=1,
                hatch=hatch,
                zorder=3
            ))

            max_x = max(max_x, end)

        # ================= OPERATOR =================

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
                linewidth=1,
                alpha=1,
                zorder=3
            ))

            max_x = max(max_x, end)

        # ================= TRANSFERT =================

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
                linewidth=1,
                alpha=0.6,
                zorder=2
            ))

            max_x = max(max_x, end)

        # ================= WAIT =================

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
                linewidth=1,
                alpha=0.6,
                zorder=2
            ))

            max_x = max(max_x, end)

        # LABEL (más limpio)
        if temps >= 0.5:
            ax.text(
                start + temps / 2,
                y_op - 0.25,
                op,
                ha="center",
                fontsize=9,
                fontweight="bold",
                color="#111827"
            )

    # ===================================================
    # LINES
    # ===================================================

    for m, y in y_positions.items():

        ax.hlines(
            y,
            0,
            max_x,
            color="#111827",
            linewidth=1.5
        )

        ax.text(
            -2,
            y,
            m,
            ha="right",
            va="center",
            fontsize=14,   # 🔥 MÁS GRANDE
            fontweight="bold",
            color="#111827"
        )

    ax.hlines(0, 0, max_x, color="#111827", linewidth=2)

    ax.text(
        -2,
        y_op,
        "Opérateur",
        ha="right",
        va="center",
        fontsize=16,   # 🔥 MÁS GRANDE
        fontweight="bold",
        color="#111827"
    )

    # ===================================================
    # AXES CLEAN
    # ===================================================

    ax.set_xlim(0, max_x + 2)
    ax.set_xticks(range(0, int(max_x) + 2, 5))
    ax.grid(axis="x", linestyle="--", alpha=0.2)

    ax.set_yticks([])

    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()

    # ===================================================
    # KPI (UNCHANGED)
    # ===================================================

    st.markdown("## KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Temps cycle", f"{round(max_x, 2)} s")
    col2.metric("Temps machine", f"{round(total_machine_time, 2)} s")
    col3.metric("Temps opérateur", f"{round(total_operator_time, 2)} s")
    col4.metric("Attente", f"{round(total_wait_time, 2)} s")

    st.success("Simogramme généré avec succès")

    st.pyplot(fig)

    # ===================================================
    # EXPORT
    # ===================================================

    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight", dpi=300)

    excel_path = "simogramme.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:

        edited_df.to_excel(writer, sheet_name="Données", index=False)

        workbook = writer.book
        worksheet = workbook.create_sheet("Simogramme")

        img = Image(image_path)
        worksheet.add_image(img, "A1")

        worksheet["A25"] = "Date"
        worksheet["B25"] = str(datetime.now())

        worksheet["A26"] = "Temps cycle"
        worksheet["B26"] = round(max_x, 2)

        worksheet["A27"] = "Temps machine"
        worksheet["B27"] = round(total_machine_time, 2)

        worksheet["A28"] = "Temps opérateur"
        worksheet["B28"] = round(total_operator_time, 2)

        worksheet["A29"] = "Temps attente"
        worksheet["B29"] = round(total_wait_time, 2)

    with open(excel_path, "rb") as f:
        st.download_button(
            "📥 Télécharger Excel",
            f,
            file_name="simogramme.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
