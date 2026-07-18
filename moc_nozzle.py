# -*- coding: utf-8 -*-
"""
moc_nozzle.py
=============

Conception du DIVERGENT d'une tuyere supersonique AXISYMETRIQUE par la
METHODE DES CARACTERISTIQUES (MOC).

Principe general
----------------
En ecoulement supersonique, permanent, isentropique et irrotationnel, les
equations d'Euler sont hyperboliques : l'information se propage le long de deux
familles de lignes caracteristiques (les ondes de Mach) :

    - C+  (dite "montante")   : pente  dy/dx = tan(theta + mu)
    - C-  (dite "descendante"): pente  dy/dx = tan(theta - mu)

ou  theta = angle local de l'ecoulement,  mu = asin(1/M) = angle de Mach.

Le long de chaque caracteristique existe une RELATION DE COMPATIBILITE. En
ecoulement PLAN, ce sont les invariants de Riemann :

    le long de C- :  theta + nu = cste
    le long de C+ :  theta - nu = cste          (nu = fonction de Prandtl-Meyer)

En AXISYMETRIQUE, un terme source (en 1/y, y = distance a l'axe) s'ajoute : les
invariants ne sont plus constants. On resout alors le maillage de proche en
proche ("unit processes") par un schema predicteur-correcteur, ce qui donne la
valeur EXACTE des grandeurs a chaque noeud d'intersection des caracteristiques.

Formulation utilisee
--------------------
On travaille en composantes cartesiennes de vitesse (u suivant l'axe x, v suivant
le rayon y). En posant la vitesse du son d'arret a0 = 1 (les positions restent en
millimetres), la relation de compatibilite le long d'une caracteristique de pente
lambda, derivee des equations d'Euler (voir demonstration ci-dessous), s'ecrit :

    A.du + B.dv + S.dx = 0
    avec  A = 2.u.v.lambda + a^2 - v^2
          B = -(a^2 - v^2).lambda
          S = (a^2 . v / y) . lambda^2          (S = 0 en ecoulement plan)

On verifie que, dans le cas plan (S = 0) et au voisinage de theta = 0, cette
relation redonne exactement  dtheta = +/- dnu, c.-a-d. les invariants de Riemann.
C'est la garantie de correction de la formulation.

References : Anderson, "Modern Compressible Flow", ch. 11 ;
             Zucrow & Hoffman, "Gas Dynamics", vol. 2.
"""

import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1) RELATIONS THERMODYNAMIQUES ET GEOMETRIQUES DE BASE
# ---------------------------------------------------------------------------

def prandtl_meyer(M, gamma):
    """Fonction de Prandtl-Meyer nu(M), en radians.

    nu(M) est l'angle dont un ecoulement sonique (M=1) doit tourner pour
    atteindre le nombre de Mach M par une detente isentropique.
    """
    if M < 1.0:
        # Physiquement nu n'est defini que pour M >= 1 ; on borne a 0.
        return 0.0
    g = gamma
    b = math.sqrt((g + 1.0) / (g - 1.0))
    t = math.sqrt(M * M - 1.0)
    return b * math.atan(t / b) - math.atan(t)


def prandtl_meyer_max(gamma):
    """Angle de detente maximal nu(M -> inf) : la detente ne peut pas depasser
    cette valeur (limite du vide)."""
    g = gamma
    return (math.pi / 2.0) * (math.sqrt((g + 1.0) / (g - 1.0)) - 1.0)


