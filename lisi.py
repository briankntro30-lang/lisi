import streamlit as st
from datetime import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Simogramme - Gestion de Production",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================
# STYLE CSS GLOBAL
# ===================================================

st.markdown("""
<style>
    /* Reset et styles de base */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Style des titres */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Style des métriques */
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Style des boutons */
    .stButton > button {
        background-color: #1f2937;
        color: white;
        border-radius: 8px;
        height: 45px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #374151;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Style des dataframes */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Sidebar améliorée */
    .css-1d391kg {
        background-color: white;
        border-right: 1px solid #e5e7eb;
    }
    
    /* Cards pour les KPIs */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .kpi-card h3 {
        color: white;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    
    .kpi-card .value {
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ===================================================
# INITIALISATION SESSION STATE
# ===================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "machines" not in st.session_state:
    st.session_state["machines"] = ["Machine 1"]

if "historique" not in st.session_state:
    st.session_state["historique"] = []

if "current_config" not in st.session_state:
    st.session_state["current_config"] = {
        "reference_piece": "",
        "numéro_machine": "",
        "pdc": "",
        "vitesse_coupe": "",
        "vitesse_avance": "",
        "coef_repo": 0.85,
        "heures_travail": 7.0
    }

if "simulations" not in st.session_state:
    st.session_state["simulations"] = []

# ===================================================
# LOGO
# ===================================================

LOGO_URL = "https://th.bing.com/th/id/R.0a38b5bebde3a9c6b070c0ad42c162d3?rik=U63XkDE5XvdVCg&riu=http%3a%2f%2fbandemfg.com%2fimages%2ffooter-logo.png&ehk=NquqcRNMxNTQUwJ5DrA7Sz1HroAbEmUUL7LemhCeyCQ%3d&risl=&pid=ImgRaw&r=0"

# ===================================================
# PAGE D'ACCUEIL
# ===================================================

def show_home():
    """Affiche la page d'accueil avec dashboard"""
    
    st.title("🏭 Dashboard Production")
    
    # Statistiques rapides
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <h3>📊 Simulations</h3>
            <div class="value">{}</div>
        </div>
        """.format(len(st.session_state["simulations"])), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <h3>⚙️ Machines</h3>
            <div class="value">{}</div>
        </div>
        """.format(len(st.session_state["machines"])), unsafe_allow_html=True)
    
    with col3:
        total_cycles = sum([s.get("temps_cycle", 0) for s in st.session_state["simulations"]])
        st.markdown("""
        <div class="kpi-card">
            <h3>⏱️ Temps total</h3>
            <div class="value">{:.0f}s</div>
        </div>
        """.format(total_cycles), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <h3>📈 Productivité</h3>
            <div class="value">{}%</div>
        </div>
        """.format("85"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Dernières simulations
    st.subheader("📋 Dernières simulations")
    
    if st.session_state["simulations"]:
        df_recent = pd.DataFrame(st.session_state["simulations"][-5:])
        df_recent = df_recent[["date", "reference_piece", "temps_cycle", "pieces_jour", "taux_machine"]]
        df_recent.columns = ["Date", "Référence", "Temps cycle (s)", "Pièces/jour", "Taux machine (%)"]
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("Aucune simulation effectuée. Allez dans l'onglet Simogramme pour créer votre première simulation.")
    
    # Graphique d'activité
    if len(st.session_state["simulations"]) > 1:
        st.subheader("📈 Évolution de la productivité")
        
        df_activity = pd.DataFrame(st.session_state["simulations"])
        df_activity["date"] = pd.to_datetime(df_activity["date"])
        
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(df_activity["date"], df_activity["pieces_jour"], marker='o', linewidth=2, color='#1f2937')
        ax.set_xlabel("Date")
        ax.set_ylabel("Pièces/jour")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

# ===================================================
# LOGIN
# ===================================================

def login():
    """Gère l'authentification"""
    
    st.markdown("## 🔐 Connexion - Simogramme")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image(LOGO_URL, width=250)
        st.markdown("---")
        
        user = st.text_input("👤 Utilisateur", placeholder="admin")
        pwd = st.text_input("🔒 Mot de passe", type="password", placeholder="••••")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("Se connecter", use_container_width=True):
                if user == "admin" and pwd == "1234":
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        st.markdown("---")
        st.info("💡 Informations de démonstration :\n- Utilisateur: admin\n- Mot de passe: 1234")

# ===================================================
# SIDEBAR (visible après login)
# ===================================================

def show_sidebar():
    """Affiche la sidebar avec navigation"""
    
    with st.sidebar:
        st.image(LOGO_URL, width=200)
        st.markdown("---")
        
        # Navigation
        st.markdown("## 📍 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.switch_page("main.py")
        
        if st.button("📊 Simogramme", use_container_width=True):
            st.switch_page("pages/1_Simogramme.py")
        
        if st.button("📜 Historique", use_container_width=True):
            st.switch_page("pages/2_Historique.py")
        
        if st.button("⚙️ Configuration", use_container_width=True):
            st.switch_page("pages/3_Configuration.py")
        
        st.markdown("---")
        
        # Informations session
        st.markdown("## ℹ️ Session")
        st.write(f"**Utilisateur:** Admin")
        st.write(f"**Simulations:** {len(st.session_state['simulations'])}")
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

# ===================================================
# MAIN
# ===================================================

if not st.session_state["logged_in"]:
    login()
    st.stop()

# Afficher la sidebar
show_sidebar()

# Page d'accueil
show_home()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime
import os

# Créer le dossier exports s'il n'existe pas
if not os.path.exists("exports"):
    os.makedirs("exports")

st.set_page_config(
    page_title="Simogramme - Création",
    page_icon="📊",
    layout="wide"
)

# ===================================================
# IMPORT DES FONCTIONS UTILITAIRES
# ===================================================

def generate_simogramme(df, machines, config):
    """Génère le graphique du simogramme"""
    
    fig, ax = plt.subplots(figsize=(18, 6))
    
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
            line, = ax.plot([x + i, x + i - h], [y, y + h], 
                          color="black", linewidth=0.6, alpha=0.6)
            line.set_clip_path(rect)
            i += spacing
    
    for _, row in df.iterrows():
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
            rect = Rectangle((start, y_positions[sys]), temps, h,
                           facecolor=COLORS["TT"], edgecolor="black")
            ax.add_patch(rect)
            if tf:
                draw_hatch(ax, rect, start, y_positions[sys], temps, h)
            max_x = max(max_x, end)
        
        elif tm:
            total_operator_time += temps
            rect = Rectangle((start, y_op), temps, h,
                           facecolor=COLORS["TM"], edgecolor="black")
            ax.add_patch(rect)
            if tf:
                draw_hatch(ax, rect, start, y_op, temps, h)
            max_x = max(max_x, end)
        
        elif ttm:
            total_operator_time += temps
            total_machine_time += temps
            rect = Rectangle((start, y_op), temps, y_positions[sys] - y_op,
                           facecolor="#FFFFFF00", edgecolor="black")
            ax.add_patch(rect)
            ax.plot([start, start + temps], [y_op, y_positions[sys]], color="black")
            max_x = max(max_x, end)
        
        elif tz:
            total_wait_time += temps
            rect = Rectangle((start, y_op), temps, h,
                           facecolor=COLORS["TZ"], edgecolor="black", alpha=0.6)
            ax.add_patch(rect)
            max_x = max(max_x, end)
        
        if temps >= 0.5:
            ax.text(start + temps/2, y_op - 0.18, op, ha="center", fontsize=9)
    
    # Lignes machines
    for m, y in y_positions.items():
        ax.hlines(y, 0, max_x, color="black", linewidth=1.5)
        ax.text(-1.5, y, m, ha="right", fontsize=14, fontweight="bold")
    
    ax.hlines(y_op, 0, max_x, color="black", linewidth=2)
    ax.text(-1.5, y_op, "Opérateur", ha="right", fontsize=16, fontweight="bold")
    
    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    
    # Calcul des KPIs
    temps_cycle = max_x
    temps_disponible = config["heures_travail"] * 3600
    pieces_jour = (temps_disponible / temps_cycle) * config["coef_repo"] if temps_cycle > 0 else 0
    taux_homme = total_operator_time / temps_cycle if temps_cycle > 0 else 0
    taux_machine = total_machine_time / temps_cycle if temps_cycle > 0 else 0
    
    kpis = {
        "temps_cycle": temps_cycle,
        "total_machine_time": total_machine_time,
        "total_operator_time": total_operator_time,
        "total_wait_time": total_wait_time,
        "taux_homme": taux_homme,
        "taux_machine": taux_machine,
        "pieces_jour": pieces_jour
    }
    
    return fig, kpis

# ===================================================
# PAGE PRINCIPALE
# ===================================================

st.title("📊 Simogramme - Création")
st.markdown("Créez et visualisez votre simogramme en temps réel")

# Configuration dans la sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuration production")
    
    reference_piece = st.text_input("Référence pièce", 
                                   value=st.session_state["current_config"]["reference_piece"])
    numéro_machine = st.text_input("Numéro de la machine",
                                  value=st.session_state["current_config"]["numéro_machine"])
    pdc = st.text_input("PDC", value=st.session_state["current_config"]["pdc"])
    vitesse_coupe = st.text_input("Vitesse de coupe",
                                 value=st.session_state["current_config"]["vitesse_coupe"])
    vitesse_avance = st.text_input("Vitesse d'avance",
                                  value=st.session_state["current_config"]["vitesse_avance"])
    
    coef_repo = st.number_input("Coefficient rendement",
                               min_value=0.1, max_value=1.0,
                               value=st.session_state["current_config"]["coef_repo"],
                               step=0.05)
    
    heures_travail = st.number_input("Heures de travail / jour",
                                    min_value=1.0, max_value=24.0,
                                    value=st.session_state["current_config"]["heures_travail"],
                                    step=0.5)
    
    # Sauvegarde de la config
    st.session_state["current_config"].update({
        "reference_piece": reference_piece,
        "numéro_machine": numéro_machine,
        "pdc": pdc,
        "vitesse_coupe": vitesse_coupe,
        "vitesse_avance": vitesse_avance,
        "coef_repo": coef_repo,
        "heures_travail": heures_travail
    })
    
    st.markdown("---")
    
    # Gestion des machines
    st.markdown("## 🏭 Machines")
    
    if st.button("➕ Ajouter machine", use_container_width=True):
        st.session_state["machines"].append(f"Machine {len(st.session_state['machines'])+1}")
        st.rerun()
    
    for machine in st.session_state["machines"]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"- {machine}")
        with col2:
            if machine != "Machine 1":
                if st.button("🗑️", key=f"del_{machine}"):
                    st.session_state["machines"].remove(machine)
                    st.rerun()

# ===================================================
# CRÉATION DU TABLEAU DES TÂCHES
# ===================================================

st.markdown("## 📝 Définition des tâches")

# Création des dataframes pour chaque machine
dfs = []
tabs = st.tabs(st.session_state["machines"])

for idx, machine in enumerate(st.session_state["machines"]):
    with tabs[idx]:
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
            key=f"df_{machine}",
            use_container_width=True,
            column_config={
                "Etape": st.column_config.TextColumn("Étape", required=True),
                "Début": st.column_config.NumberColumn("Début (s)", min_value=0.0),
                "Durée": st.column_config.NumberColumn("Durée (s)", min_value=0.0, required=True),
                "TT": st.column_config.CheckboxColumn("Temps Machine"),
                "TM": st.column_config.CheckboxColumn("Temps Opérateur"),
                "TTM": st.column_config.CheckboxColumn("Temps Machine + Opérateur"),
                "TR": st.column_config.CheckboxColumn("Temps Repos"),
                "TF": st.column_config.CheckboxColumn("Hachures")
            }
        )
        
        # Calcul automatique des débuts
        for i in range(1, len(df)):
            prev_debut = float(df.loc[i-1, "Début"])
            prev_duree = float(df.loc[i-1, "Durée"])
            auto_debut = prev_debut + prev_duree
            if df.loc[i, "Début"] == 0 or pd.isna(df.loc[i, "Début"]):
                df.loc[i, "Début"] = auto_debut
        
        df["Fin"] = df["Début"] + df["Durée"]
        df["Sys"] = machine
        dfs.append(df)

