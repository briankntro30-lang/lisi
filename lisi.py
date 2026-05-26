import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image

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
# MACHINES DYNAMIQUES
# ===================================================
if "machines" not in st.session_state:
    st.session_state["machines"] = ["M1", "M2"]

if st.button("➕ Ajouter machine"):
    new_machine = f"M{len(st.session_state['machines']) + 1}"
    st.session_state["machines"].append(new_machine)

st.title("Simogramme")
st.markdown("---")

# ===================================================
# OFFSET (INPUT UTILISATEUR)
# ===================================================
st.subheader("Décalage (Offset de démarrage)")

offset = {}

for m in st.session_state["machines"]:
    offset[m] = st.number_input(
        f"Offset {m}",
        value=0.0,
        step=0.5
    )

offset["OP"] = st.number_input(
    "Offset Opérateur",
    value=0.0,
    step=0.5
)

# ===================================================
# TABLEAUX PAR MACHINE
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
# SIMOGRAMME
# ===================================================
if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 6))

    machines = st.session_state["machines"]

    # positions Y
    y_positions = {}
    step = 1.2
    y_op = 0
    h = 0.6

    for i, m in enumerate(machines):
        if i % 2 == 0:
            y_positions[m] = step * (i // 2 + 1)
        else:
            y_positions[m] = -step * (i // 2 + 1)

    # ===================================================
    # TIME CURSOR + OFFSET
    # ===================================================
    time_cursor = {m: offset[m] for m in machines}
    time_cursor["OP"] = offset["OP"]

    max_x = 0

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

        hatch = "////" if tf else None

        # MACHINE
        if tt:

            start = time_cursor[sys]
            end = start + temps
            time_cursor[sys] = end

            ax.add_patch(Rectangle(
                (start, y_positions[sys]),
                temps,
                h,
                facecolor="#2ecc71",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

            max_x = max(max_x, end)

        # OPÉRATEUR
        elif tm:

            start = time_cursor["OP"]
            end = start + temps
            time_cursor["OP"] = end

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor="#3498db",
                edgecolor="black",
                alpha=0.9,
                hatch=hatch
            ))

            max_x = max(max_x, end)

        # TRANSFERT
        elif ttm:

            start = time_cursor["OP"]
            end = start + temps
            time_cursor["OP"] = end

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                y_positions[sys] - y_op,
                facecolor="#f39c12",
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

            ax.add_patch(Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8
            ))

            max_x = max(max_x, end)

        # LABEL
        if temps >= 0.5:
            ax.text(start + temps / 2, y_op - 0.3, op, ha="center", fontsize=8)

    # ===================================================
    # LINES
    # ===================================================
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=2)
        ax.text(-0.5, y, m, ha="right", va="center", fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-0.5, y_op, "Opérateur", ha="right", va="center", fontweight="bold")

    ax.set_xlim(0, max_x)
    ax.set_xticks([])
    ax.set_yticks([])

    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)

    # ===================================================
    # EXPORT EXCEL + IMAGE
    # ===================================================
    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight")

    excel_path = "simogramme.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        edited_df.to_excel(writer, sheet_name="Données", index=False)

        workbook = writer.book
        worksheet = workbook.create_sheet("Simogramme")

        img = Image(image_path)
        worksheet.add_image(img, "A1")

    with open(excel_path, "rb") as f:
        st.download_button(
            label="📥 Télécharger Excel",
            data=f,
            file_name="simogramme.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
