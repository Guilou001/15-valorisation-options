"""Le tableau 1 de Longstaff et Schwartz (2001), transcrit de la page 15 du PDF (RFS 14-1).

Colonnes : S, sigma, T (années), valeur américaine par différences finies, valeur
européenne Black-Scholes imprimée, valeur LSM simulée, erreur type imprimée. Puts
BERMUDÉENS : K = 40, r = 6 %, exerçables 50 fois par année, 100 000 trajectoires
(50 000 plus 50 000 antithétiques). La transcription est verrouillée par deux gardiens :
la colonne européenne doit coller à notre Black-Scholes au millième (test), et la colonne
différences finies à notre arbre CRR bermudéen à un cent et demi près (test).
"""

TABLE_1 = [
    # (s, sigma, t, fd_american, bs_european, lsm, se)
    (36, 0.20, 1, 4.478, 3.844, 4.472, 0.010),
    (36, 0.20, 2, 4.840, 3.763, 4.821, 0.012),
    (36, 0.40, 1, 7.101, 6.711, 7.091, 0.020),
    (36, 0.40, 2, 8.508, 7.700, 8.488, 0.024),
    (38, 0.20, 1, 3.250, 2.852, 3.244, 0.009),
    (38, 0.20, 2, 3.745, 2.991, 3.735, 0.011),
    (38, 0.40, 1, 6.148, 5.834, 6.139, 0.019),
    (38, 0.40, 2, 7.670, 6.979, 7.669, 0.022),
    (40, 0.20, 1, 2.314, 2.066, 2.313, 0.009),
    (40, 0.20, 2, 2.885, 2.356, 2.879, 0.010),
    (40, 0.40, 1, 5.312, 5.060, 5.308, 0.018),
    (40, 0.40, 2, 6.920, 6.326, 6.921, 0.022),
    (42, 0.20, 1, 1.617, 1.465, 1.617, 0.007),
    (42, 0.20, 2, 2.212, 1.841, 2.206, 0.010),
    (42, 0.40, 1, 4.582, 4.379, 4.588, 0.017),
    (42, 0.40, 2, 6.248, 5.736, 6.243, 0.021),
    (44, 0.20, 1, 1.110, 1.017, 1.118, 0.007),
    (44, 0.20, 2, 1.690, 1.429, 1.675, 0.009),
    (44, 0.40, 1, 3.948, 3.783, 3.957, 0.017),
    (44, 0.40, 2, 5.647, 5.202, 5.622, 0.021),
]
K = 40.0
R = 0.06
EX_PER_YEAR = 50