# ===================================================
# GÉNÉRATION DU SIMOGRAMME
# ===================================================

if dfs:
    edited_df = pd.concat(dfs, ignore_index=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Générer le simogramme", use_container_width=True):
            with st.spinner("Génération en cours..."):
                fig, kpis = generate_simogramme(edited_df, st.session_state["machines"], 
                                               st.session_state["current_config"])
                
                # Affichage des KPIs
                st.markdown("## 📈 Indicateurs de performance")
                
                kpi_cols = st.columns(4)
                with kpi_cols[0]:
                    st.metric("⏱️ Temps cycle", f"{round(kpis['temps_cycle'], 2)} s")
                with kpi_cols[1]:
                    st.metric("🤖 Temps machine", f"{round(kpis['total_machine_time'], 2)} s")
                with kpi_cols[2]:
                    st.metric("👤 Temps opérateur", f"{round(kpis['total_operator_time'], 2)} s")
                with kpi_cols[3]:
                    st.metric("⏸️ Attente", f"{round(kpis['total_wait_time'], 2)} s")
                
                kpi_cols2 = st.columns(3)
                with kpi_cols2[0]:
                    st.metric("👥 Taux Homme", f"{round(kpis['taux_homme'] * 100, 1)} %")
                with kpi_cols2[1]:
                    st.metric("🏭 Taux Machine", f"{round(kpis['taux_machine'] * 100, 1)} %")
                with kpi_cols2[2]:
                    st.metric("📦 Pièces / Jour", f"{round(kpis['pieces_jour'], 1)}")
                
                # Affichage du graphique
                st.markdown("## 🎯 Visualisation du simogramme")
                st.pyplot(fig)
                
                # Sauvegarde dans l'historique
                simulation = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reference_piece": reference_piece,
                    "numéro_machine": numéro_machine,
                    "pdc": pdc,
                    "temps_cycle": kpis['temps_cycle'],
                    "total_machine_time": kpis['total_machine_time'],
                    "total_operator_time": kpis['total_operator_time'],
                    "total_wait_time": kpis['total_wait_time'],
                    "taux_homme": kpis['taux_homme'] * 100,
                    "taux_machine": kpis['taux_machine'] * 100,
                    "pieces_jour": kpis['pieces_jour'],
                    "coef_repo": coef_repo,
                    "heures_travail": heures_travail,
                    "machines": len(st.session_state["machines"])
                }
                
                st.session_state["simulations"].append(simulation)
                
                # Sauvegarde en CSV
                df_historique = pd.DataFrame(st.session_state["simulations"])
                df_historique.to_csv("exports/historique.csv", index=False, encoding='utf-8')
                
                st.success("✅ Simogramme généré et sauvegardé avec succès!")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Simogramme - Historique",
    page_icon="📜",
    layout="wide"
)

