#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
=======

Point d'entree en ligne de commande pour la conception du divergent d'une
tuyere supersonique axisymetrique par la methode des caracteristiques (MOC).

Ce module ne contient AUCUN calcul aerodynamique : il se contente d'orchestrer
les fonctions fournies par `moc_nozzle.py` (calcul du maillage / de la paroi)
et par `plot_nozzle.py` (trace graphique), et de mettre en forme les resultats
(bilan synthetique + tableau detaille des noeuds) pour l'utilisateur.

Exemple d'utilisation :
    python3 main.py
    python3 main.py --dcol 20 --mach 3.0 --n 30 --table --save tuyere.png
"""

import argparse
import math
import sys

from moc_nozzle import design_nozzle, all_nodes, isentropic_ratios
from plot_nozzle import plot_nozzle


def build_parser():
    """Construit l'analyseur de ligne de commande (argparse)."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Conception du divergent d'une tuyere supersonique axisymetrique "
            "par la methode des caracteristiques (MOC), avec amorcage par un "
            "arc de cercle au col et section de redressement pour un "
            "ecoulement uniforme en sortie. Toutes les longueurs sont en "
            "millimetres."
        ),
    )
    parser.add_argument(
        "--dcol", type=float, default=10.0,
        help="Diametre du col en mm (defaut : 10.0)."
    )
    parser.add_argument(
        "--mach", type=float, default=2.4,
        help="Nombre de Mach de sortie vise (defaut : 2.4)."
    )
    parser.add_argument(
        "--gamma", type=float, default=1.4,
        help="Rapport des chaleurs specifiques gamma (defaut : 1.4, air)."
    )
    parser.add_argument(
        "--rc", type=float, default=1.5,
        help="Rayon de l'arc au col, en multiple du rayon de col "
             "(Rc = rc * Rt) (defaut : 1.5)."
    )
    parser.add_argument(
        "--n", type=int, default=20,
        help="Nombre de caracteristiques (finesse du maillage) (defaut : 20)."
    )
    parser.add_argument(
        "--no-match", action="store_true",
        help="Ne pas ajuster theta_max pour atteindre exactement le Mach de "
             "sortie vise (equivaut a match_exit=False)."
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="Chemin de sauvegarde de la figure (PNG). Non sauvegardee si "
             "omis."
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="Ne pas afficher la fenetre graphique (utile sans interface "
             "graphique / en mode batch)."
    )
    parser.add_argument(
        "--table", action="store_true",
        help="Imprimer le tableau detaille de tous les noeuds du maillage."
    )
    return parser


def print_summary(result):
    """Imprime un bilan synthetique et lisible de la tuyere concue."""
    Rt = result["Rt"]
    ecart_pct = 100.0 * (
        (result["area_ratio_moc"] - result["area_ratio_isen"])
        / result["area_ratio_isen"]
    )
    nb_noeuds = len(all_nodes(result))

    print("=" * 60)
    print("BILAN DE CONCEPTION DE LA TUYERE (MOC axisymetrique)")
    print("=" * 60)
    print(f"Diametre du col          : {2.0 * Rt:.4f} mm  (Rt = {Rt:.4f} mm)")
    print(f"Rayon de l'arc au col    : {result['Rc']:.4f} mm")
    print(f"Mach de sortie vise      : {result['Me_target']:.4f}")
    print(f"Mach de sortie obtenu    : {result['Me_exit']:.4f}")
    print(f"Theta max (angle paroi)  : {result['theta_max_deg']:.4f} deg")
    print(f"Longueur du divergent    : {result['L_nozzle']:.4f} mm")
    print(f"Rayon de sortie          : {result['R_exit']:.4f} mm")
    print(f"Rapport de sections MOC  : {result['area_ratio_moc']:.6f}")
    print(f"Rapport de sections isen.: {result['area_ratio_isen']:.6f}")
    print(f"Ecart MOC / isentropique : {ecart_pct:+.3f} %")
    print(f"Gamma utilise            : {result['gamma']:.4f}")
    print(f"Nombre de caracteristiques (n) : {result['n']}")
    print(f"Nombre total de noeuds   : {nb_noeuds}")
    print("=" * 60)


def print_table(result):
    """Imprime le tableau detaille de tous les noeuds du maillage."""
    gamma = result["gamma"]
    nodes = all_nodes(result)

    header = (
        f"{'idx':>4} | {'x (mm)':>10} | {'y (mm)':>10} | {'M':>7} | "
        f"{'theta (deg)':>11} | {'nu (deg)':>9} | {'p/p0':>8} | {'T/T0':>8}"
    )
    print(header)
    print("-" * len(header))
    for i, node in enumerate(nodes):
        T_T0, p_p0, _rho_rho0 = isentropic_ratios(node.M, gamma)
        theta_deg = math.degrees(node.theta)
        nu_deg = math.degrees(node.nu)
        print(
            f"{i:>4} | {node.x:>10.4f} | {node.y:>10.4f} | {node.M:>7.4f} | "
            f"{theta_deg:>11.4f} | {nu_deg:>9.4f} | {p_p0:>8.4f} | {T_T0:>8.4f}"
        )


def main(argv=None):
    """Point d'entree principal : parse les arguments, concoit la tuyere,
    imprime les resultats et trace le profil."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = design_nozzle(
            D_throat=args.dcol,
            Me=args.mach,
            gamma=args.gamma,
            Rc_ratio=args.rc,
            n=args.n,
            match_exit=not args.no_match,
        )
    except ValueError as exc:
        print(f"Erreur de conception : {exc}", file=sys.stderr)
        sys.exit(1)

    print_summary(result)

    if args.table:
        print()
        print_table(result)

    plot_nozzle(result, savepath=args.save, show=not args.no_show)


if __name__ == "__main__":
    main()
