# -*- coding: utf-8 -*-
"""
plot_nozzle.py
===============

Visualisation matplotlib du divergent d'une tuyere supersonique concu par la
methode des caracteristiques (MOC), a partir du resultat renvoye par
`design_nozzle()` (module `moc_nozzle.py`, non modifie ici).

On trace trois familles d'objets, avec une topologie EXACTE :

    - le PROFIL DE PAROI (arc de col + section de redressement)  -> ROUGE
    - les caracteristiques C+ ("montantes", pente tan(theta+mu)) -> VERT
    - les caracteristiques C- ("descendantes", pente tan(theta-mu)) -> BLEU

Rappel de topologie du maillage (voir moc_nozzle.py) :
    - `result["rows"][i]` est UNE caracteristique C- complete, ordonnee de la
      paroi (indice 0) vers l'axe (dernier indice, y = 0).
    - Les caracteristiques C+ ne sont PAS stockees explicitement : elles
      relient les points de meme rang k sur deux C- consecutives, c.-a-d.
      `rows[i-1][k]` -> `rows[i][k]`, plus le segment final vers la paroi de
      redressement `rows[-1][m]` -> `wall[m]`.
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# NB : le choix du backend (interactif ou 'Agg' non bloquant) est laisse a
# l'appelant, via la variable d'environnement MPLBACKEND ou un appel a
# matplotlib.use(...) AVANT ce module. Le bloc __main__ ci-dessous force
# explicitement 'Agg' pour son propre test, sans imposer ce choix a un
# eventuel appelant important ce module depuis une appli interactive.


# ---------------------------------------------------------------------------
# Couleurs des trois familles (constantes pour rester coherent partout)
# ---------------------------------------------------------------------------
COULEUR_PAROI = "tab:red"
COULEUR_C_PLUS = "tab:green"      # caracteristiques montantes
COULEUR_C_MOINS = "tab:blue"      # caracteristiques descendantes
COULEUR_AXE = "0.5"               # gris pour l'axe de symetrie
COULEUR_NOEUD = "black"


def _trace_caracteristiques(ax, result, alpha=1.0, linewidth=0.8):
    """Trace les caracteristiques C- (bleu) et C+ (vert) du maillage.

    `alpha`/`linewidth` permettent de reutiliser la fonction pour le trace
    "miroir" (plus discret) sans dupliquer la logique de topologie.
    """
    rows = result["rows"]
    wall = result["wall"]

    # --- C- (descendantes) : chaque rows[i] est deja une polyligne complete ---
    for row in rows:
        xs = [node.x for node in row]
        ys = [node.y for node in row]
        ax.plot(xs, ys, color=COULEUR_C_MOINS, linewidth=linewidth, alpha=alpha,
                 zorder=2)

    # --- C+ (montantes) : segments internes entre C- consecutives ---
    for i in range(1, len(rows)):
        prev_row = rows[i - 1]
        cur_row = rows[i]
        for k in range(1, len(prev_row)):
            x0, y0 = prev_row[k].x, prev_row[k].y
            x1, y1 = cur_row[k].x, cur_row[k].y
            ax.plot([x0, x1], [y0, y1], color=COULEUR_C_PLUS,
                     linewidth=linewidth, alpha=alpha, zorder=2)

    # --- C+ (montantes) : segments de redressement vers la paroi ---
    last_row = rows[-1]
    for m in range(1, len(wall)):
        x0, y0 = last_row[m].x, last_row[m].y
        x1, y1 = wall[m].x, wall[m].y
        ax.plot([x0, x1], [y0, y1], color=COULEUR_C_PLUS,
                 linewidth=linewidth, alpha=alpha, zorder=2)


def _trace_noeuds(ax, result, alpha=1.0):
    """Marque tous les noeuds d'intersection du maillage (petits points noirs)."""
    xs, ys = [], []
    for row in result["rows"]:
        for node in row:
            xs.append(node.x)
            ys.append(node.y)
    for node in result["wall"]:
        xs.append(node.x)
        ys.append(node.y)
    ax.scatter(xs, ys, s=6, color=COULEUR_NOEUD, alpha=alpha, zorder=3,
               linewidths=0)


