# scripts/54_echantillon_polarite.py
# Objectif : tirer un échantillon reproductible de relations à polarité, et
# extraire pour chacune la phrase source, afin de mesurer le taux d'inversion.

import json
import random
import re

RELATIONS = "data/processed/relations_nettoyees.json"
CORPUS = "data/processed/corpus.json"
TAILLE = 40
GRAINE = 42

POLARISEES = {
    "positively regulates", "negatively regulates",
    "increases activity of", "decreases activity of",
    "increases abundance of", "decreases abundance of",
    "positively correlated with", "negatively correlated with",
}

def phrases(texte):
    return re.split(r"(?<=[.!?])\s+", texte)

def fragments(nom):
    """Morceaux significatifs d'un nom d'entité, pour retrouver sa phrase."""
    mots = re.findall(r"[A-Za-z0-9\-]{4,}", nom)
    return [m.lower() for m in mots] or [nom.lower()]

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = [r for r in json.load(fichier)
                 if r["relation"] in POLARISEES]
with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}

print(f"Relations à polarité dans le graphe : {len(relations)}")

random.seed(GRAINE)
echantillon = random.sample(relations, min(TAILLE, len(relations)))

for i, r in enumerate(echantillon, 1):
    article = corpus.get(r["pmid"], {})
    texte = article.get("titre", "") + " " + article.get("resume", "")
    cles = fragments(r["source"]) + fragments(r["target"])
    retenues = [p for p in phrases(texte)
                if any(c in p.lower() for c in cles)]

    print(f"\n{'=' * 74}")
    print(f"{i:>2}. PMID {r['pmid']}")
    print(f"    EXTRAIT : {r['source'][:30]} --{r['relation']}--> {r['target'][:30]}")
    print(f"    origine : « {r.get('predicat_origine', '?')} »")
    print(f"    titre   : {article.get('titre', '(absent)')[:70]}")
    print("    phrases :")
    for p in retenues[:3]:
        print(f"      {p.strip()[:230]}")
    if not retenues:
        print("      (aucune phrase contenant ces entités)")