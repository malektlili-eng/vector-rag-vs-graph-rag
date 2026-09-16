# scripts/32_inventaire_extraction.py
# Objectif : caractériser la sortie brute de l'extraction avant tout traitement.

import json
from collections import Counter

FICHIER = "data/processed/extraction.jsonl"

TYPES = {"Drug", "Protein", "ChemicalSubstance", "BiologicalProcess",
         "PhenotypicFeature", "Disease", "OrganismTaxon"}
RELATIONS = {"positively regulates", "negatively regulates",
             "increases activity of", "decreases activity of",
             "increases abundance of", "decreases abundance of",
             "positively correlated with", "negatively correlated with",
             "participates in", "manifestation of", "causes"}

enregistrements = []
with open(FICHIER, "r", encoding="utf-8") as fichier:
    for ligne in fichier:
        ligne = ligne.strip()
        if ligne:
            enregistrements.append(json.loads(ligne))

relations = [r for e in enregistrements for r in e["relations"]]
vides = [e for e in enregistrements if not e["relations"]]
echecs = [e for e in enregistrements if e.get("erreur")]
durees = [e["duree"] for e in enregistrements]

print("=== VOLUME ===")
print(f"Abstracts traités     : {len(enregistrements)}")
print(f"  sans aucune relation : {len(vides)} "
      f"({len(vides) * 100 // len(enregistrements)} %)")
print(f"  échecs de parsing    : {len(echecs)}")
print(f"Relations extraites   : {len(relations)}")
print(f"  moyenne par abstract : {len(relations) / len(enregistrements):.1f}")
print(f"Durée totale          : {sum(durees) / 60:.1f} min "
      f"({sum(durees) / len(durees):.1f} s/abstract)")

print("\n=== PRÉDICATS CONFORMES ===")
conformes = Counter(r.get("relation") for r in relations
                    if r.get("relation") in RELATIONS)
for predicat, n in conformes.most_common():
    print(f"{n:>6}   {predicat}")
print(f"{sum(conformes.values()):>6}   TOTAL conforme "
      f"({sum(conformes.values()) * 100 // max(len(relations), 1)} %)")

print("\n=== PRÉDICATS HORS SCHÉMA ===")
hors = Counter(r.get("relation") for r in relations
               if r.get("relation") not in RELATIONS)
print(f"{sum(hors.values())} relations, {len(hors)} libellés distincts\n")
for predicat, n in hors.most_common(40):
    print(f"{n:>6}   {predicat}")
if len(hors) > 40:
    print(f"         ... et {len(hors) - 40} autres libellés")

print("\n=== TYPES D'ENTITÉS HORS SCHÉMA ===")
types_hors = Counter()
for r in relations:
    for champ in ("source_type", "target_type"):
        if r.get(champ) not in TYPES:
            types_hors[r.get(champ)] += 1
for type_e, n in types_hors.most_common(15):
    print(f"{n:>6}   {type_e}")
if not types_hors:
    print("   (aucun)")

print("\n=== ENTITÉS LES PLUS FRÉQUENTES ===")
entites = Counter()
for r in relations:
    for champ in ("source", "target"):
        valeur = r.get(champ)
        if isinstance(valeur, str) and valeur.strip():
            entites[valeur.strip()] += 1
print(f"{len(entites)} entités distinctes\n")
for entite, n in entites.most_common(20):
    print(f"{n:>6}   {entite[:60]}")