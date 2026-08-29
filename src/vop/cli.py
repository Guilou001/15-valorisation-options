"""Ligne de commande : le laboratoire complet, sans aucune donnée de marché."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Valorisation d'options contre vérités fermées : convergence CRR, "
                       "réplication du tableau 1 de Longstaff-Schwartz, couverture des IC "
                       "Monte Carlo, biais du LSM, Heston contre sa formule.")


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def lab(out: Path = Path("results"), n_paths: int = 100_000) -> None:
    """Toutes les expériences : quatre tables, quatre figures (~3 min)."""
    import numpy as np
    import pandas as pd

    from vop import figures
    from vop.bs import put as bs_put
    from vop.heston import call as heston_call
    from vop.heston import call_mc as heston_mc
    from vop.lsm import lsm_put
    from vop.mc import coverage
    from vop.refs import EX_PER_YEAR, TABLE_1, K, R
    from vop.trees import crr_put

    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    # 1. convergence CRR -> Black-Scholes en 1/n
    s0, sig, tt = 40.0, 0.20, 1.0
    truth = bs_put(s0, K, R, sig, tt)
    ns = np.array([25, 50, 100, 200, 400, 800, 1600, 3200])
    errs = np.array([abs(crr_put(s0, K, R, sig, tt, int(n)) - truth) for n in ns])
    pd.DataFrame({"n": ns, "erreur": errs}).to_csv(tables / "convergence_crr.csv", index=False)
    figures.fig_convergence(ns, errs, figs / "convergence_crr.png")
    pente = float(np.polyfit(np.log(ns), np.log(errs), 1)[0])

    # 2. le tableau 1 : CRR bermudéen (gardien) + notre LSM contre le publié
    rows = []
    for s, sigma, t, fd, bs_pub, lsm_pub, se_pub in TABLE_1:
        n = EX_PER_YEAR * t * 20                       # 20 pas par période d'exercice
        crr_b = crr_put(float(s), K, R, sigma, float(t), int(n), "bermudan", EX_PER_YEAR)
        notre, se = lsm_put(float(s), K, R, sigma, float(t), EX_PER_YEAR, n_paths, seed=42)
        rows.append({"s": s, "sigma": sigma, "t": t, "fd": fd, "bs_publie": bs_pub,
                     "bs_notre": bs_put(float(s), K, R, sigma, float(t)),
                     "crr_bermudeen": crr_b, "lsm_publie": lsm_pub, "se_publie": se_pub,
                     "lsm_notre": notre, "se_notre": se,
                     "dans_2se": bool(abs(notre - lsm_pub) <= 2 * (se_pub**2 + se**2) ** 0.5)})
    t1 = pd.DataFrame(rows)
    t1.round(4).to_csv(tables / "tableau1_replication.csv", index=False)
    figures.fig_table1(t1, figs / "tableau1.png")

    # 3. la couverture empirique des IC à 95 %
    cov_rows = []
    for n in (1000, 4000, 16000, 64000):
        c = coverage(40.0, K, R, 0.20, 1.0, n, n_rep=400, seed=7)
        cov_rows.append({"n_paths": n, "couverture": c, "n_rep": 400})
    cov = pd.DataFrame(cov_rows)
    cov.to_csv(tables / "couverture_ic.csv", index=False)
    figures.fig_coverage(cov, figs / "couverture_ic.png")

    # 4. le biais du LSM selon la base, en et hors échantillon (cas central 40/0,2/1)
    fd_ref = 2.314
    bias_rows = []
    for nb in (2, 3, 4, 5, 6, 8):
        v_in, se_in = lsm_put(40.0, K, R, 0.20, 1.0, EX_PER_YEAR, n_paths, n_basis=nb, seed=11)
        v_out, se_out = lsm_put(40.0, K, R, 0.20, 1.0, EX_PER_YEAR, n_paths, n_basis=nb,
                                seed=11, out_of_sample=True)
        bias_rows.append({"n_basis": nb, "in_sample": v_in, "se_in_sample": se_in,
                          "out_sample": v_out, "se_out_sample": se_out})
    bias = pd.DataFrame(bias_rows)
    bias.round(5).to_csv(tables / "biais_lsm.csv", index=False)
    figures.fig_bias(bias, fd_ref, figs / "biais_lsm.png")

    # 5. Heston : Monte Carlo contre la formule semi-fermée
    hp = dict(s=100.0, k=100.0, r=0.03, t=1.0, v0=0.04, kappa=2.0, theta=0.04, xi=0.5, rho=-0.7)
    ferme = heston_call(**hp)
    mc, se_mc = heston_mc(**hp, n_paths=200_000, n_steps=250, seed=3)
    pd.DataFrame([{"formule": ferme, "monte_carlo": mc, "erreur_type": se_mc,
                   "ecart_en_se": (mc - ferme) / se_mc, **hp}]
                 ).round(5).to_csv(tables / "heston.csv", index=False)

    n_ok = int(t1["dans_2se"].sum())
    typer.echo(f"pente de convergence CRR : {pente:.3f} (théorie -1)")
    typer.echo(f"tableau 1 : {n_ok}/20 cas dans les 2 erreurs types combinées ; "
               f"écart max |LSM - FD| {float((t1['lsm_notre'] - t1['fd']).abs().max()):.3f} $")
    typer.echo(f"gardien CRR bermudéen vs FD : écart max "
               f"{float((t1['crr_bermudeen'] - t1['fd']).abs().max()):.4f} $")
    typer.echo(f"couverture IC 95 % : {', '.join(f'{r.n_paths}: {100 * r.couverture:.1f} %' for r in cov.itertuples())}")
    typer.echo(f"Heston : formule {ferme:.4f}, MC {mc:.4f} (écart {abs(mc - ferme) / se_mc:.2f} e.t.)")


if __name__ == "__main__":
    app()
