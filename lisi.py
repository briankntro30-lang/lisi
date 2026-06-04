import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from openpyxl.drawing.image import Image
from datetime import datetime
import sqlite3
import os
import json

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
    
    # Table des configurations avec stockage JSON pour les dataframes
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
                  donnees TEXT,
                  resultats TEXT)''')
    
    conn.commit()
    conn.close()

def save_configuration(data, resultats):
    """Sauvegarde une configuration dans la base de données"""
    conn = sqlite3.connect('simogramme_data.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO configurations 
                 (date, reference_piece, numero_machine, pdc, vitesse_coupe, 
                  vitesse_avance, coef_habilete, coef_activite, coef_conditions, 
                  coef_stabilite, coef_ja_total, coef_repo, heures_travail, 
                  temps_controle, frequence_controle, machines, donnees, resultats)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['date'], data['reference_piece'], data['numero_machine'], 
               data['pdc'], data['vitesse_coupe'], data['vitesse_avance'],
               data['coef_habilete'], data['coef_activite'], data['coef_conditions'],
               data['coef_stabilite'], data['coef_ja_total'], data['coef_repo'],
               data['heures_travail'], data['temps_controle'], data['frequence_controle'],
               data['machines'], data['donnees'], resultats))
    
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
        step=0.05
    )
    
    coef_activite = st.number_input(
        "Coefficient d'activité",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05
    )
    
    coef_conditions = st.number_input(
        "Coefficient des conditions de travail",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05
    )
    
    coef_stabilite = st.number_input(
        "Coefficient de stabilité",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05
    )
    
    coef_ja_total = 1 + coef_habilete + coef_activite + coef_conditions + coef_stabilite
    
    st.metric("Coefficient JA total", f"{coef_ja_total:.2f}")
    
    st.markdown("## Coefficient de rendement opérateur")
    st.info("Ce coefficient multiplie le temps cycle de base")
    
    coef_repo = st.number_input(
        "Coefficient de rendement opérateur",
        min_value=1.00,
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
        "🎯 TM (Manuel seul)": [False],
        "🤖 TT (Tech. seul)": [False],
        "🤝 TTM (Parallèle)": [False],
        "☕ TR (Repos)": [False],
        "⏸️ TZ (Masqué)": [False],
        "/// Hachures": [False],
    })
    
    df = st.data_editor(
        default_df,
        num_rows="dynamic",
        key=m,
        use_container_width=True,
        column_config={
            "Etape": st.column_config.TextColumn("Description étape", width="medium"),
            "Début": st.column_config.NumberColumn("Début (s)", format="%.1f"),
            "Durée": st.column_config.NumberColumn("Durée (s)", format="%.1f"),
            "🎯 TM (Manuel seul)": st.column_config.CheckboxColumn("TM - Opérateur seul"),
            "🤖 TT (Tech. seul)": st.column_config.CheckboxColumn("TT - Machine seule"),
            "🤝 TTM (Parallèle)": st.column_config.CheckboxColumn("TTM - Opérateur + Machine"),
            "☕ TR (Repos)": st.column_config.CheckboxColumn("TR - Repos"),
            "⏸️ TZ (Masqué)": st.column_config.CheckboxColumn("TZ - Temps masqué"),
            "/// Hachures": st.column_config.CheckboxColumn("Hachures visuelles"),
        }
    )
    
    for i in range(1, len(df)):
        prev_debut = float(df.loc[i-1, "Début"])
        prev_duree = float(df.loc[i-1, "Durée"])
        auto_debut = prev_debut + prev_duree
        
        if pd.isna(df.loc[i, "Début"]) or df.loc[i, "Début"] == 0:
            df.loc[i, "Début"] = auto_debut
    
    df_renamed = df.rename(columns={
        "🎯 TM (Manuel seul)": "TM",
        "🤖 TT (Tech. seul)": "TT",
        "🤝 TTM (Parallèle)": "TTM",
        "☕ TR (Repos)": "TR",
        "⏸️ TZ (Masqué)": "TZ",
        "/// Hachures": "TF"
    })
    
    df_renamed["Fin"] = df_renamed["Début"] + df_renamed["Durée"]
    df_renamed["Sys"] = m
    dfs.append(df_renamed)

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
    total_machine_time = 0      # TT + TTM
    total_operator_manual = 0   # TM (opérateur seul)
    total_operator_parallel = 0 # TTM (parallèle)
    total_repos_time = 0        # TR
    total_masked_time = 0       # TZ
    
    COLORS = {
        "TM": "#ff8c00",
        "TT": "#1f4fff",
        "TTM": "#111827",
        "TR": "#9ca3af",
        "TZ": "#e5e7eb"
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
        tm = bool(row["TM"])
        tt = bool(row["TT"])
        ttm = bool(row["TTM"])
        tr = bool(row["TR"])
        tz = bool(row["TZ"])
        tf = bool(row["TF"])
        
        # TZ - Temps masqué (seulement pour l'affichage, mais compté pour taux)
        if tz:
            total_masked_time += temps
            rect = Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TZ"],
                edgecolor="black",
                alpha=0.4
            )
            ax.add_patch(rect)
            max_x = max(max_x, end)
            continue
        
        # TT - Machine seule
        if tt and not ttm:
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
        
        # TM - Opérateur seul
        elif tm and not ttm:
            total_operator_manual += temps
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
        
        # TTM - Parallèle
        elif ttm:
            total_machine_time += temps
            total_operator_parallel += temps
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
                color="black",
                linewidth=1.5
            )
            if tf:
                draw_hatch(ax, rect, start, y_op, temps, abs(y_positions[sys] - y_op))
            max_x = max(max_x, end)
        
        # TR - Repos
        elif tr:
            total_repos_time += temps
            rect = Rectangle(
                (start, y_op),
                temps,
                h,
                facecolor=COLORS["TR"],
                edgecolor="black",
                alpha=0.6
            )
            ax.add_patch(rect)
            max_x = max(max_x, end)
        
        if temps >= 0.5 and op != "" and op != "nan":
            ax.text(
                start + temps/2,
                y_op - 0.18,
                op,
                ha="center",
                fontsize=9,
                rotation=0
            )
    
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")
    
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")
    
    ax.set_xlim(-2, max_x + 2)
    ax.set_ylim(-1, 1.5)
    ax.set_yticks([])
    ax.set_xlabel("Temps (secondes)", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.2, linestyle="--")
    plt.tight_layout()
    
    # ===================================================
    # CALCULS AVEC EXCLUSION DE TZ POUR LE CYCLE
    # ===================================================
    
    # Temps humain total (TM + TTM) - TZ est inclus ici pour les taux
    temps_humain_total = total_operator_manual + total_operator_parallel + total_masked_time
    
    # Temps cycle de base (sans TZ et sans coefficients)
    temps_cycle_base = total_machine_time + total_operator_manual
    
    # Application de JA uniquement sur TM
    temps_manuel_ajuste_ja = total_operator_manual * coef_ja_total
    
    # Temps cycle avec JA (toujours sans TZ)
    temps_cycle_avec_ja = total_machine_time + temps_manuel_ajuste_ja
    
    # Application du coefficient REPO sur le temps cycle avec JA
    temps_cycle_avec_repo = temps_cycle_avec_ja * coef_repo
    
    # Impact contrôle qualité
    impact_controle = 0
    if temps_controle > 0 and frequence_controle > 0:
        temps_libre_dans_cycle = max(0, temps_cycle_avec_repo - total_machine_time - temps_manuel_ajuste_ja)
        if temps_controle > temps_libre_dans_cycle:
            impact_controle = (temps_controle - temps_libre_dans_cycle) / frequence_controle
    
    # Temps cycle final (TZ exclu)
    temps_cycle_final = temps_cycle_avec_repo + impact_controle
    
    # ===================================================
    # KPI
    # ===================================================
    
    # Taux de musculación (inclut TZ)
    # = (TM + TTM + TZ) / (TT + TTM + TM_coeff + TZ) × 100
    denominateur_musculation = (total_machine_time - total_operator_parallel) + total_operator_parallel + temps_manuel_ajuste_ja + total_masked_time
    denominateur_musculation = total_machine_time + temps_manuel_ajuste_ja + total_masked_time
    
    taux_musculation = (temps_humain_total / denominateur_musculation * 100) if denominateur_musculation > 0 else 0
    
    # Taux occupation homme (inclut TZ)
    taux_occupation_homme = temps_humain_total / temps_cycle_final if temps_cycle_final > 0 else 0
    
    # Taux occupation machine (TZ n'affecte pas la machine)
    taux_occupation_machine = total_machine_time / temps_cycle_final if temps_cycle_final > 0 else 0
    
    # Production
    heures_travail_sec = heures_travail * 3600
    pieces_heure = 3600 / temps_cycle_final if temps_cycle_final > 0 else 0
    pieces_jour = pieces_heure * heures_travail
    
    # Surcoût
    surcout_operateur = temps_manuel_ajuste_ja - total_operator_manual
    
    # ===================================================
    # AFFICHAGE
    # ===================================================
    
    st.markdown("## 📊 Indicateurs de performance")
    
    # Première ligne
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("⏱️ Temps cycle final", f"{round(temps_cycle_final, 2)} s",
                delta=f"×{coef_repo} repo")
    col2.metric("🤖 Temps machine total", f"{round(total_machine_time, 2)} s",
                delta=f"TT: {round(total_machine_time - total_operator_parallel, 2)} s, TTM: {round(total_operator_parallel, 2)} s")
    col3.metric("👤 Temps manuel (TM)", f"{round(total_operator_manual, 2)} s",
                delta=f"×{coef_ja_total:.2f} JA = {round(temps_manuel_ajuste_ja, 2)} s")
    col4.metric("💪 Taux de musculación", f"{round(taux_musculation, 1)} %",
                help="(TM + TTM + TZ) / (TT + TTM + TM_coeff + TZ) × 100")
    
    # Deuxième ligne
    col5, col6, col7, col8 = st.columns(4)
    
    col5.metric("👥 Taux occupation homme", f"{round(taux_occupation_homme * 100, 1)} %",
                help=f"TM: {round(total_operator_manual, 1)} s + TTM: {round(total_operator_parallel, 1)} s + TZ: {round(total_masked_time, 1)} s = {round(temps_humain_total, 1)} s")
    col6.metric("🏭 Taux occupation machine", f"{round(taux_occupation_machine * 100, 1)} %")
    col7.metric("📦 Pièces / Heure", f"{round(pieces_heure, 1)}")
    col8.metric("📅 Pièces / Jour", f"{round(pieces_jour, 1)}")
    
    # Détail des calculs
    with st.expander("📐 Détail des calculs"):
        st.markdown("### ⏱️ Temps mesurés")
        st.write(f"- **TM** (Temps Manuel - opérateur seul): **{round(total_operator_manual, 2)} s**")
        st.write(f"- **TTM** (Temps parallèle): **{round(total_operator_parallel, 2)} s**")
        st.write(f"- **TT** (Temps machine seul): **{round(total_machine_time - total_operator_parallel, 2)} s**")
        st.write(f"- **TR** (Temps repos): **{round(total_repos_time, 2)} s**")
        st.write(f"- **TZ** (Temps masqué): **{round(total_masked_time, 2)} s**")
        
        st.markdown("### 📈 Temps humain total (inclut TZ)")
        st.write(f"- TM + TTM + TZ = {round(total_operator_manual, 2)} + {round(total_operator_parallel, 2)} + {round(total_masked_time, 2)} = **{round(temps_humain_total, 2)} s**")
        
        st.markdown("### 📊 Application des coefficients")
        st.write(f"- Coefficient JA: **{coef_habilete} + {coef_activite} + {coef_conditions} + {coef_stabilite} + 1 = {coef_ja_total:.2f}**")
        st.write(f"- TM corrigé JA = {round(total_operator_manual, 2)} × {coef_ja_total:.2f} = **{round(temps_manuel_ajuste_ja, 2)} s**")
        st.write(f"- Surcoût opérateur: **+{round(surcout_operateur, 2)} s**")
        
        st.markdown("### 🔄 Temps cycle (TZ exclu du cycle)")
        st.write(f"- Temps machine (TT + TTM): **{round(total_machine_time, 2)} s**")
        st.write(f"- Temps manuel corrigé (TM_coeff): **+ {round(temps_manuel_ajuste_ja, 2)} s**")
        st.write(f"- = Temps cycle base: **{round(temps_cycle_avec_ja, 2)} s**")
        st.write(f"- Coefficient rendement (REPO): **× {coef_repo}**")
        st.write(f"- = Temps cycle avec REPO: **{round(temps_cycle_avec_repo, 2)} s**")
        
        if impact_controle > 0:
            st.write(f"- Impact contrôle qualité: **+ {round(impact_controle, 2)} s**")
            st.write(f"- = Temps cycle final: **{round(temps_cycle_final, 2)} s**")
        else:
            st.write(f"- = Temps cycle final: **{round(temps_cycle_final, 2)} s**")
        
        st.markdown("### 💪 Calcul du taux de musculación (inclut TZ)")
        st.write(f"- Numérateur (TM + TTM + TZ) = **{round(temps_humain_total, 2)} s**")
        st.write(f"- Dénominateur (TT + TTM + TM_coeff + TZ) = {round(total_machine_time - total_operator_parallel, 2)} + {round(total_operator_parallel, 2)} + {round(temps_manuel_ajuste_ja, 2)} + {round(total_masked_time, 2)} = **{round(denominateur_musculation, 2)} s**")
        st.write(f"- Taux = {round(temps_humain_total, 2)} / {round(denominateur_musculation, 2)} × 100 = **{round(taux_musculation, 1)} %**")
    
    # Légende
    with st.expander("🎨 Légende des couleurs"):
        st.markdown("""
        - 🟠 **Orange** = TM (Temps Manuel - opérateur seul)
        - 🔵 **Bleu** = TT (Temps Technologique - machine seule)
        - ⚫ **Noir** = TTM (Temps parallèle - opérateur + machine)
        - 🩶 **Gris** = TR (Temps Repos)
        - ⬜ **Gris clair** = TZ (Temps Masqué) - **Compté pour les taux mais exclu du temps cycle**
        """)
    
    st.success("✅ Simogramme généré avec succès")
    st.pyplot(fig)
    
    # ===================================================
    # EXPORTS
    # ===================================================
    
    image_path = "simogramme.png"
    fig.savefig(image_path, bbox_inches="tight", dpi=300)
    
    excel_path = "simogramme.xlsx"
    
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Export dataframe complet
        df_export = edited_df.copy()
        df_export = df_export.rename(columns={
            "TM": "TM (Manuel seul)",
            "TT": "TT (Tech. seul)",
            "TTM": "TTM (Parallèle)",
            "TR": "TR (Repos)",
            "TZ": "TZ (Masqué)",
            "TF": "Hachures"
        })
        df_export.to_excel(writer, sheet_name="Données", index=False)
        
        workbook = writer.book
        worksheet = workbook.create_sheet("Résultats")
        
        worksheet["A1"] = "SIMULATEUR SIMOGRAMME"
        worksheet["A1"].font = workbook.add_font(bold=True, size=14)
        worksheet["A3"] = "Date"
        worksheet["B3"] = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        worksheet["A4"] = "Référence pièce"
        worksheet["B4"] = reference_piece
        worksheet["A5"] = "Numéro machine"
        worksheet["B5"] = numéro_machine
        worksheet["A6"] = "PDC"
        worksheet["B6"] = pdc
        worksheet["A7"] = "Vitesse de coupe"
        worksheet["B7"] = vitesse_coupe
        worksheet["A8"] = "Vitesse d'avance"
        worksheet["B8"] = vitesse_avance
        
        worksheet["A10"] = "COEFFICIENTS"
        worksheet["A11"] = "Habileté"
        worksheet["B11"] = coef_habilete
        worksheet["A12"] = "Activité"
        worksheet["B12"] = coef_activite
        worksheet["A13"] = "Conditions"
        worksheet["B13"] = coef_conditions
        worksheet["A14"] = "Stabilité"
        worksheet["B14"] = coef_stabilite
        worksheet["A15"] = "JA Total"
        worksheet["B15"] = round(coef_ja_total, 2)
        worksheet["A16"] = "Rendement (REPO)"
        worksheet["B16"] = coef_repo
        
        worksheet["A18"] = "RÉSULTATS"
        worksheet["A19"] = "Temps machine (TT+TTM)"
        worksheet["B19"] = round(total_machine_time, 2)
        worksheet["A20"] = "Temps manuel (TM)"
        worksheet["B20"] = round(total_operator_manual, 2)
        worksheet["A21"] = "Temps parallèle (TTM)"
        worksheet["B21"] = round(total_operator_parallel, 2)
        worksheet["A22"] = "Temps masqué (TZ)"
        worksheet["B22"] = round(total_masked_time, 2)
        worksheet["A23"] = "Temps humain total (TM+TTM+TZ)"
        worksheet["B23"] = round(temps_humain_total, 2)
        worksheet["A24"] = "Temps manuel corrigé (TM×JA)"
        worksheet["B24"] = round(temps_manuel_ajuste_ja, 2)
        worksheet["A25"] = "Temps cycle final"
        worksheet["B25"] = round(temps_cycle_final, 2)
        worksheet["A26"] = "Taux de musculación"
        worksheet["B26"] = round(taux_musculation, 1)
        worksheet["A27"] = "Taux occupation homme"
        worksheet["B27"] = round(taux_occupation_homme * 100, 1)
        worksheet["A28"] = "Taux occupation machine"
        worksheet["B28"] = round(taux_occupation_machine * 100, 1)
        worksheet["A29"] = "Pièces / Heure"
        worksheet["B29"] = round(pieces_heure, 1)
        worksheet["A30"] = "Pièces / Jour"
        worksheet["B30"] = round(pieces_jour, 1)
        
        img = Image(image_path)
        worksheet.add_image(img, 'D1')
    
    # ===================================================
    # SAUVEGARDE BDD avec résultats
    # ===================================================
    
    resultats = json.dumps({
        'total_machine_time': total_machine_time,
        'total_operator_manual': total_operator_manual,
        'total_operator_parallel': total_operator_parallel,
        'total_masked_time': total_masked_time,
        'total_repos_time': total_repos_time,
        'temps_humain_total': temps_humain_total,
        'temps_manuel_ajuste_ja': temps_manuel_ajuste_ja,
        'temps_cycle_final': temps_cycle_final,
        'taux_musculation': taux_musculation,
        'taux_occupation_homme': taux_occupation_homme,
        'taux_occupation_machine': taux_occupation_machine,
        'pieces_heure': pieces_heure,
        'pieces_jour': pieces_jour
    })
    
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
    
    save_configuration(config_data, resultats)
    
    with open(excel_path, "rb") as f:
        st.download_button(
            "📥 Télécharger Excel",
            f,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(excel_path):
        os.remove(excel_path)

# ===================================================
# HISTORIQUE
# ===================================================

if "show_history" in st.session_state and st.session_state["show_history"]:
    st.markdown("## 📚 Historique des simulations")
    
    configurations = load_configurations()
    
    if configurations:
        # Créer un dataframe simple pour l'affichage
        history_data = []
        for config in configurations:
            try:
                resultats = json.loads(config[18]) if len(config) > 18 else {}
                history_data.append({
                    'Date': config[1],
                    'Référence': config[2],
                    'Machine': config[3],
                    'JA Total': config[11],
                    'Repo': config[12],
                    'Temps cycle (s)': resultats.get('temps_cycle_final', 0),
                    'Pièces/heure': resultats.get('pieces_heure'),)}