def inverse_prandtl_meyer(nu_target, gamma, tol=1e-12, itmax=100):
    """Inversion nu -> M par Newton-Raphson.

    On cherche M tel que prandtl_meyer(M) = nu_target. La derivee analytique
    dnu/dM = sqrt(M^2 - 1) / (M . (1 + (g-1)/2 . M^2)) accelere la convergence.
    """
    if nu_target <= 0.0:
        return 1.0
    nu_max = prandtl_meyer_max(gamma)
    # On reste strictement sous la limite du vide pour eviter M -> infini.
    nu_target = min(nu_target, nu_max * (1.0 - 1e-9))
    g = gamma
    M = 2.0  # estimation initiale
    for _ in range(itmax):
        f = prandtl_meyer(M, g) - nu_target
        dnu_dM = math.sqrt(M * M - 1.0) / (M * (1.0 + 0.5 * (g - 1.0) * M * M))
        step = f / dnu_dM
        M -= step
        if M < 1.0 + 1e-9:
            M = 1.0 + 1e-9  # on ne redescend pas dans le subsonique
        if abs(step) < tol:
            break
    return M


def mach_angle(M):
    """Angle de Mach mu = asin(1/M) (radians). Borne a M >= 1 (mu <= 90 deg)."""
    return math.asin(1.0 / max(M, 1.0))


def sound_speed(M, gamma):
    """Vitesse du son locale a, avec la convention vitesse du son d'arret a0 = 1.

    Relation energie : a^2 = a0^2 - (g-1)/2 . V^2  et  V = M.a
    => a = 1 / sqrt(1 + (g-1)/2 . M^2)
    """
    return 1.0 / math.sqrt(1.0 + 0.5 * (gamma - 1.0) * M * M)


def isentropic_ratios(M, gamma):
    """Rapports isentropiques (grandeur locale / grandeur d'arret) : T/T0, p/p0,
    rho/rho0. Fournis pour documenter l'etat "exact" a chaque noeud."""
    g = gamma
    T_T0 = 1.0 / (1.0 + 0.5 * (g - 1.0) * M * M)
    p_p0 = T_T0 ** (g / (g - 1.0))
    rho_rho0 = T_T0 ** (1.0 / (g - 1.0))
    return T_T0, p_p0, rho_rho0


def area_mach_relation(M, gamma):
    """Rapport de sections isentropique A/A* (relation de Hugoniot).

    Sert de verification independante : pour une tuyere axisymetrique,
    A/A* = (R_sortie / R_col)^2 doit egaler A/A*(Me).
    """
    g = gamma
    return (1.0 / M) * ((2.0 / (g + 1.0)) *
                        (1.0 + 0.5 * (g - 1.0) * M * M)) ** ((g + 1.0) / (2.0 * (g - 1.0)))


# ---------------------------------------------------------------------------
# 2) NOEUD DU MAILLAGE
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """Un noeud du maillage des caracteristiques : position (mm) + etat de
    l'ecoulement. u, v sont les composantes de vitesse (avec a0 = 1)."""
    x: float          # position axiale (mm)
    y: float          # position radiale = distance a l'axe (mm)
    theta: float      # angle de l'ecoulement (rad)
    nu: float         # angle de Prandtl-Meyer (rad)
    M: float          # nombre de Mach
    mu: float         # angle de Mach (rad)
    u: float          # composante axiale de vitesse (a0 = 1)
    v: float          # composante radiale de vitesse (a0 = 1)


def make_node(x, y, theta, M, gamma):
    """Construit un noeud complet a partir de la position, de l'angle
    d'ecoulement et du nombre de Mach."""
    a = sound_speed(M, gamma)
    V = M * a
    return Node(x=x, y=y, theta=theta,
                nu=prandtl_meyer(M, gamma), M=M, mu=mach_angle(M),
                u=V * math.cos(theta), v=V * math.sin(theta))


def _state_from_uv(u, v, gamma):
    """Reconstruit (theta, M, mu, a) a partir des composantes de vitesse."""
    V = math.hypot(u, v)
    a2 = 1.0 - 0.5 * (gamma - 1.0) * V * V     # a^2 = a0^2 - (g-1)/2 V^2, a0=1
    a2 = max(a2, 1e-12)
    a = math.sqrt(a2)
    M = V / a
    theta = math.atan2(v, u)
    mu = mach_angle(M) if M > 1.0 else math.pi / 2.0
    return theta, M, mu, a


