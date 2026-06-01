import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image as XLImage
from datetime import datetime
import os

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

with st.sidebar:

    st.image(LOGO_URL, width=220)

    st.title("Configuration")

    st.markdown("## Informations production")

    reference_piece = st.text_input("Référence pièce")
    numéro_machine = st.text_input("Numéro de la machine")
    pdc = st.text_input("PDC")
    vitesse_coupe = st.text_input("Vitesse de coupe")
    vitesse_avance = st.text_input("Vitesse d'avance")

    coef_repo = st.number_input(
        "Coefficient rendement opérateur",
        min_value=0.10,
        max_value=5.00,
        value=1.00,
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

    # ===================================================
    # TEMPS DE RÉFÉRENCE MACHINE
    # ===================================================

    temps_reference_machine = st.number_input(
        "Temps de référence machine (s) - Ce que la machine pourrait produire pendant le contrôle",
        min_value=0.0,
        value=0.0,
        step=1.0,
        help="Si le contrôle dure 30s et la machine peut produire 20s, la perte réelle est de 10s"
    )

    st.markdown("---")

    # ===================================================
    # CONTRÔLE QUALITÉ (MULTIPLE)
    # ===================================================

    st.markdown("## Contrôle qualité")

    if "qc_controls" not in st.session_state:
        st.session_state["qc_controls"] = [
            {"nom": "QC1", "temps": 0.0, "frequence": 10}
        ]

    if st.button("➕ Ajouter contrôle qualité"):

        st.session_state["qc_controls"].append(
            {
                "nom": f"QC{len(st.session_state['qc_controls'])+1}",
                "temps": 0.0,
                "frequence": 10
            }
        )
        st.rerun()

    for i, qc in enumerate(st.session_state["qc_controls"]):

        st.markdown(f"### {qc['nom']}")

        qc["temps"] = st.number_input(
            f"Temps contrôle (s)",
            min_value=0.0,
            key=f"qc_temps_{i}",
            value=qc["temps"]
        )

        qc["frequence"] = st.number_input(
            f"Fréquence (pièces)",
            min_value=1,
            key=f"qc_freq_{i}",
            value=qc["frequence"]
        )

    st.markdown("---")

    # ===================================================
    # MACHINE MANAGEMENT
    # ===================================================

    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]

    if st.button("➕ Ajouter machine"):

        st.session_state["machines"].append(
            f"M{len(st.session_state['machines'])+1}"
        )

        st.rerun()

# ===================================================
# TABLES
# ===================================================

dfs = []

