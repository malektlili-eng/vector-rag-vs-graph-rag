# scripts/50_exporter_classement_graphe.py
# Objectif : enregistrer le classement de documents produit par le graphe,
# sous le même format que celui du vectoriel, pour l'étape de génération.

import json
import re
from collections import defaultdict, Counter

RELATIONS = "data/processed/relations_nettoyees.json"
JEU = "data/processed/jeu_de_test.json"
SORTIE = "data/processed/classement_graphe.json"

PROFONDEUR = 2
MAXI = 20

MOTS_VIDES = {
    "which", "what", "does", "do", "is", "are", "the", "a", "an", "of", "in",
    "to", "for", "by", "as", "other", "another", "besides", "also", "has",
    "have", "been", "shown", "reported", "described", "cause", "causes",
    "inhibit", "inhibits", "activate", "activates", "upregulate", "downregulate",
    "drug", "compound", "process", "receptor", "protein", "enzyme", "hormone",
    "antidepressant", "same", "that", "this", "with", "and", "or", "name",
    "currently", "classified", "selective", "potent", "potently", "patients",
}
GRECQUES = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu",
    "ν": "nu", "ξ": "xi", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega",
}
def canon(texte):
    t = texte.lower().strip()
    for grec, latin in GRECQUES.items():
        t = t.replace(grec, latin)
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

aretes = defaultdict(list)
for r in relations:
    s, t = canon(r["source"]), canon(r["target"])
    if not s or not t or s == t:
        continue
    a = {"s": s, "t": t, "pmid": r["pmid"]}
    aretes[s].append(a)
    aretes[t].append(a)

def ancrer(question):
    mots = [m for m in re.findall(r"[a-zA-Z0-9\-]+", question.lower())
            if m not in MOTS_VIDES and len(m) > 3]
    trouves, couverts = [], set()
    for taille in (3, 2, 1):
        for debut in range(len(mots) - taille + 1):
            if any(i in couverts for i in range(debut, debut + taille)):
                continue
            cle = canon(" ".join(mots[debut:debut + taille]))
            if cle in aretes and len(cle) >= 4:
                trouves.append(cle)
                couverts.update(range(debut, debut + taille))
    return trouves

def classer(question):
    ancres = ancrer(question)
    score, vus = Counter(), set(ancres)
    frontiere = list(ancres)
    for saut in range(1, PROFONDEUR + 1):
        suivante = []
        for noeud in frontiere:
            for a in aretes.get(noeud, []):
                poids = 1.0 / saut
                if a["s"] in ancres or a["t"] in ancres:
                    poids *= 2.0
                score[a["pmid"]] += poids
                voisin = a["t"] if a["s"] == noeud else a["s"]
                if voisin not in vus:
                    vus.add(voisin)
                    suivante.append(voisin)
        frontiere = suivante
    return ancres, [p for p, _ in score.most_common(MAXI)]

with open(JEU, "r", encoding="utf-8") as fichier:
    questions = json.load(fichier)

sortie = []
for q in questions:
    ancres, classement = classer(q["question"])
    sortie.append({"id": q["id"], "type": q["type"],
                   "attendus": sorted(set(q.get("pmids", []))),
                   "ancres": ancres, "classement": classement})

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(sortie, fichier, ensure_ascii=False, indent=2)

vides = [l["id"] for l in sortie if not l["classement"]]
print(f"Classements enregistrés : {len(sortie)}")
print(f"Sans aucun document : {len(vides)}"
      f"{'  → ' + ', '.join(vides) if vides else ''}")
print(f"Fichier écrit : {SORTIE}")