# ---------------------------------------------------------------------------
# 3) "UNIT PROCESSES" DE LA METHODE DES CARACTERISTIQUES
#    (schema predicteur-correcteur : coefficients moyennes -> solution exacte)
# ---------------------------------------------------------------------------

def _compat_coeffs(u, v, a, lam, y):
    """Coefficients (A, B, S) de la relation de compatibilite  A.du+B.dv+S.dx=0
    le long d'une caracteristique de pente lam, au point (u, v, a, y)."""
    a2 = a * a
    A = 2.0 * u * v * lam + a2 - v * v
    B = -(a2 - v * v) * lam
    # Terme source axisymetrique (nul si v = 0, c.-a-d. sur l'axe). Le signe
    # decoule de la continuite axisymetrique : (a^2-u^2)u_x - uv(u_y+v_x)
    # + (a^2-v^2)v_y = -a^2 v/y.
    S = 0.0 if abs(v) < 1e-14 else -(a2 * v / y) * lam * lam
    return A, B, S


def interior_point(p_minus, p_plus, gamma, n_corr=4):
    """Point INTERIEUR : intersection de la C- passant par p_minus (en haut a
    gauche) et de la C+ passant par p_plus (en bas a gauche).

    On resout simultanement :
      - la geometrie   : intersection des deux caracteristiques,
      - la compatibilite : 2 equations lineaires -> (u, v) au nouveau point.
    Schema predicteur-correcteur type Heun : les coefficients (A, B, S) sont la
    MOYENNE des valeurs aux deux extremites de chaque caracteristique (integration
    trapezoidale). Ce choix annule proprement le terme source sur l'axe (ou v=0)
    et donne la solution "exacte" a convergence.
    """
    # Etat courant du nouveau point (initialise par la moyenne des amonts).
    th3 = 0.5 * (p_minus.theta + p_plus.theta)
    M3 = 0.5 * (p_minus.M + p_plus.M)
    mu3 = mach_angle(M3)
    x3 = y3 = 0.0

    for k in range(n_corr):
        # --- Pentes des deux caracteristiques (predicteur : amont ; puis
        #     correcteur : moyenne amont <-> nouveau point) ---
        if k == 0:
            th_m, mu_m = p_minus.theta, p_minus.mu
            th_p, mu_p = p_plus.theta, p_plus.mu
        else:
            th_m = 0.5 * (p_minus.theta + th3); mu_m = 0.5 * (p_minus.mu + mu3)
            th_p = 0.5 * (p_plus.theta + th3);  mu_p = 0.5 * (p_plus.mu + mu3)
        lam_m = math.tan(th_m - mu_m)   # pente C- (descendante)
        lam_p = math.tan(th_p + mu_p)   # pente C+ (montante)

        # --- Geometrie : intersection des deux droites caracteristiques ---
        # C- :  y - y_m = lam_m (x - x_m)   ;   C+ :  y - y_p = lam_p (x - x_p)
        x3 = (lam_m * p_minus.x - lam_p * p_plus.x + p_plus.y - p_minus.y) \
            / (lam_m - lam_p)
        y3 = p_minus.y + lam_m * (x3 - p_minus.x)

        # --- Etats moyens (amont <-> nouveau point) pour les coefficients ---
        if k == 0:
            sm = (p_minus.u, p_minus.v, sound_speed(p_minus.M, gamma),
                  0.5 * (p_minus.y + y3))
            sp = (p_plus.u, p_plus.v, sound_speed(p_plus.M, gamma),
                  0.5 * (p_plus.y + y3))
        else:
            a3 = sound_speed(M3, gamma); V3 = M3 * a3
            u3g, v3g = V3 * math.cos(th3), V3 * math.sin(th3)
            sm = (0.5 * (p_minus.u + u3g), 0.5 * (p_minus.v + v3g),
                  0.5 * (sound_speed(p_minus.M, gamma) + a3), 0.5 * (p_minus.y + y3))
            sp = (0.5 * (p_plus.u + u3g), 0.5 * (p_plus.v + v3g),
                  0.5 * (sound_speed(p_plus.M, gamma) + a3), 0.5 * (p_plus.y + y3))

        A1, B1, S1 = _compat_coeffs(sm[0], sm[1], sm[2], lam_m, sm[3])
        A2, B2, S2 = _compat_coeffs(sp[0], sp[1], sp[2], lam_p, sp[3])

        # --- Systeme lineaire 2x2 en (u3, v3) ---
        #  A1 u3 + B1 v3 = A1 u_m + B1 v_m - S1 (x3 - x_m)  = C1
        #  A2 u3 + B2 v3 = A2 u_p + B2 v_p - S2 (x3 - x_p)  = C2
        C1 = A1 * p_minus.u + B1 * p_minus.v - S1 * (x3 - p_minus.x)
        C2 = A2 * p_plus.u + B2 * p_plus.v - S2 * (x3 - p_plus.x)
        det = A1 * B2 - A2 * B1
        u3 = (C1 * B2 - C2 * B1) / det
        v3 = (A1 * C2 - A2 * C1) / det

        th3, M3, mu3, _ = _state_from_uv(u3, v3, gamma)

    return make_node(x3, y3, th3, M3, gamma)