for m in st.session_state["machines"]:

    # ===================================================
    # HEADER
    # ===================================================

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

        else:
            st.write("")

    # ===================================================
    # DATAFRAME
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

    df = st.data_editor(
        default_df,
        num_rows="dynamic",
        key=m,
        use_container_width=True
    )

    # ===================================================
    # AUTO CALCUL DÉBUT
    # ===================================================

    for i in range(1, len(df)):

        prev_debut = float(df.loc[i-1, "Début"])
        prev_duree = float(df.loc[i-1, "Durée"])

        auto_debut = prev_debut + prev_duree

        if (
            df.loc[i, "Début"] == 0
            or pd.isna(df.loc[i, "Début"])
        ):
            df.loc[i, "Début"] = auto_debut

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
        y_positions[m] = (
            step * ((i // 2) + 1)
            * (1 if i % 2 == 0 else -1)
        )

    max_x = 0

    total_machine_time = 0
    total_operator_time = 0
    total_wait_time = 0
    total_ttm_time = 0

    COLORS = {
        "TT": "#1f4fff",
        "TM": "#ff8c00",
        "TTM": "#111827",
        "TZ": "#9ca3af"
    }

    # ===================================================
    # DRAW HATCH
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
        tr = bool(row["TR"])
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
            total_ttm_time += temps

            rect = Rectangle(
                (start, y_op),
                temps,
                y_positions[sys] - y_op,
                facecolor="#FFFFFF00",
                edgecolor="black"
            )
            ax.add_patch(rect)

            ax.plot(
                [start, end],
                [y_op, y_positions[sys]],
                color="black"
            )

            if tf:
                draw_hatch(
                    ax, rect,
                    start, y_op,
                    temps,
                    abs(y_positions[sys] - y_op)
                )

            max_x = max(max_x, end)

        elif tr:
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
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)

        ax.text(
            -1.5, y,
            m,
            ha="right",
            fontsize=14,
            fontweight="bold"
        )

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)

    ax.text(
        -1.5,
        y_op,
        "Opérateur",
        ha="right",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()

    # ===================================================
    # SAFETY INIT
    # ===================================================

    total_operator_time = total_operator_time if "total_operator_time" in locals() else 0
    total_machine_time = total_machine_time if "total_machine_time" in locals() else 0
    total_wait_time = total_wait_time if "total_wait_time" in locals() else 0
    total_ttm_time = total_ttm_time if "total_ttm_time" in locals() else 0
    max_x = max_x if "max_x" in locals() else 0

    # ===================================================
    # CALCUL IMPACT CONTRÔLE QUALITÉ (LOGIC CORREGIDA)
    # ===================================================
    
    # Tiempo perdido total por controles de calidad
    # Por cada control: pérdida = max(0, temps_control - temps_reference_machine)
    # Luego se divide por la frecuencia para obtener el impacto por pieza
    
    temps_perdu_par_piece = 0
    
    for qc in st.session_state.get("qc_controls", []):
        temps_qc = qc.get("temps", 0)
        freq_qc = qc.get("frequence", 1)
        
        if temps_qc > 0 and freq_qc > 0:
            # Pérdida real por este control (no puede ser negativa)
            perte_reelle = max(0, temps_qc - temps_reference_machine)
            # Impacto por pieza = pérdida real / frecuencia
            temps_perdu_par_piece += perte_reelle / freq_qc
            
            # Debug info (se mostrará en expansión)
            if 'debug_qc' not in st.session_state:
                st.session_state.debug_qc = []
            st.session_state.debug_qc.append({
                'nom': qc['nom'],
                'temps_control': temps_qc,
                'temps_ref_machine': temps_reference_machine,
                'perte_reelle': perte_reelle,
                'frequence': freq_qc,
                'impact_par_piece': perte_reelle / freq_qc
            })

    # ===================================================
    # KPI CALC
    # ===================================================

    temps_operateur_corrige = total_operator_time * coef_repo
    surcout_operateur = temps_operateur_corrige - total_operator_time

    # Temps cycle = temps total du cycle + temps perdu par les contrôles
    temps_cycle = max_x + surcout_operateur + temps_perdu_par_piece

    # Taux Machine = Temps Machine réel (TT + TTM) / Temps Cycle
    temps_machine_reel = total_machine_time + total_ttm_time
    taux_machine = temps_machine_reel / temps_cycle if temps_cycle > 0 else 0

    # Taux Opérateur = Temps Opérateur corrigé / Temps Cycle
    taux_operateur = temps_operateur_corrige / temps_cycle if temps_cycle > 0 else 0

    # Productivité
    pieces_heure = 3600 / temps_cycle if temps_cycle > 0 else 0
    pieces_jour = pieces_heure * heures_travail

    # ===================================================
    # UI KPI
    # ===================================================

    st.markdown("## KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Temps cycle", f"{round(temps_cycle, 2)} s")
    col2.metric("Temps machine réel", f"{round(temps_machine_reel, 2)} s")
    col3.metric("Temps opérateur corrigé", f"{round(temps_operateur_corrige, 2)} s")
    col4.metric("Temps perdu / pièce", f"{round(temps_perdu_par_piece, 2)} s")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Taux Opérateur", f"{round(taux_operateur * 100, 1)} %")
    col6.metric("Taux Machine", f"{round(taux_machine * 100, 1)} %")
    col7.metric("Pièces / Heure", f"{round(pieces_heure, 1)}")
    col8.metric("Pièces / Jour", f"{round(pieces_jour, 1)}")

    # Explicación detallada del impacto
    if temps_perdu_par_piece > 0:
        
        with st.expander("📊 Détail du calcul d'impact des contrôles qualité"):
            
            st.markdown(f"**Temps de référence machine:** {temps_reference_machine} secondes")
            st.markdown("**Formule:** Perte réelle = max(0, Temps contrôle - Temps référence machine)")
            st.markdown("**Impact par pièce = Perte réelle / Fréquence**")
            st.markdown("---")
            
            for debug in st.session_state.get('debug_qc', []):
                st.markdown(f"**{debug['nom']}:**")
                st.markdown(f"- Temps contrôle: {debug['temps_control']}s")
                st.markdown(f"- Temps référence machine: {debug['temps_ref_machine']}s")
                st.markdown(f"- Perte réelle: {debug['perte_reelle']}s")
                st.markdown(f"- Fréquence: 1/{debug['frequence']} pièces")
                st.markdown(f"- **Impact: +{round(debug['impact_par_piece'], 2)}s par pièce**")
                st.markdown("---")
            
            st.info(f"💡 Impact total sur le temps de cycle: +{round(temps_perdu_par_piece, 2)} secondes par pièce")
            st.info(f"📉 Réduction de productivité: de {round(3600/max_x, 1)} à {round(pieces_heure, 1)} pièces/heure")

    st.success("Simogramme généré avec succès")
    st.pyplot(fig)
    
    # Sauvegarder la figure pour l'export Excel
    fig.savefig("simogramme.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Limpiar debug
    if 'debug_qc' in st.session_state:
        del st.session_state.debug_qc

    # ===================================================
    # EXCEL EXPORT
    # ===================================================

    excel_path = "simogramme.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:

        edited_df.to_excel(writer, sheet_name="Données", index=False)

        workbook = writer.book
        worksheet = workbook.create_sheet("Simogramme")

        worksheet["A1"] = "Référence pièce"
        worksheet["B1"] = reference_piece

        worksheet["A2"] = "Numéro de la machine"
        worksheet["B2"] = numéro_machine

        worksheet["A3"] = "PDC"
        worksheet["B3"] = pdc

        worksheet["A4"] = "Coefficient rendement"
        worksheet["B4"] = coef_repo

        worksheet["A5"] = "Temps référence machine"
        worksheet["B5"] = temps_reference_machine

        worksheet["A6"] = "Date"
        worksheet["B6"] = str(datetime.now())

        worksheet["A8"] = "Temps cycle (avec contrôles)"
        worksheet["B8"] = round(temps_cycle, 2)

        worksheet["A9"] = "Temps machine réel"
        worksheet["B9"] = round(temps_machine_reel, 2)

        worksheet["A10"] = "Temps opérateur corrigé"
        worksheet["B10"] = round(temps_operateur_corrige, 2)

        worksheet["A11"] = "Temps perdu par pièce"
        worksheet["B11"] = round(temps_perdu_par_piece, 2)

        worksheet["A12"] = "Taux Opérateur"
        worksheet["B12"] = round(taux_operateur * 100, 2)

        worksheet["A13"] = "Taux Machine"
        worksheet["B13"] = round(taux_machine * 100, 2)

        worksheet["A14"] = "Pièces / Heure"
        worksheet["B14"] = round(pieces_heure, 1)

        worksheet["A15"] = "Pièces / Jour"
        worksheet["B15"] = round(pieces_jour, 1)

        # Détail des contrôles qualité con la nueva lógica
        worksheet["A17"] = "Détail contrôles qualité (avec logique de perte réelle)"
        worksheet["A18"] = "Nom contrôle"
        worksheet["B18"] = "Temps contrôle (s)"
        worksheet["C18"] = "Temps réf machine (s)"
        worksheet["D18"] = "Perte réelle (s)"
        worksheet["E18"] = "Fréquence"
        worksheet["F18"] = "Impact (s/pièce)"

        row = 19
        for qc in st.session_state.get("qc_controls", []):
            worksheet[f"A{row}"] = qc["nom"]
            worksheet[f"B{row}"] = qc["temps"]
            worksheet[f"C{row}"] = temps_reference_machine
            perte = max(0, qc["temps"] - temps_reference_machine)
            worksheet[f"D{row}"] = round(perte, 2)
            worksheet[f"E{row}"] = qc["frequence"]
            impact = perte / qc["frequence"] if qc["frequence"] > 0 else 0
            worksheet[f"F{row}"] = round(impact, 2)
            row += 1

        # Ajouter l'image du simogramme
        image_path = os.path.join(os.getcwd(), "simogramme.png")

        if os.path.exists(image_path):
            img = XLImage(image_path)
            img.width = 800
            img.height = 300
            worksheet.add_image(img, "H2")

    # ===================================================
    # DOWNLOAD
    # ===================================================

    with open(excel_path, "rb") as f:
        st.download_button(
            "📥 Télécharger Excel",
            f,
            file_name="simogramme.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
