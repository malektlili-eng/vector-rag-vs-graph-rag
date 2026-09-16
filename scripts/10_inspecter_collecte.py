# scripts/10_inspecter_collecte.py
# Objectif : examiner la distribution des longueurs et repérer les abstracts
# trop courts pour contenir une chaîne de relations.

import json
from collections import Counter

#FICHIER = "data/raw/pubmed_pilote.json"
FICHIER = "data/processed/corpus_pilote.json"

with open(FICHIER, "r", encoding="utf-8") as fichier:
    collecte = json.load(fichier)

par_medicament = Counter(a["medicament"] for a in collecte)
print("=== ABSTRACTS PAR MÉDICAMENT ===")
for medicament, n in par_medicament.most_common():
    print(f"{medicament:<22}{n:>4}")

longueurs = sorted(len(a["resume"].split()) for a in collecte)
print("\n=== DISTRIBUTION DES LONGUEURS ===")
for seuil in (50, 100, 150, 200, 300):
    n = sum(1 for l in longueurs if l < seuil)
    print(f"moins de {seuil:>3} mots : {n:>3} abstracts ({n * 100 // len(longueurs)} %)")

print("\n=== LES 8 PLUS COURTS ===")
courts = sorted(collecte, key=lambda a: len(a["resume"].split()))[:8]
for abstract in courts:
    n = len(abstract["resume"].split())
    print(f"\n[{n} mots] {abstract['medicament']} — PMID {abstract['pmid']} ({abstract['annee']})")
    print(f"  {abstract['titre'][:90]}")
    print(f"  {abstract['resume'][:180]}")

print("\n=== ANNÉES ===")
annees = Counter(a["annee"][:3] + "0s" for a in collecte if a["annee"])
for decennie, n in sorted(annees.items()):
    print(f"{decennie} : {n}")