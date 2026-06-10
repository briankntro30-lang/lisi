import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from datetime import datetime
import sqlite3
import json
import io
import os

# ===================================================
# CONFIG
# ===================================================

st.set_page_config(page_title="Simogramme", layout="wide")

st.markdown("""
<style>
.main { background-color: #f4f6f9; }
h1, h2, h3 { color: #1f2937; font-weight: 700; }
.stButton>button {
    background-color: #1f2937; color: white;
    border-radius: 8px; height: 45px; font-weight: bold; border: none;
}
.stButton>button:hover { background-color: #374151; }
.metric-card {
    background-color: white; padding: 15px; border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;
}
.metric-value { font-size: 32px; font-weight: bold; color: #1f2937; }
.metric-label { font-size: 14px; color: #6b7280; margin-top: 5px; }
.metric-delta { font-size: 12px; margin-top: 5px; }
.info-icon {
    display: inline-block; width: 16px; height: 16px;
    background-color: #6b7280; color: white; border-radius: 50%;
    text-align: center; font-size: 11px; font-weight: bold;
    line-height: 16px; margin-left: 5px; cursor: help; font-family: monospace;
}
.legend-color {
    display: inline-block; width: 20px; height: 20px;
    border-radius: 3px; margin-right: 5px; vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

LOGO_URL = "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0"
st.image(LOGO_URL, width=250)

# ===================================================
# DATABASE
# ===================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simogramme_data.db")

def init_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS configurations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT, 
                      numero_of TEXT, 
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
                      machines TEXT, 
                      donnees TEXT, 
                      resultats TEXT)''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur d'initialisation de la base de données: {str(e)}")
        return False

def save_configuration(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO configurations
                     (date, numero_of, reference_piece, numero_machine, pdc, vitesse_coupe,
                      vitesse_avance, coef_habilete, coef_activite, coef_conditions,
                      coef_stabilite, coef_ja_total, coef_repo, heures_travail,
                      machines, donnees, resultats)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (data['date'], data['numero_of'], data['reference_piece'],
                   data['numero_machine'], data['pdc'], data['vitesse_coupe'],
                   data['vitesse_avance'], data['coef_habilete'], data['coef_activite'],
                   data['coef_conditions'], data['coef_stabilite'], data['coef_ja_total'],
                   data['coef_repo'], data['heures_travail'], data['machines'],
                   data['donnees'], data['resultats']))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {str(e)}")
        return False

def load_configurations():
    try:
        conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(DB_PATH)
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## Connexion - Simogramme")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Utilisateur")
        pwd = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if user == "admin" and pwd == "1234":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()

# ===================================================
# SESSION STATE INIT
# ===================================================

if "loaded_config" not in st.session_state:
    st.session_state["loaded_config"] = None

if "machines" not in st.session_state:
    st.session_state["machines"] = ["M1"]

if "show_history" not in st.session_state:
    st.session_state["show_history"] = False

# ===================================================
# APPLY LOADED CONFIG
# ===================================================

if st.session_state["loaded_config"] is not None:
    cfg = st.session_state["loaded_config"]
    
    st.session_state["num_of"] = cfg[2] or ""
    st.session_state["ref_piece"] = cfg[3] or ""
    st.session_state["num_machine"] = cfg[4] or ""
    st.session_state["pdc"] = cfg[5] or ""
    st.session_state["vit_coupe"] = cfg[6] or ""
    st.session_state["vit_avance"] = cfg[7] or ""
    st.session_state["habilete"] = float(cfg[8]) if cfg[8] else 0.0
    st.session_state["activite"] = float(cfg[9]) if cfg[9] else 0.0
    st.session_state["conditions"] = float(cfg[10]) if cfg[10] else 0.0
    st.session_state["stabilite"] = float(cfg[11]) if cfg[11] else 0.0
    st.session_state["repo"] = float(cfg[13]) if cfg[13] else 1.0
    st.session_state["heures"] = float(cfg[14]) if cfg[14] else 7.0

    try:
        machines_restored = json.loads(cfg[15])
        st.session_state["machines"] = machines_restored
    except Exception:
        st.session_state["machines"] = ["M1"]

    try:
        df_all = pd.read_json(cfg[16])
        rename_map = {"TM": "TM 🕐", "TT": "TT 🤖", "TTM": "TTM ⚡",
                      "TR": "TR ☕", "TZ": "TZ ⚫", "TF": "TF 🎨"}
        
        for old, new in rename_map.items():
            if old in df_all.columns:
                df_all.rename(columns={old: new}, inplace=True)
        
        for m in st.session_state["machines"]:
            if "Sys" in df_all.columns:
                df_m = df_all[df_all["Sys"] == m].copy()
            else:
                df_m = df_all.copy()
            
            df_m.drop(columns=["Sys", "Fin"], errors="ignore", inplace=True)
            
            bool_cols = ["TM 🕐", "TT 🤖", "TTM ⚡", "TR ☕", "TZ ⚫", "TF 🎨"]
            for col in bool_cols:
                if col not in df_m.columns:
                    df_m[col] = False
                else:
                    df_m[col] = df_m[col].astype(bool)
            
            df_m.reset_index(drop=True, inplace=True)
            st.session_state[f"preload_table_{m}"] = df_m
    except Exception as e:
        st.warning(f"Impossible de restaurer les tables: {e}")

    st.session_state["loaded_config"] = None

# ===================================================
# SIDEBAR
# ===================================================

with st.sidebar:
    st.image(LOGO_URL, width=220)
    st.title("Configuration")

    st.markdown("## Informations production")
    numero_of = st.text_input("Numéro OF", key="num_of")
    reference_piece = st.text_input("Référence pièce", key="ref_piece")
    numero_machine = st.text_input("Numéro de la machine", key="num_machine")
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
    st.metric("Coefficient JA total", f"{coef_ja_total:.3f}")

    st.markdown("## Coefficient de rendement opérateur")
    coef_repo = st.number_input("Coefficient de rendement opérateur", min_value=1.00, max_value=5.00, value=1.00, step=0.05, key="repo")
    heures_travail = st.number_input("Heures de travail / jour", min_value=1.0, max_value=24.0, value=7.0, step=0.5, key="heures")

    st.markdown("---")
    if st.button("➕ Ajouter machine"):
        new_m = f"M{len(st.session_state['machines']) + 1}"
        st.session_state["machines"].append(new_m)
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
# HISTORIQUE
# ===================================================

if st.session_state["show_history"]:
    st.markdown("## Historique des simulations")
    configurations = load_configurations()
    if configurations:
        for cfg in configurations:
            of_val = cfg[2] or "—"
            pdc_val = cfg[5] or "—"
            mach_val = cfg[4] or "—"
            label = f"OF: {of_val} | PDC: {pdc_val} | Machine: {mach_val} | {cfg[1][:16] if cfg[1] else 'Date inconnue'}"
            
            with st.expander(label):
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"**Référence pièce:** {cfg[3]} | **Vc:** {cfg[6]} | **Vf:** {cfg[7]}")
                    st.write(f"**Coef JA:** {float(cfg[12]):.3f} | **Coef REPO:** {cfg[13]} | **Heures/j:** {cfg[14]}")
                    try:
                        res = json.loads(cfg[17])
                        st.write(f"**Temps cycle:** {round(res.get('temps_cycle_final', 0), 3)} s | "
                                f"**Pièces/h:** {round(res.get('pieces_heure', 0), 1)} | "
                                f"**Pièces/j:** {round(res.get('pieces_jour', 0), 1)}")
                    except Exception:
                        pass
                with col_btn:
                    if st.button("📂 Charger", key=f"load_{cfg[0]}"):
                        st.session_state["loaded_config"] = cfg
                        st.session_state["show_history"] = False
                        st.rerun()
                    if st.button("🗑️ Supprimer", key=f"del_{cfg[0]}"):
                        delete_configuration(cfg[0])
                        st.rerun()
    else:
        st.info("Aucune simulation sauvegardée")
    st.markdown("---")

# ===================================================
# LÉGENDE
# ===================================================

st.markdown("### Légende des types de temps")
leg_cols = st.columns(5)
leg_items = [
    ("#ff8c00", "TM", "Temps Manuel - Opérateur seul", "Temps manuel"),
    ("#1f4fff", "TT", "Temps Technologique - Machine seule", "Temps machine"),
    ("#111827", "TTM", "Opérateur + machine simultanément", "Temps parallèle"),
    ("#9ca3af", "TR", "Temps de Repos", "Temps repos"),
    ("#e5e7eb", "TZ", "Temps Masqué - non productif", "Temps masqué"),
]
for col, (color, code, tip, label) in zip(leg_cols, leg_items):
    with col:
        st.markdown(
            f'<div style="text-align:center;">'
            f'<span class="legend-color" style="background-color:{color};"></span>'
            f'<strong>{code}</strong>'
            f'<span class="info-icon" title="{tip}">?</span>'
            f'<br><small>{label}</small></div>',
            unsafe_allow_html=True)
st.markdown("---")

# ===================================================
# TABLES
# ===================================================

BOOL_COLS = ["TM 🕐", "TT 🤖", "TTM ⚡", "TR ☕", "TZ ⚫", "TF 🎨"]

def make_empty_df():
    return pd.DataFrame([{
        "Etape": "", 
        "Debut": 0.0, 
        "Duree": 0.0,
        "TM 🕐": False, 
        "TT 🤖": False, 
        "TTM ⚡": False,
        "TR ☕": False, 
        "TZ ⚫": False, 
        "TF 🎨": False,
    }])

dfs_for_save = []
tables_output = {}

for m in st.session_state["machines"]:
    col_title, col_del = st.columns([6, 1])
    with col_title:
        st.subheader(f"Tableau {m}")
    with col_del:
        if m != "M1":
            if st.button("🗑️", key=f"del_machine_{m}"):
                st.session_state["machines"].remove(m)
                st.session_state.pop(f"preload_table_{m}", None)
                st.rerun()
        else:
            st.write("")

    if f"preload_table_{m}" in st.session_state:
        initial = st.session_state.pop(f"preload_table_{m}")
        for bc in BOOL_COLS:
            if bc not in initial.columns:
                initial[bc] = False
            else:
                initial[bc] = initial[bc].fillna(False).astype(bool)
    else:
        initial = make_empty_df()

    df_edited = st.data_editor(
        initial,
        num_rows="dynamic",
        key=f"editor_{m}",
        use_container_width=True,
        column_config={
            "Etape": st.column_config.TextColumn("Description étape", width="medium"),
            "Debut": st.column_config.NumberColumn(
                "Début (s)",
                min_value=0.0,
                step=0.1,
                format="%.3f"
            ),
            "Duree": st.column_config.NumberColumn(
                "Durée (s)",
                min_value=0.0,
                step=0.1,
                format="%.3f"
            ),
            "TM 🕐": st.column_config.CheckboxColumn("TM"),
            "TT 🤖": st.column_config.CheckboxColumn("TT"),
            "TTM ⚡": st.column_config.CheckboxColumn("TTM"),
            "TR ☕": st.column_config.CheckboxColumn("TR"),
            "TZ ⚫": st.column_config.CheckboxColumn("TZ"),
            "TF 🎨": st.column_config.CheckboxColumn("TF"),
        }
    )
    tables_output[m] = df_edited

    df_calc = df_edited.copy()
    for col in df_calc.columns:
        if " " in col and col.split(' ')[0] in ['TM', 'TT', 'TTM', 'TR', 'TZ', 'TF']:
            df_calc.rename(columns={col: col.split(' ')[0]}, inplace=True)
    
    df_calc["Debut"] = pd.to_numeric(df_calc["Debut"], errors='coerce').fillna(0)
    df_calc["Duree"] = pd.to_numeric(df_calc["Duree"], errors='coerce').fillna(0)
    df_calc["Fin"] = df_calc["Debut"] + df_calc["Duree"]
    df_calc["Sys"] = m
    dfs_for_save.append(df_calc)

edited_df = pd.concat(dfs_for_save, ignore_index=True) if dfs_for_save else pd.DataFrame()

# ===================================================
# GÉNÉRATION DU SIMOGRAMME
# ===================================================

if st.button("Générer le simogramme"):
    if edited_df.empty or edited_df["Duree"].sum() == 0:
        st.error("Veuillez saisir des données dans au moins une table")
        st.stop()

    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
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

    max_x = total_machine_time = total_operator_manual = 0
    total_operator_parallel = total_repos_time = total_masked_time = 0

    COLORS = {"TM": "#ff8c00", "TT": "#1f4fff", "TTM": "#111827", "TR": "#9ca3af", "TZ": "#e5e7eb"}

    def draw_hatch(ax, rect, x, y, w, ht, spacing=0.2):
        i = 0
        while i < w + ht:
            ln, = ax.plot([x + i, x + i - ht], [y, y + ht], color="black", linewidth=0.6, alpha=0.6)
            ln.set_clip_path(rect)
            i += spacing

    for _, row in edited_df.iterrows():
        op = str(row["Etape"]) if pd.notna(row["Etape"]) else ""
        start = float(row["Debut"])
        temps = float(row["Duree"])
        end = start + temps
        sys = str(row["Sys"])
        
        tm = bool(row.get("TM", False))
        tt = bool(row.get("TT", False))
        ttm = bool(row.get("TTM", False))
        tr = bool(row.get("TR", False))
        tz = bool(row.get("TZ", False))
        tf = bool(row.get("TF", False))

        if tz:
            total_masked_time += temps
            r = Rectangle((start, y_op), temps, h, facecolor=COLORS["TZ"], edgecolor="black", alpha=0.4)
            ax.add_patch(r)
            if tf and temps > 0:
                draw_hatch(ax, r, start, y_op, temps, h)
            max_x = max(max_x, end)
            continue

        if tt and not ttm:
            total_machine_time += temps
            yp = y_positions.get(sys, 0)
            r = Rectangle((start, yp), temps, h, facecolor=COLORS["TT"], edgecolor="black")
            ax.add_patch(r)
            if tf and temps > 0:
                draw_hatch(ax, r, start, yp, temps, h)
            max_x = max(max_x, end)
            
        elif tm and not ttm:
            total_operator_manual += temps
            r = Rectangle((start, y_op), temps, h, facecolor=COLORS["TM"], edgecolor="black")
            ax.add_patch(r)
            if tf and temps > 0:
                draw_hatch(ax, r, start, y_op, temps, h)
            max_x = max(max_x, end)
            
        elif ttm:
            total_machine_time += temps
            total_operator_parallel += temps
            yp = y_positions.get(sys, 0)
            r = Rectangle((start, y_op), temps, yp - y_op, facecolor="#FFFFFF00", edgecolor="black")
            ax.add_patch(r)
            ax.plot([start, start + temps], [y_op, yp], color="black", linewidth=1.5)
            if tf and temps > 0:
                draw_hatch(ax, r, start, y_op, temps, abs(yp - y_op))
            max_x = max(max_x, end)
            
        elif tr:
            total_repos_time += temps
            r = Rectangle((start, y_op), temps, h, facecolor=COLORS["TR"], edgecolor="black", alpha=0.6)
            ax.add_patch(r)
            if tf and temps > 0:
                draw_hatch(ax, r, start, y_op, temps, h)
            max_x = max(max_x, end)

        if temps >= 0.5 and op not in ("", "nan"):
            ax.text(start + temps / 2, y_op - 0.18, op, ha="center", fontsize=9)

    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")
    
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")

    ax.legend(handles=[
        Patch(facecolor=COLORS["TM"], edgecolor='black', label='TM - Temps Manuel'),
        Patch(facecolor=COLORS["TT"], edgecolor='black', label='TT - Temps Machine'),
        Patch(facecolor=COLORS["TTM"], edgecolor='black', label='TTM - Temps Parallèle'),
        Patch(facecolor=COLORS["TR"], edgecolor='black', label='TR - Temps Repos'),
        Patch(facecolor=COLORS["TZ"], edgecolor='black', alpha=0.4, label='TZ - Temps Masqué'),
    ], loc='upper right', framealpha=0.9)
    
    ax.set_xlim(-2, max_x + 2)
    ax.set_ylim(-1.5, 1.5)
    ax.set_yticks([])
    ax.set_xlabel("Temps (secondes)", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.2, linestyle="--")
    plt.tight_layout()

    # Calculs
    temps_humain_total_reel = total_operator_manual + total_operator_parallel + total_masked_time
    temps_cycle_sans_coef = total_machine_time + total_operator_manual
    temps_manuel_ajuste_ja = total_operator_manual * coef_ja_total
    temps_cycle_avec_ja = total_machine_time + temps_manuel_ajuste_ja
    temps_cycle_final = temps_cycle_avec_ja * coef_repo
    taux_occ_homme = (temps_humain_total_reel / temps_cycle_sans_coef * 100) if temps_cycle_sans_coef > 0 else 0
    taux_occ_machine = (total_machine_time / temps_cycle_sans_coef * 100) if temps_cycle_sans_coef > 0 else 0
    pieces_heure = 3600 / temps_cycle_final if temps_cycle_final > 0 else 0
    pieces_jour = pieces_heure * heures_travail

    partie_entiere = int(temps_cycle_final)
    fraction = temps_cycle_final - partie_entiere
    multiple_5 = round(fraction * 20) / 20
    if multiple_5 >= 1.0:
        multiple_5 = 0.95
        partie_entiere += 1
    fraction_code = int(multiple_5 * 100)
    fraction_str = "01" if fraction_code == 0 else str(fraction_code).zfill(2)
    code_temps = f"{partie_entiere}A{fraction_str}"

    # KPI
    st.markdown("## Indicateurs de performance")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    def kpi(col, val, label, delta=""):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div>'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-delta">{delta}</div></div>', unsafe_allow_html=True)
    
    kpi(c1, f"{round(temps_cycle_final, 3)} s", "Temps cycle final", f"×{coef_repo} repo")
    kpi(c2, f"{round(temps_cycle_final / 36, 3)} UM", "Temps cycle final (UM)", f"×{coef_repo} repo")
    kpi(c3, f"{round(total_machine_time, 3)} s", "Temps machine total",
        f"TT:{round(total_machine_time - total_operator_parallel, 3)}s TTM:{round(total_operator_parallel, 3)}s")
    kpi(c4, f"{round(total_operator_manual, 3)} s", "Temps manuel (TM)",
        f"×{round(coef_ja_total, 3)} JA = {round(temps_manuel_ajuste_ja, 3)} s")
    kpi(c5, f"{round(taux_occ_homme, 1)} %", "Taux occupation homme",
        f"TM+TTM+TZ = {round(temps_humain_total_reel, 3)} s")

    c6, c7, c8, c9 = st.columns(4)
    kpi(c6, f"{round(taux_occ_machine, 1)} %", "Taux occupation machine", f"TT+TTM = {round(total_machine_time, 3)} s")
    kpi(c7, f"{round(pieces_heure, 1)}", "Pièces / Heure")
    kpi(c8, f"{round(pieces_jour, 1)}", "Pièces / Jour")
    kpi(c9, f"{round(total_repos_time, 3)} s", "Temps repos (TR)")

    with st.expander("Détail des calculs"):
        details = [
            ("TM (opérateur seul)", f"{round(total_operator_manual, 3)} s"),
            ("TTM (parallèle)", f"{round(total_operator_parallel, 3)} s"),
            ("TT (machine seul)", f"{round(total_machine_time - total_operator_parallel, 3)} s"),
            ("TR (repos)", f"{round(total_repos_time, 3)} s"),
            ("TZ (masqué)", f"{round(total_masked_time, 3)} s"),
            ("Temps humain total réel", f"{round(temps_humain_total_reel, 3)} s"),
            ("Temps cycle sans coeff.", f"{round(temps_cycle_sans_coef, 3)} s"),
            ("Coefficient JA", f"{coef_ja_total:.3f}"),
            ("TM corrigé JA", f"{round(total_operator_manual, 3)} × {coef_ja_total:.3f} = {round(temps_manuel_ajuste_ja, 3)} s"),
            ("Temps cycle avec JA", f"{round(temps_cycle_avec_ja, 3)} s"),
            ("Coefficient REPO", f"×{coef_repo}"),
            ("Temps cycle final", f"{round(temps_cycle_final, 3)} s"),
            ("CODE TEMPS", code_temps)
        ]
        for k, v in details:
            st.write(f"**{k}:** {v}")

    st.success("Simogramme généré avec succès")
    st.pyplot(fig)

    # Sauvegarde
    save_data = {
        'date': str(datetime.now()),
        'numero_of': numero_of,
        'reference_piece': reference_piece,
        'numero_machine': numero_machine,
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
        'machines': json.dumps(st.session_state["machines"]),
        'donnees': edited_df.to_json(),
        'resultats': json.dumps({
            'total_machine_time': total_machine_time,
            'total_operator_manual': total_operator_manual,
            'total_operator_parallel': total_operator_parallel,
            'total_masked_time': total_masked_time,
            'total_repos_time': total_repos_time,
            'temps_cycle_final': temps_cycle_final,
            'pieces_heure': pieces_heure,
            'pieces_jour': pieces_jour,
        })
    }

    cb1, cb2, cb3 = st.columns(3)

    with cb1:
        if st.button("💾 Sauvegarder", key="save_btn"):
            if save_configuration(save_data):
                st.success(f"✅ Sauvegardé dans: {DB_PATH}")

    with cb2:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name="Données", index=False)
            pd.DataFrame({
                "Métrique": ["Temps cycle final (s)", "Temps machine total (s)", "Temps manuel TM (s)",
                            "Taux occupation homme (%)", "Taux occupation machine (%)", "Pièces/Heure", "Pièces/Jour", "CODE TEMPS"],
                "Valeur": [round(temps_cycle_final, 3), round(total_machine_time, 3), round(total_operator_manual, 3),
                          round(taux_occ_homme, 1), round(taux_occ_machine, 1), round(pieces_heure, 1), round(pieces_jour, 1), code_temps]
            }).to_excel(writer, sheet_name="Résultats", index=False)
            pd.DataFrame({
                "Paramètre": ["Date", "Numéro OF", "Référence pièce", "Numéro machine", "PDC",
                             "Vitesse coupe", "Vitesse avance", "Coef JA", "Coef REPO", "CODE TEMPS"],
                "Valeur": [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), numero_of, reference_piece,
                          numero_machine, pdc, vitesse_coupe, vitesse_avance, round(coef_ja_total, 3), coef_repo, code_temps]
            }).to_excel(writer, sheet_name="Informations", index=False)
        out.seek(0)
        st.download_button("📥 Télécharger Excel", data=out,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with cb3:
        img_out = io.BytesIO()
        fig.savefig(img_out, format='png', bbox_inches="tight", dpi=150, facecolor='white')
        img_out.seek(0)
        st.download_button("🖼️ Télécharger PNG")
