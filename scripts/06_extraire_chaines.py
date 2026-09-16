# scripts/06_extraire_chaines.py
# Objectif : valider la linéarité des chemins candidats, reconstruire les chaînes
# dans l'ordre Drug → ... → Disease, et les matérialiser en JSON.

import yaml
import json
from collections import Counter, defaultdict

CHEMIN = "data/raw/indication_paths.yaml"
SORTIE = "data/processed/chaines_candidates.json"

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

def reconstruire(chemin, types):
    """Retourne la liste ordonnée des liens si le chemin est une ligne simple
    Drug → ... → Disease, sinon None."""
    liens = chemin["links"]
    sortants = defaultdict(list)
    entrants = Counter()
    for lien in liens:
        sortants[lien["source"]].append(lien)
        entrants[lien["target"]] += 1

    departs = [i for i, t in types.items() if t == "Drug" and entrants[i] == 0]
    if len(departs) != 1:
        return None

    courant = departs[0]
    ordonnes = []
    vus = {courant}
    while courant in sortants:
        if len(sortants[courant]) != 1:
            return None                      # branche
        lien = sortants[courant][0]
        ordonnes.append(lien)
        courant = lien["target"]
        if courant in vus:
            return None                      # cycle
        vus.add(courant)

    if types.get(courant) != "Disease":
        return None
    if len(ordonnes) != len(liens):
        return None                          # liens non parcourus
    return ordonnes

print("Chargement en cours...")
with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)
print("Chargement terminé.\n")

chaines = []
motifs = Counter()
rejets = Counter()

for chemin in donnees:
    liens = chemin["links"]
    types = {n["id"]: normaliser(n["label"]) for n in chemin["nodes"]}
    noms = {n["id"]: n["name"] for n in chemin["nodes"]}

    if not (2 <= len(liens) <= 3):
        rejets["longueur hors 2-3 sauts"] += 1
        continue
    if any(l["key"] == "treats" for l in liens):
        rejets["contient une arête treats"] += 1
        continue
    if not all(t in TYPES_RETENUS for t in types.values()):
        rejets["type hors schéma"] += 1
        continue
    if not all(l["key"] in RELATIONS_RETENUES for l in liens):
        rejets["relation hors schéma"] += 1
        continue

    ordonnes = reconstruire(chemin, types)
    if ordonnes is None:
        rejets["structure non linéaire"] += 1
        continue

    etapes = [
        {
            "source": noms[l["source"]], "source_id": l["source"],
            "source_type": types[l["source"]],
            "relation": l["key"],
            "cible": noms[l["target"]], "cible_id": l["target"],
            "cible_type": types[l["target"]],
        }
        for l in ordonnes
    ]
    motif = " → ".join(
        [etapes[0]["source_type"]] + [e["cible_type"] for e in etapes]
    )
    motifs[motif] += 1

    chaines.append({
        "id": chemin["graph"].get("_id"),
        "medicament": chemin["graph"].get("drug"),
        "maladie": chemin["graph"].get("disease"),
        "n_sauts": len(etapes),
        "motif": motif,
        "entites_pont": [e["cible"] for e in etapes[:-1]],
        "etapes": etapes,
    })

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(chaines, fichier, ensure_ascii=False, indent=2)

par_medicament = Counter(c["medicament"] for c in chaines)

print(f"Chaînes linéaires validées : {len(chaines)}")
print(f"Médicaments concernés      : {len(par_medicament)}")
print(f"Fichier écrit              : {SORTIE}\n")

print("=== MOTIFS VALIDÉS ===")
for motif, n in motifs.most_common():
    print(f"{n:>5}   {motif}")

print("\n=== MOTIFS DE REJET ===")
for motif, n in rejets.most_common():
    print(f"{n:>5}   {motif}")

print("\n=== MÉDICAMENTS AVEC LE PLUS DE CHAÎNES ===")
for medicament, n in par_medicament.most_common(20):
    print(f"{n:>3}   {medicament}")