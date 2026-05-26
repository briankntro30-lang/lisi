import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ===================================================
# CONFIG
# ===================================================

st.set_page_config(page_title="Simogramme", layout="wide")

st.title("Simogramme dynamique")

# ===================================================
# DATA (NO RESOURCE COLUMN)
# ===================================================

df = pd.DataFrame({
    "Operation": ["A", "B", "C", "D"],
    "Time_s": [1.2, 2.0, 1.5, 2.2],

    "TT": [True, False, True, False],
    "TM": [False, True, False, True],
    "TTM": [False, False, False, True],
    "TZ": [False, False, False, False],
    "TF": [False, True, False, False],
})

edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# ===================================================
# DRAW
# ===================================================

if st.button("Générer"):

    fig, ax = plt.subplots(figsize=(16, 6))

    h = 0.6
    start = 0
    max_x = 0

    # FIXED LINES (machine + operator)
    y_machine = 2
    y_operator = 0

    for i, row in edited_df.iterrows():

        op = str(row["Operation"])
        t = float(row["Time_s"])

        tt = bool(row["TT"])
        tm = bool(row["TM"])
        ttm = bool(row["TTM"])
        tz = bool(row["TZ"])
        tf = bool(row["TF"])

        end = start + t
        max_x = max(max_x, end)

        hatch = "////" if tf else None

        # ===================================================
        # POSITION LOGIC
        # ===================================================

        if tt:
            y = y_machine
            color = "#2ecc71"

        elif tm:
            y = y_operator
            color = "#3498db"

        elif ttm:
            # 🔥 BETWEEN LINES (IMPORTANT PART)
            y = (y_machine + y_operator) / 2
            color = "#f39c12"

        elif tz:
            y = y_operator - 1
            color = "gray"

        else:
            y = y_operator
            color = "#95a5a6"

        # ===================================================
        # DRAW BLOCK
        # ===================================================

        ax.add_patch(Rectangle(
            (start, y),
            t,
            h,
            facecolor=color,
            edgecolor="black",
            alpha=0.9,
            hatch=hatch
        ))

        # LABEL
        if t >= 0.5:
            ax.text(
                start + t / 2,
                y - 0.4,
                op,
                ha="center",
                fontsize=10,
                fontweight="bold"
            )

        start += t

    # ===================================================
    # LINES
    # ===================================================

    ax.hlines(y_machine, 0, max_x, color="black", linewidth=2)
    ax.hlines(y_operator, 0, max_x, color="black", linewidth=2)

    ax.text(-1.2, y_machine, "Machine", va="center", ha="right", fontsize=12, fontweight="bold")
    ax.text(-1.2, y_operator, "Opérateur", va="center", ha="right", fontsize=12, fontweight="bold")

    # ===================================================
    # CLEAN
    # ===================================================

    ax.set_xlim(0, max_x)
    ax.set_xticks([])
    ax.set_yticks([])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)
