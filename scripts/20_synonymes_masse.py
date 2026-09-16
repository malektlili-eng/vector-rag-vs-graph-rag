# scripts/20_synonymes_masse.py
# Objectif : récupérer les synonymes UniProt de toutes les protéines des chaînes
# candidates, en vue du pré-criblage PubMed.

import json
import time
import urllib.request

CHAINES = "data/processed/chaines_candidates.json"
SORTIE = "data/processed/synonymes_toutes_proteines.json"

def interroger(accession):
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    with urllib.request.urlopen(url, timeout=30) as reponse:
        return json.load(reponse)

def extraire_noms(fiche):
    noms = []
    description = fiche.get("proteinDescription", {})

    def ajouter_bloc(bloc):
        if not bloc:
            return
        complet = bloc.get("fullName", {}).get("value")
        if complet:
            noms.append(complet)
        for court in bloc.get("shortNames", []):
            if court.get("value"):
                noms.append(court["value"])

    ajouter_bloc(description.get("recommendedName"))
    for alternatif in description.get("alternativeNames", []):
        ajouter_bloc(alternatif)
    for gene in fiche.get("genes", []):
        principal = gene.get("geneName", {}).get("value")
        if principal:
            noms.append(principal)
        for synonyme in gene.get("synonyms", []):
            if synonyme.get("value"):
                noms.append(synonyme["value"])

    vus, uniques = set(), []
    for nom in noms:
        if nom.lower() not in vus:
            vus.add(nom.lower())
            uniques.append(nom)
    return uniques

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

proteines = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        for nom, identifiant, type_e in (
            (etape["source"], etape["source_id"], etape["source_type"]),
            (etape["cible"], etape["cible_id"], etape["cible_type"]),
        ):
            if type_e == "Protein" and identifiant.startswith("UniProt:"):
                proteines[identifiant] = nom

print(f"Protéines distinctes à interroger : {len(proteines)}")
print("Durée estimée : environ", len(proteines) // 2, "secondes\n")

table = {}
echecs = 0
for i, (identifiant, nom) in enumerate(proteines.items(), 1):
    accession = identifiant.split(":", 1)[1]
    try:
        synonymes = extraire_noms(interroger(accession))
    except Exception as erreur:
        print(f"  ÉCHEC {accession} ({nom[:36]}) : {erreur}")
        synonymes, echecs = [], echecs + 1
    table[identifiant] = {"nom_drugmechdb": nom, "synonymes": synonymes}
    if i % 20 == 0:
        print(f"  {i}/{len(proteines)}...")
    time.sleep(0.4)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(table, fichier, ensure_ascii=False, indent=2)

sans_syn = sum(1 for v in table.values() if len(v["synonymes"]) <= 1)
print(f"\nProtéines traitées : {len(table)}")
print(f"Échecs de requête  : {echecs}")
print(f"Avec 1 seule désignation : {sans_syn}")
print(f"Fichier écrit : {SORTIE}")