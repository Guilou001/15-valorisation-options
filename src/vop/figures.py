"""Quatre figures : la convergence CRR, la réplication du tableau 1, la couverture, le biais LSM."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gvf.style import OKABE_ITO, appliquer, formateur  # noqa: F401

# La palette et les réglages viennent de la couche partagée du portefeuille : les mêmes
# couleurs et la même virgule décimale dans tous les dépôts, corrigées à un seul endroit.


def use_style():
    """Les réglages communs, puis le formateur d'axe en français."""
    appliquer()
    return formateur()


def fig_convergence(ns: np.ndarray, errors: np.ndarray, dest: Path) -> None:
    """|CRR - Black-Scholes| en log-log : la pente doit valoir -1 (convergence en 1/n)."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    ax.loglog(ns, errors, marker="o", ms=4, color=OKABE_ITO[0], label="erreur CRR européenne")
    # la droite se cale sur le point le PLUS convergé : partir du point le plus grossier la
    # décalait vers le haut et donnait à croire que le modèle converge plus vite que la théorie
    ref = errors[-1] * ns[-1] / ns
    ax.loglog(ns, ref, linestyle="--", color=OKABE_ITO[3],
              label=f"pente -1 calée sur n = {ns[-1]} (théorie : erreur en 1/n)")
    pente = np.polyfit(np.log(ns), np.log(errors), 1)[0]
    ax.set_xlabel("Nombre de pas de l'arbre n (échelle logarithmique)")
    ax.set_ylabel("Erreur absolue |CRR moins Black-Scholes|\n(dollars par option, échelle logarithmique)",
                  fontsize=9.5)
    ax.legend(fontsize=9, title=f"pente mesurée : {pente:.2f}".replace(".", ","))
    ax.set_title("L'arbre CRR converge vers Black-Scholes au taux théorique en 1/n")
    _ = fr
    fig.savefig(dest)
    plt.close(fig)


def fig_table1(df: pd.DataFrame, dest: Path) -> None:
    """Les 20 cas du tableau 1 : l'écart LSM (nôtre et publié) aux différences finies, en cents."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    x = np.arange(len(df))
    ax.errorbar(x - 0.12, (df["lsm_notre"] - df["fd"]) * 100, yerr=2 * df["se_notre"] * 100,
                fmt="o", ms=4, color=OKABE_ITO[0], label="notre LSM (± 2 erreurs types)")
    ax.errorbar(x + 0.12, (df["lsm_publie"] - df["fd"]) * 100, yerr=2 * df["se_publie"] * 100,
                fmt="s", ms=4, color=OKABE_ITO[3], label="LSM publié par Longstaff-Schwartz (± 2 erreurs types)")
    ax.axhline(0, color="0.3", linewidth=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(r.s)}/{r.sigma:.1f}/{int(r.t)}".replace(".", ",")
                        for r in df.itertuples()], rotation=60, fontsize=7.5)
    ax.set_xlabel("Cas : prix initial du sous-jacent (dollars) / volatilité annualisée / échéance (années)",
                  fontsize=9.5)
    ax.set_ylabel("Écart du prix simulé à la valeur publiée\npar différences finies (cents par option)",
                  fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=9)
    ax.set_title("Vingt puts bermudéens : notre LSM retombe sur le tableau 1 de 2001, aux erreurs types près")
    fig.savefig(dest)
    plt.close(fig)


def fig_coverage(df: pd.DataFrame, dest: Path) -> None:
    """La couverture empirique des intervalles à 95 %, par taille d'échantillon."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    ax.plot(df["n_paths"], df["couverture"] * 100, marker="o", color=OKABE_ITO[0])
    ax.axhline(95, color=OKABE_ITO[3], linestyle="--", label="nominal : 95 %")
    lo = 95 - 1.96 * np.sqrt(0.95 * 0.05 / df["n_rep"].iloc[0]) * 100
    hi = 95 + 1.96 * np.sqrt(0.95 * 0.05 / df["n_rep"].iloc[0]) * 100
    ax.axhspan(lo, hi, color="0.92", zorder=0,
               label=f"bande d'échantillonnage à 95 % du test lui-même "
                     f"({int(df['n_rep'].iloc[0])} répétitions)")
    ax.set_xscale("log")
    ax.set_xlabel("Nombre de trajectoires par estimation (échelle logarithmique)")
    ax.set_ylabel(f"Part des {int(df['n_rep'].iloc[0])} intervalles qui contiennent\n"
                  f"la valeur Black-Scholes exacte (%)", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=9)
    ax.set_title("Un intervalle à 95 % qui contient la vérité 95 fois sur 100 : vérifié, pas supposé")
    fig.savefig(dest)
    plt.close(fig)


def fig_bias(df: pd.DataFrame, fd_value: float, dest: Path) -> None:
    """Le biais du LSM selon le nombre de fonctions de base, moyenné sur les graines."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    n_g = int(df["n_graines"].iloc[0]) if "n_graines" in df else 1
    for col, name, color in [("in_sample", "mêmes trajectoires (le choix du papier)", OKABE_ITO[0]),
                             ("out_sample", "trajectoires neuves (biaisé vers le bas par construction)", OKABE_ITO[3])]:
        ax.errorbar(df["n_basis"], (df[col] - fd_value) * 100, yerr=2 * df[f"se_{col}"] * 100,
                    marker="o", ms=4, color=color,
                    label=f"{name}, moyenne de {n_g} graines")
    ax.axhline(0, color="0.3", linewidth=0.9, label="différences finies (référence)")
    ax.set_xlabel("Nombre de polynômes de Laguerre dans la base")
    ax.set_ylabel("Écart à la référence par différences finies\n(cents par option)", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=8, loc="lower right",
              title=f"moyennes de {n_g} graines, barres = ± 2 erreurs types entre graines",
              title_fontsize=8)
    ecarts = (df["in_sample"] - df["out_sample"]) * 100
    ax.set_title(f"Réutiliser les trajectoires d'estimation ajoute de {ecarts.min():.1f} à "
                 f"{ecarts.max():.1f} cent,\net l'écart croît avec la base "
                 f"(mesuré, {n_g} graines)".replace(".", ","), fontsize=11.5)
    fig.savefig(dest)
    plt.close(fig)
