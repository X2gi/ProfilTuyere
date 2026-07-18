---
name: feedback-sous-agents-sonnet
description: "Utiliser des sous-agents Sonnet pour les taches de code simples, garder Opus pour le reste"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b034988e-6443-49ce-8c80-62d7a74702d9
  modified: 2026-07-18T11:24:11.721Z
---

Pour les taches de code **simples et bien specifiees** (fichiers periph., CLI,
visualisation, doc), deleguer a des sous-agents **Sonnet** (jusqu'a 3) plutot
que de « gaspiller » Opus.

**Why:** L'utilisateur l'a demande explicitement en cours de projet
(« Tu peux utiliser jusqu'a 3 sous agents sonnet pour les taches de code simple,
pas la peine de gaspiller opus »).

**How to apply:** Garder Opus pour la partie a fort enjeu (physique/algorithme,
debug fin, decisions d'architecture) ; donner aux sous-agents Sonnet un contrat
d'interface precis + une consigne de verification autonome, puis relire/verifier
leur sortie. Voir [[project-profil-tuyere]].