def _annoter_mach(ax, result):
    """Annote le nombre de Mach sur quelques noeuds seulement (axe + sortie),
    pour ne pas surcharger la figure."""
    # Points sur l'axe : dernier noeud de chaque C- (y ~ 0). On ne garde
    # qu'une poignee d'indices bien espaces (pas un sur deux) pour eviter que
    # les etiquettes ne se chevauchent le long de l'axe.
    rows = result["rows"]
    n_annot = min(4, len(rows))
    indices = sorted(set(
        round(i * (len(rows) - 1) / (n_annot - 1)) for i in range(n_annot)
    )) if n_annot > 1 else [0]
    for i in indices:
        axis_node = rows[i][-1]
        ax.annotate(f"M={axis_node.M:.2f}",
                    xy=(axis_node.x, axis_node.y),
                    xytext=(0, -12), textcoords="offset points",
                    fontsize=6, ha="center", color=COULEUR_C_MOINS,
                    rotation=90 if i != indices[-1] else 0)

    # Point de sortie (fin de la paroi de redressement).
    exit_node = result["wall"][-1]
    ax.annotate(f"Me={exit_node.M:.3f}",
                xy=(exit_node.x, exit_node.y),
                xytext=(6, 6), textcoords="offset points",
                fontsize=7, fontweight="bold", color=COULEUR_PAROI)

    # Point au col (premier point de l'arc, theta=0, M=1).
    x0, y0 = result["arc_pts"][0]
    ax.annotate("M=1.0 (col)", xy=(x0, y0), xytext=(-6, 8),
                textcoords="offset points", fontsize=6, ha="right",
                color=COULEUR_PAROI)


