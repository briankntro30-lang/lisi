import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def generate_simogramme(dfs, state):
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

        y_positions[m] = (
            step * ((i // 2) + 1)
            * (1 if i % 2 == 0 else -1)
        )

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
    # HATCH
    # ===================================================

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

    # ===================================================
    # DRAW
    # ===================================================

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

        # ===================================================
        # TT
        # ===================================================

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
                draw_hatch(
                    ax,
                    rect,
                    start,
                    y_positions[sys],
                    temps,
                    h
                )

            max_x = max(max_x, end)

        # ===================================================
        # TM
        # ===================================================

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
                draw_hatch(
                    ax,
                    rect,
                    start,
                    y_op,
                    temps,
                    h
                )

            max_x = max(max_x, end)

        # ===================================================
        # TTM
        # ===================================================

        elif ttm:

            total_operator_time += temps
            total_machine_time += temps

            rect = Rectangle(
                (start, y_op),
                temps,
                y_positions[sys] - y_op,
                facecolor="#FFFFFF00",
                edgecolor="black"
            )

            ax.add_patch(rect)

            ax.plot(
                [start, start + temps],
                [y_op, y_positions[sys]],
                color="black"
            )

            if tf:
                draw_hatch(
                    ax,
                    rect,
                    start,
                    y_op,
                    temps,
                    abs(y_positions[sys] - y_op)
                )

            max_x = max(max_x, end)

        # ===================================================
        # TR
        # ===================================================

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

        # ===================================================
        # TEXT
        # ===================================================

        if temps >= 0.5:

            ax.text(
                start + temps/2,
                y_op - 0.18,
                op,
                ha="center",
                fontsize=9
            )

    # ===================================================
    # LINES
    # ===================================================

    for m, y in y_positions.items():

        ax.hlines(
            y,
            0,
            max_x,
            color="black",
            linewidth=1.5
        )

        ax.text(
            -1.5,
            y,
            m,
            ha="right",
            fontsize=14,
            fontweight="bold"
        )

    ax.hlines(
        y_op,
        0,
        max_x,
        color="black",
        linewidth=2
    )

    ax.text(
        -1.5,
        y_op,
        "Opérateur",
        ha="right",
        fontsize=16,
        fontweight="bold"
    )

    # ===================================================
    # GRAPH SETTINGS
    # ===================================================

    ax.set_xlim(0, max_x + 2)

    ax.set_yticks([])

    ax.grid(axis="x", alpha=0.2)

    plt.tight_layout()

    # ===================================================
    # KPI
    # ===================================================

    temps_cycle = max_x
    
    temps_disponible = heures_travail * 3600

    pieces_jour = (
        (temps_disponible / temps_cycle)
        * coef_repo
        if temps_cycle > 0 else 0
    )

    taux_homme = (
        total_operator_time / temps_cycle
        if temps_cycle > 0 else 0
    )

    taux_machine = (
        total_machine_time / temps_cycle
        if temps_cycle > 0 else 0
    )

    st.markdown("## KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Temps cycle",
        f"{round(temps_cycle, 2)} s"
    )

    col2.metric(
        "Temps machine",
        f"{round(total_machine_time, 2)} s"
    )

    col3.metric(
        "Temps opérateur",
        f"{round(total_operator_time, 2)} s"
    )

    col4.metric(
        "Attente",
        f"{round(total_wait_time, 2)} s"
    )

    col5, col6, col7 = st.columns(3)

    col5.metric(
        "Taux Homme",
        f"{round(taux_homme * 100, 1)} %"
    )

    col6.metric(
        "Taux Machine",
        f"{round(taux_machine * 100, 1)} %"
    )

    col7.metric(
        "Pièces / Jour",
        f"{round(pieces_jour, 1)}"
    )

    st.success("Simogramme généré avec succès")

    st.pyplot(fig)

    # ===================================================
    # SAVE IMAGE
    # ===================================================

    image_path = "simogramme.png"

    fig.savefig(
        image_path,
        bbox_inches="tight",
        dpi=300
    )

