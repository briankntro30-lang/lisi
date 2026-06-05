import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime
import sqlite3
import json
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.drawing.image import Image as XLImage

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
.metric-card {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    text-align: center;
}
.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #1f2937;
}
.metric-label {
    font-size: 14px;
    color: #6b7280;
    margin-top: 5px;
}
.metric-delta {
    font-size: 12px;
    margin-top: 5px;
}
.info-icon {
    display: inline-block;
    width: 16px;
    height: 16px;
    background-color: #6b7280;
    color: white;
    border-radius: 50%;
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    line-height: 16px;
    margin-left: 5px;
    cursor: help;
    font-family: monospace;
}
.info-icon:hover {
    background-color: #1f2937;
}
.legend-color {
    display: inline-block;
    width: 20px;
    height: 20px;
    border-radius: 3px;
    margin-right: 5px;
    vertical-align: middle;
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
    conn = sqlite3.connect('simogramme_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS configurations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, reference_piece TEXT, numero_machine TEXT,
                  pdc TEXT, vitesse_coupe TEXT, vitesse_avance TEXT,
                  coef_habilete REAL, coef_activite REAL, coef_conditions REAL,
                  coef_stabilite REAL, coef_ja_total REAL, coef_repo REAL,
                  heures_travail REAL, machines TEXT, donnees TEXT, resultats TEXT)''')
    conn.commit()
    conn.close()

def save_configuration(data):
    try:
        conn = sqlite3.connect('simogramme_data.db')
        c = conn.cursor()
        c.execute("""INSERT INTO configurations 
                     (date, reference_piece, numero_machine, pdc, vitesse_coupe, 
                      vitesse_avance, coef_habilete, coef_activite, coef_conditions, 
                      coef_stabilite, coef_ja_total, coef_repo, heures_travail, 
                      machines, donnees, resultats)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (data['date'], data['reference_piece'], data['numero_machine'], 
                   data['pdc'], data['vitesse_coupe'], data['vitesse_avance'],
                   data['coef_habilete'], data['coef_activite'], data['coef_conditions'],
                   data['coef_stabilite'], data['coef_ja_total'], data['coef_repo'],
                   data['heures_travail'], data['machines'], data['donnees'], data['resultats']))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {str(e)}")
        return False

def load_configurations():
    try:
        conn = sqlite3.connect('simogramme_data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM configurations ORDER BY date DESC')
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Erreur chargement: {str(e)}")
        return []

def delete_configuration(config_id):
    try:
        conn = sqlite3.connect('simogramme_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM configurations WHERE id = ?', (config_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur suppression: {str(e)}")
        return False

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
    reference_piece = st.text_input("Référence pièce", key="ref_piece")
    numéro_machine = st.text_input("Numéro de la machine", key="num_machine")
    pdc = st.text_input("PDC", key="pdc")
    vitesse_coupe = st.text_input("Vitesse de coupe", key="vit_coupe")
    vitesse_avance = st.text_input("Vitesse d'avance", key="vit_avance")
    
    st.markdown("## Coefficient JA (Jugement d'Allure)")
    st.info("Les coefficients sont des valeurs entre 0 et 1, la somme sera ajoutée à 1")
    
    coef_habilete = st.number_input("Coefficient d'habileté", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="habilete")
    coef_activite = st.number_input("Coefficient d'activité", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="activite")
    coef_conditions = st.number_input("Coefficient des conditions de travail", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="conditions")
    coef_stabilite = st.number_input("Coefficient de stabilité", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="stabilite")
    coef_ja_total = 1 + coef_habilete + coef_activite + coef_conditions + coef_stabilite
    st.metric("Coefficient JA total", f"{coef_ja_total:.2f}")
    
    st.markdown("## Coefficient de rendement opérateur")
    coef_repo = st.number_input("Coefficient de rendement opérateur", min_value=1.00, max_value=5.00, value=1.00, step=0.05, key="repo")
    heures_travail = st.number_input("Heures de travail / jour", min_value=1.0, max_value=24.0, value=7.0, step=0.5, key="heures")
    
    st.markdown("---")
    if "machines" not in st.session_state:
        st.session_state["machines"] = ["M1"]
    
    if st.button("➕ Ajouter machine"):
        st.session_state["machines"].append(f"M{len(st.session_state['machines'])+1}")
        st.rerun()
    
    st.markdown("---")
    st.markdown("## Historique des simulations")
    if st.button("📊 Voir historique"):
        st.session_state["show_history"] = True
        st.rerun()
    if st.button("❌ Fermer historique"):
        st.session_state["show_history"] = False
        st.rerun()

# ===================================================
# AFFICHAGE HISTORIQUE
# ===================================================

if st.session_state.get("show_history", False):
    st.markdown("## Historique des simulations")
    configurations = load_configurations()
    if configurations:
        for config in configurations:
            with st.expander(f"Simulation du {config[1]}"):
                st.write(f"**Référence pièce:** {config[2]}")
                st.write(f"**Numéro machine:** {config[3]}")
                st.write(f"**PDC:** {config[4]}")
                st.write(f"**Vitesse de coupe:** {config[5]}")
                st.write(f"**Vitesse d'avance:** {config[6]}")
                if st.button(f"🗑️ Supprimer", key=f"del_{config[0]}"):
                    if delete_configuration(config[0]):
                        st.success("Simulation supprimée!")
                        st.rerun()
    else:
        st.info("Aucune simulation sauvegardée")
    st.markdown("---")

# ===================================================
# LÉGENDE
# ===================================================

def afficher_legende():
    st.markdown("### 📖 Légende des types de temps")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("""<div style="text-align: center;"><span class="legend-color" style="background-color: #ff8c00;"></span><strong>TM</strong><span class="info-icon" title="Temps Manuel - Opérateur seul">?</span><br><small>Temps manuel</small></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div style="text-align: center;"><span class="legend-color" style="background-color: #1f4fff;"></span><strong>TT</strong><span class="info-icon" title="Temps Technologique - Machine seule">?</span><br><small>Temps machine</small></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div style="text-align: center;"><span class="legend-color" style="background-color: #111827;"></span><strong>TTM</strong><span class="info-icon" title="Temps de Travail en Manuel - Opérateur et machine simultanément">?</span><br><small>Temps parallèle</small></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""<div style="text-align: center;"><span class="legend-color" style="background-color: #9ca3af;"></span><strong>TR</strong><span class="info-icon" title="Temps de Repos - Pause opérateur">?</span><br><small>Temps repos</small></div>""", unsafe_allow_html=True)
    with col5:
        st.markdown("""<div style="text-align: center;"><span class="legend-color" style="background-color: #e5e7eb;"></span><strong>TZ</strong><span class="info-icon" title="Temps Masqué - Temps non productif">?</span><br><small>Temps masqué</small></div>""", unsafe_allow_html=True)
    st.markdown("---")

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
                st.rerun()
        else:
            st.write("")
    
    default_df = pd.DataFrame({
        "Etape": [""], "Debut": [0.0], "Duree": [0.0],
        "TM 🕐": [False], "TT 🤖": [False], "TTM ⚡": [False],
        "TR ☕": [False], "TZ ⚫": [False], "TF 🎨": [False],
    })
    
    df = st.data_editor(
        default_df, num_rows="dynamic", key=f"table_{m}", use_container_width=True,
        column_config={
            "Etape": st.column_config.TextColumn("Description étape", width="medium"),
            "Debut": st.column_config.NumberColumn("Début (s)", format="%.1f"),
            "Duree": st.column_config.NumberColumn("Durée (s)", format="%.1f"),
            "TM 🕐": st.column_config.CheckboxColumn("TM"),
            "TT 🤖": st.column_config.CheckboxColumn("TT"),
            "TTM ⚡": st.column_config.CheckboxColumn("TTM"),
            "TR ☕": st.column_config.CheckboxColumn("TR"),
            "TZ ⚫": st.column_config.CheckboxColumn("TZ"),
            "TF 🎨": st.column_config.CheckboxColumn("TF"),
        }
    )
    
    for i in range(1, len(df)):
        prev_debut = float(df.iloc[i-1]["Debut"])
        prev_duree = float(df.iloc[i-1]["Duree"])
        auto_debut = prev_debut + prev_duree
        if pd.isna(df.iloc[i]["Debut"]) or df.iloc[i]["Debut"] == 0:
            df.iloc[i, df.columns.get_loc("Debut")] = auto_debut
    
    df_copy = df.copy()
    df_copy.columns = [col.split(' ')[0] if ' ' in col else col for col in df_copy.columns]
    df_copy["Fin"] = df_copy["Debut"] + df_copy["Duree"]
    df_copy["Sys"] = m
    dfs.append(df_copy)

if dfs:
    edited_df = pd.concat(dfs, ignore_index=True)
else:
    edited_df = pd.DataFrame()

afficher_legende()

# ===================================================
# GENERATE SIMOGRAMME
# ===================================================

if st.button("Générer le simogramme"):
    if edited_df.empty:
        st.error("Veuillez ajouter au moins une machine avec des données")
        st.stop()
    
    edited_df["Debut"] = pd.to_numeric(edited_df["Debut"], errors='coerce').fillna(0)
    edited_df["Duree"] = pd.to_numeric(edited_df["Duree"], errors='coerce').fillna(0)
    edited_df["Fin"] = edited_df["Debut"] + edited_df["Duree"]
    
    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_visible(False)
    ax.set_frame_on(False)
    
    machines = st.session_state["machines"]
    y_positions = {}
    step = 0.6
    h = 0.22
    y_op = 0
    
    for i, m in enumerate(machines):
        if i % 2 == 0:
            y_positions[m] = step * ((i // 2) + 1)
        else:
            y_positions[m] = -step * ((i // 2) + 1)
    
    max_x = 0
    total_machine_time = 0
    total_operator_manual = 0
    total_operator_parallel = 0
    total_repos_time = 0
    total_masked_time = 0
    
    COLORS = {"TM": "#ff8c00", "TT": "#1f4fff", "TTM": "#111827", "TR": "#9ca3af", "TZ": "#e5e7eb"}
    
    def draw_hatch(ax, rect, x, y, w, ht, spacing=0.2):
        i = 0
        while i < w + ht:
            line, = ax.plot([x + i, x + i - ht], [y, y + ht], color="black", linewidth=0.6, alpha=0.6)
            line.set_clip_path(rect)
            i += spacing
    
    for idx, row in edited_df.iterrows():
        op = str(row["Etape"]) if pd.notna(row["Etape"]) else ""
        start = float(row["Debut"])
        temps = float(row["Duree"])
        end = start + temps
        sys = str(row["Sys"])
        
        tm = bool(row["TM"]) if "TM" in row and pd.notna(row["TM"]) else False
        tt = bool(row["TT"]) if "TT" in row and pd.notna(row["TT"]) else False
        ttm = bool(row["TTM"]) if "TTM" in row and pd.notna(row["TTM"]) else False
        tr = bool(row["TR"]) if "TR" in row and pd.notna(row["TR"]) else False
        tz = bool(row["TZ"]) if "TZ" in row and pd.notna(row["TZ"]) else False
        tf = bool(row["TF"]) if "TF" in row and pd.notna(row["TF"]) else False
        
        if tz:
            total_masked_time += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TZ"], edgecolor="black", alpha=0.4)
            ax.add_patch(rect)
            if tf and temps > 0 and h > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
            continue
        
        if tt and not ttm:
            total_machine_time += temps
            rect = Rectangle((start, y_positions.get(sys, 0)), temps, h, facecolor=COLORS["TT"], edgecolor="black")
            ax.add_patch(rect)
            if tf and temps > 0 and h > 0:
                draw_hatch(ax, rect, start, y_positions.get(sys, 0), temps, h)
            max_x = max(max_x, end)
        elif tm and not ttm:
            total_operator_manual += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TM"], edgecolor="black")
            ax.add_patch(rect)
            if tf and temps > 0 and h > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
        elif ttm:
            total_machine_time += temps
            total_operator_parallel += temps
            rect = Rectangle((start, y_op), temps, y_positions.get(sys, 0) - y_op, facecolor="#FFFFFF00", edgecolor="black")
            ax.add_patch(rect)
            ax.plot([start, start + temps], [y_op, y_positions.get(sys, 0)], color="black", linewidth=1.5)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_op, temps, abs(y_positions.get(sys, 0) - y_op))
            max_x = max(max_x, end)
        elif tr:
            total_repos_time += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TR"], edgecolor="black", alpha=0.6)
            ax.add_patch(rect)
            if tf and temps > 0 and h > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
        
        if temps >= 0.5 and op != "" and op != "nan":
            ax.text(start + temps/2, y_op - 0.18, op, ha="center", fontsize=9, rotation=0, wrap=True)
    
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")
    
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["TM"], edgecolor='black', label='TM - Temps Manuel'),
        Patch(facecolor=COLORS["TT"], edgecolor='black', label='TT - Temps Machine'),
        Patch(facecolor=COLORS["TTM"], edgecolor='black', label='TTM - Temps Parallèle'),
        Patch(facecolor=COLORS["TR"], edgecolor='black', label='TR - Temps Repos'),
        Patch(facecolor=COLORS["TZ"], edgecolor='black', alpha=0.4, label='TZ - Temps Masqué')
    ]
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9)
    
    ax.set_xlim(-2, max_x + 2)
    ax.set_ylim(-1.5, 1.5)
    ax.set_yticks([])
    ax.set_xlabel("Temps (secondes)", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.2, linestyle="--")
    plt.tight_layout()
    
    # ===================================================
    # CALCULS
    # ===================================================
    
    temps_humain_total_reel = total_operator_manual + total_operator_parallel + total_masked_time
    temps_cycle_sans_coef = total_machine_time + total_operator_manual
    temps_manuel_ajuste_ja = total_operator_manual * coef_ja_total
    temps_cycle_avec_ja = total_machine_time + temps_manuel_ajuste_ja
    temps_cycle_final = temps_cycle_avec_ja * coef_repo
    
    taux_occupation_homme = (temps_humain_total_reel / temps_cycle_sans_coef * 100) if temps_cycle_sans_coef > 0 else 0
    taux_occupation_machine = (total_machine_time / temps_cycle_sans_coef * 100) if temps_cycle_sans_coef > 0 else 0
    
    pieces_heure = 3600 / temps_cycle_final if temps_cycle_final > 0 else 0
    pieces_jour = pieces_heure * heures_travail
    
    # ===================================================
    # AFFICHAGE KPI
    # ===================================================
    
    st.markdown("## Indicateurs de performance")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(temps_cycle_final, 2)} s</div><div class="metric-label">Temps cycle final</div><div class="metric-delta">×{coef_repo} repo</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(total_machine_time, 2)} s</div><div class="metric-label">Temps machine total</div><div class="metric-delta">TT: {round(total_machine_time - total_operator_parallel, 2)} s, TTM: {round(total_operator_parallel, 2)} s</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(total_operator_manual, 2)} s</div><div class="metric-label">Temps manuel (TM)</div><div class="metric-delta">×{round(coef_ja_total, 2)} JA = {round(temps_manuel_ajuste_ja, 2)} s</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(taux_occupation_homme, 1)} %</div><div class="metric-label">Taux occupation homme</div><div class="metric-delta">TM+TTM+TZ = {round(temps_humain_total_reel, 1)} s</div></div>""", unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(taux_occupation_machine, 1)} %</div><div class="metric-label">Taux occupation machine</div><div class="metric-delta">TT+TTM = {round(total_machine_time, 1)} s</div></div>""", unsafe_allow_html=True)
    with col6:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(pieces_heure, 1)}</div><div class="metric-label">Pièces / Heure</div></div>""", unsafe_allow_html=True)
    with col7:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(pieces_jour, 1)}</div><div class="metric-label">Pièces / Jour</div></div>""", unsafe_allow_html=True)
    with col8:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{round(total_repos_time, 2)} s</div><div class="metric-label">Temps repos (TR)</div></div>""", unsafe_allow_html=True)
    
    with st.expander("Détail des calculs"):
        st.write(f"**TM (opérateur seul):** {round(total_operator_manual, 2)} s")
        st.write(f"**TTM (parallèle):** {round(total_operator_parallel, 2)} s")
        st.write(f"**TT (machine seul):** {round(total_machine_time - total_operator_parallel, 2)} s")
        st.write(f"**TR (repos):** {round(total_repos_time, 2)} s")
        st.write(f"**TZ (masqué):** {round(total_masked_time, 2)} s")
        st.write(f"**Temps humain total réel:** {round(temps_humain_total_reel, 2)} s")
        st.write(f"**Temps cycle sans coefficients:** {round(temps_cycle_sans_coef, 2)} s")
        st.write(f"**Coefficient JA:** {coef_ja_total:.2f}")
        st.write(f"**TM corrigé JA:** {round(total_operator_manual, 2)} × {coef_ja_total:.2f} = {round(temps_manuel_ajuste_ja, 2)} s")
        st.write(f"**Temps cycle avec JA:** {round(temps_cycle_avec_ja, 2)} s")
        st.write(f"**Coefficient REPO:** ×{coef_repo}")
        st.write(f"**Temps cycle final:** {round(temps_cycle_final, 2)} s")
    
    st.success("Simogramme généré avec succès")
    st.pyplot(fig)
    
    # ===================================================
    # BOUTONS
    # ===================================================
    
    save_data = {
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
        'machines': str(st.session_state["machines"]),
        'donnees': edited_df.to_json(),
        'resultats': json.dumps({'total_machine_time': total_machine_time, 'total_operator_manual': total_operator_manual, 'total_operator_parallel': total_operator_parallel, 'total_masked_time': total_masked_time, 'total_repos_time': total_repos_time, 'temps_cycle_final': temps_cycle_final, 'pieces_heure': pieces_heure, 'pieces_jour': pieces_jour})
    }
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("💾 Sauvegarder", key="save_btn"):
            if save_configuration(save_data):
                st.success("✅ Sauvegardé!")
    
    with col_btn2:
        # Export Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export = edited_df.copy()
            df_export.to_excel(writer, sheet_name="Données", index=False)
            
            # Créer feuille résultats
            results_data = {
                "Métrique": ["Temps cycle final (s)", "Temps machine total (s)", "Temps manuel TM (s)", 
                            "Taux occupation homme (%)", "Taux occupation machine (%)", "Pièces / Heure", "Pièces / Jour"],
                "Valeur": [round(temps_cycle_final, 2), round(total_machine_time, 2), round(total_operator_manual, 2),
                          round(taux_occupation_homme, 1), round(taux_occupation_machine, 1), round(pieces_heure, 1), round(pieces_jour, 1)]
            }
            pd.DataFrame(results_data).to_excel(writer, sheet_name="Résultats", index=False)
            
            # Informations production
            info_data = {
                "Paramètre": ["Date", "Référence pièce", "Numéro machine", "PDC", "Vitesse coupe", "Vitesse avance", "Coefficient JA", "Coefficient REPO"],
                "Valeur": [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reference_piece, numéro_machine, pdc, vitesse_coupe, vitesse_avance, round(coef_ja_total, 2), coef_repo]
            }
            pd.DataFrame(info_data).to_excel(writer, sheet_name="Informations", index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Télécharger Excel",
            data=output,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col_btn3:
        # Télécharger image
        img_output = io.BytesIO()
        fig.savefig(img_output, format='png', bbox_inches="tight", dpi=150, facecolor='white')
        img_output.seek(0)
        st.download_button(
            label="🖼️ Télécharger PNG",
            data=img_output,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )
