# CLAUDE.md

Ce fichier oriente les futures sessions de travail sur ce depot.

## Objectif du projet

Concevoir le **divergent d'une tuyere supersonique axisymetrique** par la
**methode des caracteristiques (MOC)**, avec amorcage par un arc de cercle au
col et une section de redressement assurant un ecoulement uniforme en
sortie. Toutes les longueurs sont en **millimetres**.

## Structure du depot

- `moc_nozzle.py` — coeur du calcul MOC : relations thermodynamiques
  (Prandtl-Meyer, isentropiques), classe `Node`, « unit processes » (point
  interieur, point sur l'axe, point de paroi), et `design_nozzle(...)` qui
  concoit la tuyere complete et renvoie un dict `result`. Voir aussi
  `all_nodes(result)`.
- `plot_nozzle.py` — visualisation matplotlib du profil et du maillage
  (`plot_nozzle(result, ...)`).
- `main.py` — point d'entree en ligne de commande (argparse) : appelle
  `design_nozzle`, imprime un bilan synthetique et, en option, un tableau
  detaille des noeuds, puis appelle `plot_nozzle`.
- `memory/` — memoire persistante du projet (fiches de contexte + index
  `MEMORY.md`), versionnee dans le depot pour rester visible. L'emplacement
  attendu par Claude Code (`~/.claude/projects/.../memory`) est un lien
  symbolique vers ce dossier : les fiches sont donc a la fois chargees
  automatiquement en debut de session et suivies par git.

Lancer :

```bash
python3 main.py --help
```

## Regles de travail

- **Commiter regulierement, et pas seulement a la fin.** Faire un commit a
  chaque etape logique / fonctionnalite terminee (par ex. : ajout d'une
  fonction, correction d'un bug, mise a jour de la doc), avec un message clair
  decrivant le changement. Ne pas accumuler tout le travail dans un unique
  commit final.

## Conventions

- Longueurs en **millimetres**.
- Angles stockes dans le code (`theta`, `nu`, `mu` de la classe `Node`) en
  **radians** ; conversion en degres uniquement a l'affichage
  (`math.degrees(...)`).
- `gamma` par defaut = 1.4 (air).

## Point de vigilance

L'amorcage au col utilise l'hypothese d'onde simple (`nu = theta` sur l'arc
de cercle) plutot qu'une analyse transsonique complete. Cela cause un
**ecart systematique d'environ 2 a 3 %** entre le rapport de sections calcule
par la MOC et la valeur isentropique exacte — c'est un biais connu de la
methode, documente dans `README.md`, pas une erreur a corriger a la legere.

Ne pas modifier `moc_nozzle.py` ni `plot_nozzle.py` sans concertation : ils
constituent le coeur de calcul / visualisation valide du projet.