def axis_point(p_minus, gamma, n_corr=4):
    """Point sur l'AXE (y = 0) : par symetrie theta = 0, v = 0.

    La C- issue de p_minus atteint l'axe ; la relation de compatibilite le long
    de cette C- fournit alors la vitesse (donc le Mach) sur l'axe. Le terme
    source s'annule a l'extremite "axe" (v = 0) : la moyenne trapezoidale ne
    retient donc que la moitie de la contribution du point amont.
    """
    M3, mu3 = p_minus.M, p_minus.mu
    a3 = sound_speed(M3, gamma); u3 = M3 * a3
    am = sound_speed(p_minus.M, gamma)
    x3 = p_minus.x - p_minus.y / math.tan(p_minus.theta - p_minus.mu)

    for _ in range(n_corr):
        lam_m = math.tan(0.5 * (p_minus.theta + 0.0) - 0.5 * (p_minus.mu + mu3))
        x3 = p_minus.x - p_minus.y / lam_m      # intersection C- / axe

        # Coefficients = moyenne (amont) et (axe, ou v = 0 -> source nulle).
        A1m, B1m, S1m = _compat_coeffs(p_minus.u, p_minus.v, am, lam_m, p_minus.y)
        A13, B13, S13 = _compat_coeffs(u3, 0.0, a3, lam_m, p_minus.y)  # v=0 -> S=0
        A1, B1, S1 = 0.5 * (A1m + A13), 0.5 * (B1m + B13), 0.5 * (S1m + S13)

        # A1 (u3 - u_m) + B1 (0 - v_m) + S1 (x3 - x_m) = 0
        u3 = p_minus.u + (B1 * p_minus.v - S1 * (x3 - p_minus.x)) / A1
        V3 = abs(u3)
        a3 = math.sqrt(max(1.0 - 0.5 * (gamma - 1.0) * V3 * V3, 1e-12))
        M3 = V3 / a3
        mu3 = mach_angle(M3)
    return make_node(x3, 0.0, 0.0, M3, gamma)


def wall_point(feed, wall_prev, gamma):
    """Point de PAROI de la section de redressement.

    La paroi est une ligne de courant : pour ANNULER l'onde C+ montante issue du
    point interieur `feed` (et rendre l'ecoulement uniforme), la paroi tourne de
    facon a epouser l'ecoulement. Le noeud de paroi herite donc de l'etat de
    `feed` (meme theta, meme Mach) ; sa position est l'intersection de :
      - la ligne de courant paroi (pente = moyenne des angles theta),
      - la caracteristique C+ issue de `feed`.
    """
    thetaW, MW, nuW, muW = feed.theta, feed.M, feed.nu, feed.mu
    sw = math.tan(0.5 * (wall_prev.theta + thetaW))     # pente de la paroi
    sc = math.tan(feed.theta + feed.mu)                 # pente de la C+ (montante)
    # Intersection paroi (issue de wall_prev) / C+ (issue de feed) :
    xW = (feed.y - wall_prev.y - sc * feed.x + sw * wall_prev.x) / (sw - sc)
    yW = wall_prev.y + sw * (xW - wall_prev.x)
    return make_node(xW, yW, thetaW, MW, gamma)


