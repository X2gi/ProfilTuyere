# ProfilTuyere

Conception du **divergent d'une tuyere supersonique axisymetrique** par la
**methode des caracteristiques (MOC)**, avec amorcage par un **arc de cercle
au col** et une **section de redressement** garantissant un ecoulement
**uniforme et parallele a l'axe en sortie**.

Toutes les longueurs manipulees par le code sont exprimees en **millimetres**.

## Physique

En ecoulement supersonique, permanent, isentropique et irrotationnel, les
equations d'Euler sont hyperboliques : l'information se propage le long de
deux familles de lignes caracteristiques (les ondes de Mach) :

- **C+** (dite « montante ») : pente `dy/dx = tan(theta + mu)`
- **C-** (dite « descendante ») : pente `dy/dx = tan(theta - mu)`

ou `theta` est l'angle local de l'ecoulement et `mu = asin(1/M)` l'angle de
Mach.

Le long de chaque caracteristique existe une **relation de compatibilite**.
En **ecoulement plan**, ce sont les invariants de Riemann :

- le long de C- : `theta + nu = constante`
- le long de C+ : `theta - nu = constante`

ou `nu` est la **fonction de Prandtl-Meyer**, l'angle dont un ecoulement
sonique (M = 1) doit tourner pour atteindre le nombre de Mach M par une
detente isentropique.

En **axisymetrique**, un **terme source en 1/y** (y = distance a l'axe)
s'ajoute aux relations de compatibilite : les invariants de Riemann plans ne
sont plus rigoureusement constants. Le maillage est alors resolu de proche en
proche (« unit processes » : point interieur, point sur l'axe, point de
paroi) par un schema predicteur-correcteur qui integre ce terme source a
chaque pas.

L'amorcage de la detente se fait sur un **arc de cercle** tangent au col
(rayon `Rc = Rc_ratio x Rt`), suivi d'une **section de redressement** ou la
paroi est deformee pour annuler progressivement les ondes C+ residuelles et
rendre l'ecoulement uniforme (theta = 0 partout) au plan de sortie.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
# Cas par defaut : col de 10 mm, Mach de sortie 2.4, air (gamma = 1.4)
python3 main.py

# Col de 20 mm, Mach de sortie 3.0, maillage plus fin, tableau des noeuds
# et sauvegarde de la figure
python3 main.py --dcol 20 --mach 3.0 --n 30 --table --save tuyere.png
```

### Options disponibles

| Option        | Type  | Defaut | Description |
|---------------|-------|--------|-------------|
| `--dcol`      | float | 10.0   | Diametre du col (mm) |
| `--mach`      | float | 2.4    | Nombre de Mach de sortie vise |
| `--gamma`     | float | 1.4    | Rapport des chaleurs specifiques |
| `--rc`        | float | 1.5    | Rayon de l'arc au col, en multiple du rayon de col (`Rc = rc x Rt`) |
| `--n`         | int   | 20     | Nombre de caracteristiques (finesse du maillage) |
| `--no-match`  | flag  | -      | N'ajuste pas theta_max pour atteindre exactement le Mach de sortie vise |
| `--save`      | str   | None   | Chemin de sauvegarde de la figure (PNG) |
| `--no-show`   | flag  | -      | N'affiche pas la fenetre graphique (mode batch, sans interface graphique) |
| `--table`     | flag  | -      | Imprime le tableau detaille de tous les noeuds du maillage |

## Sortie

`main.py` imprime d'abord un **bilan synthetique** (diametre du col, Mach
vise/obtenu, theta_max, longueur, rayon de sortie, rapports de sections MOC
et isentropique et leur ecart en %, nombre de noeuds), puis, si `--table` est
present, un **tableau** avec, pour chaque noeud : index, position (x, y en
mm), Mach, angle d'ecoulement theta (deg), angle de Prandtl-Meyer nu (deg),
p/p0 et T/T0.

Le graphe produit par `plot_nozzle` affiche :

- le **profil de la paroi** (arc au col + section de redressement) en
  **rouge**,
- les caracteristiques **C+** (montantes) en **vert**,
- les caracteristiques **C-** (descendantes) en **bleu**.

## Limites / precision

L'amorcage de la detente sur l'arc de cercle au col utilise l'**hypothese
d'onde simple** (`nu = theta`) plutot qu'une veritable analyse transsonique
du col (ligne sonique courbe, ecoulement rotationnel pres de la paroi). Cette
approximation introduit un **ecart systematique d'environ 2 a 3 %** entre le
rapport de sections calcule par la MOC (`area_ratio_moc`) et la valeur
isentropique exacte (`area_ratio_isen`) — c'est un biais connu et documente
de cette methode de conception, pas un bug.

La plage de validation confortable de ce code est **Me ~ 1.5 - 3.5** pour
l'air (`gamma = 1.4`). Des Mach de sortie tres eleves ou des `gamma` proches
de 1 peuvent faire degenerer le maillage (arc trop serre, points de paroi
qui se croisent, etc.) ; dans ce cas, `design_nozzle` leve une `ValueError`
explicite plutot que de renvoyer une geometrie aberrante.

## References

- J. D. Anderson, *Modern Compressible Flow*, chapitre 11 (Method of
  Characteristics).
- M. J. Zucrow, J. D. Hoffman, *Gas Dynamics*, volume 2.
