import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image
from datetime import datetime
import sqlite3
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
# DATABASE SETUP
# ===================================================

def init_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect('simogramme_data.db')
    c = conn.cursor()
    
    # Table des configurations
    c.execute('''CREATE TABLE IF NOT EXISTS configurations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  reference_piece TEXT,
                  numero_machine TEXT,
                  pdc TEXT,
                  vitesse_coupe TEXT,
                  vitesse_avance TEXT,
                  coef_habilete REAL,
                  coef_activite REAL,
                  coef_conditions REAL,
                  coef_stabilite REAL,
                  coef_ja_total REAL,
                  coef_repo REAL,
                  heures_travail REAL,
                  temps_controle REAL,
                  frequence_controle INTEGER,
                  machines TEXT,
                  donnees TEXT)''')
    
    conn.commit()
    conn.close()

def save_configuration(data):
    """Sauvegarde une configuration dans la base de données"""
    conn = sqlite3.connect('simogramme_data.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO configurations 
                 (date, reference_piece, numero_machine, pdc, vitesse_coupe, 
                  vitesse_avance, coef_habilete, coef_activite, coef_conditions, 
                  coef_stabilite, coef_ja_total, coef_repo, heures_travail, 
                  temps_controle, frequence_controle, machines, donnees)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['date'], data['reference_piece'], data['numero_machine'], 
               data['pdc'], data['vitesse_coupe'], data['vitesse_avance'],
               data['coef_habilete'], data['coef_activite'], data['coef_conditions'],
               data['coef_stabilite'], data['coef_ja_total'], data['coef_repo'],
               data['heures_travail'], data['temps_controle'], data['frequence_controle'],
               data['machines'], data['donnees']))
    
    conn.commit()
    conn.close()

def load_configurations():
    """Charge toutes les configurations depuis la base de données"""
    conn = sqlite3.connect('simogramme_data.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM configurations ORDER BY date DESC')
    rows = c.fetchall()
    
    conn.close()
    return rows

