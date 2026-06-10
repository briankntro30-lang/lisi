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

# ===================================================
# STYLE
# ===================================================

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
.info-icon:hover { background-color: #1f2937; }
.legend-color {
    display: inline-block; width: 20px; height: 20px;
    border-radius: 3px; margin-right: 5px; vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

# ===================================================
# LOGO
# ===================================================

LOGO_URL = "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0"
st.image(LOGO_URL, width=250)

# ===================================================
# DATABASE
# ===================================================

DB_PATH = os.path.join(os.path.expanduser("~"), "simogramme_data.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(DB_PATH)
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
# EMPTY TABLE HELPER
# ===================================================

EMPTY_ROW = {"Etape": "", "Debut": 0.0, "Duree": 0.0,
             "TM 🕐": False, "TT 🤖": False, "TTM ⚡": False,
             "TR ☕": False, "TZ ⚫": False, "TF 🎨": False}

def empty_table():
    return pd.DataFrame([EMPTY_ROW.copy()])

# ===================================================
# LOGIN
# ===================================================

def login():
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ===================================================
# SESSION STATE INIT
# ===================================================

if "machines" not in st.session_state:
    st.session_state["machines"] = ["M1"]

# table_data_M1, table_data_M2, etc. — persistent DataFrames per machine
for m in st.session_state["machines"]:
    if f"table_data_{m}" not in st.session_state:
        st.session_state[f"table_data_{m}"] = empty_table()

if "show_history" not in st.session_state:
    st.session_state["show_history"] = False

# ===================================================
# LOAD FROM HISTORY → SESSION STATE
# ===================================================

def load_into_session(config):
    """Restore a saved configuration into session_state so the UI reflects it."""
    # Sidebar fields — set via widget keys
    st.session_state["ref_piece"]   = config[2] or ""
    st.session_state["num_machine"] = config[3] or ""
    st.session_state["pdc"]         = config[4] or ""
    st.session_state["vit_coupe"]   = config[5] or ""
    st.session_state["vit_avance"]  = config[6] or ""
    st.session_state["habilete"]    = float(config[7])
    st.session_state["activite"]    = float(config[8])
    st.session_state["conditions"]  = float(config[9])
    st.session_state["stabilite"]   = float(config[10])
    st.session_state["repo"]        = float(config[12])
    st.session_state["heures"]      = float(config[13])

    # Machines list
    try:
        machines = json.loads(config[14].replace("'", '"'))
    except Exception:
        machines = ["M1"]
    st.session_state["machines"] = machines

    # Table data per machine — donnees is a JSON of the full concatenated df with "Sys" column
    try:
        df_all = pd.read_json(config[15])
        # Restore emoji column names if they were stripped
        rename = {"TM": "TM 🕐", "TT": "TT 🤖", "TTM": "TTM ⚡",
                  "TR": "TR ☕", "TZ": "TZ ⚫", "TF": "TF 🎨"}
        df_all.rename(columns=rename, inplace=True)

        for m in machines:
            df_m = df_all[df_all["Sys"] == m].copy()
            df_m.drop(columns=["Sys", "Fin"], errors="ignore", inplace=True)
            if df_m.empty:
                st.session_state[f"table_data_{m}"] = empty_table()
            else:
                df_m.reset_index(drop=True, inplace=True)
                st.session_state[f"table_data_{m}"] = df_m
    except Exception as e:
        st.error(f"Erreur restauration tables: {e}")
        for m in machines:
            st.session_state[f"table_data_{m}"] = empty_table()

# ===================================================
# SIDEBAR
# ===================================================

with st.sidebar:
    st.image(LOGO_URL, width=220)
    st.title("Configuration")

    st.markdown("## Informations production")
    numero_of      = st.text_input("Numéro OF",              key="num_of")
    reference_piece = st.text_input("Référence pièce",       key="ref_piece")
    numéro_machine  = st.text_input("Numéro de la machine",  key="num_machine")
    pdc             = st.text_input("PDC",                    key="pdc")
    vitesse_coupe   = st.text_input("Vitesse de coupe",       key="vit_coupe")
    vitesse_avance  = st.text_input("Vitesse d'avance",       key="vit_avance")

    st.markdown("## Coefficient JA (Jugement d'Allure)")
    st.info("Les coefficients sont des valeurs entre 0 et 1, la somme sera ajoutée à 1")
    coef_habilete   = st.number_input("Coefficient d'habileté",              min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="habilete")
    coef_activite   = st.number_input("Coefficient d'activité",              min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="activite")
    coef_conditions = st.number_input("Coefficient des conditions de travail", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="conditions")
    coef_stabilite  = st.number_input("Coefficient de stabilité",            min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="stabilite")
    coef_ja_total   = 1 + coef_habilete + coef_activite + coef_conditions + coef_stabilite
    st.metric("Coefficient JA total", f"{coef_ja_total:.2f}")

    st.markdown("## Coefficient de rendement opérateur")
    coef_repo     = st.number_input("Coefficient de rendement opérateur", min_value=1.00, max_value=5.00, value=1.00, step=0.05, key="repo")
    heures_travail = st.number_input("Heures de travail / jour",           min_value=1.0,  max_value=24.0, value=7.0,  step=0.5,  key="heures")

    st.markdown("---")
    if st.button("➕ Ajouter machine"):
        new_name = f"M{len(st.session_state['machines']) + 1}"
        st.session_state["machines"].append(new_name)
        st.session_state[f"table_data_{new_name}"] = empty_table()
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
        for config in configurations:
            label = f"Simulation du {config[1]}  |  Pièce: {config[2]}  |  Machine: {config[3]}"
            with st.expander(label):
                col_info, col_actions = st.columns([3, 1])
                with col_info:
                    st.write(f"**PDC:** {config[4]}  |  **Vc:** {config[5]}  |  **Vf:** {config[6]}")
                    st.write(f"**Coef JA:** {config[11]:.2f}  |  **Coef REPO:** {config[12]}  |  **Heures/jour:** {config[13]}")
                    try:
                        res = json.loads(config[16])
                        st.write(f"**Temps cycle final:** {round(res.get('temps_cycle_final', 0), 2)} s  |  "
                                 f"**Pièces/h:** {round(res.get('pieces_heure', 0), 1)}  |  "
                                 f"**Pièces/jour:** {round(res.get('pieces_jour', 0), 1)}")
                    except Exception:
                        pass
                with col_actions:
                    if st.button("📂 Charger", key=f"load_{config[0]}"):
                        load_into_session(config)
                        st.session_state["show_history"] = False
                        st.rerun()
                    if st.button("🗑️ Supprimer", key=f"del_hist_{config[0]}"):
                        delete_configuration(config[0])
                        st.success("Supprimé!")
                        st.rerun()
    else:
        st.info("Aucune simulation sauvegardée")
    st.markdown("---")

# ===================================================
# LÉGENDE
# ===================================================

def afficher_legende():
    st.markdown("### Légende des types de temps")
    col1, col2, col3, col4, col5 = st.columns(5)
    items = [
        (col1, "#ff8c00", "TM", "Temps Manuel - Opérateur seul",          "Temps manuel"),
        (col2, "#1f4fff", "TT", "Temps Technologique - Machine seule",     "Temps machine"),
        (col3, "#111827", "TTM","Temps de Travail en Manuel - simultané",  "Temps parallèle"),
        (col4, "#9ca3af", "TR", "Temps de Repos - Pause opérateur",        "Temps repos"),
        (col5, "#e5e7eb", "TZ", "Temps Masqué - Temps non productif",      "Temps masqué"),
    ]
    for col, color, code, tip, label in items:
        with col:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<span class="legend-color" style="background-color:{color};"></span>'
                f'<strong>{code}</strong>'
                f'<span class="info-icon" title="{tip}">?</span>'
                f'<br><small>{label}</small></div>',
                unsafe_allow_html=True
            )
    st.markdown("---")

# ===================================================
# TABLES — READ from session_state, WRITE back on change
# ===================================================

dfs = []

for m in st.session_state["machines"]:
    col_title, col_delete = st.columns([6, 1])
    with col_title:
        st.subheader(f"Tableau {m}")
    with col_delete:
        if m != "M1":
            if st.button("🗑️", key=f"del_machine_{m}"):
                st.session_state["machines"].remove(m)
                st.session_state.pop(f"table_data_{m}", None)
                st.rerun()
        else:
            st.write("")

    # Use persisted data as the starting value
    initial_df = st.session_state.get(f"table_data_{m}", empty_table())

    df = st.data_editor(
        initial_df,
        num_rows="dynamic",
        key=f"editor_{m}",
        use_container_width=True,
        column_config={
            "Etape":   st.column_config.TextColumn("Description étape", width="medium"),
            "Debut":   st.column_config.NumberColumn("Début (s)",   format="%.1f"),
            "Duree":   st.column_config.NumberColumn("Durée (s)",   format="%.1f"),
            "TM 🕐":  st.column_config.CheckboxColumn("TM"),
            "TT 🤖":  st.column_config.CheckboxColumn("TT"),
            "TTM ⚡": st.column_config.CheckboxColumn("TTM"),
            "TR ☕":  st.column_config.CheckboxColumn("TR"),
            "TZ ⚫":  st.column_config.CheckboxColumn("TZ"),
            "TF 🎨":  st.column_config.CheckboxColumn("TF"),
        }
    )

    # Persist whatever the user typed/edited
    st.session_state[f"table_data_{m}"] = df.copy()

    # Normalize column names (strip emoji) for processing
    df_copy = df.copy()
    df_copy.columns = [col.split(' ')[0] if ' ' in col else col for col in df_copy.columns]
    df_copy["Debut"] = pd.to_numeric(df_copy["Debut"], errors='coerce').fillna(0)
    df_copy["Duree"] = pd.to_numeric(df_copy["Duree"], errors='coerce').fillna(0)
    df_copy["Fin"]   = df_copy["Debut"] + df_copy["Duree"]
    df_copy["Sys"]   = m
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
    if edited_df.empty or edited_df["Duree"].sum() == 0:
        st.error("Veuillez saisir des données dans au moins une table")
        st.stop()

    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.set_frame_on(False)

    machines   = st.session_state["machines"]
    y_positions = {}
    step = 0.6
    h    = 0.22
    y_op = 0

    for i, m in enumerate(machines):
        y_positions[m] = step * ((i // 2) + 1) if i % 2 == 0 else -step * ((i // 2) + 1)

    max_x = 0
    total_machine_time      = 0
    total_operator_manual   = 0
    total_operator_parallel = 0
    total_repos_time        = 0
    total_masked_time       = 0

    COLORS = {"TM": "#ff8c00", "TT": "#1f4fff", "TTM": "#111827", "TR": "#9ca3af", "TZ": "#e5e7eb"}

    def draw_hatch(ax, rect, x, y, w, ht, spacing=0.2):
        i = 0
        while i < w + ht:
            ln, = ax.plot([x + i, x + i - ht], [y, y + ht], color="black", linewidth=0.6, alpha=0.6)
            ln.set_clip_path(rect)
            i += spacing

    for _, row in edited_df.iterrows():
        op    = str(row["Etape"]) if pd.notna(row["Etape"]) else ""
        start = float(row["Debut"])
        temps = float(row["Duree"])
        end   = start + temps
        sys   = str(row["Sys"])

        tm  = bool(row.get("TM",  False))
        tt  = bool(row.get("TT",  False))
        ttm = bool(row.get("TTM", False))
        tr  = bool(row.get("TR",  False))
        tz  = bool(row.get("TZ",  False))
        tf  = bool(row.get("TF",  False))

        if tz:
            total_masked_time += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TZ"], edgecolor="black", alpha=0.4)
            ax.add_patch(rect)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
            continue

        if tt and not ttm:
            total_machine_time += temps
            rect = Rectangle((start, y_positions.get(sys, 0)), temps, h, facecolor=COLORS["TT"], edgecolor="black")
            ax.add_patch(rect)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_positions.get(sys, 0), temps, h)
            max_x = max(max_x, end)
        elif tm and not ttm:
            total_operator_manual += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TM"], edgecolor="black")
            ax.add_patch(rect)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
        elif ttm:
            total_machine_time      += temps
            total_operator_parallel += temps
            y_m = y_positions.get(sys, 0)
            rect = Rectangle((start, y_op), temps, y_m - y_op, facecolor="#FFFFFF00", edgecolor="black")
            ax.add_patch(rect)
            ax.plot([start, start + temps], [y_op, y_m], color="black", linewidth=1.5)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_op, temps, abs(y_m - y_op))
            max_x = max(max_x, end)
        elif tr:
            total_repos_time += temps
            rect = Rectangle((start, y_op), temps, h, facecolor=COLORS["TR"], edgecolor="black", alpha=0.6)
            ax.add_patch(rect)
            if tf and temps > 0:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)

        if temps >= 0.5 and op not in ("", "nan"):
            ax.text(start + temps / 2, y_op - 0.18, op, ha="center", fontsize=9)

    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")

    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")

    legend_elements = [
        Patch(facecolor=COLORS["TM"], edgecolor='black', label='TM - Temps Manuel'),
        Patch(facecolor=COLORS["TT"], edgecolor='black', label='TT - Temps Machine'),
        Patch(facecolor=COLORS["TTM"], edgecolor='black', label='TTM - Temps Parallèle'),
        Patch(facecolor=COLORS["TR"], edgecolor='black', label='TR - Temps Repos'),
        Patch(facecolor=COLORS["TZ"], edgecolor='black', alpha=0.4, label='TZ - Temps Masqué'),
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

    temps_humain_total_reel  = total_operator_manual + total_operator_parallel + total_masked_time
    temps_cycle_sans_coef    = total_machine_time + total_operator_manual
    temps_manuel_ajuste_ja   = total_operator_manual * coef_ja_total
    temps_cycle_avec_ja      = total_machine_time + temps_manuel_ajuste_ja
    temps_cycle_final        = temps_cycle_avec_ja * coef_repo

    taux_occupation_homme    = (temps_humain_total_reel / temps_cycle_sans_coef * 100) if temps_cycle_sans_coef > 0 else 0
    taux_occupation_machine  = (total_machine_time / temps_cycle_sans_coef * 100)      if temps_cycle_sans_coef > 0 else 0
    pieces_heure             = 3600 / temps_cycle_final if temps_cycle_final > 0 else 0
    pieces_jour              = pieces_heure * heures_travail

    # Code temps (Excel uniquement)
    partie_entiere = int(temps_cycle_final)
    fraction       = temps_cycle_final - partie_entiere
    multiple_5     = round(fraction * 20) / 20
    if multiple_5 >= 1.0:
        multiple_5 = 0.95
        partie_entiere += 1
    fraction_code = int(multiple_5 * 100)
    fraction_str  = "01" if fraction_code == 0 else str(fraction_code).zfill(2)
    code_temps    = f"{partie_entiere}A{fraction_str}"

    # ===================================================
    # KPI
    # ===================================================

    st.markdown("## Indicateurs de performance")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(temps_cycle_final,2)} s</div><div class="metric-label">Temps cycle final</div><div class="metric-delta">×{coef_repo} repo</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(temps_cycle_final/36,3)} UM</div><div class="metric-label">Temps cycle final</div><div class="metric-delta">×{coef_repo} repo</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(total_machine_time,2)} s</div><div class="metric-label">Temps machine total</div><div class="metric-delta">TT: {round(total_machine_time-total_operator_parallel,2)} s, TTM: {round(total_operator_parallel,2)} s</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(total_operator_manual,2)} s</div><div class="metric-label">Temps manuel (TM)</div><div class="metric-delta">×{round(coef_ja_total,2)} JA = {round(temps_manuel_ajuste_ja,2)} s</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(taux_occupation_homme,1)} %</div><div class="metric-label">Taux occupation homme</div><div class="metric-delta">TM+TTM+TZ = {round(temps_humain_total_reel,1)} s</div></div>', unsafe_allow_html=True)

    col6, col7, col8, col9 = st.columns(4)
    with col6:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(taux_occupation_machine,1)} %</div><div class="metric-label">Taux occupation machine</div><div class="metric-delta">TT+TTM = {round(total_machine_time,1)} s</div></div>', unsafe_allow_html=True)
    with col7:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(pieces_heure,1)}</div><div class="metric-label">Pièces / Heure</div></div>', unsafe_allow_html=True)
    with col8:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(pieces_jour,1)}</div><div class="metric-label">Pièces / Jour</div></div>', unsafe_allow_html=True)
    with col9:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{round(total_repos_time,2)} s</div><div class="metric-label">Temps repos (TR)</div></div>', unsafe_allow_html=True)

    with st.expander("Détail des calculs"):
        st.write(f"**TM (opérateur seul):** {round(total_operator_manual,2)} s")
        st.write(f"**TTM (parallèle):** {round(total_operator_parallel,2)} s")
        st.write(f"**TT (machine seul):** {round(total_machine_time-total_operator_parallel,2)} s")
        st.write(f"**TR (repos):** {round(total_repos_time,2)} s")
        st.write(f"**TZ (masqué):** {round(total_masked_time,2)} s")
        st.write(f"**Temps humain total réel:** {round(temps_humain_total_reel,2)} s")
        st.write(f"**Temps cycle sans coefficients:** {round(temps_cycle_sans_coef,2)} s")
        st.write(f"**Coefficient JA:** {coef_ja_total:.2f}")
        st.write(f"**TM corrigé JA:** {round(total_operator_manual,2)} × {coef_ja_total:.2f} = {round(temps_manuel_ajuste_ja,2)} s")
        st.write(f"**Temps cycle avec JA:** {round(temps_cycle_avec_ja,2)} s")
        st.write(f"**Coefficient REPO:** ×{coef_repo}")
        st.write(f"**Temps cycle final:** {round(temps_cycle_final,2)} s")
        st.write(f"**CODE TEMPS:** {code_temps}")

    st.success("Simogramme généré avec succès")
    st.pyplot(fig)

    # ===================================================
    # BOUTONS
    # ===================================================

    # Build donnees JSON from current session tables (with emoji column names intact)
    all_frames = []
    for m in st.session_state["machines"]:
        df_m = st.session_state.get(f"table_data_{m}", empty_table()).copy()
        # strip emoji for storage consistency
        df_m.columns = [col.split(' ')[0] if ' ' in col else col for col in df_m.columns]
        df_m["Fin"] = pd.to_numeric(df_m["Debut"], errors='coerce').fillna(0) + pd.to_numeric(df_m["Duree"], errors='coerce').fillna(0)
        df_m["Sys"] = m
        all_frames.append(df_m)
    donnees_df = pd.concat(all_frames, ignore_index=True)

    save_data = {
        'date':             str(datetime.now()),
        'reference_piece':  reference_piece,
        'numero_machine':   numéro_machine,
        'pdc':              pdc,
        'vitesse_coupe':    vitesse_coupe,
        'vitesse_avance':   vitesse_avance,
        'coef_habilete':    coef_habilete,
        'coef_activite':    coef_activite,
        'coef_conditions':  coef_conditions,
        'coef_stabilite':   coef_stabilite,
        'coef_ja_total':    coef_ja_total,
        'coef_repo':        coef_repo,
        'heures_travail':   heures_travail,
        'machines':         json.dumps(st.session_state["machines"]),
        'donnees':          donnees_df.to_json(),
        'resultats':        json.dumps({
            'total_machine_time':      total_machine_time,
            'total_operator_manual':   total_operator_manual,
            'total_operator_parallel': total_operator_parallel,
            'total_masked_time':       total_masked_time,
            'total_repos_time':        total_repos_time,
            'temps_cycle_final':       temps_cycle_final,
            'pieces_heure':            pieces_heure,
            'pieces_jour':             pieces_jour,
        })
    }

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("💾 Sauvegarder", key="save_btn"):
            if save_configuration(save_data):
                st.success("✅ Simulation sauvegardée!")

    with col_btn2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            donnees_df.to_excel(writer, sheet_name="Données", index=False)
            pd.DataFrame({
                "Métrique": ["Temps cycle final (s)", "Temps machine total (s)", "Temps manuel TM (s)",
                             "Taux occupation homme (%)", "Taux occupation machine (%)",
                             "Pièces / Heure", "Pièces / Jour", "CODE TEMPS"],
                "Valeur":   [round(temps_cycle_final,2), round(total_machine_time,2),
                             round(total_operator_manual,2), round(taux_occupation_homme,1),
                             round(taux_occupation_machine,1), round(pieces_heure,1),
                             round(pieces_jour,1), code_temps]
            }).to_excel(writer, sheet_name="Résultats", index=False)
            pd.DataFrame({
                "Paramètre": ["Date","Référence pièce","Numéro machine","PDC",
                              "Vitesse coupe","Vitesse avance","Coefficient JA","Coefficient REPO","CODE TEMPS"],
                "Valeur":    [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reference_piece,
                              numéro_machine, pdc, vitesse_coupe, vitesse_avance,
                              round(coef_ja_total,2), coef_repo, code_temps]
            }).to_excel(writer, sheet_name="Informations", index=False)
        output.seek(0)
        st.download_button(
            label="📥 Télécharger Excel",
            data=output,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_btn3:
        img_output = io.BytesIO()
        fig.savefig(img_output, format='png', bbox_inches="tight", dpi=150, facecolor='white')
        img_output.seek(0)
        st.download_button(
            label="🖼️ Télécharger PNG",
            data=img_output,
            file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )
