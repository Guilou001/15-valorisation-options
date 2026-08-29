"""Toutes les vérités sont fermées : parité, convergence, bornes, transcription verrouillée."""

import numpy as np
import pytest

from vop.bs import call as bs_call
from vop.bs import put as bs_put
from vop.heston import call as heston_call
from vop.heston import put as heston_put
from vop.lsm import gbm_paths, laguerre_basis, lsm_put
from vop.mc import euro_put_mc
from vop.refs import EX_PER_YEAR, TABLE_1, K, R
from vop.trees import crr_put


def test_put_call_parity_exact():
    s, k, r, sig, t = 42.0, 40.0, 0.06, 0.3, 1.5
    assert bs_call(s, k, r, sig, t) - bs_put(s, k, r, sig, t) == pytest.approx(
        s - k * np.exp(-r * t), abs=1e-12)


def test_bs_hand_value_from_table1():
    # la cellule 40/0,20/1 du tableau 1 : 2,066 (refaite à la main dans le README)
    assert bs_put(40.0, 40.0, 0.06, 0.20, 1.0) == pytest.approx(2.066, abs=5e-4)


def test_table1_bs_column_locks_the_transcription():
    # LE gardien : la colonne européenne publiée doit coller à notre Black-Scholes au
    # millième sur les 20 lignes ; une faute de frappe dans refs.py ferait échouer ce test
    for s, sigma, t, _fd, bs_pub, _lsm, _se in TABLE_1:
        assert bs_put(float(s), K, R, sigma, float(t)) == pytest.approx(bs_pub, abs=1.1e-3), (s, sigma, t)


def test_crr_european_converges_to_bs():
    v = crr_put(40.0, 40.0, 0.06, 0.2, 1.0, 2000)
    assert v == pytest.approx(bs_put(40.0, 40.0, 0.06, 0.2, 1.0), abs=2e-3)


def test_crr_order_one_convergence():
    truth = bs_put(40.0, 40.0, 0.06, 0.2, 1.0)
    e200 = abs(crr_put(40.0, 40.0, 0.06, 0.2, 1.0, 200) - truth)
    e800 = abs(crr_put(40.0, 40.0, 0.06, 0.2, 1.0, 800) - truth)
    assert e800 < e200 / 2.5                     # en 1/n : diviser n par 4 divise l'erreur par ~4


def test_exercise_ordering_european_bermudan_american():
    args = (36.0, 40.0, 0.06, 0.2, 1.0)
    eu = crr_put(*args, 1000)
    berm = crr_put(*args, 1000, "bermudan", EX_PER_YEAR)
    am = crr_put(*args, 1000, "american")
    assert eu < berm <= am + 1e-9
    assert am - berm < 0.01                      # 50 dates par an : presque américain


def test_crr_bermudan_guards_fd_column():
    # second gardien : l'arbre bermudéen retombe sur les différences finies publiées
    for s, sigma, t, fd, _bs, _lsm, _se in TABLE_1[:6]:
        n = EX_PER_YEAR * t * 10
        v = crr_put(float(s), K, R, sigma, float(t), int(n), "bermudan", EX_PER_YEAR)
        assert v == pytest.approx(fd, abs=0.02), (s, sigma, t)


def test_mc_within_four_se_of_bs():
    est, se = euro_put_mc(40.0, 40.0, 0.06, 0.2, 1.0, 100_000, seed=1)
    assert abs(est - bs_put(40.0, 40.0, 0.06, 0.2, 1.0)) < 4 * se


def test_antithetic_reduces_variance():
    _, se_anti = euro_put_mc(40.0, 40.0, 0.06, 0.2, 1.0, 40_000, seed=2, antithetic=True)
    _, se_plain = euro_put_mc(40.0, 40.0, 0.06, 0.2, 1.0, 40_000, seed=2, antithetic=False)
    assert se_anti < se_plain


def test_lsm_beats_european_and_stays_below_american():
    eu = bs_put(36.0, 40.0, 0.06, 0.2, 1.0)
    am = crr_put(36.0, 40.0, 0.06, 0.2, 1.0, 1000, "american")
    v, se = lsm_put(36.0, 40.0, 0.06, 0.2, 1.0, EX_PER_YEAR, n_paths=40_000, seed=5)
    assert v > eu + 0.3                          # l'exercice anticipé vaut ~0,63 $ ici
    assert v < am + 4 * se


