"""Black-Scholes fermé : la vérité de référence de tout le dépôt."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def d1_d2(s: float, k: float, r: float, sigma: float, t: float) -> tuple[float, float]:
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    return d1, d1 - sigma * np.sqrt(t)


def call(s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, d2 = d1_d2(s, k, r, sigma, t)
    return float(s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2))


def put(s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, d2 = d1_d2(s, k, r, sigma, t)
    return float(k * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1))
