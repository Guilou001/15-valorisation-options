#set document(title: "Calculer le prix d'une option et vérifier la marge d'erreur", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [valorisation-options], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Calculer le prix d'une option et vérifier la marge d'erreur]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/15-valorisation-options")[Guilou001/15-valorisation-options]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Une option donne le droit d'acheter ou de vendre un actif à un prix fixé, selon les dates prévues au contrat. Ce droit a un prix aujourd'hui, même si personne ne connaît le cours futur de l'actif.

Ce projet compare plusieurs façons de calculer ce prix. Il utilise des cas où une formule ou un article fournit une référence, sans données de marché.

*Une estimation n'est utile que si son prix et sa marge d'erreur résistent à des vérifications.*

== Vérifier une promesse de précision

Une simulation produit un prix estimé et un intervalle qui cherche à contenir le vrai prix. Un intervalle annoncé à 95 % devrait le contenir dans environ 95 % des répétitions indépendantes.

#figure(image("../results/figures/presentation.png", width: 100%), caption: [Fréquence à laquelle les intervalles annoncés à 95 % contiennent le prix connu])

Chaque point vient de 400 répétitions. L'axe horizontal indique la part des intervalles qui contiennent le prix connu. Les bandes grises montrent la variabilité approximative attendue si la couverture réelle vaut 95 % et les répétitions sont indépendantes.

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Trajectoires par estimation*],
    [*Intervalles contenant le prix connu*],
    [1 000],
    [96,25 %],
    [4 000],
    [94,75 %],
    [16 000],
    [94,75 %],
    [64 000],
    [94,00 %],
)

Ces écarts autour de 95 % restent compatibles avec le nombre de répétitions. #link("results/tables/couverture_ic.csv")[Résultats du contrôle].

== Vérifier aussi les prix

Le dépôt reproduit vingt cas publiés par Longstaff et Schwartz. Il respecte leurs dates d'exercice, soit cinquante possibilités par année. Tous les prix simulés restent à moins de deux erreurs types combinées des prix simulés publiés.

Il compare aussi un arbre de prix à la formule de Black-Scholes, puis une simulation du modèle de Heston à son calcul par intégration numérique.

== Un piège mesuré

Apprendre quand exercer une option puis mesurer sa valeur sur les mêmes trajectoires donne un avantage artificiel. Ici, cette réutilisation ajoute environ 0,8 à 1,0 cent par option par rapport à des trajectoires neuves. Le dépôt mesure cet écart sur seize tirages indépendants.

Ces contrôles portent sur des modèles et des paramètres fixés. Ils ne prouvent pas que le prix calculé correspond au prix auquel une option réelle pourrait être achetée ou vendue.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pytest\nuv run vop lab", block: true, lang: "bash")

Aucun téléchargement de données de marché n'est nécessaire. Le laboratoire complet inclut les répétitions statistiques et prend plusieurs minutes. Le graphique de présentation se régénère hors réseau avec #raw("uv run python scripts/figure_presentation.py"), depuis les tableaux publiés.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

Option pricing methods are checked against analytic and published references. Repeated simulations test confidence-interval coverage, while independent paths reveal a small upward effect from reusing training simulations.
