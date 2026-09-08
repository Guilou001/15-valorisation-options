"""Draw the README figure from published results, without rerunning the study.

Run from the repository with ``uv run python scripts/figure_presentation.py``.
The input tables remain the numerical source of truth.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GREEN, GREY = "#176B96", "#C56628", "#14816D", "#718096"
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#CBD5E0",
        "text.color": "#172B3A",
        "axes.labelcolor": "#172B3A",
        "xtick.color": "#425466",
        "ytick.color": "#425466",
        "axes.axisbelow": True,
    }
)


def number(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def finish(fig, axes, title, note, path="results/figures/presentation.png"):
    for ax in np.asarray(axes, dtype=object).ravel():
        ax.grid(axis="x", color="#EDF0F3", linewidth=0.8)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    fig.suptitle(title, x=0.02, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.02, 0.015, note, ha="left", va="bottom", fontsize=9, color="#526575")
    fig.tight_layout(rect=(0, 0.075, 1, 0.91))
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    d = pd.read_csv(ROOT / "results/tables/couverture_ic.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(d))
    for i, row in d.iterrows():
        half = 1.96 * np.sqrt(0.95 * 0.05 / row.n_rep) * 100
        ax.plot([95 - half, 95 + half], [i, i], color="#E2E8F0", linewidth=15, solid_capstyle="butt")
    ax.scatter(d.couverture * 100, y, color=BLUE, s=85, zorder=3)
    ax.axvline(95, color=ORANGE, linestyle="--", label="Niveau annoncé de 95 %")
    ax.set_yticks(y, [number(v, 0) for v in d.n_paths])
    ax.set_ylabel("Trajectoires simulées par estimation")
    ax.set_xlabel("Estimations dont l'intervalle contient le prix connu (%)")
    ax.set_xlim(91, 99)
    ax.legend(frameon=False)
    finish(
        fig,
        [ax],
        "La fréquence observée reste proche des 95 % annoncés",
        "Prix théorique connu · 400 répétitions par taille de simulation · aucun cours de marché\n"
        "Gris clair = plage approximative à 95 % d'une fréquence observée si la vraie couverture vaut 95 % et les répétitions sont indépendantes.",
    )


if __name__ == "__main__":
    main()