# Initialiser la base de données
init_database()

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
    numéro_machine = st.text_input("Numéro de la machine")
    pdc = st.text_input("PDC")
    vitesse_coupe = st.text_input("Vitesse de coupe")
    vitesse_avance = st.text_input("Vitesse d'avance")
    
    st.markdown("## Coefficient JA (Jugement d'Allure)")
    st.info("Les coefficients sont des valeurs entre 0 et 1, la somme sera ajoutée à 1")
    
    coef_habilete = st.number_input(
        "Coefficient d'habileté",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Habileté de l'opérateur"
    )
    
    coef_activite = st.number_input(
        "Coefficient d'activité",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Activité de l'opérateur"
    )
    
    coef_conditions = st.number_input(
        "Coefficient des conditions de travail",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Conditions de travail"
    )
    
    coef_stabilite = st.number_input(
        "Coefficient de stabilité",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Stabilité du processus"
    )
    
    # Calcul du coefficient JA total (somme des 4 + 1)
    coef_ja_total = 1 + coef_habilete + coef_activite + coef_conditions + coef_stabilite
    
    st.metric("Coefficient JA total", f"{coef_ja_total:.2f}")
    
    st.markdown("## Coefficient de rendement opérateur")
    coef_repo = st.number_input(
        "Coefficient de rendement opérateur",
        min_value=1.00,
        max_value=5.00,
        value=1.00,
        step=0.05,
        help="Coefficient supérieur à 1"
    )
    
    heures_travail = st.number_input(
        "Heures de travail / jour",
        min_value=1.0,
        max_value=24.0,
        value=7.0,
        step=0.5
    )
    
    st.markdown("## Contrôle qualité")
    
    temps_controle = st.number_input(
        "Temps contrôle (s)",
        min_value=0.0,
        value=0.0,
        step=1.0
    )
    
    frequence_controle = st.number_input(
        "Fréquence contrôle (pièces)",
        min_value=1,
        value=10,
        step=1
    )
    
    st.markdown("---")
    
    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]
    
    if st.button("➕ Ajouter machine"):
        st.session_state["machines"].append(
            f"M{len(st.session_state['machines'])+1}"
        )
        st.rerun()
    
    st.markdown("---")
    st.markdown("## Historique des simulations")
    
    if st.button("📊 Voir historique"):
        st.session_state["show_history"] = True
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
        else:
            st.write("")
    
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
    
    for i in range(1, len(df)):
        prev_debut = float(df.loc[i-1, "Début"])
        prev_duree = float(df.loc[i-1, "Durée"])
        auto_debut = prev_debut + prev_duree
        
        if (df.loc[i, "Début"] == 0 or pd.isna(df.loc[i, "Début"])):
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
            ax.text(
                start + temps/2,
                y_op - 0.18,
                op,
                ha="center",
                fontsize=9
            )
    
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")
    
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")
    
    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    
    # ===================================================
    # CALCULS AVEC COEFFICIENTS
    # ===================================================
    
    # Application du coefficient JA (somme des 4 + 1)
    temps_operateur_ja = total_operator_time * coef_ja_total
    
    # Application du coefficient de rendement
    temps_operateur_corrige = temps_operateur_ja * coef_repo
    
    surcout_operateur = temps_operateur_corrige - total_operator_time
    
    # Contrôle qualité
    temps_libre_machine = max(0, max_x - total_operator_time)
    impact_controle = 0
    
    if temps_controle > 0:
        if temps_controle > temps_libre_machine:
            impact_controle = (temps_controle - temps_libre_machine) / frequence_controle
    
    # Temps cycle
    temps_cycle = max_x + surcout_operateur + impact_controle
    
    temps_disponible = heures_travail * 3600
    pieces_heure = 3600 / temps_cycle if temps_cycle > 0 else 0
    pieces_jour = pieces_heure * heures_travail
    
    taux_homme = temps_operateur_corrige / temps_cycle if temps_cycle > 0 else 0
    taux_machine = total_machine_time / temps_cycle if temps_cycle > 0 else 0
    
    # ===================================================
    # AFFICHAGE KPI
    # ===================================================
    
    st.markdown("## KPI")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Temps cycle", f"{round(temps_cycle, 2)} s")
    col2.metric("Temps machine", f"{round(total_machine_time, 2)} s")
    col3.metric("Temps opérateur", f"{round(total_operator_time, 2)} s")
    col4.metric("Attente", f"{round(total_wait_time, 2)} s")
    
    col5, col6, col7, col8 = st.columns(4)
    
    col5.metric("Taux Homme", f"{round(taux_homme * 100, 1)} %")
    col6.metric("Taux Machine", f"{round(taux_machine * 100, 1)} %")
    col7.metric("Pièces / Heure", f"{round(pieces_heure, 1)}")
    col8.metric("Pièces / Jour", f"{round(pieces_jour, 1)}")
    
    # Affichage des détails des coefficients
    with st.expander("Détails des coefficients appliqués"):
        st.write(f"Temps opérateur de base: {round(total_operator_time, 2)} s")
        st.write(f"Coefficient JA (H+AC+CT+S): {coef_habilete} + {coef_activite} + {coef_conditions} + {coef_stabilite} = {coef_ja_total:.2f}")
        st.write(f"Temps opérateur avec JA: {round(temps_operateur_ja, 2)} s")
        st.write(f"Coefficient de rendement: {coef_repo}")
        st.write(f"Temps opérateur final: {round(temps_operateur_corrige, 2)} s")
        st.write(f"Surtemps opérateur: +{round(surcout_operateur, 2)} s")
    
    st.success("Simogramme généré avec succès")
    st.pyplot(fig)
    
    # ===================================================
    # SAVE IMAGE
    # ===================================================
    
    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight", dpi=300)
    
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
        worksheet["A4"] = "Vitesse de coupe"
        worksheet["B4"] = vitesse_coupe
        worksheet["A5"] = "Vitesse d'avance"
        worksheet["B5"] = vitesse_avance
        worksheet["A6"] = "Date"
        worksheet["B6"] = str(datetime.now())
        
        # Coefficients JA
        worksheet["A7"] = "Coefficient habileté"
        worksheet["B7"] = coef_habilete
        worksheet["A8"] = "Coefficient activité"
        worksheet["B8"] = coef_activite
        worksheet["A9"] = "Coefficient conditions"
        worksheet["B9"] = coef_conditions
        worksheet["A10"] = "Coefficient stabilité"
        worksheet["B10"] = coef_stabilite
        worksheet["A11"] = "Coefficient JA total"
        worksheet["B11"] = round(coef_ja_total, 2)
        worksheet["A12"] = "Coefficient rendement"
        worksheet["B12"] = coef_repo
        worksheet["A13"] = "Heures travail/jour"
        worksheet["B13"] = heures_travail
        
        # KPI
        worksheet["A14"] = "Temps cycle"
        worksheet["B14"] = round(temps_cycle, 2)
        worksheet["A15"] = "Temps machine"
        worksheet["B15"] = round(total_machine_time, 2)
        worksheet["A16"] = "Temps opérateur"
        worksheet["B16"] = round(total_operator_time, 2)
        worksheet["A17"] = "Temps attente"
        worksheet["B17"] = round(total_wait_time, 2)
        worksheet["A18"] = "Taux Homme"
        worksheet["B18"] = round(taux_homme * 100, 2)
        worksheet["A19"] = "Taux Machine"
        worksheet["B19"] = round(taux_machine * 100, 2)
        worksheet["A20"] = "Pièces / Heure"
        worksheet["B20"] = round(pieces_heure, 1)
        worksheet["A21"] = "Pièces / Jour"
        worksheet["B21"] = round(pieces_jour, 1)
        
        img = Image(image_path)
        worksheet.add_image(img, 'C1')
    
    # ===================================================
    # SAUVEGARDE BDD
    # ===================================================
    
    config_data = {
        'date': str(datetime.now()),
        'reference_piece': reference_piece,
        'numero_machine': numéro_machine,
        'pdc': pdc,
        'vitesse_coupe': vitesse_coupe,
        'vitesse_avance': vitesse_avance,
        'coef_habilete': coef_habilete,
        'coef_activite': coef_activite,
        'coef_conditions': coef_conditions,
        'coef_stabilite': coef_stabilite,
        'coef_ja_total': coef_ja_total,
        'coef_repo': coef_repo,
        'heures_travail': heures_travail,
        'temps_controle': temps_controle,
        'frequence_controle': frequence_controle,
        'machines': str(st.session_state["machines"]),
        'donnees': edited_df.to_json()
    }
    
    save_configuration(config_data)
    
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

# ===================================================
# HISTORIQUE
# ===================================================

if "show_history" in st.session_state and st.session_state["show_history"]:
    st.markdown("## Historique des simulations")
    
    configurations = load_configurations()
    
    if configurations:
        df_history = pd.DataFrame(configurations, 
                                  columns=['ID', 'Date', 'Référence', 'Machine', 'PDC', 
                                          'Vitesse coupe', 'Vitesse avance', 'Habilité', 
                                          'Activité', 'Conditions', 'Stabilité', 'JA Total',
                                          'Repo', 'Heures', 'Temps contrôle', 'Fréquence',
                                          'Machines', 'Données'])
        
        st.dataframe(df_history[['Date', 'Référence', 'Machine', 'JA Total', 'Repo']], 
                    use_container_width=True)
        
        if st.button("Fermer l'historique"):
            st.session_state["show_history"] = False
            st.rerun()
    else:
        st.info("Aucune simulation enregistrée")
        
        if st.button("Fermer"):
            st.session_state["show_history"] = False
            st.rerun()
