# scripts/14_nomenclature_reelle.py
# Objectif : observer comment le corpus nomme réellement les concepts que
# DrugMechDB désigne par leurs noms canoniques.

import json
import re
from collections import defaultdict

CORPUS = "data/processed/corpus_pilote.json"

# Mot-clé de tête -> médicament dont on inspecte le corpus
SONDES = [
    ("venlafaxine", "transporter"),
    ("venlafaxine", "reuptake"),
    ("propylthiouracil", "peroxidase"),
    ("filgrastim", "receptor"),
    ("metolazone", "cotransporter"),
    ("metolazone", "sodium"),
]

FENETRE = 90   # caractères de contexte de part et d'autre

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

textes = defaultdict(list)
for article in corpus:
    textes[article["medicament"].lower()].append(
        (article["pmid"], article["titre"] + " " + article["resume"])
    )

for medicament, sonde in SONDES:
    print(f"\n{'=' * 70}")
    print(f"  {medicament} — occurrences de « {sonde} »")
    print("=" * 70)
    trouves = 0
    for pmid, texte in textes[medicament.lower()]:
        for m in re.finditer(sonde, texte, flags=re.IGNORECASE):
            debut = max(0, m.start() - FENETRE)
            fin = min(len(texte), m.end() + FENETRE)
            extrait = texte[debut:fin].replace("\n", " ")
            print(f"  [{pmid}] ...{extrait}...")
            trouves += 1
            break                     # une occurrence par abstract suffit
        if trouves >= 6:
            break
    if trouves == 0:
        print("  (aucune occurrence)")