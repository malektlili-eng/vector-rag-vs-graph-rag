# scripts/49_courbe_rappel.py
# Objectif : mesurer le rappel des deux pipelines à plusieurs valeurs de K,
# et déterminer le budget documentaire dont le vectoriel a besoin pour égaler
# le graphe.

import json
import re
from collections import defaultdict, Counter

RELATIONS = "data/processed/relations_nettoyees.json"
JEU = "data/processed/jeu_de_test.json"
VECTORIEL = "data/processed/classement_vectoriel.json"
SORTIE = "data/processed/courbe_rappel.json"

VALEURS_K = [1, 3, 5, 10, 20]
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
# ---------- Graphe : classement complet par question
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

def classement_graphe(question):
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
    return [p for p, _ in score.most_common()]

with open(JEU, "r", encoding="utf-8") as fichier:
    questions = json.load(fichier)
with open(VECTORIEL, "r", encoding="utf-8") as fichier:
    vectoriel = {l["id"]: l for l in json.load(fichier)}

# ---------- Rappel à chaque K
def rappel(classement, attendus, k):
    if not attendus:
        return None
    return len(set(classement[:k]) & set(attendus)) / len(attendus)

lignes = []
for q in questions:
    attendus = sorted(set(q.get("pmids", [])))
    lignes.append({
        "id": q["id"], "type": q["type"], "attendus": attendus,
        "vect": vectoriel.get(q["id"], {}).get("classement", []),
        "graphe": classement_graphe(q["question"]),
    })

courbe = {"vectoriel": {}, "graphe": {}}
for k in VALEURS_K:
    for nom, champ in (("vectoriel", "vect"), ("graphe", "graphe")):
        valeurs = [rappel(l[champ], l["attendus"], k) for l in lignes]
        valeurs = [v for v in valeurs if v is not None]
        courbe[nom][k] = sum(valeurs) / len(valeurs)

print(f"{'K':>4}{'vectoriel':>12}{'graphe':>10}{'écart':>10}")
for k in VALEURS_K:
    v, g = courbe["vectoriel"][k], courbe["graphe"][k]
    print(f"{k:>4}{v:>12.2f}{g:>10.2f}{g - v:>+10.2f}")

# ---------- Par catégorie
print("\n=== PAR CATÉGORIE ===")
for genre in ("single-hop", "pont", "intersection"):
    sous = [l for l in lignes if l["type"] == genre]
    if not sous:
        continue
    print(f"\n{genre}  ({len(sous)} questions)")
    print(f"{'K':>4}{'vectoriel':>12}{'graphe':>10}{'écart':>10}")
    for k in VALEURS_K:
        v = sum(rappel(l["vect"], l["attendus"], k) for l in sous) / len(sous)
        g = sum(rappel(l["graphe"], l["attendus"], k) for l in sous) / len(sous)
        print(f"{k:>4}{v:>12.2f}{g:>10.2f}{g - v:>+10.2f}")

# ---------- Budget équivalent
cible = courbe["graphe"][5]
equivalent = None
for k in range(1, 51):
    v = [rappel(l["vect"], l["attendus"], k) for l in lignes]
    v = [x for x in v if x is not None]
    if sum(v) / len(v) >= cible:
        equivalent = k
        break

print(f"\n=== BUDGET DOCUMENTAIRE ÉQUIVALENT ===")
print(f"Le graphe atteint {cible:.2f} de rappel avec 5 documents.")
if equivalent:
    print(f"Le vectoriel atteint ce niveau avec {equivalent} documents "
          f"(soit {equivalent / 5:.1f}× plus).")
else:
    print("Le vectoriel n'atteint pas ce niveau, même avec 50 documents.")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump({"courbe": courbe, "detail": lignes},
              fichier, ensure_ascii=False, indent=2)
print(f"\nFichier écrit : {SORTIE}")