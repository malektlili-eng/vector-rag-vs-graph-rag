# scripts/48_pipeline_graphe.py
# Objectif : construire le graphe à partir des relations extraites, ancrer chaque
# question sur ses nœuds, traverser à deux sauts, et mesurer le rappel de documents.

import json
import re
from collections import defaultdict, Counter

RELATIONS = "data/processed/relations_nettoyees.json"
JEU = "data/processed/jeu_de_test.json"
SORTIE = "data/processed/recuperation_graphe.json"

K = 5                    # même budget documentaire que le Pipeline A
PROFONDEUR = 2

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
#def canon(texte):
#    t = re.sub(r"\s*\([^)]*\)\s*", " ", texte.lower().strip())
#    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
#    t = re.sub(r"\s+", " ", t).strip()
#    t = re.sub(r"[\s\-]+", "", t)
#    return t[:-1] if t.endswith("s") and len(t) > 4 else t
def canon(texte):
    t = texte.lower().strip()
    for grec, latin in GRECQUES.items():
        t = t.replace(grec, latin)
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t
    
# ---------- Construction du graphe
with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

libelles = defaultdict(Counter)
aretes = defaultdict(list)          # nœud -> arêtes incidentes (les deux sens)

for r in relations:
    s, t = canon(r["source"]), canon(r["target"])
    if not s or not t or s == t:
        continue
    libelles[s][r["source"]] += 1
    libelles[t][r["target"]] += 1
    arete = {"s": s, "t": t, "relation": r["relation"], "pmid": r["pmid"],
             "src": r["source"], "tgt": r["target"]}
    aretes[s].append(arete)
    aretes[t].append(arete)

def libelle(cle):
    return libelles[cle].most_common(1)[0][0]

print(f"Nœuds : {len(aretes)}")
print(f"Arêtes : {sum(len(v) for v in aretes.values()) // 2}")

# ---------- Ancrage
def ancrer(question):
    """Nœuds du graphe mentionnés dans la question, du plus long au plus court."""
    mots = [m for m in re.findall(r"[a-zA-Z0-9\-]+", question.lower())
            if m not in MOTS_VIDES and len(m) > 3]
    trouves, couverts = [], set()
    # on tente les groupes de 3, puis 2, puis 1 mot
    for taille in (3, 2, 1):
        for debut in range(len(mots) - taille + 1):
            if any(i in couverts for i in range(debut, debut + taille)):
                continue
            cle = canon(" ".join(mots[debut:debut + taille]))
            if cle in aretes and len(cle) >= 4:
                trouves.append(cle)
                couverts.update(range(debut, debut + taille))
    return trouves

# ---------- Traversée
def traverser(depart, profondeur=PROFONDEUR):
    """Arêtes atteintes en partant des nœuds d'ancrage, avec leur distance."""
    atteintes, vus = [], set(depart)
    frontiere = list(depart)
    for saut in range(1, profondeur + 1):
        suivante = []
        for noeud in frontiere:
            for a in aretes.get(noeud, []):
                atteintes.append({**a, "saut": saut})
                voisin = a["t"] if a["s"] == noeud else a["s"]
                if voisin not in vus:
                    vus.add(voisin)
                    suivante.append(voisin)
        frontiere = suivante
    return atteintes

# ---------- Classement des documents
def classer(atteintes, ancres):
    """Un document est d'autant mieux classé qu'il porte des arêtes proches
    des points d'ancrage et qu'il en porte plusieurs."""
    score = Counter()
    detail = defaultdict(list)
    for a in atteintes:
        poids = 1.0 / a["saut"]
        if a["s"] in ancres or a["t"] in ancres:
            poids *= 2.0                     # arête directement incidente
        score[a["pmid"]] += poids
        detail[a["pmid"]].append(
            f"{a['src'][:22]} --{a['relation'][:18]}--> {a['tgt'][:22]}")
    return score, detail

# ---------- Évaluation
with open(JEU, "r", encoding="utf-8") as fichier:
    questions = json.load(fichier)

lignes, sans_ancrage = [], []
for q in questions:
    ancres = ancrer(q["question"])
    if not ancres:
        sans_ancrage.append(q["id"])
    atteintes = traverser(ancres)
    score, detail = classer(atteintes, set(ancres))
    recuperes = [p for p, _ in score.most_common(K)]

    attendus = set(q.get("pmids", []))
    trouves = attendus & set(recuperes)
    rappel = len(trouves) / len(attendus) if attendus else None

    lignes.append({
        "id": q["id"], "type": q["type"],
        "ancres": [libelle(a) for a in ancres],
        "n_aretes": len(atteintes),
        "recuperes": recuperes, "attendus": sorted(attendus),
        "rappel": rappel,
    })

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(lignes, fichier, ensure_ascii=False, indent=2)

avec = [l for l in lignes if l["rappel"] is not None]
print(f"\n=== GRAPH RAG — rappel@{K} ===")
print(f"Global : {sum(l['rappel'] for l in avec) / len(avec):.2f}")
for genre in ("single-hop", "pont", "intersection"):
    sous = [l for l in avec if l["type"] == genre]
    if sous:
        m = sum(l["rappel"] for l in sous) / len(sous)
        print(f"  {genre:<14} {m:.2f}  ({len(sous)} questions)")

print(f"\nQuestions sans ancrage : {len(sans_ancrage)}"
      f"{'  → ' + ', '.join(sans_ancrage) if sans_ancrage else ''}")

print("\n=== DÉTAIL PAR QUESTION ===")
for l in lignes:
    marque = "--" if l["rappel"] is None else f"{l['rappel']:.2f}"
    print(f"\n{l['id']} [{l['type']}]  rappel {marque}  "
          f"({l['n_aretes']} arêtes atteintes)")
    print(f"  ancres : {', '.join(l['ancres']) if l['ancres'] else 'AUCUNE'}")
    print(f"  attendus  : {', '.join(l['attendus'])}")
    print(f"  récupérés : {', '.join(l['recuperes'])}")