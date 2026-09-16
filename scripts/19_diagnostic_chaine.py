# scripts/19_diagnostic_chaine.py
# Objectif : tracer pas à pas l'appariement d'une chaîne pour localiser
# l'origine d'un échec de couverture.

import json
import re
from collections import defaultdict

CHAINES = "data/processed/chaines_candidates.json"
CORPUS = "data/processed/corpus_pilote.json"
SYN_PROT = "data/processed/synonymes_proteines.json"
SYN_PROC = "data/processed/synonymes_processus.json"

CIBLE = "metolazone"

formes = defaultdict(list)
for fichier_syn in (SYN_PROT, SYN_PROC):
    with open(fichier_syn, "r", encoding="utf-8") as fichier:
        for entree in json.load(fichier).values():
            formes[entree["nom_drugmechdb"]].extend(entree["synonymes"])
formes["Thiazide-sensitive sodium-chloride cotransporter"] = []
formes["Solute carrier family 12 member 3"].append("sodium-chloride cotransporter")

def trouve(forme, texte):
    if len(forme) <= 4 and forme.isupper():
        return re.search(rf"\b{re.escape(forme)}\b", texte) is not None
    return re.search(rf"\b{re.escape(forme.lower())}\b", texte.lower()) is not None

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() == CIBLE]

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = [a for a in json.load(fichier)
              if a["medicament"].lower() == CIBLE]

print(f"Chaînes {CIBLE} : {len(chaines)} — abstracts : {len(corpus)}\n")

for chaine in chaines:
    print(f"CHAÎNE : {chaine['medicament']} → {chaine['maladie']}")
    print(f"MOTIF  : {chaine['motif']}\n")
    for i, etape in enumerate(chaine["etapes"], 1):
        print(f"  Étape {i}")
        for role in ("source", "cible"):
            nom = etape[role]
            liste = formes.get(nom, [nom])
            print(f"    {role:<7} : « {nom} »  (type {etape[role + '_type']})")
            print(f"    formes  : {liste if liste else '[aucune — nom brut utilisé]'}")
            docs = [a for a in corpus
                    if any(trouve(f, a["titre"] + " " + a["resume"])
                           for f in (liste or [nom]))]
            print(f"    présent dans {len(docs)} abstracts"
                  f"{' → ' + ', '.join(d['pmid'] for d in docs[:5]) if docs else ''}")
        print()

print("=== VÉRIFICATION BRUTE DANS LE CORPUS ===")
for terme in ("metolazone", "sodium-chloride cotransporter", "cotransporter"):
    n = sum(1 for a in corpus
            if terme.lower() in (a["titre"] + " " + a["resume"]).lower())
    print(f"  « {terme} » : {n} abstracts")