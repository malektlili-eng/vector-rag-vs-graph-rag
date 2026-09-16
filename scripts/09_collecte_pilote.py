# scripts/09_collecte_pilote.py
# Objectif : collecter les abstracts du pilote et figer la liste des PMID.

import json
import time
from Bio import Entrez

Entrez.email = "malektlili.eng@gmail.com"   

N_PAR_MEDICAMENT = 30
SORTIE = "data/raw/pubmed_pilote.json"

MEDICAMENTS = [
    "venlafaxine", "epoprostenol", "propylthiouracil",
    "filgrastim", "metolazone",
]

def requete(medicament):
    return (
        f'"{medicament}"[Title/Abstract] AND hasabstract AND english[lang] '
        f'AND (mechanism[Title/Abstract] OR receptor[Title/Abstract] '
        f'OR inhibit*[Title/Abstract] OR bind*[Title/Abstract] '
        f'OR pathway[Title/Abstract] OR regulat*[Title/Abstract] '
        f'OR activat*[Title/Abstract] OR express*[Title/Abstract] '
        f'OR "mode of action"[Title/Abstract]) '
        f'AND "journal article"[Publication Type] '
        f'NOT ("comment"[Publication Type] OR "editorial"[Publication Type] '
        f'OR "news"[Publication Type] OR "retracted publication"[Publication Type])'
    )

def chercher_pmids(medicament, n):
    poignee = Entrez.esearch(db="pubmed", term=requete(medicament),
                             retmax=n, sort="relevance")
    resultat = Entrez.read(poignee)
    poignee.close()
    time.sleep(0.4)
    return list(resultat["IdList"])

def recuperer(pmids):
    poignee = Entrez.efetch(db="pubmed", id=",".join(pmids), retmode="xml")
    resultat = Entrez.read(poignee)
    poignee.close()
    time.sleep(0.4)
    return resultat["PubmedArticle"]

def texte_resume(article):
    """Reconstitue le résumé, qui peut être découpé en sections étiquetées."""
    contenu = article["MedlineCitation"]["Article"].get("Abstract", {})
    morceaux = contenu.get("AbstractText", [])
    parties = []
    for morceau in morceaux:
        etiquette = getattr(morceau, "attributes", {}).get("Label")
        parties.append(f"{etiquette}: {morceau}" if etiquette else str(morceau))
    return " ".join(parties).strip()

def annee(article):
    date = (article["MedlineCitation"]["Article"]["Journal"]
            ["JournalIssue"]["PubDate"])
    return date.get("Year") or date.get("MedlineDate", "")[:4]

collecte = []
vides = 0

for medicament in MEDICAMENTS:
    print(f"Collecte : {medicament}...")
    pmids = chercher_pmids(medicament, N_PAR_MEDICAMENT)
    articles = recuperer(pmids)

    for article in articles:
        resume = texte_resume(article)
        if not resume:
            vides += 1
            continue
        citation = article["MedlineCitation"]
        collecte.append({
            "pmid": str(citation["PMID"]),
            "medicament": medicament,
            "titre": str(citation["Article"]["ArticleTitle"]),
            "annee": annee(article),
            "journal": str(citation["Article"]["Journal"]["Title"]),
            "resume": resume,
        })

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(collecte, fichier, ensure_ascii=False, indent=2)

longueurs = [len(a["resume"].split()) for a in collecte]

print(f"\nAbstracts collectés  : {len(collecte)}")
print(f"Résumés vides écartés : {vides}")
print(f"Longueur moyenne      : {sum(longueurs) // len(longueurs)} mots")
print(f"Longueur min / max    : {min(longueurs)} / {max(longueurs)} mots")
print(f"Fichier écrit         : {SORTIE}")