# ===================================================
# CHARGEMENT DES DONNÉES
# ===================================================

def load_historique():
    """Charge l'historique des simulations"""
    if st.session_state["simulations"]:
        return pd.DataFrame(st.session_state["simulations"])
    return pd.DataFrame()

# ===================================================
# FONCTIONS D'ANALYSE
# ===================================================

def analyze_performance(df):
    """Analyse les performances"""
    
    if df.empty:
        return None
    
    stats = {
        "total_simulations": len(df),
        "avg_temps_cycle": df["temps_cycle"].mean(),
        "avg_pieces_jour": df["pieces_jour"].mean(),
        "best_pieces_jour": df["pieces_jour"].max(),
        "avg_taux_machine": df["taux_machine"].mean(),
        "best_taux_machine": df["taux_machine"].max()
    }
    
    return stats

def plot_trend(df, column, title):
    """Crée un graphique de tendance"""
    if df.empty:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[column],
        mode='lines+markers',
        name=column,
        line=dict(color='#1f2937', width=2),
        marker=dict(size=8, color='#ff8c00')
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=column,
        template="plotly_white",
        height=400
    )
    
    return fig

# ===================================================
# PAGE PRINCIPALE
# ===================================================

st.title("📜 Historique des simulations")
st.markdown("Consultez et analysez l'historique de vos simulations")

