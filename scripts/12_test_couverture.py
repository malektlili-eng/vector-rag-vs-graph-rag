# scripts/12_test_couverture.py
# Objectif : vérifier, sans appel LLM, si les entités des chaînes DrugMechDB
# apparaissent dans le corpus PubMed collecté. Condition nécessaire à l'extraction.

import json
from collections import defaultdict

CHAINES = "data/processed/chaines_candidates.json"
CORPUS = "data/processed/corpus_pilote.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() in MEDICAMENTS]

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

# Index : médicament -> textes concaténés (titre + résumé), en minuscules
textes = defaultdict(list)
for article in corpus:
    textes[article["medicament"].lower()].append(
        (article["titre"] + " " + article["resume"]).lower()
    )

def presente(nom, docs):
    """Nombre d'abstracts contenant ce nom d'entité."""
    cible = nom.lower()
    return sum(1 for d in docs if cible in d)

def cooccurrence(source, cible, docs):
    """Nombre d'abstracts contenant les deux entités."""
    a, b = source.lower(), cible.lower()
    return sum(1 for d in docs if a in d and b in d)

introuvables = set()
resultats = []

for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    etapes = []
    for etape in chaine["etapes"]:
        n_source = presente(etape["source"], docs)
        n_cible = presente(etape["cible"], docs)
        n_duo = cooccurrence(etape["source"], etape["cible"], docs)
        if n_source == 0:
            introuvables.add((etape["source"], etape["source_type"]))
        if n_cible == 0:
            introuvables.add((etape["cible"], etape["cible_type"]))
        etapes.append(n_duo)
    resultats.append((chaine, etapes))

complets = [r for r in resultats if all(n > 0 for n in r[1])]
partiels = [r for r in resultats if any(n > 0 for n in r[1]) and not all(n > 0 for n in r[1])]
vides = [r for r in resultats if all(n == 0 for n in r[1])]

print(f"Chaînes examinées        : {len(resultats)}")
print(f"  toutes étapes couvertes : {len(complets)}")
print(f"  partiellement couvertes : {len(partiels)}")
print(f"  aucune étape couverte   : {len(vides)}\n")

print("=== DÉTAIL PAR CHAÎNE ===")
for chaine, etapes in resultats:
    marques = " ".join("OK" if n else "--" for n in etapes)
    print(f"[{marques}] {chaine['medicament']} → {chaine['maladie'][:34]}")

print(f"\n=== ENTITÉS INTROUVABLES DANS LE CORPUS ({len(introuvables)}) ===")
for nom, type_entite in sorted(introuvables, key=lambda x: x[1]):
    print(f"  {type_entite:<20} {nom}")