# scripts/13_couverture_souple.py
# Objectif : mesurer combien d'entités deviennent détectables lorsqu'on relâche
# progressivement le critère d'appariement textuel.

import json
import re
from collections import defaultdict

CHAINES = "data/processed/chaines_candidates.json"
CORPUS = "data/processed/corpus_pilote.json"

MEDICAMENTS = {"venlafaxine", "epoprostenol", "propylthiouracil",
               "filgrastim", "metolazone"}

MOTS_VIDES = {"of", "the", "and", "a", "an", "in", "to", "for", "on", "by", "with"}

def tokeniser(texte):
    return [t for t in re.findall(r"[a-z0-9]+", texte.lower())
            if t not in MOTS_VIDES and len(t) > 2]

def niveau_1(entite, doc):
    """Phrase exacte."""
    return entite.lower() in doc

def niveau_2(entite, doc):
    """Deux derniers mots significatifs, comme phrase."""
    tokens = tokeniser(entite)
    if len(tokens) < 2:
        return niveau_1(entite, doc)
    return " ".join(tokens[-2:]) in doc

def niveau_3(entite, doc):
    """Tous les tokens significatifs présents, même dispersés,
    et même à l'intérieur d'un mot plus long (uptake ⊂ reuptake)."""
    tokens = tokeniser(entite)
    if not tokens:
        return False
    return all(t in doc for t in tokens)

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = [c for c in json.load(fichier)
               if c["medicament"].lower() in MEDICAMENTS]

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

textes = defaultdict(list)
for article in corpus:
    textes[article["medicament"].lower()].append(
        (article["titre"] + " " + article["resume"]).lower()
    )

entites = {}
for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    for etape in chaine["etapes"]:
        for nom, type_e in ((etape["source"], etape["source_type"]),
                            (etape["cible"], etape["cible_type"])):
            if nom in entites:
                continue
            entites[nom] = (
                type_e,
                sum(1 for d in docs if niveau_1(nom, d)),
                sum(1 for d in docs if niveau_2(nom, d)),
                sum(1 for d in docs if niveau_3(nom, d)),
            )

print(f"{'Entité':<48}{'exact':>7}{'phrase':>8}{'tokens':>8}")
for nom, (type_e, n1, n2, n3) in sorted(entites.items(), key=lambda x: x[1][0]):
    print(f"{nom[:47]:<48}{n1:>7}{n2:>8}{n3:>8}")

for niveau, indice in (("exact", 1), ("phrase", 2), ("tokens", 3)):
    trouvees = sum(1 for v in entites.values() if v[indice] > 0)
    print(f"\nNiveau {niveau:<8} : {trouvees}/{len(entites)} entités détectées")

# Couverture des chaînes au niveau le plus souple
def couvre(etape, docs):
    a, b = etape["source"], etape["cible"]
    return sum(1 for d in docs if niveau_3(a, d) and niveau_3(b, d))

complets = 0
for chaine in chaines:
    docs = textes[chaine["medicament"].lower()]
    if all(couvre(e, docs) > 0 for e in chaine["etapes"]):
        complets += 1
print(f"\nChaînes entièrement couvertes (niveau tokens) : {complets}/{len(chaines)}")