# ---------------------------------------------------------------------------
# 4) CONCEPTION COMPLETE DE LA TUYERE
# ---------------------------------------------------------------------------

def _build_field(D_throat, theta_max, gamma, n):
    """Construit le maillage complet pour un theta_max donne et renvoie
    (rows, wall, arc_pts). `rows[i]` = liste des noeuds de la i-eme C- (de la
    paroi vers l'axe). `wall` = noeuds de la paroi de redressement."""
    Rt = 0.5 * D_throat                       # rayon au col (mm)

    # --- Points de detente repartis sur l'arc de cercle du col ---
    # Rayon de l'arc gere par le parametre Rc_ratio dans design_nozzle ; ici on
    # recoit la geometrie via l'attribut de fonction (voir design_nozzle).
    Rc = _build_field.Rc                      # rayon de l'arc (mm)
    cx, cy = 0.0, Rt + Rc                      # centre de l'arc (au-dessus du col)

    expansion = []
    for i in range(1, n + 1):
        # Angle de paroi croissant de theta_max/n jusqu'a theta_max.
        th = theta_max * i / n
        # Position sur l'arc de cercle (tangent horizontal au col) :
        x = Rc * math.sin(th)
        y = cy - Rc * math.cos(th)
        # Hypothese d'onde simple (detente de Prandtl-Meyer depuis le sonique) :
        # au niveau de la paroi, nu = theta -> Mach local.
        M = inverse_prandtl_meyer(th, gamma)
        expansion.append(make_node(x, y, th, M, gamma))

    # --- Marche du maillage : reflexions successives sur l'axe ---
    rows = []
    prev = []
    for i in range(n):
        line = [expansion[i]]                 # depart au point de detente i
        # Intersections avec les C+ reflechies des lignes precedentes :
        for k in range(1, len(prev)):
            line.append(interior_point(line[k - 1], prev[k], gamma))
        # La C- atteint enfin l'axe :
        line.append(axis_point(line[-1], gamma))
        rows.append(line)
        prev = line

    # --- Paroi de redressement : on annule les C+ reflechies (derniere C-) ---
    last = rows[-1]                            # derniere C- (de E_n a l'axe A_n)
    wall = [last[0]]                           # depart : dernier point de l'arc E_n
    for m in range(1, len(last)):
        wall.append(wall_point(last[m], wall[-1], gamma))

    # --- Echantillonnage fin de l'arc pour un trace de paroi lisse ---
    arc_pts = []
    for j in range(101):
        th = theta_max * j / 100.0
        arc_pts.append((Rc * math.sin(th), cy - Rc * math.cos(th)))

    return rows, wall, arc_pts


