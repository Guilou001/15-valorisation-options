"""L'arbre binomial de Cox, Ross et Rubinstein : européen, américain, bermudéen.

Le tableau 1 de Longstaff et Schwartz (2001) valorise des puts BERMUDÉENS exerçables
50 fois par année, pas des américains continus : l'arbre doit donc n'autoriser l'exercice
qu'aux pas alignés sur ces dates (n multiple de 50 x T), faute de quoi la comparaison
échouerait pour une mauvaise raison.
"""

from __future__ import annotations

import numpy as np


def crr_put(s: float, k: float, r: float, sigma: float, t: float, n: int,
            exercise: str = "european", ex_per_year: int = 50) -> float:
    """Le put CRR ; `exercise` vaut european, american ou bermudan (ex_per_year dates/an).

    Pour le bermudéen, n doit être un multiple de ex_per_year x t (alignement exact).
    """
    dt = t / n
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp(r * dt) - d) / (u - d)
    disc = np.exp(-r * dt)
    if exercise == "bermudan":
        step = round(n / (ex_per_year * t))
        if abs(step * ex_per_year * t - n) > 1e-9 or step < 1:
            raise ValueError("n doit être un multiple de ex_per_year x t")
    j = np.arange(n + 1)
    prices = s * u ** (n - j) * d**j
    values = np.maximum(k - prices, 0.0)
    for i in range(n - 1, -1, -1):
        values = disc * (p * values[:-1] + (1.0 - p) * values[1:])
        prices = s * u ** (i - np.arange(i + 1)) * d ** np.arange(i + 1)
        if exercise == "american":
            values = np.maximum(values, k - prices)
        elif exercise == "bermudan" and i > 0 and i % step == 0:
            values = np.maximum(values, k - prices)
    return float(values[0])
