import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import openpyxl

st.set_page_config(page_title="Simogramme", layout="wide")

st.image(
    "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0",
    width=250
)

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

st.title("Simogramme")
st.markdown("---")

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
    height=160,
    column_config={
        "Sys": st.column_config.SelectboxColumn(
            "Sys",
            options=["M1", "M2"]
        )
    }
)

if st.button("Générer le simogramme"):

    fig, ax = plt.subplots(figsize=(16, 4))

    y_m1 = 1.2
    y_op = 0
    y_m2 = -1.2

    h = 0.6
    debut = 0
    max_x = 0

    toggle_m2 = True

    has_m2 = (edited_df["Sys"] == "M2").any()

    for i, (_, row) in enumerate(edited_df.iterrows()):

        op = str(row["Op"])
        temps = float(row["Temps"])
        sys = str(row["Sys"])

        tt = bool(row["TT"])
        tm = bool(row["TM"])
        ttm = bool(row["TTM"])
        tz = bool(row["TZ"])
        tf = bool(row["TF"])

        fin = debut + temps
        max_x = fin

        hatch = "////" if tf else None

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

        elif tz:
            ax.add_patch(Rectangle(
                (debut, y_op),
                temps,
                h,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8
            ))

        if temps >= 0.5:
            y_text = y_op - (0.2 if i % 2 == 0 else 0.45)
            ax.text(debut + temps / 2, y_text, op, ha="center", fontsize=8)

        debut += temps

    ax.hlines(y_m1, 0, max_x, color="black", linewidth=2)

    if has_m2:
        ax.hlines(y_m2, 0, max_x, color="black", linewidth=2)
        ax.text(-0.5, y_m2, "Machine 2", ha="right", va="center", fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)

    ax.text(-0.5, y_m1, "Machine 1", ha="right", va="center", fontweight="bold")
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

    # Sauvegarder le graphique comme image
    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight")

    # Créer fichier Excel
    excel_path = "simogramme.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:

        # Sauvegarder tableau
        edited_df.to_excel(writer, sheet_name="Données", index=False)

        # Accéder workbook + worksheet
        workbook = writer.book
        worksheet = workbook.create_sheet("Simogramme")

        # Ajouter image
        from openpyxl.drawing.image import Image

        img = Image(image_path)

        # Position image
        worksheet.add_image(img, "A1")

    # Bouton téléchargement
    with open(excel_path, "rb") as f:
        st.download_button(
            label="Télécharger Excel",
            data=f,
            file_name="simogramme.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
