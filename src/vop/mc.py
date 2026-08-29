"""Monte Carlo GBM : variables antithétiques, intervalles de confiance, couverture testée.

Un intervalle « à 95 % » n'a de sens que s'il contient la vraie valeur 95 fois sur 100 :
le dépôt le VÉRIFIE en répétant l'estimation sur des graines indépendantes et en comptant.
"""

from __future__ import annotations

import numpy as np

from vop.bs import put as bs_put


def gbm_terminal(s: float, r: float, sigma: float, t: float, n_paths: int,
                 rng: np.random.Generator, antithetic: bool = True) -> np.ndarray:
    """Les prix terminaux sous la mesure risque-neutre ; moitié antithétique si demandé."""
    if antithetic:
        z = rng.standard_normal(n_paths // 2)
        z = np.concatenate([z, -z])
    else:
        z = rng.standard_normal(n_paths)
    return s * np.exp((r - 0.5 * sigma**2) * t + sigma * np.sqrt(t) * z)


def euro_put_mc(s: float, k: float, r: float, sigma: float, t: float, n_paths: int,
                seed: int = 0, antithetic: bool = True) -> tuple[float, float]:
    """(prix, erreur type) du put européen ; l'erreur type respecte l'appariement antithétique."""
    rng = np.random.default_rng(seed)
    st = gbm_terminal(s, r, sigma, t, n_paths, rng, antithetic)
    payoff = np.exp(-r * t) * np.maximum(k - st, 0.0)
    if antithetic:
        paired = 0.5 * (payoff[: n_paths // 2] + payoff[n_paths // 2:])
        return float(paired.mean()), float(paired.std(ddof=1) / np.sqrt(len(paired)))
    return float(payoff.mean()), float(payoff.std(ddof=1) / np.sqrt(n_paths))


def coverage(s: float, k: float, r: float, sigma: float, t: float, n_paths: int,
             n_rep: int = 400, level: float = 1.96, seed: int = 0) -> float:
    """La couverture EMPIRIQUE de l'intervalle à 95 % : la part des répétitions où il
    contient la valeur Black-Scholes exacte."""
    truth = bs_put(s, k, r, sigma, t)
    hits = 0
    for i in range(n_rep):
        est, se = euro_put_mc(s, k, r, sigma, t, n_paths, seed=seed + i)
        if abs(est - truth) <= level * se:
            hits += 1
    return hits / n_rep
