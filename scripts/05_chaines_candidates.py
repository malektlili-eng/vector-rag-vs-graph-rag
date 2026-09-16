# scripts/05_chaines_candidates.py
# Objectif : identifier les chemins DrugMechDB compatibles avec le schéma retenu
# et exploitables comme chaînes multi-hop de 2 à 3 sauts.

import yaml
from collections import Counter

CHEMIN = "data/raw/indication_paths.yaml"

TYPES_RETENUS = {
    "Drug", "Disease", "BiologicalProcess", "Protein",
    "ChemicalSubstance", "PhenotypicFeature", "OrganismTaxon",
}
FUSIONS = {
    "MolecularActivity": "BiologicalProcess",
    "Pathway": "BiologicalProcess",
    "GeneFamily": "Protein",
}
RELATIONS_RETENUES = {
    "positively regulates", "positively correlated with",
    "decreases activity of", "negatively regulates", "causes",
    "negatively correlated with", "participates in",
    "increases activity of", "manifestation of", "increases abundance of",
}

def normaliser(label):
    return FUSIONS.get(label, label)

print("Chargement en cours...")
with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)
print("Chargement terminé.\n")

compatibles = []
motifs = Counter()
rejets = Counter()

for chemin in donnees:
    liens = chemin["links"]
    types = {n["id"]: normaliser(n["label"]) for n in chemin["nodes"]}

    # Filtre 1 : longueur exploitable
    if not (2 <= len(liens) <= 3):
        rejets["longueur hors 2-3 sauts"] += 1
        continue

    # Filtre 2 : présence d'un raccourci treats
    if any(l["key"] == "treats" for l in liens):
        rejets["contient une arête treats"] += 1
        continue

    # Filtre 3 : tous les types dans le schéma
    if not all(t in TYPES_RETENUS for t in types.values()):
        rejets["type hors schéma"] += 1
        continue

    # Filtre 4 : toutes les relations dans le schéma
    if not all(l["key"] in RELATIONS_RETENUES for l in liens):
        rejets["relation hors schéma"] += 1
        continue

    compatibles.append(chemin)
    motif = " → ".join(
        [types[liens[0]["source"]]] + [types[l["target"]] for l in liens]
    )
    motifs[motif] += 1

medicaments = {c["graph"].get("drug") for c in compatibles}

print(f"Chemins compatibles     : {len(compatibles)} / {len(donnees)}")
print(f"Médicaments concernés   : {len(medicaments)}")

print("\n=== MOTIFS DE CHAÎNES DISPONIBLES ===")
for motif, n in motifs.most_common(15):
    print(f"{n:>5}   {motif}")

print("\n=== MOTIFS DE REJET ===")
for motif, n in rejets.most_common():
    print(f"{n:>5}   {motif}")