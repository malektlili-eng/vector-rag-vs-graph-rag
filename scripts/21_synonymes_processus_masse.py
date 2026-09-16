# scripts/21_synonymes_processus_masse.py
# Objectif : récupérer les synonymes Gene Ontology de tous les processus biologiques
# des chaînes candidates, en vue du criblage complet.

import json
import time
import urllib.request
import urllib.parse

CHAINES = "data/processed/chaines_candidates.json"
SORTIE = "data/processed/synonymes_tous_processus.json"

def interroger(identifiant):
    encode = urllib.parse.quote(identifiant, safe="")
    url = f"https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{encode}"
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
        if valeur and synonyme.get("type") in ("exact", "narrow"):
            noms.append(valeur)
    vus, uniques = set(), []
    for nom in noms:
        if nom.lower() not in vus:
            vus.add(nom.lower())
            uniques.append(nom)
    return uniques

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

processus = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        for nom, identifiant, type_e in (
            (etape["source"], etape["source_id"], etape["source_type"]),
            (etape["cible"], etape["cible_id"], etape["cible_type"]),
        ):
            if type_e == "BiologicalProcess" and identifiant.startswith("GO:"):
                processus[identifiant] = nom

print(f"Processus distincts à interroger : {len(processus)}")
print(f"Durée estimée : environ {len(processus) // 2} secondes\n")

table = {}
echecs = 0
for i, (identifiant, nom) in enumerate(processus.items(), 1):
    try:
        synonymes = extraire_noms(interroger(identifiant))
    except Exception as erreur:
        print(f"  ÉCHEC {identifiant} ({nom[:36]}) : {erreur}")
        synonymes, echecs = [], echecs + 1
    table[identifiant] = {"nom_drugmechdb": nom, "synonymes": synonymes}
    if i % 25 == 0:
        print(f"  {i}/{len(processus)}...")
    time.sleep(0.5)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(table, fichier, ensure_ascii=False, indent=2)

sans_syn = sum(1 for v in table.values() if len(v["synonymes"]) <= 1)
print(f"\nProcessus traités : {len(table)}")
print(f"Échecs de requête : {echecs}")
print(f"Avec 1 seule désignation : {sans_syn} "
      f"({sans_syn * 100 // max(len(table), 1)} %)")
print(f"Fichier écrit : {SORTIE}")