# scripts/16_couverture_normalisee.py
# Objectif : remesurer la couverture des chaînes en utilisant la table de synonymes.

import json
import re
from collections import defaultdict

CHAINES = "data/processed/chaines_candidates.json"
CORPUS = "data/processed/corpus_pilote.json"
SYNONYMES = "data/processed/synonymes_proteines.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

# Variantes lexicales relevées lors du sondage de nomenclature (script 14)
VARIANTES = {
    "serotonin uptake": ["serotonin reuptake", "5-ht reuptake"],
    "norepinephrine uptake": ["norepinephrine reuptake", "ne reuptake",
                              "noradrenaline reuptake"],
    "dopamine uptake": ["dopamine reuptake"],
}

with open(SYNONYMES, "r", encoding="utf-8") as fichier:
    table = json.load(fichier)

# nom DrugMechDB -> liste de formes acceptées
formes = {}
for entree in table.values():
    formes[entree["nom_drugmechdb"]] = entree["synonymes"]
for nom, liste in VARIANTES.items():
    formes[nom] = [nom] + liste

def trouve(forme, texte):
    """Mot entier ; casse respectée pour les sigles courts."""
    if len(forme) <= 4 and forme.isupper():
        return re.search(rf"\b{re.escape(forme)}\b", texte) is not None
    return re.search(rf"\b{re.escape(forme.lower())}\b", texte.lower()) is not None

def present(nom, texte):
    for forme in formes.get(nom, [nom]):
        if trouve(forme, texte):
            return True
    return False

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() in MEDICAMENTS]

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

textes = defaultdict(list)
for article in corpus:
    textes[article["medicament"].lower()].append(
        article["titre"] + " " + article["resume"]
    )

complets = 0
print("=== COUVERTURE PAR CHAÎNE ===")
for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    marques, ok = [], True
    for etape in chaine["etapes"]:
        n = sum(1 for d in docs
                if present(etape["source"], d) and present(etape["cible"], d))
        marques.append(f"{n:>2}" if n else " -")
        if n == 0:
            ok = False
    complets += ok
    print(f"[{' '.join(marques)}] {chaine['medicament']} → {chaine['maladie'][:32]}")

print(f"\nChaînes entièrement couvertes : {complets}/{len(chaines)}")

print("\n=== ENTITÉS ENCORE INTROUVABLES ===")
manquantes = set()
for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    for etape in chaine["etapes"]:
        for nom, type_e in ((etape["source"], etape["source_type"]),
                            (etape["cible"], etape["cible_type"])):
            if not any(present(nom, d) for d in docs):
                manquantes.add((type_e, nom))
for type_e, nom in sorted(manquantes):
    print(f"  {type_e:<20} {nom}")