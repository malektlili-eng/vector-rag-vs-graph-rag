# scripts/53_verifier_jeu_de_test.py
# Objectif : recompter les effectifs du jeu de test à partir du fichier lui-même,
# afin de vérifier les chiffres rapportés dans le rapport.

import json
from collections import Counter

JEU = "data/processed/jeu_de_test.json"

with open(JEU, "r", encoding="utf-8") as fichier:
    jeu = json.load(fichier)

multihop = [q for q in jeu if q["id"].startswith("MH")]
singlehop = [q for q in jeu if q["id"].startswith("SH")]
ponts = [q["entite_pont"] for q in multihop if "entite_pont" in q]

print(f"Questions au total        : {len(jeu)}")
print(f"  multi-hop              : {len(multihop)}")
print(f"  single-hop (contrôle)  : {len(singlehop)}")
print(f"Entités ponts distinctes : {len(set(ponts))}")

print("\n=== ENTITÉS PONTS ===")
for pont, n in Counter(ponts).most_common():
    marque = "  ← partagée" if n > 1 else ""
    print(f"  {n}x  {pont}{marque}")

print("\n=== CATÉGORIES ===")
for categorie, n in Counter(q.get("categorie", "(absente)")
                            for q in jeu).most_common():
    print(f"  {n:>2}  {categorie}")

print("\n=== QUESTIONS SANS PMID ===")
sans = [q["id"] for q in jeu if not q.get("pmids")]
print(f"  {len(sans)}" + (f"  → {', '.join(sans)}" if sans else ""))