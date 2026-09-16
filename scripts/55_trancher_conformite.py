# scripts/55_trancher_conformite.py
# Objectif : départager les deux comptes de conformité au schéma, en calculant
# les deux définitions sur le même fichier d'extraction brute.

import json

EXTRACTION = "data/processed/extraction.jsonl"

SCHEMA = {
    "positively regulates", "negatively regulates",
    "positively correlated with", "negatively correlated with",
    "increases activity of", "decreases activity of",
    "increases abundance of", "decreases abundance of",
    "causes", "participates in", "manifestation of",
}

TYPES = {
    "Drug", "Disease", "BiologicalProcess", "Protein",
    "ChemicalSubstance", "PhenotypicFeature", "OrganismTaxon",
}

relations = []
with open(EXTRACTION, "r", encoding="utf-8") as fichier:
    for ligne in fichier:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            enregistrement = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if isinstance(enregistrement, dict) and "relations" in enregistrement:
            relations.extend(enregistrement["relations"])
        elif isinstance(enregistrement, list):
            relations.extend(enregistrement)
        elif isinstance(enregistrement, dict) and "relation" in enregistrement:
            relations.append(enregistrement)

print(f"Relations lues : {len(relations)}")

def predicat(r):
    return (r.get("relation") or r.get("predicate") or "").strip()

def types_valides(r):
    ts = r.get("source_type"), r.get("target_type")
    return all(t in TYPES for t in ts)

predicat_ok = [r for r in relations if predicat(r) in SCHEMA]
les_deux = [r for r in predicat_ok if types_valides(r)]
predicat_ok_type_ko = [r for r in predicat_ok if not types_valides(r)]

print(f"\nDéfinition A — prédicat au schéma seul   : {len(predicat_ok)}")
print(f"Définition B — prédicat ET types valides : {len(les_deux)}")
print(f"Écart (prédicat correct, type invalide)  : {len(predicat_ok_type_ko)}")

print("\n=== LES CAS DE L'ÉCART ===")
for r in predicat_ok_type_ko:
    print(f"  [{r.get('source_type')}] {str(r.get('source'))[:26]:<26}"
          f" --{predicat(r)[:22]:<22}--> "
          f"[{r.get('target_type')}] {str(r.get('target'))[:26]}")