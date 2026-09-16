# scripts/04_relations_typees.py
# Objectif : mesurer, pour chaque type de relation, les types d'entités qu'il relie
# et sa fréquence RESTREINTE au schéma d'extraction retenu.

import yaml
from collections import Counter, defaultdict

CHEMIN = "data/raw/indication_paths.yaml"

TYPES_RETENUS = {
    "Drug", "Disease", "BiologicalProcess",
    "Protein", "ChemicalSubstance", "PhenotypicFeature",
    "OrganismTaxon",
}
FUSIONS = {
    "MolecularActivity": "BiologicalProcess",
    "Pathway": "BiologicalProcess",
    "GeneFamily": "Protein",
}

def normaliser(label):
    return FUSIONS.get(label, label)

print("Chargement en cours...")
with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)
print("Chargement terminé.\n")

med_total = defaultdict(set)        # médicaments, tous usages confondus
med_utilisable = defaultdict(set)   # médicaments, extrémités dans le schéma
paires = defaultdict(Counter)       # (type source, type cible) par relation

for chemin in donnees:
    medicament = chemin["graph"].get("drug", "<inconnu>")
    type_par_id = {n["id"]: normaliser(n["label"]) for n in chemin["nodes"]}

    for lien in chemin["links"]:
        relation = lien["key"]
        ts = type_par_id.get(lien["source"], "<?>")
        tt = type_par_id.get(lien["target"], "<?>")

        med_total[relation].add(medicament)
        paires[relation][(ts, tt)] += 1

        if ts in TYPES_RETENUS and tt in TYPES_RETENUS:
            med_utilisable[relation].add(medicament)

# --- Relations exploitables, triées par fréquence dans le schéma
exploitables = [
    (r, len(med_utilisable[r]), len(med_total[r]))
    for r in med_total
    if med_utilisable[r]
]
exploitables.sort(key=lambda x: x[1], reverse=True)

print("=== RELATIONS EXPLOITABLES (extrémités dans le schéma) ===")
print(f"{'Relation':<32}{'Utilisable':>11}{'Total':>8}   Paires de types dominantes")
for relation, utilisable, total in exploitables[:25]:
    top = paires[relation].most_common(2)
    resume = " ; ".join(f"{s}→{t}" for (s, t), _ in top)
    print(f"{relation:<32}{utilisable:>11}{total:>8}   {resume}")

# --- Relations perdues à cause des exclusions d'entités
perdues = [(r, len(m)) for r, m in med_total.items() if not med_utilisable[r]]
perdues.sort(key=lambda x: x[1], reverse=True)

print("\n=== RELATIONS DEVENUES INUTILISABLES ===")
for relation, total in perdues[:15]:
    (s, t), _ = paires[relation].most_common(1)[0]
    print(f"{relation:<32}{total:>6} médicaments   (ex. {s} → {t})")

print(f"\nRelations exploitables : {len(exploitables)} / {len(med_total)}")