# Chargement des données
df_historique = load_historique()

# ===================================================
# STATISTIQUES GLOBALES
# ===================================================

if not df_historique.empty:
    stats = analyze_performance(df_historique)
    
    st.markdown("## 📊 Statistiques globales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total simulations", stats["total_simulations"])
    with col2:
        st.metric("Temps cycle moyen", f"{stats['avg_temps_cycle']:.1f} s")
    with col3:
        st.metric("Productivité moyenne", f"{stats['avg_pieces_jour']:.0f} pièces/jour")
    with col4:
        st.metric("Meilleur taux machine", f"{stats['best_taux_machine']:.1f} %")
    
    st.markdown("---")
    
    # ===================================================
    # FILTRES
    # ===================================================
    
    st.markdown("## 🔍 Filtres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_range = st.date_input(
            "Période",
            value=(datetime.now() - timedelta(days=30), datetime.now())
        )
    
    with col2:
        if len(date_range) == 2:
            mask = (pd.to_datetime(df_historique["date"]).dt.date >= date_range[0]) & \
                   (pd.to_datetime(df_historique["date"]).dt.date <= date_range[1])
            df_filtered = df_historique[mask]
        else:
            df_filtered = df_historique
    
    with col3:
        if "reference_piece" in df_filtered.columns:
            references = ["Toutes"] + df_filtered["reference_piece"].unique().tolist()
            selected_ref = st.selectbox("Référence pièce", references)
            if selected_ref != "Toutes":
                df_filtered = df_filtered[df_filtered["reference_piece"] == selected_ref]
    
    # ===================================================
    # TABLEAU DES SIMULATIONS
    # ===================================================
    
    st.markdown("## 📋 Liste des simulations")
    
    display_df = df_filtered.copy()
    if not display_df.empty:
        display_df = display_df[["date", "reference_piece", "numéro_machine", 
                                 "temps_cycle", "pieces_jour", "taux_machine", "taux_homme"]]
        display_df.columns = ["Date", "Référence", "Machine", "Temps cycle (s)", 
                              "Pièces/jour", "Taux machine (%)", "Taux homme (%)"]
        
        st.dataframe(display_df, use_container_width=True, height=300)
    
    # ===================================================
    # GRAPHIQUES D'ANALYSE
    # ===================================================
    
    if not df_filtered.empty:
        st.markdown("## 📈 Analyses et tendances")
        
        tab1, tab2, tab3 = st.tabs(["📊 Tendances", "📉 Corrélations", "📋 Détails"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_temps = plot_trend(df_filtered, "temps_cycle", "Évolution du temps de cycle")
                if fig_temps:
                    st.plotly_chart(fig_temps, use_container_width=True)
            
            with col2:
                fig_productivite = plot_trend(df_filtered, "pieces_jour", "Évolution de la productivité")
                if fig_productivite:
                    st.plotly_chart(fig_productivite, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Corrélation temps cycle / productivité
                fig_corr = px.scatter(df_filtered, x="temps_cycle", y="pieces_jour",
                                     title="Corrélation temps cycle vs productivité",
                                     labels={"temps_cycle": "Temps cycle (s)", 
                                            "pieces_jour": "Pièces/jour"},
                                     trendline="ols",
                                     color_discrete_sequence=["#1f2937"])
                fig_corr.update_layout(template="plotly_white")
                st.plotly_chart(fig_corr, use_container_width=True)
            
            with col2:
                # Distribution des taux machine
                fig_dist = px.histogram(df_filtered, x="taux_machine",
                                       title="Distribution des taux machine",
                                       labels={"taux_machine": "Taux machine (%)"},
                                       nbins=20,
                                       color_discrete_sequence=["#ff8c00"])
                fig_dist.update_layout(template="plotly_white")
                st.plotly_chart(fig_dist, use_container_width=True)
        
        with tab3:
            # Statistiques détaillées
            st.markdown("### Statistiques détaillées")
            
            stats_detail = df_filtered[["temps_cycle", "pieces_jour", "taux_machine", "taux_homme"]].describe()
            st.dataframe(stats_detail, use_container_width=True)
            
            # Export
            st.markdown("### Export des données")
            csv = df_filtered.to_csv(index=False, encoding='utf-8')
            st.download_button(
                "📥 Télécharger l'historique (CSV)",
                csv,
                file_name=f"historique_simulations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

else:
    st.info("📭 Aucune simulation enregistrée. Allez dans l'onglet Simogramme pour créer votre première simulation.")

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Simogramme - Configuration",
    page_icon="⚙️",
    layout="wide"
)

# ===================================================
# FONCTIONS DE GESTION DE CONFIGURATION
# ===================================================

def save_config_to_file(config, filename="config.json"):
    """Sauvegarde la configuration dans un fichier JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config_from_file(filename="config.json"):
    """Charge la configuration depuis un fichier JSON"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def export_config_csv(config):
    """Exporte la configuration en CSV"""
    df = pd.DataFrame([config])
    return df.to_csv(index=False, encoding='utf-8')

# ===================================================
# PAGE PRINCIPALE
# ===================================================

st.title("⚙️ Configuration du système")
st.markdown("Personnalisez les paramètres généraux de l'application")

# ===================================================
# CONFIGURATION GÉNÉRALE
# ===================================================

st.markdown("## 🏭 Paramètres généraux")

col1, col2 = st.columns(2)

with col1:
    default_coef = st.number_input(
        "Coefficient rendement par défaut",
        min_value=0.1, max_value=1.0,
        value=0.85, step=0.05,
        help="Coefficient utilisé par défaut pour les nouvelles simulations"
    )
    
    default_heures = st.number_input(
        "Heures de travail par défaut",
        min_value=1.0, max_value=24.0,
        value=7.0, step=0.5,
        help="Nombre d'heures par défaut pour les nouvelles simulations"
    )

with col2:
    theme = st.selectbox(
        "Thème de l'application",
        ["Clair", "Sombre"],
        help="Choisissez l'apparence de l'application"
    )
    
    language = st.selectbox(
        "Langue",
        ["Français", "English", "Español"],
        help="Langue de l'interface"
    )

# ===================================================
# CONFIGURATION DES MACHINES
# ===================================================

st.markdown("## 🏭 Configuration des machines")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Machines disponibles")
    
    for idx, machine in enumerate(st.session_state["machines"]):
        col_a, col_b, col_c = st.columns([3, 1, 1])
        with col_a:
            new_name = st.text_input(f"Nom machine {idx+1}", value=machine, key=f"rename_{machine}")
            if new_name != machine:
                st.session_state["machines"][idx] = new_name
        with col_b:
            if st.button("🔧", key=f"config_{machine}"):
                st.info(f"Configuration avancée de {machine} à venir...")
        with col_c:
            if machine != "Machine 1":
                if st.button("🗑️", key=f"del_config_{machine}"):
                    st.session_state["machines"].remove(machine)
                    st.rerun()

with col2:
    st.markdown("### Actions")
    if st.button("➕ Ajouter machine", use)
