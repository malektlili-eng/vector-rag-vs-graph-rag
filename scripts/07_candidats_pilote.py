# scripts/07_candidats_pilote.py
# Objectif : lister les médicaments disposant d'au moins une chaîne du motif dominant,
# afin de sélectionner les 5 médicaments du pilote.

import json
from collections import defaultdict

FICHIER = "data/processed/chaines_candidates.json"
MOTIF_CIBLE = "Drug → Protein → BiologicalProcess → Disease"

with open(FICHIER, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

par_medicament = defaultdict(list)
for chaine in chaines:
    par_medicament[chaine["medicament"]].append(chaine)

candidats = []
for medicament, liste in par_medicament.items():
    cibles = [c for c in liste if c["motif"] == MOTIF_CIBLE]
    if cibles:
        proteines = {c["etapes"][0]["cible"] for c in cibles}
        candidats.append((medicament, len(cibles), len(liste),
                          sorted(proteines), [c["maladie"] for c in cibles]))

candidats.sort(key=lambda x: (-x[1], -x[2]))

print(f"Médicaments avec au moins une chaîne du motif dominant : {len(candidats)}\n")
print(f"{'Médicament':<28}{'Cible':>6}{'Total':>7}   Protéine visée / maladies")
for medicament, n_cible, n_total, proteines, maladies in candidats[:30]:
    print(f"{medicament:<28}{n_cible:>6}{n_total:>7}   "
          f"{proteines[0][:34]} | {maladies[0][:28]}")