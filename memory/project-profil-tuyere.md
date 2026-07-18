---
name: project-profil-tuyere
description: "Projet ProfilTuyere - conception du divergent d'une tuyere supersonique par methode des caracteristiques"
metadata: 
  node_type: memory
  type: project
  originSessionId: b034988e-6443-49ce-8c80-62d7a74702d9
  modified: 2026-07-18T11:24:29.248Z
---

Projet Python (dans DemoVsCode/ProfilTuyere) : conception du **divergent d'une
tuyere supersonique AXISYMETRIQUE** par la **methode des caracteristiques
(MOC)**, en millimetres. Utilisateur francophone, profil ingenieur
(aerodynamique/compressible) ; code et echanges en francais.

**Choix de conception valides avec l'utilisateur :**
- Geometrie **axisymetrique** (pas plane).
- Amorcage au col par un **arc de cercle** (rayon Rc = Rc_ratio x Rt, defaut 1.5)
  puis **section de redressement** MOC -> ecoulement uniforme et parallele en
  sortie (theta=0, M=Me).
- Entrees exposees : diametre de col, Mach de sortie, gamma (defaut 1.4), rayon
  d'arc, nombre de caracteristiques n.
- Visualisation : profil paroi **rouge**, C+ montantes **vertes**, C-
  descendantes **bleues**.

**Structure :** `moc_nozzle.py` (coeur MOC : Prandtl-Meyer, unit processes
predicteur-correcteur en composantes u,v, `design_nozzle` avec bissection sur
theta_max pour atteindre Me), `plot_nozzle.py` (matplotlib), `main.py` (CLI
argparse + tableau des noeuds). Angles en radians dans le code, degres a
l'affichage.

**Point de vigilance :** l'amorcage utilise l'hypothese d'onde simple (nu=theta)
sur l'arc -> **biais systematique ~2-3 %** entre le rapport de sections MOC et la
valeur isentropique exacte (documente, pas un bug). Plage confortable Me
~1.5-3.5 (air) ; Me tres eleve ou gamma proche de 1 peuvent degenerer le
maillage (leve alors une ValueError explicite). Amelioration possible non
encore faite : ligne d'amorcage transsonique (methode de Sauer) ; export CSV des
noeuds. Voir [[feedback-commits-reguliers]] et [[feedback-sous-agents-sonnet]].
