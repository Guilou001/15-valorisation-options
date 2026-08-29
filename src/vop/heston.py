"""Heston (1993) : la formule semi-fermée par fonction caractéristique, et son Monte Carlo.

La formulation « little Heston trap » d'Albrecher, Mayer, Schoutens et Tistaert (2007)
évite les discontinuités numériques du log complexe ; l'intégrale est faite par quadrature
adaptative. Le Monte Carlo (schéma d'Euler à troncature complète) doit retomber sur la
formule : c'est la vérité connue du volet stochastique.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad


def _cf(u: complex, s: float, r: float, t: float, v0: float, kappa: float,
        theta: float, xi: float, rho: float) -> complex:
    """La fonction caractéristique de ln(S_T), formulation stable (little trap)."""
    x = np.log(s)
    d = np.sqrt((rho * xi * 1j * u - kappa) ** 2 + xi**2 * (1j * u + u**2))
    g = (kappa - rho * xi * 1j * u - d) / (kappa - rho * xi * 1j * u + d)
    exp_dt = np.exp(-d * t)
    c = (r * 1j * u * t + kappa * theta / xi**2
         * ((kappa - rho * xi * 1j * u - d) * t - 2.0 * np.log((1.0 - g * exp_dt) / (1.0 - g))))
    dd = (kappa - rho * xi * 1j * u - d) / xi**2 * ((1.0 - exp_dt) / (1.0 - g * exp_dt))
    return np.exp(c + dd * v0 + 1j * u * x)


def call(s: float, k: float, r: float, t: float, v0: float, kappa: float,
         theta: float, xi: float, rho: float) -> float:
    """Le call européen par les deux probabilités P1 et P2 de Heston."""
    lnk = np.log(k)

    def p_j(j: int) -> float:
        def integrand(u: float) -> float:
            if j == 1:
                num = _cf(u - 1j, s, r, t, v0, kappa, theta, xi, rho)
                den = _cf(-1j, s, r, t, v0, kappa, theta, xi, rho)
                phi = num / den
            else:
                phi = _cf(u, s, r, t, v0, kappa, theta, xi, rho)
            return float(np.real(np.exp(-1j * u * lnk) * phi / (1j * u)))

        integral, _ = quad(integrand, 1e-8, 200.0, limit=400)
        return 0.5 + integral / np.pi

    return float(s * p_j(1) - k * np.exp(-r * t) * p_j(2))


def put(s: float, k: float, r: float, t: float, v0: float, kappa: float,
        theta: float, xi: float, rho: float) -> float:
    """Par parité put-call : P = C - S + K e^(-rT)."""
    return call(s, k, r, t, v0, kappa, theta, xi, rho) - s + k * np.exp(-r * t)


def call_mc(s: float, k: float, r: float, t: float, v0: float, kappa: float,
            theta: float, xi: float, rho: float, n_paths: int = 100_000,
            n_steps: int = 200, seed: int = 0) -> tuple[float, float]:
    """(prix, erreur type) par Euler à troncature complète (Lord et coauteurs, 2010)."""
    rng = np.random.default_rng(seed)
    dt = t / n_steps
    half = n_paths // 2
    z1 = rng.standard_normal((half, n_steps))
    z2 = rng.standard_normal((half, n_steps))
    z1 = np.vstack([z1, -z1])
    z2 = np.vstack([z2, -z2])
    zs = rho * z1 + np.sqrt(1.0 - rho**2) * z2
    v = np.full(n_paths, v0)
    lns = np.full(n_paths, np.log(s))
    for i in range(n_steps):
        v_plus = np.maximum(v, 0.0)
        lns = lns + (r - 0.5 * v_plus) * dt + np.sqrt(v_plus * dt) * zs[:, i]
        v = v + kappa * (theta - v_plus) * dt + xi * np.sqrt(v_plus * dt) * z1[:, i]
    payoff = np.exp(-r * t) * np.maximum(np.exp(lns) - k, 0.0)
    paired = 0.5 * (payoff[:half] + payoff[half:])
    return float(paired.mean()), float(paired.std(ddof=1) / np.sqrt(half))
