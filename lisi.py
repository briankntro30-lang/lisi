import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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

</style>
""", unsafe_allow_html=True)

st.image("https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png", width=250)

# ===================================================
# LOGIN
# ===================================================

def login():
    st.markdown("## Connexion")

    user = st.text_input("User")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state["logged_in"] = True
            st.rerun()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ===================================================
# SIDEBAR
# ===================================================

with st.sidebar:

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Add machine"):
        st.session_state["machines"].append(f"M{len(st.session_state['machines'])+1}")

    offset = {}
    for m in st.session_state["machines"]:
        offset[m] = st.number_input(f"Offset {m}", value=0.0)

    offset["OP"] = st.number_input("Offset OP", value=0.0)

# ===================================================
# TABLES
# ===================================================

dfs = []

for m in st.session_state["machines"]:

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
        key=m
    )

    df["Sys"] = m
    dfs.append(df)

edited_df = pd.concat(dfs, ignore_index=True)

# ===================================================
# SIMOGRAMME
# ===================================================

if st.button("Generate"):

    fig, ax = plt.subplots(figsize=(18, 6))

    machines = st.session_state["machines"]

    y_positions = {m: i * 0.6 for i, m in enumerate(machines)}
    y_op = -0.5

    time_cursor = {m: offset[m] for m in machines}
    time_cursor["OP"] = offset["OP"]

    max_x = 0

    for _, row in edited_df.iterrows():

        op = row["Etape"]
        t = float(row["Temps"])
        sys = row["Sys"]

        tt = row["TT"]
        tm = row["TM"]
        ttm = row["TTM"]
        tf = row["TF"]

        start = None

        # ================= MACHINE =================
        if tt:

            start = time_cursor[sys]
            end = start + t
            time_cursor[sys] = end

            ax.add_patch(Rectangle(
                (start, y_positions[sys]),
                t,
                0.3,
                facecolor="#1f4fff",
                edgecolor="black",
                hatch="///" if tf else None
            ))

            max_x = max(max_x, end)

        # ================= OP =================
        elif tm:

            start = time_cursor["OP"]
            end = start + t
            time_cursor["OP"] = end

            ax.add_patch(Rectangle(
                (start, y_op),
                t,
                0.3,
                facecolor="#ff8c00",
                edgecolor="black",
                hatch="///" if tf else None
            ))

            max_x = max(max_x, end)

        # ================= TTM =================
        elif ttm:

            start = max(time_cursor["OP"], time_cursor[sys])
            end = start + t
            time_cursor["OP"] = end
            time_cursor[sys] = end

            ax.add_patch(Rectangle(
                (start, y_op),
                t,
                y_positions[sys] - y_op,
                facecolor="#111827",
                edgecolor="black",
                alpha=0.5
            ))

            # ✔ UNA SOLA DIAGONAL
            if tf:
                ax.plot(
                    [start, start + t],
                    [y_op, y_positions[sys]],
                    color="black",
                    linewidth=1
                )

            max_x = max(max_x, end)

        # ================= WAIT =================
        elif row["TZ"]:

            start = time_cursor["OP"]
            end = start + t
            time_cursor["OP"] = end

            ax.add_patch(Rectangle(
                (start, y_op),
                t,
                0.3,
                facecolor="#9ca3af",
                edgecolor="black"
            ))

            max_x = max(max_x, end)

        if start is not None:
            ax.text(start + t/2, y_op - 0.2, str(op), ha="center")

    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black")

    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])
    plt.tight_layout()
    st.pyplot(fig)
