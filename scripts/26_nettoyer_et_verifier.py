# scripts/26_nettoyer_et_verifier.py
# Objectif : nettoyer le corpus de travail, puis vérifier que chaque saut de chaque
# chaîne reste porté par au moins un article après nettoyage.

import json
import re
from collections import defaultdict

ENTREE = "data/raw/pubmed_corpus.json"
CHAINES = "data/processed/chaines_retenues.json"
SORTIE = "data/processed/corpus.json"
LONGUEUR_MIN = 50

BALISE = re.compile(r"<[^>]+>")
ESPACES = re.compile(r"\s+")

def nettoyer(texte):
    return ESPACES.sub(" ", BALISE.sub(" ", texte)).strip()

with open(ENTREE, "r", encoding="utf-8") as fichier:
    brut = json.load(fichier)

corpus, ecartes = [], []
for article in brut:
    resume = nettoyer(article["resume"])
    if len(resume.split()) < LONGUEUR_MIN:
        ecartes.append(article)
        continue
    corpus.append({**article, "resume": resume,
                   "titre": nettoyer(article["titre"])})

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(corpus, fichier, ensure_ascii=False, indent=2)

avec_balises = sum(1 for a in brut if BALISE.search(a["resume"]))
perdus_cibles = sum(1 for a in ecartes
                    if any(p["role"] == "cible" for p in a["provenance"]))

print(f"Abstracts en entrée      : {len(brut)}")
print(f"  contenaient du balisage : {avec_balises}")
print(f"  écartés (< {LONGUEUR_MIN} mots)   : {len(ecartes)}"
      f" (dont {perdus_cibles} ciblé{'s' if perdus_cibles > 1 else ''})")
print(f"Corpus nettoyé           : {len(corpus)}")

# --- Vérification d'intégrité des chaînes
porteurs = defaultdict(set)          # (chaine, saut) -> pmids présents
for article in corpus:
    for p in article["provenance"]:
        if p["role"] == "cible":
            porteurs[(p["chaine"], p["saut"])].add(article["pmid"])

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

intactes, rompues, fragiles = [], [], []
print("\n=== INTÉGRITÉ DES CHAÎNES ===")
for chaine in chaines:
    comptes = [len(porteurs[(chaine.get("id"), i)])
               for i in range(1, len(chaine["etapes"]) + 1)]
    medicament = chaine["etapes"][0]["source"]
    etat = "ROMPUE " if min(comptes) == 0 else ("fragile" if min(comptes) <= 2
                                                else "       ")
    print(f"  [{' '.join(f'{n:>2}' for n in comptes)}] {etat} "
          f"{medicament} → {chaine['maladie'][:32]}")
    if min(comptes) == 0:
        rompues.append(chaine)
    elif min(comptes) <= 2:
        fragiles.append(chaine)
    else:
        intactes.append(chaine)

print(f"\nChaînes intactes  : {len(intactes)}")
print(f"Chaînes fragiles  : {len(fragiles)}   (un saut porté par 1 ou 2 articles)")
print(f"Chaînes rompues   : {len(rompues)}")
for chaine in rompues:
    print(f"    {chaine['etapes'][0]['source']} → {chaine['maladie']}")

longueurs = [len(a["resume"].split()) for a in corpus]
n_cibles = sum(1 for a in corpus
               if any(p["role"] == "cible" for p in a["provenance"]))
print(f"\nCorpus : {len(corpus)} abstracts "
      f"({n_cibles} ciblés / {len(corpus) - n_cibles} distracteurs)")
print(f"Longueur moyenne : {sum(longueurs) // len(longueurs)} mots")
print(f"Fichier écrit    : {SORTIE}")