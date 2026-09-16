# scripts/36_verifier_processus.py
# Objectif : chercher toute mention d'un processus des chaînes, sous n'importe
# quelle forme, et observer ce à quoi elle est reliée.

import json
from collections import Counter

RELATIONS = "data/processed/relations_nettoyees.json"

SONDES = {
    "recapture NE/5-HT": ["reuptake", "uptake", "transporter"],
    "agrégation plaquettaire": ["platelet", "aggregation"],
    "angiogenèse": ["angiogen", "vascular"],
    "fibrinolyse": ["fibrinolys", "plasmin", "clot", "lysis"],
    "sécrétion acide": ["acid secretion", "gastric acid"],
}

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

for nom, motifs in SONDES.items():
    print(f"\n{'=' * 72}")
    print(f"  {nom}")
    print("=" * 72)
    trouvees = [r for r in relations
                if any(m in r["source"].lower() or m in r["target"].lower()
                       for m in motifs)]
    print(f"{len(trouvees)} relation(s)\n")

    en_source = [r for r in trouvees
                 if any(m in r["source"].lower() for m in motifs)]
    print(f"  Comme SOURCE ({len(en_source)}) :")
    for r in en_source[:8]:
        print(f"    {r['source'][:34]} --{r['relation']}--> "
              f"[{r['target_type']}] {r['target'][:34]}")
    if not en_source:
        print("    (aucune)")

    en_cible = [r for r in trouvees
                if any(m in r["target"].lower() for m in motifs)]
    print(f"\n  Comme CIBLE ({len(en_cible)}) :")
    for r in en_cible[:8]:
        print(f"    [{r['source_type']}] {r['source'][:30]} "
              f"--{r['relation']}--> {r['target'][:34]}")
    if not en_cible:
        print("    (aucune)")

print(f"\n{'=' * 72}")
print("  RELATIONS DONT LA CIBLE EST UNE MALADIE")
print("=" * 72)
vers_maladie = [r for r in relations if r["target_type"] == "Disease"]
print(f"{len(vers_maladie)} relation(s) sur {len(relations)}\n")
types_source = Counter(r["source_type"] for r in vers_maladie)
for type_e, n in types_source.most_common():
    print(f"  {n:>4}  depuis {type_e}")
print()
for r in vers_maladie[:15]:
    print(f"    [{r['source_type']}] {r['source'][:28]} "
          f"--{r['relation']}--> {r['target'][:34]}")