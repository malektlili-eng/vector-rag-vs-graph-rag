# scripts/23_analyser_criblage.py
# Objectif : caractériser les chaînes retenues — seuil, motifs, profondeur —
# avant de fixer la sélection définitive.

import json
from collections import Counter

CRIBLAGE = "data/processed/criblage.json"

with open(CRIBLAGE, "r", encoding="utf-8") as fichier:
    resultats = json.load(fichier)

print("=== EFFET DU SEUIL ===")
print(f"{'seuil':>6}{'chaînes':>9}{'médicaments':>13}{'2 sauts':>9}{'3 sauts':>9}")
for seuil in (1, 2, 3, 4, 5, 10, 20):
    retenues = [r for r in resultats if r["minimum"] >= seuil]
    meds = {r["medicament"] for r in retenues}
    deux = sum(1 for r in retenues if r["n_sauts"] == 2)
    trois = sum(1 for r in retenues if r["n_sauts"] == 3)
    print(f"{seuil:>6}{len(retenues):>9}{len(meds):>13}{deux:>9}{trois:>9}")

SEUIL = 4
retenues = [r for r in resultats if r["minimum"] >= SEUIL]

print(f"\n=== MOTIFS DES CHAÎNES RETENUES (seuil {SEUIL}) ===")
for motif, n in Counter(r["motif"] for r in retenues).most_common():
    print(f"{n:>4}   {motif}")

print(f"\n=== MOTIFS DES CHAÎNES ÉCARTÉES ===")
ecartees = [r for r in resultats if r["minimum"] < SEUIL]
for motif, n in Counter(r["motif"] for r in ecartees).most_common(8):
    print(f"{n:>4}   {motif}")

print(f"\n=== CHAÎNES RETENUES (seuil {SEUIL}) ===")
for r in sorted(retenues, key=lambda x: -x["minimum"]):
    entites = " → ".join([r["etapes"][0]["source"]] +
                         [e["cible"] for e in r["etapes"]])
    print(f"\n  min {r['minimum']:>4} | {r['motif']}")
    print(f"  {entites[:110]}")