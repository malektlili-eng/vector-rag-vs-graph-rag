# scripts/18_couverture_finale.py
# Objectif : combiner les trois sources de synonymes (UniProt, GO, variantes
# manuelles), corriger l'appariement par suffixes, et remesurer la couverture.

import json
import re
from collections import defaultdict

CHAINES = "data/processed/chaines_candidates.json"
CORPUS = "data/processed/corpus_pilote.json"
SYN_PROT = "data/processed/synonymes_proteines.json"
SYN_PROC = "data/processed/synonymes_processus.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

# Variantes relevées au script 14, absentes des deux bases de référence
VARIANTES = {
    "serotonin uptake": ["serotonin reuptake", "5-HT reuptake"],
    "dopamine uptake": ["dopamine reuptake"],
}

SUFFIXE_MOTS_MIN = 2
SUFFIXE_CARS_MIN = 20

def suffixes(terme):
    """Suffixes du terme conservant le groupe nominal de tête."""
    mots = terme.split()
    produits = []
    for debut in range(1, len(mots) - SUFFIXE_MOTS_MIN + 1):
        candidat = " ".join(mots[debut:])
        if len(candidat) >= SUFFIXE_CARS_MIN:
            produits.append(candidat)
    return produits

# --- Construction de la table de formes
formes = defaultdict(list)

for fichier_syn in (SYN_PROT, SYN_PROC):
    with open(fichier_syn, "r", encoding="utf-8") as fichier:
        for entree in json.load(fichier).values():
            formes[entree["nom_drugmechdb"]].extend(entree["synonymes"])

for nom, liste in VARIANTES.items():
    formes[nom].extend(liste)

# Ajout des suffixes, puis déduplication
for nom in list(formes):
    enrichi = list(formes[nom])
    for forme in formes[nom]:
        enrichi.extend(suffixes(forme))
    vus, propre = set(), []
    for forme in enrichi:
        if forme.lower() not in vus:
            vus.add(forme.lower())
            propre.append(forme)
    formes[nom] = propre

print("=== FORMES ACCEPTÉES PAR ENTITÉ ===")
for nom in sorted(formes):
    print(f"\n{nom}")
    for forme in formes[nom]:
        print(f"    {forme}")

# --- Appariement
def trouve(forme, texte):
    if len(forme) <= 4 and forme.isupper():
        return re.search(rf"\b{re.escape(forme)}\b", texte) is not None
    return re.search(rf"\b{re.escape(forme.lower())}\b", texte.lower()) is not None

def present(nom, texte):
    return any(trouve(f, texte) for f in formes.get(nom, [nom]))

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
print("\n=== COUVERTURE PAR CHAÎNE ===")
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

manquantes = set()
for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    for etape in chaine["etapes"]:
        for nom, type_e in ((etape["source"], etape["source_type"]),
                            (etape["cible"], etape["cible_type"])):
            if not any(present(nom, d) for d in docs):
                manquantes.add((type_e, nom))

print("\n=== ENTITÉS ENCORE INTROUVABLES ===")
for type_e, nom in sorted(manquantes):
    print(f"  {type_e:<20} {nom}")