def test_lsm_matches_crr_bermudan_within_se():
    berm = crr_put(40.0, 40.0, 0.06, 0.2, 1.0, 1000, "bermudan", EX_PER_YEAR)
    v, se = lsm_put(40.0, 40.0, 0.06, 0.2, 1.0, EX_PER_YEAR, n_paths=60_000, seed=6)
    assert abs(v - berm) < 3.5 * se


def test_gbm_paths_are_antithetic_and_martingale():
    rng = np.random.default_rng(0)
    p = gbm_paths(100.0, 0.05, 0.2, 1.0, 50, 20_000, rng)
    half = len(p) // 2
    # les log-rendements des moitiés sont opposés exactement
    lr = np.log(p[:, -1] / p[:, 0]) - (0.05 - 0.02) * 1.0
    assert np.allclose(lr[:half], -lr[half:], atol=1e-10)
    # martingale actualisée : E[S_T] = S_0 e^(rT)
    assert p[:, -1].mean() == pytest.approx(100.0 * np.exp(0.05), rel=5e-3)


def test_laguerre_basis_shape_and_first_polynomials():
    x = np.array([0.5, 1.0])
    b = laguerre_basis(x, 2)
    assert b.shape == (2, 3)
    assert b[:, 0] == pytest.approx([1.0, 1.0])
    assert b[:, 1] == pytest.approx(np.exp(-x / 2))            # L_0 = 1
    assert b[:, 2] == pytest.approx(np.exp(-x / 2) * (1 - x))  # L_1 = 1 - x


def test_heston_degenerates_to_black_scholes():
    # vol de vol nulle et v0 = theta : la variance est constante, Heston = Black-Scholes
    bs = bs_call(100.0, 100.0, 0.03, 0.2, 1.0)
    h = heston_call(100.0, 100.0, 0.03, 1.0, v0=0.04, kappa=2.0, theta=0.04, xi=1e-6, rho=0.0)
    assert h == pytest.approx(bs, abs=2e-4)


def test_heston_put_call_parity():
    hp = dict(s=100.0, k=95.0, r=0.03, t=1.0, v0=0.04, kappa=2.0, theta=0.04, xi=0.5, rho=-0.7)
    c = heston_call(**hp)
    p = heston_put(**hp)
    assert c - p == pytest.approx(100.0 - 95.0 * np.exp(-0.03), abs=1e-8)


def test_crr_refuse_un_type_d_exercice_inconnu():
    with pytest.raises(ValueError):
        crr_put(40.0, 40.0, 0.06, 0.20, 1.0, 100, "asiatique")
    # le garde-fou d'alignement bermudéen existait mais n'était pas testé
    with pytest.raises(ValueError):
        crr_put(40.0, 40.0, 0.06, 0.20, 1.0, 999, "bermudan", 50)


def test_lsm_hors_echantillon_est_borne_par_la_valeur_bermudeenne():
    # la règle d'exercice estimée, appliquée à des trajectoires neuves, ne peut pas battre la
    # règle optimale : l'estimateur est biaisé vers le BAS par construction
    v_out, se = lsm_put(40.0, 40.0, 0.06, 0.20, 1.0, 50, 20_000, n_basis=3, seed=11,
                        out_of_sample=True)
    v_in, _ = lsm_put(40.0, 40.0, 0.06, 0.20, 1.0, 50, 20_000, n_basis=3, seed=11)
    borne = crr_put(40.0, 40.0, 0.06, 0.20, 1.0, 1000, "bermudan", 50)
    assert v_out <= v_in + 3 * se
    assert v_out <= borne + 3 * se


def test_les_trajectoires_de_valorisation_ne_recyclent_pas_une_autre_graine():
    # « seed + 1 » faisait des trajectoires de valorisation de la graine g les trajectoires
    # d'estimation de la graine g + 1 : deux répétitions voisines n'étaient plus indépendantes
    from vop.lsm import gbm_paths

    a = gbm_paths(40.0, 0.06, 0.20, 1.0, 10, 64, np.random.default_rng(101))
    v_a, _ = lsm_put(40.0, 40.0, 0.06, 0.20, 1.0, 10, 64, n_basis=3, seed=100, out_of_sample=True)
    b = gbm_paths(40.0, 0.06, 0.20, 1.0, 10, 64, np.random.default_rng(100 + 1_000_000))
    assert not np.allclose(a, b)
    assert np.isfinite(v_a)
