# scripts/11_nettoyer_corpus.py
# Objectif : produire le corpus pilote nettoyé — suppression du balisage,
# normalisation des espaces, filtrage des textes trop courts.

import json
import re

ENTREE = "data/raw/pubmed_pilote.json"
SORTIE = "data/processed/corpus_pilote.json"
LONGUEUR_MIN = 50

BALISE = re.compile(r"<[^>]+>")
ESPACES = re.compile(r"\s+")

def nettoyer(texte):
    texte = BALISE.sub(" ", texte)          # retire <b>, <i>, <sup>...
    texte = ESPACES.sub(" ", texte)         # normalise espaces et retours ligne
    return texte.strip()

with open(ENTREE, "r", encoding="utf-8") as fichier:
    brut = json.load(fichier)

corpus = []
ecartes = []

for article in brut:
    resume = nettoyer(article["resume"])
    if len(resume.split()) < LONGUEUR_MIN:
        ecartes.append((article["pmid"], article["medicament"], len(resume.split())))
        continue
    corpus.append({**article,
                   "resume": resume,
                   "titre": nettoyer(article["titre"])})

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(corpus, fichier, ensure_ascii=False, indent=2)

avec_balises = sum(1 for a in brut if BALISE.search(a["resume"]))

print(f"Abstracts en entrée   : {len(brut)}")
print(f"Contenaient du balisage : {avec_balises}")
print(f"Écartés (< {LONGUEUR_MIN} mots) : {len(ecartes)}")
for pmid, medicament, n in ecartes:
    print(f"   PMID {pmid} — {medicament} ({n} mots)")
print(f"Corpus final          : {len(corpus)}")
print(f"Fichier écrit         : {SORTIE}")