def plot_nozzle(result, mirror=True, show_nodes=True, annotate_mach=False,
                 savepath=None, show=True):
    """Trace la geometrie complete de la tuyere (maillage MOC + profil).

    Parametres
    ----------
    result : dict
        Sortie de `moc_nozzle.design_nozzle(...)`.
    mirror : bool
        Si True, retrace en plus le profil et les caracteristiques symetrises
        (y -> -y) pour visualiser la tuyere entiere (haut + bas), avec une
        transparence reduite pour le maillage miroir.
    show_nodes : bool
        Si True, marque les noeuds d'intersection du maillage.
    annotate_mach : bool
        Si True, annote le nombre de Mach sur quelques noeuds cles
        (axe, col, sortie) pour ne pas surcharger la figure.
    savepath : str ou None
        Si fourni, enregistre la figure a ce chemin (dpi=150).
    show : bool
        Si True, appelle plt.show() (bloquant si un backend interactif est
        utilise -- a eviter en environnement automatise, cf. backend 'Agg').

    Retour
    ------
    (fig, ax) : la figure et les axes matplotlib crees.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Axe de symetrie (y = 0), trait mixte fin gris ---
    x_max = max(x for x, y in result["profile"])
    ax.axhline(0.0, color=COULEUR_AXE, linewidth=0.8, linestyle="-.",
               zorder=1)

    # --- Maillage des caracteristiques (moitie haute, trait plein) ---
    _trace_caracteristiques(ax, result, alpha=1.0, linewidth=0.8)

    # --- Profil de paroi (rouge, epais) ---
    prof_x = [p[0] for p in result["profile"]]
    prof_y = [p[1] for p in result["profile"]]
    ax.plot(prof_x, prof_y, color=COULEUR_PAROI, linewidth=2.5, zorder=4)

    # --- Noeuds d'intersection ---
    if show_nodes:
        _trace_noeuds(ax, result, alpha=1.0)

    # --- Symetrie (moitie basse), plus discrete pour ne pas surcharger ---
    if mirror:
        ax.plot(prof_x, [-y for y in prof_y], color=COULEUR_PAROI,
                 linewidth=2.5, zorder=4)
        _trace_caracteristiques_miroir(ax, result, alpha=0.35, linewidth=0.6)
        if show_nodes:
            xs, ys = [], []
            for row in result["rows"]:
                for node in row:
                    xs.append(node.x)
                    ys.append(-node.y)
            for node in result["wall"]:
                xs.append(node.x)
                ys.append(-node.y)
            ax.scatter(xs, ys, s=6, color=COULEUR_NOEUD, alpha=0.35,
                       zorder=3, linewidths=0)

    # --- Annotations de Mach (facultatif) ---
    if annotate_mach:
        _annoter_mach(ax, result)

    # --- Mise en forme des axes ---
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.grid(True, linewidth=0.4, alpha=0.4)
    marge = 0.08 * max(x_max, result["R_exit"])
    ax.set_xlim(-0.02 * x_max, x_max + marge)
    if mirror:
        ax.set_ylim(-(result["R_exit"] + marge), result["R_exit"] + marge)
    else:
        ax.set_ylim(-marge * 0.2, result["R_exit"] + marge)

    # --- Legende : un seul handle par famille de couleur ---
    handles = [
        Line2D([0], [0], color=COULEUR_PAROI, linewidth=2.5,
               label="Profil (paroi)"),
        Line2D([0], [0], color=COULEUR_C_PLUS, linewidth=1.2,
               label="C+ (montantes)"),
        Line2D([0], [0], color=COULEUR_C_MOINS, linewidth=1.2,
               label="C- (descendantes)"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9, framealpha=0.9)

    # --- Titre informatif ---
    titre = (
        "Tuyere supersonique MOC  |  "
        f"Me = {result['Me_exit']:.3f} (cible {result['Me_target']:.2f})  |  "
        f"theta_max = {result['theta_max_deg']:.2f} deg  |  "
        f"L = {result['L_nozzle']:.2f} mm  |  "
        f"A/A* = {result['area_ratio_moc']:.3f} "
        f"(isentropique: {result['area_ratio_isen']:.3f})"
    )
    ax.set_title(titre, fontsize=10)

    fig.tight_layout()

    if savepath is not None:
        fig.savefig(savepath, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    return fig, ax


def _trace_caracteristiques_miroir(ax, result, alpha=0.35, linewidth=0.6):
    """Version symetrisee (y -> -y) de `_trace_caracteristiques`, utilisee
    pour afficher la moitie basse de la tuyere quand `mirror=True`."""
    rows = result["rows"]
    wall = result["wall"]

    for row in rows:
        xs = [node.x for node in row]
        ys = [-node.y for node in row]
        ax.plot(xs, ys, color=COULEUR_C_MOINS, linewidth=linewidth,
                 alpha=alpha, zorder=2)

    for i in range(1, len(rows)):
        prev_row = rows[i - 1]
        cur_row = rows[i]
        for k in range(1, len(prev_row)):
            x0, y0 = prev_row[k].x, -prev_row[k].y
            x1, y1 = cur_row[k].x, -cur_row[k].y
            ax.plot([x0, x1], [y0, y1], color=COULEUR_C_PLUS,
                     linewidth=linewidth, alpha=alpha, zorder=2)

    last_row = rows[-1]
    for m in range(1, len(wall)):
        x0, y0 = last_row[m].x, -last_row[m].y
        x1, y1 = wall[m].x, -wall[m].y
        ax.plot([x0, x1], [y0, y1], color=COULEUR_C_PLUS,
                 linewidth=linewidth, alpha=alpha, zorder=2)


if __name__ == "__main__":
    # Exemple de test : ne doit jamais ouvrir de fenetre bloquante -> backend
    # 'Agg' force explicitement, et show=False (on sauvegarde seulement).
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt  # noqa: F811 (re-import apres switch backend)

    from moc_nozzle import design_nozzle

    resultat = design_nozzle(10.0, 2.4)

    fig, ax = plot_nozzle(resultat, mirror=True, show_nodes=True,
                          annotate_mach=True, savepath="tuyere.png",
                          show=False)
    plt.close(fig)

    print("Figure enregistree : tuyere.png")
    print(f"  Me_exit = {resultat['Me_exit']:.4f}  "
          f"(cible {resultat['Me_target']})")
    print(f"  theta_max = {resultat['theta_max_deg']:.3f} deg")
    print(f"  L_nozzle = {resultat['L_nozzle']:.3f} mm, "
          f"R_exit = {resultat['R_exit']:.3f} mm")
    print(f"  A/A* (MOC) = {resultat['area_ratio_moc']:.4f}  "
          f"vs isentropique = {resultat['area_ratio_isen']:.4f}")
