# scripts/25_collecte_ciblee.py
# Objectif : construire le corpus de travail — articles porteurs de chaque saut
# des chaînes retenues, complétés de distracteurs sur les mêmes médicaments.

import json
import re
import time
from collections import defaultdict
from Bio import Entrez

Entrez.email = "votre.adresse@exemple.org"      # ← ton adresse réelle

CHAINES = "data/processed/chaines_retenues.json"
SYN_PROT = "data/processed/synonymes_toutes_proteines.json"
SYN_PROC = "data/processed/synonymes_tous_processus.json"
SORTIE = "data/raw/pubmed_corpus.json"

CIBLES_PAR_SAUT = 8
DISTRACTEURS_PAR_MEDICAMENT = 20
SYNONYMES_MAX = 8

# --- Table des formes acceptées (identique au criblage)
formes = {}
for fichier_syn in (SYN_PROT, SYN_PROC):
    with open(fichier_syn, "r", encoding="utf-8") as fichier:
        for entree in json.load(fichier).values():
            formes[entree["nom_drugmechdb"]] = entree["synonymes"]

def nettoyer(terme):
    return re.sub(r'["\[\]()]', " ", terme).strip()

def bloc(nom):
    liste = formes.get(nom, [nom]) or [nom]
    retenus, vus = [], set()
    for terme in liste:
        propre = nettoyer(terme)
        if len(propre) < 3 or propre.lower() in vus:
            continue
        vus.add(propre.lower())
        retenus.append(f'"{propre}"[Title/Abstract]')
        if len(retenus) >= SYNONYMES_MAX:
            break
    return "(" + " OR ".join(retenus) + ")"

def chercher(requete, n):
    poignee = Entrez.esearch(db="pubmed", term=requete, retmax=n,
                             sort="relevance")
    resultat = Entrez.read(poignee)
    poignee.close()
    time.sleep(0.4)
    return list(resultat["IdList"])

def requete_generale(medicament):
    return (f'"{nettoyer(medicament)}"[Title/Abstract] AND hasabstract '
            f'AND english[lang] AND "journal article"[Publication Type]')

# --- Phase 1 : articles porteurs des sauts
with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

provenance = defaultdict(list)      # pmid -> liste de descriptions
medicaments = set()

print(f"Chaînes à couvrir : {len(chaines)}\n")
for chaine in chaines:
    medicament = chaine["etapes"][0]["source"]
    medicaments.add(medicament)
    print(f"  {medicament} → {chaine['maladie'][:34]}")
    for i, etape in enumerate(chaine["etapes"], 1):
        requete = (f'"{nettoyer(medicament)}"[Title/Abstract] AND hasabstract '
                   f'AND english[lang] AND {bloc(etape["source"])} '
                   f'AND {bloc(etape["cible"])}')
        pmids = chercher(requete, CIBLES_PAR_SAUT)
        print(f"     saut {i} : {len(pmids)} article(s)")
        for pmid in pmids:
            provenance[pmid].append({
                "role": "cible",
                "chaine": chaine.get("id"),
                "saut": i,
                "source": etape["source"],
                "relation": etape["relation"],
                "cible": etape["cible"],
            })

cibles = set(provenance)
print(f"\nArticles ciblés (uniques) : {len(cibles)}")

# --- Phase 2 : distracteurs
print("\nCollecte des distracteurs...")
for medicament in sorted(medicaments):
    pmids = chercher(requete_generale(medicament),
                     DISTRACTEURS_PAR_MEDICAMENT * 3)
    ajoutes = 0
    for pmid in pmids:
        if pmid in provenance:
            continue
        provenance[pmid].append({"role": "distracteur",
                                 "medicament": medicament})
        ajoutes += 1
        if ajoutes >= DISTRACTEURS_PAR_MEDICAMENT:
            break
    print(f"  {medicament:<24} +{ajoutes}")

tous = list(provenance)
print(f"\nArticles à récupérer : {len(tous)}")

# --- Phase 3 : récupération des textes
def texte_resume(article):
    contenu = article["MedlineCitation"]["Article"].get("Abstract", {})
    parties = []
    for morceau in contenu.get("AbstractText", []):
        etiquette = getattr(morceau, "attributes", {}).get("Label")
        parties.append(f"{etiquette}: {morceau}" if etiquette else str(morceau))
    return " ".join(parties).strip()

def annee(article):
    date = (article["MedlineCitation"]["Article"]["Journal"]
            ["JournalIssue"]["PubDate"])
    return date.get("Year") or date.get("MedlineDate", "")[:4]

corpus, vides = [], 0
for debut in range(0, len(tous), 100):
    lot = tous[debut:debut + 100]
    poignee = Entrez.efetch(db="pubmed", id=",".join(lot), retmode="xml")
    articles = Entrez.read(poignee)["PubmedArticle"]
    poignee.close()
    time.sleep(0.4)
    for article in articles:
        resume = texte_resume(article)
        if not resume:
            vides += 1
            continue
        citation = article["MedlineCitation"]
        pmid = str(citation["PMID"])
        corpus.append({
            "pmid": pmid,
            "titre": str(citation["Article"]["ArticleTitle"]),
            "annee": annee(article),
            "journal": str(citation["Article"]["Journal"]["Title"]),
            "resume": resume,
            "provenance": provenance[pmid],   # métadonnée d'analyse uniquement
        })
    print(f"  {min(debut + 100, len(tous))}/{len(tous)} récupérés")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(corpus, fichier, ensure_ascii=False, indent=2)

n_cibles = sum(1 for a in corpus
               if any(p["role"] == "cible" for p in a["provenance"]))
longueurs = [len(a["resume"].split()) for a in corpus]

print(f"\nCorpus final     : {len(corpus)} abstracts")
print(f"  dont ciblés    : {n_cibles}")
print(f"  distracteurs   : {len(corpus) - n_cibles}")
print(f"Résumés vides écartés : {vides}")
print(f"Longueur moyenne : {sum(longueurs) // len(longueurs)} mots")
print(f"Fichier écrit    : {SORTIE}")