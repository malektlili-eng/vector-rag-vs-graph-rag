# -*- coding: utf-8 -*-
"""
58 - Decoupage du corpus en passages courts.

Objectif : construire une seconde unite d'indexation pour le pipeline A.

La baseline du notebook 47 encode chaque document entier, titre compris :
titre + ligne vide + resume. Ce script produit des passages courts, afin de
mesurer quelle part de l'ecart vectoriel/graphe tenait au choix de l'unite
d'indexation plutot qu'a l'architecture.

Chaque passage commence par le titre de son document, comme dans la
baseline. Sans ce titre, les passages perdraient une information que la
baseline possedait : la comparaison changerait deux choses a la fois et
desavantagerait le vectoriel, a l'inverse du but recherche.

Deux granularites sont produites, pour ne pas faire reposer le resultat
sur un reglage arbitraire :

    granularite 3p : 3 phrases, pas 2  ->  1 phrase de recouvrement
    granularite 2p : 2 phrases, pas 1  ->  1 phrase de recouvrement

Le recouvrement evite qu'une relation enoncee a cheval sur deux phrases
soit coupee par une frontiere de passage.

Chaque passage enregistre aussi `fin_car`, la position dans le resume ou
se termine sa derniere phrase. Le notebook 61 s'en sert pour savoir si le
passage se trouvait dans la partie du document que le modele d'encodage
lisait reellement : ce modele tronque ses entrees, et la troncature ne
peut se mesurer qu'avec son propre tokeniseur, disponible sur Colab.

Sorties : data/processed/passages_3p.json
          data/processed/passages_2p.json
"""

import json
import os
import re
import statistics

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTREE = os.path.join(DOSSIER, "data", "processed", "corpus.json")

GRANULARITES = [
    ("3p", 3, 2),
    ("2p", 2, 1),
]

# Abreviations frequentes en biomedical : le point qui les suit ne
# termine pas une phrase. Sans cette protection, "e.g." ou "Fig. 2"
# produirait des passages tronques au mauvais endroit.
ABREVIATIONS = [
    "e.g.", "i.e.", "vs.", "cf.", "et al.", "approx.", "ca.",
    "Fig.", "fig.", "Tab.", "tab.", "No.", "no.", "vol.", "Vol.",
    "Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "St.", "Inc.", "Ltd.",
    "min.", "max.", "sec.", "hr.", "wk.", "mo.", "yr.",
]


def decouper_en_phrases(texte):
    """Decoupe un texte en phrases, en protegeant les abreviations."""
    t = texte.strip()
    for i, abr in enumerate(ABREVIATIONS):
        t = t.replace(abr, "\x00%d\x00" % i)
    morceaux = re.split(r"(?<=[.!?])\s+", t)
    phrases = []
    for p in morceaux:
        for i, abr in enumerate(ABREVIATIONS):
            p = p.replace("\x00%d\x00" % i, abr)
        p = p.strip()
        if p:
            phrases.append(p)
    return phrases


def fins_de_phrases(resume, phrases):
    """Position, dans le resume, de la fin de chaque phrase.

    Chaque phrase est une sous-chaine exacte du resume, dans l'ordre :
    on la cherche a partir de la fin de la precedente.
    """
    fins = []
    curseur = 0
    for p in phrases:
        debut = resume.find(p, curseur)
        if debut < 0:
            raise ValueError("phrase introuvable dans le resume")
        curseur = debut + len(p)
        fins.append(curseur)
    return fins


def fenetres(n, taille, pas):
    """Indices [debut, fin) des fenetres glissantes sur n phrases."""
    if n <= taille:
        return [(0, n)]
    bornes = []
    i = 0
    while i < n:
        bornes.append((i, min(i + taille, n)))
        if i + taille >= n:
            break
        i += pas
    return bornes


def construire(corpus, taille, pas):
    passages = []
    for article in corpus:
        resume = article.get("resume") or ""
        if not resume.strip():
            continue
        titre = (article.get("titre") or "").strip()
        phrases = decouper_en_phrases(resume)
        fins = fins_de_phrases(resume, phrases)
        for rang, (d, f) in enumerate(fenetres(len(phrases), taille, pas)):
            corps = " ".join(phrases[d:f])
            passages.append({
                "id": "%s_p%d" % (article["pmid"], rang),
                "pmid": article["pmid"],
                "rang": rang,
                "texte": titre + "\n\n" + corps if titre else corps,
                "fin_car": fins[f - 1],
            })
    return passages


def main():
    with open(ENTREE, encoding="utf-8") as f:
        corpus = json.load(f)

    avec_resume = [a for a in corpus if (a.get("resume") or "").strip()]
    sans_titre = sum(1 for a in avec_resume if not (a.get("titre") or "").strip())
    print("resumes en entree :", len(corpus))
    if len(avec_resume) != len(corpus):
        print("resumes vides ignores :", len(corpus) - len(avec_resume))
    print("documents sans titre :", sans_titre)
    print()

    for etiquette, taille, pas in GRANULARITES:
        passages = construire(corpus, taille, pas)
        sortie = os.path.join(DOSSIER, "data", "processed",
                              "passages_%s.json" % etiquette)
        with open(sortie, "w", encoding="utf-8") as f:
            json.dump(passages, f, ensure_ascii=False, indent=1)

        mots = [len(p["texte"].split()) for p in passages]
        docs = set(p["pmid"] for p in passages)
        perdus = set(a["pmid"] for a in avec_resume) - docs

        print("granularite %s : %d phrases, pas %d, titre en tete" % (etiquette, taille, pas))
        print("  passages produits     :", len(passages))
        print("  passages par document : %.1f en moyenne" % (len(passages) / len(docs)))
        print("  mots par passage      : moyenne %.0f | mediane %d | min %d | max %d"
              % (sum(mots) / len(mots), statistics.median(mots), min(mots), max(mots)))
        print("  documents perdus      :", len(perdus))
        print("  ecrit :", os.path.basename(sortie))
        print()

    print("La troncature se mesure dans le notebook 61, avec le tokeniseur")
    print("du modele d'encodage.")


if __name__ == "__main__":
    main()
