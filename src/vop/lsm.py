"""Longstaff-Schwartz (2001) : la régression des moindres carrés pour l'exercice anticipé.

L'algorithme du papier, à la lettre : trajectoires GBM (moitié antithétique), régression à
chaque date d'exercice sur les seules trajectoires DANS LA MONNAIE, base constante plus
polynômes de Laguerre pondérés, décision d'exercice par la valeur de continuation estimée,
puis valorisation par actualisation des flux d'arrêt SUR LES MÊMES trajectoires (l'option
`out_of_sample` refait la valorisation sur des trajectoires neuves : la différence entre
les deux mesure le biais de réutilisation, le second twist du dépôt).
"""

from __future__ import annotations

import numpy as np


def laguerre_basis(x: np.ndarray, n_basis: int) -> np.ndarray:
    """Constante + les n_basis premiers polynômes de Laguerre pondérés exp(-x/2) L_k(x)."""
    from numpy.polynomial.laguerre import lagval

    cols = [np.ones_like(x)]
    w = np.exp(-x / 2.0)
    for kdeg in range(n_basis):
        c = np.zeros(kdeg + 1)
        c[kdeg] = 1.0
        cols.append(w * lagval(x, c))
    return np.column_stack(cols)


def gbm_paths(s: float, r: float, sigma: float, t: float, n_steps: int, n_paths: int,
              rng: np.random.Generator) -> np.ndarray:
    """Trajectoires (n_paths, n_steps + 1), moitié antithétique, pas t/n_steps."""
    dt = t / n_steps
    z = rng.standard_normal((n_paths // 2, n_steps))
    z = np.vstack([z, -z])
    log_increments = (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    log_paths = np.cumsum(log_increments, axis=1)
    return s * np.exp(np.column_stack([np.zeros(len(z)), log_paths]))


def _exercise_rule(paths: np.ndarray, k: float, r: float, dt: float, n_basis: int):
    """Estime les coefficients de continuation à chaque date (en arrière) ; les retourne."""
    n_steps = paths.shape[1] - 1
    cash = np.maximum(k - paths[:, -1], 0.0)
    tau = np.full(len(paths), n_steps)
    coefs: dict[int, np.ndarray] = {}
    for i in range(n_steps - 1, 0, -1):
        s_i = paths[:, i]
        itm = (k - s_i) > 0.0
        if itm.sum() < n_basis + 2:
            continue
        x = laguerre_basis(s_i[itm] / k, n_basis)
        y = cash[itm] * np.exp(-r * dt * (tau[itm] - i))
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        coefs[i] = beta
        cont = x @ beta
        ex_now = (k - s_i[itm]) >= np.maximum(cont, 0.0) + 1e-12
        idx = np.where(itm)[0][ex_now]
        cash[idx] = k - s_i[idx]
        tau[idx] = i
    return coefs, cash, tau


def lsm_put(s: float, k: float, r: float, sigma: float, t: float, ex_per_year: int = 50,
            n_paths: int = 100_000, n_basis: int = 3, seed: int = 0,
            out_of_sample: bool = False) -> tuple[float, float]:
    """(prix, erreur type) du put bermudéen par LSM.

    Par défaut, la valorisation réutilise les trajectoires d'estimation (le choix du
    papier, biais faible vers le bas) ; out_of_sample applique la règle estimée à des
    trajectoires NEUVES (estimateur à biais bas garanti).
    """
    n_steps = int(round(ex_per_year * t))
    dt = t / n_steps
    rng = np.random.default_rng(seed)
    paths = gbm_paths(s, r, sigma, t, n_steps, n_paths, rng)
    coefs, cash, tau = _exercise_rule(paths, k, r, dt, n_basis)
    if out_of_sample:
        # décalage franc : avec « seed + 1 », les trajectoires de valorisation de la graine g
        # étaient exactement les trajectoires d'estimation de la graine g + 1, ce qui corrèle
        # entre elles les répétitions d'une expérience multi-graines
        paths = gbm_paths(s, r, sigma, t, n_steps, n_paths,
                          np.random.default_rng(seed + 1_000_000))
        cash = np.maximum(k - paths[:, -1], 0.0)
        tau = np.full(len(paths), n_steps)
        stopped = np.zeros(len(paths), dtype=bool)
        for i in range(1, n_steps):
            if i not in coefs:
                continue
            s_i = paths[:, i]
            itm = ((k - s_i) > 0.0) & ~stopped
            if not itm.any():
                continue
            x = laguerre_basis(s_i[itm] / k, coefs[i].shape[0] - 1)
            cont = x @ coefs[i]
            ex_now = (k - s_i[itm]) >= np.maximum(cont, 0.0) + 1e-12
            idx = np.where(itm)[0][ex_now]
            cash[idx] = k - paths[idx, i]
            tau[idx] = i
            stopped[idx] = True
    disc = cash * np.exp(-r * dt * tau)
    half = len(disc) // 2
    paired = 0.5 * (disc[:half] + disc[half:])
    return float(paired.mean()), float(paired.std(ddof=1) / np.sqrt(half))
