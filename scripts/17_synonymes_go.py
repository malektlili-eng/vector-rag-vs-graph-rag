# scripts/17_synonymes_go.py
# Objectif : récupérer les synonymes des processus biologiques depuis Gene Ontology,
# en miroir de ce qui a été fait pour les protéines via UniProt.

import json
import time
import urllib.request
import urllib.parse

CHAINES = "data/processed/chaines_candidates.json"
SORTIE = "data/processed/synonymes_processus.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

def interroger(identifiant):
    encode = urllib.parse.quote(identifiant, safe="")
    url = (f"https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{encode}")
    requete = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.load(reponse)

def extraire_noms(reponse):
    resultats = reponse.get("results") or []
    if not resultats:
        return []
    terme = resultats[0]
    noms = []
    if terme.get("name"):
        noms.append(terme["name"])
    for synonyme in terme.get("synonyms", []):
        valeur = synonyme.get("name")
        # on garde les synonymes exacts et étroits, on écarte les "related"
        if valeur and synonyme.get("type") in ("exact", "narrow"):
            noms.append(valeur)
    vus, uniques = set(), []
    for nom in noms:
        if nom.lower() not in vus:
            vus.add(nom.lower())
            uniques.append(nom)
    return uniques

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() in MEDICAMENTS]

processus = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        for nom, identifiant, type_e in (
            (etape["source"], etape["source_id"], etape["source_type"]),
            (etape["cible"], etape["cible_id"], etape["cible_type"]),
        ):
            if type_e == "BiologicalProcess" and identifiant.startswith("GO:"):
                processus[identifiant] = nom

print(f"Processus à interroger : {len(processus)}\n")

table = {}
for identifiant, nom_drugmechdb in processus.items():
    try:
        synonymes = extraire_noms(interroger(identifiant))
    except Exception as erreur:
        print(f"  ÉCHEC {identifiant} : {erreur}")
        synonymes = []
    table[identifiant] = {"nom_drugmechdb": nom_drugmechdb,
                          "synonymes": synonymes}
    print(f"{nom_drugmechdb[:44]:<46} {len(synonymes):>2} désignations")
    for synonyme in synonymes:
        print(f"      {synonyme}")
    print()
    time.sleep(0.5)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(table, fichier, ensure_ascii=False, indent=2)

print(f"Fichier écrit : {SORTIE}")