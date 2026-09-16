# scripts/15_synonymes_uniprot.py
# Objectif : récupérer les désignations alternatives des protéines des chaînes
# du pilote, depuis l'API UniProt, pour construire une table de normalisation.

import json
import time
import urllib.request

CHAINES = "data/processed/chaines_candidates.json"
SORTIE = "data/processed/synonymes_proteines.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

def interroger(accession):
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    with urllib.request.urlopen(url, timeout=30) as reponse:
        return json.load(reponse)

def extraire_noms(fiche):
    """Rassemble toutes les désignations d'une protéine."""
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
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() in MEDICAMENTS]

proteines = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        for nom, identifiant, type_e in (
            (etape["source"], etape["source_id"], etape["source_type"]),
            (etape["cible"], etape["cible_id"], etape["cible_type"]),
        ):
            if type_e == "Protein" and identifiant.startswith("UniProt:"):
                proteines[identifiant] = nom

print(f"Protéines à interroger : {len(proteines)}\n")

table = {}
for identifiant, nom_drugmechdb in proteines.items():
    accession = identifiant.split(":", 1)[1]
    try:
        fiche = interroger(accession)
        synonymes = extraire_noms(fiche)
    except Exception as erreur:
        print(f"  ÉCHEC {accession} : {erreur}")
        synonymes = []
    table[identifiant] = {
        "nom_drugmechdb": nom_drugmechdb,
        "synonymes": synonymes,
    }
    print(f"{nom_drugmechdb[:44]:<46} {len(synonymes):>2} désignations")
    for synonyme in synonymes:
        print(f"      {synonyme}")
    print()
    time.sleep(0.5)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(table, fichier, ensure_ascii=False, indent=2)

print(f"Fichier écrit : {SORTIE}")