# scripts/29_collecte_ciblee_v2.py
# Objectif : reconstruire le corpus en priorisant les articles à vocabulaire
# mécanistique, avec complément non filtré lorsque le filtre est trop restrictif.

import json
import re
import time
from collections import defaultdict
from Bio import Entrez

Entrez.email = "malektlili.eng@gmail.com"      # ← ton adresse réelle

CHAINES = "data/processed/chaines_retenues.json"
SYN_PROT = "data/processed/synonymes_toutes_proteines.json"
SYN_PROC = "data/processed/synonymes_tous_processus.json"
SORTIE = "data/raw/pubmed_corpus.json"

CIBLES_PAR_SAUT = 8
DISTRACTEURS_PAR_MEDICAMENT = 20
SYNONYMES_MAX = 8

MECANISTIQUE = (
    '(mechanism[Title/Abstract] OR receptor[Title/Abstract] '
    'OR inhibit*[Title/Abstract] OR bind*[Title/Abstract] '
    'OR pathway[Title/Abstract] OR regulat*[Title/Abstract] '
    'OR activat*[Title/Abstract] OR express*[Title/Abstract] '
    'OR "mode of action"[Title/Abstract])'
)

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

def base(medicament, etape):
    return (f'"{nettoyer(medicament)}"[Title/Abstract] AND hasabstract '
            f'AND english[lang] AND {bloc(etape["source"])} '
            f'AND {bloc(etape["cible"])}')

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

provenance = defaultdict(list)
medicaments = set()
stats = {"filtres": 0, "complements": 0}

print(f"Chaînes à couvrir : {len(chaines)}\n")
for chaine in chaines:
    medicament = chaine["etapes"][0]["source"]
    medicaments.add(medicament)
    print(f"  {medicament} → {chaine['maladie'][:32]}")

    for i, etape in enumerate(chaine["etapes"], 1):
        socle = base(medicament, etape)

        # 1. articles à vocabulaire mécanistique, en priorité
        prioritaires = chercher(f"{socle} AND {MECANISTIQUE}", CIBLES_PAR_SAUT)

        # 2. complément non filtré si le compte est insuffisant
        complement = []
        if len(prioritaires) < CIBLES_PAR_SAUT:
            manque = CIBLES_PAR_SAUT - len(prioritaires)
            for pmid in chercher(socle, CIBLES_PAR_SAUT * 2):
                if pmid not in prioritaires:
                    complement.append(pmid)
                if len(complement) >= manque:
                    break

        stats["filtres"] += len(prioritaires)
        stats["complements"] += len(complement)
        print(f"     saut {i} : {len(prioritaires)} mécanistique(s)"
              f" + {len(complement)} complément(s)")

        for pmid in prioritaires + complement:
            provenance[pmid].append({
                "role": "cible",
                "chaine": chaine.get("id"),
                "saut": i,
                "source": etape["source"],
                "relation": etape["relation"],
                "cible": etape["cible"],
                "filtre_mecanistique": pmid in prioritaires,
            })

print(f"\nArticles ciblés (uniques) : {len(provenance)}")
print(f"  dont issus du filtre mécanistique : {stats['filtres']}")
print(f"  compléments non filtrés           : {stats['complements']}")

# --- Distracteurs
print("\nCollecte des distracteurs...")
for medicament in sorted(medicaments):
    requete = (f'"{nettoyer(medicament)}"[Title/Abstract] AND hasabstract '
               f'AND english[lang] AND "journal article"[Publication Type]')
    ajoutes = 0
    for pmid in chercher(requete, DISTRACTEURS_PAR_MEDICAMENT * 3):
        if pmid in provenance:
            continue
        provenance[pmid].append({"role": "distracteur", "medicament": medicament})
        ajoutes += 1
        if ajoutes >= DISTRACTEURS_PAR_MEDICAMENT:
            break
    print(f"  {medicament:<24} +{ajoutes}")

tous = list(provenance)
print(f"\nArticles à récupérer : {len(tous)}")

# --- Récupération
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
            "provenance": provenance[pmid],
        })
    print(f"  {min(debut + 100, len(tous))}/{len(tous)} récupérés")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(corpus, fichier, ensure_ascii=False, indent=2)

n_cibles = sum(1 for a in corpus
               if any(p["role"] == "cible" for p in a["provenance"]))
print(f"\nCorpus : {len(corpus)} abstracts "
      f"({n_cibles} ciblés / {len(corpus) - n_cibles} distracteurs)")
print(f"Résumés vides écartés : {vides}")
print(f"Fichier écrit : {SORTIE}")