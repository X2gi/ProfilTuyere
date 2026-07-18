---
name: feedback-commits-reguliers
description: "L'utilisateur veut des petits commits reguliers pendant le travail, pas un unique commit final"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b034988e-6443-49ce-8c80-62d7a74702d9
  modified: 2026-07-18T11:24:02.991Z
---

Pendant que j'ecris/modifie des fichiers, je dois faire de **petits commits
reguliers** a chaque etape logique (nouvelle fonction, correction, doc), au lieu
d'accumuler tout le travail et de laisser l'utilisateur faire un gros commit
final lui-meme.

**Why:** Sur le projet ProfilTuyere, j'ai tout ecrit sans commiter et
l'utilisateur a du faire le commit « v1 générée » a la fin ; il a explicitement
demande que ce soit moi qui commite au fil de l'eau.

**How to apply:** Committer des que qu'une unite coherente est terminee et
verifiee, avec un message clair. Le depot travaille directement sur `main`
(workflow de l'utilisateur, remote origin present). Cette regle est aussi
inscrite dans le `CLAUDE.md` du projet. Voir [[project-profil-tuyere]].