def design_nozzle(D_throat, Me, gamma=1.4, Rc_ratio=1.5, n=20,
                  match_exit=True):
    """Concoit le divergent complet.

    Parametres
    ----------
    D_throat : diametre du col (mm)
    Me       : nombre de Mach de sortie vise
    gamma    : rapport des chaleurs specifiques (1.4 = air)
    Rc_ratio : rayon de l'arc au col en multiple du rayon de col (Rc = k.Rt)
    n        : nombre de caracteristiques (finesse du maillage)
    match_exit : si True, ajuste theta_max pour que le Mach de sortie = Me exact

    Retour : dictionnaire avec le maillage, la paroi, le profil et un bilan.
    """
    Rt = 0.5 * D_throat
    _build_field.Rc = Rc_ratio * Rt           # transmet la geometrie de l'arc

    # Estimation initiale : theta_max = nu(Me)/2 (resultat exact en plan).
    theta_max = 0.5 * prandtl_meyer(Me, gamma)

    def exit_mach(tmax):
        rows, wall, _ = _build_field(D_throat, tmax, gamma, n)
        return rows[-1][-1].M, rows, wall     # Mach sur l'axe en sortie (A_n)

    Me_calc, rows, wall = exit_mach(theta_max)

    # --- Bouclage (bissection) sur theta_max pour atteindre Me exactement ---
    # En axisymetrique, nu(Me)/2 n'est qu'une valeur de depart : le terme source
    # decale le Mach de sortie. Le Mach de sortie croit de facon monotone avec
    # theta_max, ce qui permet une bissection robuste (insensible aux etats
    # degeneres pres du col qui perturberaient une secante).
    if match_exit:
        lo, hi = math.radians(0.25), 0.5 * prandtl_meyer(Me, gamma)
        # On s'assure que hi encadre bien la cible (sinon on l'elargit).
        for _ in range(20):
            Mhi, _, _ = exit_mach(hi)
            if Mhi >= Me or hi >= math.radians(60.0):
                break
            hi *= 1.3
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            Mmid, rows_m, wall_m = exit_mach(mid)
            if not math.isfinite(Mmid):
                hi = mid                     # etat degenere -> on reduit
                continue
            if abs(Mmid - Me) < 1e-6:
                rows, wall = rows_m, wall_m
                theta_max = mid
                break
            if Mmid < Me:
                lo = mid
            else:
                hi = mid
            rows, wall, theta_max = rows_m, wall_m, mid
        Me_calc = rows[-1][-1].M

    _, _, arc_pts = _build_field(D_throat, theta_max, gamma, n)

    # --- Profil de paroi complet (rouge) : arc + section de redressement ---
    profile = list(arc_pts) + [(w.x, w.y) for w in wall[1:]]

    exit_node = wall[-1]
    R_exit = exit_node.y

    # --- Garde-fou : detecte un maillage degenere (Mach de sortie tres eleve,
    # gamma proche de 1, arc trop serre...) et echoue proprement au lieu de
    # renvoyer une geometrie aberrante. ---
    ok = (math.isfinite(R_exit) and R_exit > Rt
          and math.isfinite(exit_node.x) and exit_node.x > 0.0
          and abs(Me_calc - Me) < 0.02)
    if not ok:
        raise ValueError(
            "Maillage MOC degenere pour ces parametres "
            "(Me=%.2f, gamma=%.3f, n=%d). Essayez un Mach de sortie plus "
            "modere (typiquement 1.5-3.5 pour l'air) ou augmentez n."
            % (Me, gamma, n))

    # Verification : rapport de sections MOC vs relation isentropique.
    area_ratio_moc = (R_exit / Rt) ** 2
    area_ratio_isen = area_mach_relation(Me, gamma)

    return {
        "rows": rows,               # noeuds des C- (chaque C- : paroi -> axe)
        "wall": wall,               # noeuds de la paroi de redressement
        "arc_pts": arc_pts,         # echantillonnage fin de l'arc du col
        "profile": profile,         # profil de paroi (x, y) en mm
        "Rt": Rt,
        "Rc": Rc_ratio * Rt,
        "theta_max_deg": math.degrees(theta_max),
        "Me_target": Me,
        "Me_exit": Me_calc,
        "L_nozzle": exit_node.x,    # longueur du divergent (mm)
        "R_exit": R_exit,           # rayon de sortie (mm)
        "area_ratio_moc": area_ratio_moc,
        "area_ratio_isen": area_ratio_isen,
        "gamma": gamma,
        "n": n,
    }


def all_nodes(result):
    """Liste a plat de tous les noeuds interieurs/axe/paroi (pour le tableau)."""
    nodes = []
    for row in result["rows"]:
        nodes.extend(row)
    nodes.extend(result["wall"])
    return nodes
