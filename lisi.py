import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from datetime import datetime
import sqlite3
import json
import io
import os

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

DB_PATH = r"C:\Users\BFRANCOCANTERO\Downloads\Data\simogramme_data.db"
try:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    open(DB_PATH, 'a').close()
except Exception:
    DB_PATH = os.path.join(os.path.expanduser("~"), "simogramme_data.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS configurations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, numero_of TEXT, reference_piece TEXT, numero_machine TEXT,
                  pdc TEXT, vitesse_coupe TEXT, vitesse_avance TEXT,
                  coef_habilete REAL, coef_activite REAL, coef_conditions REAL,
                  coef_stabilite REAL, coef_ja_total REAL, coef_repo REAL,
                  heures_travail REAL, machines TEXT, donnees TEXT, resultats TEXT)''')
    # migration: add numero_of if old DB
    cols = [r[1] for r in conn.execute("PRAGMA table_info(configurations)").fetchall()]
    if "numero_of" not in cols:
        conn.execute("ALTER TABLE configurations ADD COLUMN numero_of TEXT DEFAULT ''")
    conn.commit()
    conn.close()

def save_configuration(data):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO configurations
                     (date, numero_of, reference_piece, numero_machine, pdc, vitesse_coupe,
                      vitesse_avance, coef_habilete, coef_activite, coef_conditions,
                      coef_stabilite, coef_ja_total, coef_repo, heures_travail,
                      machines, donnees, resultats)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
        st.error(f"Erreur sauvegarde: {e}")
        return False

def load_configurations():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM configurations ORDER BY date DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur chargement: {e}")
        return pd.DataFrame()

def delete_configuration(config_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('DELETE FROM configurations WHERE id = ?', (config_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erreur suppression: {e}")

init_database()

# ===================================================
# LOGIN
# ===================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## Connexion - Simogramme")
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Utilisateur")
        pwd  = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if user == "admin" and pwd == "1234":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()

# ===================================================
# SESSION STATE DEFAULTS
# ===================================================

if "machines" not in st.session_state:
    st.session_state["machines"] = ["M1"]
if "show_history" not in st.session_state:
    st.session_state["show_history"] = False
# This holds the last generated save_data dict so the save button can access it
if "pending_save" not in st.session_state:
    st.session_state["pending_save"] = None
# This holds a config dict to restore on next render
if "loaded_config" not in st.session_state:
    st.session_state["loaded_config"] = None
# Cached figure bytes for download
if "fig_bytes" not in st.session_state:
    st.session_state["fig_bytes"] = None
if "excel_bytes" not in st.session_state:
    st.session_state["excel_bytes"] = None

# ===================================================
# APPLY LOADED CONFIG before widgets render
# ===================================================

if st.session_state["loaded_config"] is not None:
    cfg = st.session_state["loaded_config"]
    st.session_state["num_of"]      = str(cfg.get("numero_of", "") or "")
    st.session_state["ref_piece"]   = str(cfg.get("reference_piece", "") or "")
    st.session_state["num_machine"] = str(cfg.get("numero_machine", "") or "")
    st.session_state["pdc"]         = str(cfg.get("pdc", "") or "")
    st.session_state["vit_coupe"]   = str(cfg.get("vitesse_coupe", "") or "")
    st.session_state["vit_avance"]  = str(cfg.get("vitesse_avance", "") or "")
    st.session_state["habilete"]    = float(cfg.get("coef_habilete", 0.0) or 0.0)
    st.session_state["activite"]    = float(cfg.get("coef_activite", 0.0) or 0.0)
    st.session_state["conditions"]  = float(cfg.get("coef_conditions", 0.0) or 0.0)
    st.session_state["stabilite"]   = float(cfg.get("coef_stabilite", 0.0) or 0.0)
    st.session_state["repo"]        = float(cfg.get("coef_repo", 1.0) or 1.0)
    st.session_state["heures"]      = float(cfg.get("heures_travail", 7.0) or 7.0)
    try:
        machines_r = json.loads(cfg.get("machines", '["M1"]'))
    except Exception:
        machines_r = ["M1"]
    st.session_state["machines"] = machines_r
    try:
        donnees_str = cfg.get("donnees", "")
        if donnees_str:
            df_all = pd.read_json(donnees_str)
            rename_map = {"TM":"TM 🕐","TT":"TT 🤖","TTM":"TTM ⚡","TR":"TR ☕","TZ":"TZ ⚫","TF":"TF 🎨"}
            df_all.rename(columns=rename_map, inplace=True)
            for m in machines_r:
                df_m = df_all[df_all["Sys"]==m].copy() if "Sys" in df_all.columns else df_all.copy()
                df_m.drop(columns=["Sys","Fin"], errors="ignore", inplace=True)
                df_m.reset_index(drop=True, inplace=True)
                st.session_state[f"preload_{m}"] = df_m
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
    numero_of       = st.text_input("Numéro OF",             key="num_of")
    reference_piece = st.text_input("Référence pièce",        key="ref_piece")
    numéro_machine  = st.text_input("Numéro de la machine",   key="num_machine")
    pdc             = st.text_input("PDC",                    key="pdc")
    vitesse_coupe   = st.text_input("Vitesse de coupe",       key="vit_coupe")
    vitesse_avance  = st.text_input("Vitesse d'avance",       key="vit_avance")

    st.markdown("## Coefficient JA (Jugement d'Allure)")
    st.info("Les coefficients sont des valeurs entre 0 et 1, la somme sera ajoutée à 1")
    coef_habilete   = st.number_input("Coefficient d'habileté",               min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="habilete")
    coef_activite   = st.number_input("Coefficient d'activité",               min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="activite")
    coef_conditions = st.number_input("Coefficient des conditions de travail", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="conditions")
    coef_stabilite  = st.number_input("Coefficient de stabilité",             min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="stabilite")
    coef_ja_total   = 1 + coef_habilete + coef_activite + coef_conditions + coef_stabilite
    st.metric("Coefficient JA total", f"{coef_ja_total:.2f}")

    st.markdown("## Coefficient de rendement opérateur")
    coef_repo      = st.number_input("Coefficient de rendement opérateur", min_value=1.0, max_value=5.0, value=1.0, step=0.05, key="repo")
    heures_travail = st.number_input("Heures de travail / jour",           min_value=1.0, max_value=24.0, value=7.0, step=0.5, key="heures")

    st.markdown("---")
    if st.button("➕ Ajouter machine"):
        new_m = f"M{len(st.session_state['machines'])+1}"
        st.session_state["machines"].append(new_m)
        st.rerun()

    st.markdown("---")
    st.markdown("## Historique")
    if st.button("📊 Voir historique"):
        st.session_state["show_history"] = True
        st.rerun()
    if st.button("❌ Fermer historique"):
        st.session_state["show_history"] = False
        st.rerun()
    st.caption(f"DB: {DB_PATH}")

# ===================================================
# HISTORIQUE
# ===================================================

if st.session_state["show_history"]:
    st.markdown("## Historique des simulations")
    df_hist = load_configurations()
    if not df_hist.empty:
        for _, row in df_hist.iterrows():
            of_v  = row.get("numero_of","") or "—"
            pdc_v = row.get("pdc","") or "—"
            m_v   = row.get("numero_machine","") or "—"
            d_v   = str(row.get("date",""))[:16]
            with st.expander(f"OF: {of_v}  |  PDC: {pdc_v}  |  Machine: {m_v}  |  {d_v}"):
                ci, cb = st.columns([3,1])
                with ci:
                    st.write(f"**Réf:** {row.get('reference_piece','')}  |  **Vc:** {row.get('vitesse_coupe','')}  |  **Vf:** {row.get('vitesse_avance','')}")
                    st.write(f"**JA:** {float(row.get('coef_ja_total',1)):.4f}  |  **REPO:** {row.get('coef_repo',1)}  |  **H/j:** {row.get('heures_travail',7)}")
                    try:
                        res = json.loads(row.get("resultats","{}"))
                        st.write(f"**Tc:** {round(res.get('temps_cycle_final',0),4)} s  |  "
                                 f"**P/h:** {round(res.get('pieces_heure',0),2)}  |  "
                                 f"**P/j:** {round(res.get('pieces_jour',0),2)}")
                    except Exception:
                        pass
                with cb:
                    if st.button("📂 Charger", key=f"load_{row['id']}"):
                        st.session_state["loaded_config"] = row.to_dict()
                        st.session_state["show_history"]  = False
                        st.rerun()
                    if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                        delete_configuration(int(row["id"]))
                        st.rerun()
    else:
        st.info("Aucune simulation sauvegardée")
        st.caption(f"Fichier DB: {DB_PATH}")
    st.markdown("---")

# ===================================================
# LÉGENDE
# ===================================================

st.markdown("### Légende des types de temps")
leg_cols = st.columns(5)
for col, (color, code, tip, label) in zip(leg_cols, [
    ("#ff8c00","TM","Temps Manuel - Opérateur seul","Temps manuel"),
    ("#1f4fff","TT","Temps Technologique - Machine seule","Temps machine"),
    ("#111827","TTM","Opérateur + machine simultanément","Temps parallèle"),
    ("#9ca3af","TR","Temps de Repos","Temps repos"),
    ("#e5e7eb","TZ","Temps Masqué - non productif","Temps masqué"),
]):
    with col:
        st.markdown(f'<div style="text-align:center;"><span class="legend-color" style="background-color:{color};"></span>'
                    f'<strong>{code}</strong><span class="info-icon" title="{tip}">?</span>'
                    f'<br><small>{label}</small></div>', unsafe_allow_html=True)
st.markdown("---")

# ===================================================
# TABLES — stable keys, no session_state writes per render
# ===================================================

BOOL_COLS = ["TM 🕐","TT 🤖","TTM ⚡","TR ☕","TZ ⚫","TF 🎨"]

def make_empty_df():
    return pd.DataFrame([{"Etape":"","Debut":0.0,"Duree":0.0,
        "TM 🕐":False,"TT 🤖":False,"TTM ⚡":False,
        "TR ☕":False,"TZ ⚫":False,"TF 🎨":False}])

dfs_calc = []

for m in st.session_state["machines"]:
    ct, cd = st.columns([6,1])
    with ct:
        st.subheader(f"Tableau {m}")
    with cd:
        if m != "M1":
            if st.button("🗑️", key=f"del_machine_{m}"):
                st.session_state["machines"].remove(m)
                st.session_state.pop(f"preload_{m}", None)
                st.rerun()
        else:
            st.write("")

    if f"preload_{m}" in st.session_state:
        initial = st.session_state.pop(f"preload_{m}")
        for bc in BOOL_COLS:
            if bc not in initial.columns:
                initial[bc] = False
            initial[bc] = initial[bc].fillna(False).astype(bool)
        for nc in ["Debut","Duree"]:
            if nc in initial.columns:
                initial[nc] = pd.to_numeric(initial[nc], errors='coerce').fillna(0.0)
    else:
        initial = make_empty_df()

    df_out = st.data_editor(
        initial,
        num_rows="dynamic",
        key=f"editor_{m}",
        use_container_width=True,
        column_config={
            "Etape":   st.column_config.TextColumn("Description étape", width="medium"),
            "Debut":   st.column_config.NumberColumn("Début (s)"),
            "Duree":   st.column_config.NumberColumn("Durée (s)"),
            "TM 🕐":  st.column_config.CheckboxColumn("TM"),
            "TT 🤖":  st.column_config.CheckboxColumn("TT"),
            "TTM ⚡": st.column_config.CheckboxColumn("TTM"),
            "TR ☕":  st.column_config.CheckboxColumn("TR"),
            "TZ ⚫":  st.column_config.CheckboxColumn("TZ"),
            "TF 🎨":  st.column_config.CheckboxColumn("TF"),
        }
    )

    df_c = df_out.copy()
    df_c.columns = [col.split(' ')[0] if ' ' in col else col for col in df_c.columns]
    df_c["Debut"] = pd.to_numeric(df_c["Debut"], errors='coerce').fillna(0)
    df_c["Duree"] = pd.to_numeric(df_c["Duree"], errors='coerce').fillna(0)
    df_c["Fin"]   = df_c["Debut"] + df_c["Duree"]
    df_c["Sys"]   = m
    dfs_calc.append(df_c)

edited_df = pd.concat(dfs_calc, ignore_index=True) if dfs_calc else pd.DataFrame()

# ===================================================
# GENERATE BUTTON
# ===================================================

if st.button("Générer le simogramme"):
    if edited_df.empty or edited_df["Duree"].sum() == 0:
        st.error("Veuillez saisir des données dans au moins une table")
        st.stop()

    # ---------- draw ----------
    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.set_frame_on(False)

    machines = st.session_state["machines"]
    y_pos = {}
    step=0.6; h=0.22; y_op=0
    for i,m in enumerate(machines):
        y_pos[m] = step*((i//2)+1) if i%2==0 else -step*((i//2)+1)

    max_x=tm_total=man_total=par_total=rep_total=msk_total=0
    COLORS={"TM":"#ff8c00","TT":"#1f4fff","TTM":"#111827","TR":"#9ca3af","TZ":"#e5e7eb"}

    def hatch(ax,rect,x,y,w,ht,sp=0.2):
        i=0
        while i<w+ht:
            ln,=ax.plot([x+i,x+i-ht],[y,y+ht],color="black",lw=0.6,alpha=0.6)
            ln.set_clip_path(rect); i+=sp

    for _,row in edited_df.iterrows():
        op=str(row["Etape"]) if pd.notna(row["Etape"]) else ""
        s=float(row["Debut"]); t=float(row["Duree"]); e=s+t; sy=str(row["Sys"])
        tm=bool(row.get("TM",False)); tt=bool(row.get("TT",False))
        ttm=bool(row.get("TTM",False)); tr=bool(row.get("TR",False))
        tz=bool(row.get("TZ",False)); tf=bool(row.get("TF",False))
        if tz:
            msk_total+=t
            r=Rectangle((s,y_op),t,h,facecolor=COLORS["TZ"],edgecolor="black",alpha=0.4)
            ax.add_patch(r)
            if tf and t>0: hatch(ax,r,s,y_op,t,h)
            max_x=max(max_x,e); continue
        if tt and not ttm:
            tm_total+=t; yp=y_pos.get(sy,0)
            r=Rectangle((s,yp),t,h,facecolor=COLORS["TT"],edgecolor="black")
            ax.add_patch(r)
            if tf and t>0: hatch(ax,r,s,yp,t,h)
            max_x=max(max_x,e)
        elif tm and not ttm:
            man_total+=t
            r=Rectangle((s,y_op),t,h,facecolor=COLORS["TM"],edgecolor="black")
            ax.add_patch(r)
            if tf and t>0: hatch(ax,r,s,y_op,t,h)
            max_x=max(max_x,e)
        elif ttm:
            tm_total+=t; par_total+=t; yp=y_pos.get(sy,0)
            r=Rectangle((s,y_op),t,yp-y_op,facecolor="#FFFFFF00",edgecolor="black")
            ax.add_patch(r)
            ax.plot([s,s+t],[y_op,yp],color="black",lw=1.5)
            if tf and t>0: hatch(ax,r,s,y_op,t,abs(yp-y_op))
            max_x=max(max_x,e)
        elif tr:
            rep_total+=t
            r=Rectangle((s,y_op),t,h,facecolor=COLORS["TR"],edgecolor="black",alpha=0.6)
            ax.add_patch(r)
            if tf and t>0: hatch(ax,r,s,y_op,t,h)
            max_x=max(max_x,e)
        if t>=0.5 and op not in ("","nan"):
            ax.text(s+t/2,y_op-0.18,op,ha="center",fontsize=9)

    for m,y in y_pos.items():
        ax.hlines(y,0,max_x,color="black",lw=1.5)
        ax.text(-1.5,y,m,ha="right",fontsize=14,fontweight="bold")
    ax.hlines(y_op,0,max_x,color="black",lw=2)
    ax.text(-1.5,y_op,"Opérateur",ha="right",fontsize=16,fontweight="bold")
    ax.legend(handles=[
        Patch(facecolor=COLORS["TM"],edgecolor='black',label='TM - Temps Manuel'),
        Patch(facecolor=COLORS["TT"],edgecolor='black',label='TT - Temps Machine'),
        Patch(facecolor=COLORS["TTM"],edgecolor='black',label='TTM - Temps Parallèle'),
        Patch(facecolor=COLORS["TR"],edgecolor='black',label='TR - Temps Repos'),
        Patch(facecolor=COLORS["TZ"],edgecolor='black',alpha=0.4,label='TZ - Temps Masqué'),
    ],loc='upper right',framealpha=0.9)
    ax.set_xlim(-2,max_x+2); ax.set_ylim(-1.5,1.5); ax.set_yticks([])
    ax.set_xlabel("Temps (secondes)",fontsize=12,fontweight="bold")
    ax.grid(axis="x",alpha=0.2,linestyle="--")
    plt.tight_layout()

    # ---------- calculs ----------
    hum = man_total+par_total+msk_total
    cyc_brut = tm_total+man_total
    man_ja   = man_total*coef_ja_total
    cyc_ja   = tm_total+man_ja
    cyc_fin  = cyc_ja*coef_repo
    taux_h   = (hum/cyc_brut*100) if cyc_brut>0 else 0
    taux_m   = (tm_total/cyc_brut*100) if cyc_brut>0 else 0
    p_h      = 3600/cyc_fin if cyc_fin>0 else 0
    p_j      = p_h*heures_travail

    pe=int(cyc_fin); fr=cyc_fin-pe; m5=round(fr*20)/20
    if m5>=1.0: m5=0.95; pe+=1
    fc=int(m5*100)
    code_temps=f"{pe}A{'01' if fc==0 else str(fc).zfill(2)}"

    # ---------- KPI ----------
    st.markdown("## Indicateurs de performance")
    def kpi(col,val,label,delta=""):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div>'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-delta">{delta}</div></div>',unsafe_allow_html=True)
    c1,c2,c3,c4,c5=st.columns(5)
    kpi(c1,f"{round(cyc_fin,2)} s","Temps cycle final",f"×{coef_repo} repo")
    kpi(c2,f"{round(cyc_fin/36,3)} UM","Temps cycle final",f"×{coef_repo} repo")
    kpi(c3,f"{round(tm_total,2)} s","Temps machine total",
        f"TT:{round(tm_total-par_total,4)}s TTM:{round(par_total,4)}s")
    kpi(c4,f"{round(man_total,2)} s","Temps manuel (TM)",
        f"×{round(coef_ja_total,2)} JA = {round(man_ja,4)} s")
    kpi(c5,f"{round(taux_h,2)} %","Taux occupation homme",f"TM+TTM+TZ = {round(hum,2)} s")
    c6,c7,c8,c9=st.columns(4)
    kpi(c6,f"{round(taux_m,2)} %","Taux occupation machine",f"TT+TTM = {round(tm_total,2)} s")
    kpi(c7,f"{round(p_h,2)}","Pièces / Heure")
    kpi(c8,f"{round(p_j,2)}","Pièces / Jour")
    kpi(c9,f"{round(rep_total,2)} s","Temps repos (TR)")

    with st.expander("Détail des calculs"):
        for k,v in [
            ("TM",f"{round(man_total,4)} s"),("TTM",f"{round(par_total,4)} s"),
            ("TT",f"{round(tm_total-par_total,4)} s"),("TR",f"{round(rep_total,4)} s"),
            ("TZ",f"{round(msk_total,4)} s"),("Temps humain total",f"{round(hum,4)} s"),
            ("Temps cycle brut",f"{round(cyc_brut,4)} s"),("Coef JA",f"{coef_ja_total:.4f}"),
            ("TM×JA",f"{round(man_ja,4)} s"),("Cycle avec JA",f"{round(cyc_ja,4)} s"),
            ("×REPO",f"×{coef_repo}"),("Temps cycle final",f"{round(cyc_fin,4)} s"),
            ("CODE TEMPS",code_temps),
        ]:
            st.write(f"**{k}:** {v}")

    st.success("Simogramme généré avec succès")
    st.pyplot(fig)

    # ---------- prepare Excel bytes ----------
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
        edited_df.to_excel(writer, sheet_name="Données", index=False)
        pd.DataFrame({
            "Métrique":["Temps cycle final (s)","Temps machine (s)","Temps manuel (s)",
                        "Taux occ. homme (%)","Taux occ. machine (%)","Pièces/h","Pièces/j","CODE TEMPS"],
            "Valeur":  [round(cyc_fin,4),round(tm_total,4),round(man_total,4),
                        round(taux_h,2),round(taux_m,2),round(p_h,2),round(p_j,2),code_temps]
        }).to_excel(writer, sheet_name="Résultats", index=False)
        pd.DataFrame({
            "Paramètre":["Date","OF","Réf. pièce","Machine","PDC","Vc","Vf","JA","REPO","CODE TEMPS"],
            "Valeur":   [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),numero_of,reference_piece,
                         numéro_machine,pdc,vitesse_coupe,vitesse_avance,
                         round(coef_ja_total,4),coef_repo,code_temps]
        }).to_excel(writer, sheet_name="Informations", index=False)
    excel_buf.seek(0)

    # ---------- prepare PNG bytes ----------
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches="tight", dpi=150, facecolor='white')
    img_buf.seek(0)

    # ---------- store everything in session_state ----------
    st.session_state["fig_bytes"]   = img_buf.getvalue()
    st.session_state["excel_bytes"] = excel_buf.getvalue()
    st.session_state["pending_save"] = {
        'date':            str(datetime.now()),
        'numero_of':       numero_of,
        'reference_piece': reference_piece,
        'numero_machine':  numéro_machine,
        'pdc':             pdc,
        'vitesse_coupe':   vitesse_coupe,
        'vitesse_avance':  vitesse_avance,
        'coef_habilete':   coef_habilete,
        'coef_activite':   coef_activite,
        'coef_conditions': coef_conditions,
        'coef_stabilite':  coef_stabilite,
        'coef_ja_total':   coef_ja_total,
        'coef_repo':       coef_repo,
        'heures_travail':  heures_travail,
        'machines':        json.dumps(st.session_state["machines"]),
        'donnees':         edited_df.to_json(),
        'resultats':       json.dumps({
            'total_machine_time':      tm_total,
            'total_operator_manual':   man_total,
            'total_operator_parallel': par_total,
            'total_masked_time':       msk_total,
            'total_repos_time':        rep_total,
            'temps_cycle_final':       cyc_fin,
            'pieces_heure':            p_h,
            'pieces_jour':             p_j,
        })
    }

# ===================================================
# ACTION BUTTONS — always visible after first generate
# ===================================================

if st.session_state["pending_save"] is not None:
    st.markdown("---")
    cb1, cb2, cb3 = st.columns(3)

    with cb1:
        if st.button("💾 Sauvegarder", key="save_btn"):
            if save_configuration(st.session_state["pending_save"]):
                st.success(f"✅ Sauvegardé !")

    with cb2:
        if st.session_state["excel_bytes"]:
            st.download_button(
                "📥 Télécharger Excel",
                data=st.session_state["excel_bytes"],
                file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with cb3:
        if st.session_state["fig_bytes"]:
            st.download_button(
                "🖼️ Télécharger PNG",
                data=st.session_state["fig_bytes"],
                file_name=f"simogramme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png"
            )
