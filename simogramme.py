import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def generate_simogramme(dfs, state):

    df = dfs[0]
    fig, ax = plt.subplots(figsize=(16,6))

    max_x = 0
    y = 0

    for _, r in df.iterrows():

        rect = Rectangle(
            (r["Début"], y),
            r["Durée"],
            0.5,
            facecolor="#1f4fff",
            edgecolor="black"
        )

        ax.add_patch(rect)
        max_x = max(max_x, r["Début"] + r["Durée"])

    ax.set_xlim(0, max_x + 2)
    ax.set_yticks([])

    kpis = {
        "temps_cycle": max_x,
        "taux_machine": 0.8,
        "taux_operateur": 0.7,
        "pieces_heure": 3600 / max_x if max_x else 0,
        "pieces_jour": (3600 / max_x) * state["heures_travail"] if max_x else 0
    }

    return fig, kpis
