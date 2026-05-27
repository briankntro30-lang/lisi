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

.main { background-color: #f4f6f9; }

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
}

.stButton>button:hover {
    background-color: #374151;
}

</style>
""", unsafe_allow_html=True)

# ===================================================
# LOGIN CLEAN
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

    st.title("Configuration")

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Ajouter machine"):
        st.session_state["machines"].append(f"M{len(st.session_state['machines'])+1}")

    st.markdown("---")

    offset = {}
    for m in st.session_state["machines"]:
        offset[m] = st.number_input(f"Offset {m}", value=0.0, step=0.5)

    offset["OP"] = st.number_input("Offset Opérateur", value=0.0, step=0.5)

# ===================================================
# TITLE
# ===================================================

st.title("Simogramme Industriel")
st.markdown("---")

# ===================================================
# TABLES
# ===================================================

dfs = []

for m in st.session_state["machines"]:

    st.subheader(f"Tableau {m}")

    df = st.data_editor(
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
        key=m,
        use_container_width=True
    )

    df["Sys"] = m
    dfs.append(df)

edited_df = pd.concat(dfs, ignore_index=True)

# ===================================================
# GENERATION
# ===================================================

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(18, 6))

    machines = st.session_state["machines"]

    # ===================================================
    # POSITIONS (COMPACT + CENTER OP)
    # ===================================================

    y_positions = {}
    step = 0.6   # compact
    h = 0.22     # thin bars
    y_op = 0

    for i, m in enumerate(machines):
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

    for _, row in edited_df.iterrows():

        op = str(row["Etape"])
        temps = float(row["Temps"])
        sys = str(row["Sys"])

        tt = bool(row["TT"])
        tm = bool(row["TM"])
        ttm = bool(row["TTM"])
        tz = bool(row["TZ"])
        tf = bool(row["TF"])

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
                hatch="///" if tf else None,
                zorder=3
            ))

            # 🔥 DIAGONAL 45° IF TF
            if tf:
                ax.plot(
                    [start, start + temps],
                    [y_positions[sys], y_positions[sys] + h],
                    color="black",
                    linewidth=1
                )

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
                alpha=1
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
                alpha=0.6
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
                alpha=0.6
            ))

            max_x = max(max_x, end)

        # LABEL
        if temps >= 0.5:
            ax.text(start + temps / 2, y_op - 0.18,
                    op, ha="center", fontsize=9, fontweight="bold")

    # ===================================================
    # LINES
    # ===================================================

    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", va="center",
                fontsize=14, fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)

    ax.text(-1.5, y_op, "Opérateur",
            ha="right", va="center",
            fontsize=16, fontweight="bold")

    # ===================================================
    # AXIS CLEAN
    # ===================================================

    ax.set_xlim(0, max_x + 2)
    ax.set_xticks(range(0, int(max_x) + 2, 5))
    ax.grid(axis="x", linestyle="--", alpha=0.2)
    ax.set_yticks([])

    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()

    # ===================================================
    # KPI
    # ===================================================

    st.markdown("## KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Temps cycle", f"{round(max_x, 2)} s")
    col2.metric("Temps machine", f"{round(total_machine_time, 2)} s")
    col3.metric("Temps opérateur", f"{round(total_operator_time, 2)} s")
    col4.metric("Attente", f"{round(total_wait_time, 2)} s")

    st.pyplot(fig)

    # ===================================================
    # EXPORT
    # ===================================================

    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight", dpi=300)

    excel_path = "simogramme.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:

        edited_df.to_excel(writer, sheet_name="Données", index=False)

        wb = writer.book
        ws = wb.create_sheet("Simogramme")

        img = Image(image_path)
        ws.add_image(img, "A1")

        ws["A25"] = "Date"
        ws["B25"] = str(datetime.now())
