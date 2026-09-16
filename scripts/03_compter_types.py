# scripts/03_compter_types.py
# Objectif : compter, sur l'intégralité du dataset, les types d'entités et de
# relations, avec le nombre de médicaments distincts pour chacun (contrôle de biais).

import yaml
from collections import Counter, defaultdict

CHEMIN = "data/raw/indication_paths.yaml"

print("Chargement en cours...")
with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)
print("Chargement terminé.\n")

occurrences_types = Counter()
medicaments_par_type = defaultdict(set)

occurrences_relations = Counter()
medicaments_par_relation = defaultdict(set)

total_liens = 0
total_noeuds = 0

for chemin in donnees:
    medicament = chemin["graph"].get("drug", "<inconnu>")

    for noeud in chemin["nodes"]:
        type_entite = noeud["label"]
        occurrences_types[type_entite] += 1
        medicaments_par_type[type_entite].add(medicament)
        total_noeuds += 1

    for lien in chemin["links"]:
        type_relation = lien["key"]
        occurrences_relations[type_relation] += 1
        medicaments_par_relation[type_relation].add(medicament)
        total_liens += 1

print(f"Chemins : {len(donnees)}")
print(f"Nœuds   : {total_noeuds}")
print(f"Liens   : {total_liens}")
print(f"Médicaments distincts : "
      f"{len({c['graph'].get('drug') for c in donnees})}")

print("\n=== TYPES D'ENTITÉS ===")
print(f"{'Type':<28}{'Occurrences':>13}{'Médicaments':>14}")
for type_entite, n in occurrences_types.most_common():
    print(f"{type_entite:<28}{n:>13}{len(medicaments_par_type[type_entite]):>14}")

print("\n=== TYPES DE RELATIONS ===")
print(f"{'Relation':<34}{'Occurrences':>13}{'Médicaments':>14}")
for type_relation, n in occurrences_relations.most_common():
    print(f"{type_relation:<34}{n:>13}{len(medicaments_par_relation[type_relation]):>14}")