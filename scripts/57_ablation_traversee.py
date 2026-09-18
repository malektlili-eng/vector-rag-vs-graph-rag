# scripts/57_ablation_traversee.py
# Ablation : compare le pipeline par graphe a profondeur 1 (ancrage seul)
# et a profondeur 2 (ancrage + traversee), pour tester le mecanisme de dilution.
import json, re
from collections import defaultdict, Counter

D = "data/processed/"
K = 5
MOTS_VIDES = {
    "which","what","does","do","is","are","the","a","an","of","in","to","for","by","as",
    "other","another","besides","also","has","have","been","shown","reported","described",
    "cause","causes","inhibit","inhibits","activate","activates","upregulate","downregulate",
    "drug","compound","process","receptor","protein","enzyme","hormone","antidepressant",
    "same","that","this","with","and","or","name","currently","classified","selective",
    "potent","potently","patients",
}
GRECQUES = {"α":"alpha","β":"beta","γ":"gamma","δ":"delta","ε":"epsilon","ζ":"zeta",
            "η":"eta","θ":"theta","ι":"iota","κ":"kappa","λ":"lambda","μ":"mu","ν":"nu",
            "ξ":"xi","π":"pi","ρ":"rho","σ":"sigma","τ":"tau","φ":"phi","χ":"chi",
            "ψ":"psi","ω":"omega"}

def canon(texte):
    t = texte.lower().strip()
    for g, l in GRECQUES.items():
        t = t.replace(g, l)
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t

relations = json.load(open(D + "relations_nettoyees.json", encoding="utf-8"))
aretes = defaultdict(list)
for r in relations:
    s, t = canon(r["source"]), canon(r["target"])
    if not s or not t or s == t:
        continue
    a = {"s": s, "t": t, "pmid": r["pmid"]}
    aretes[s].append(a); aretes[t].append(a)

def ancrer(q):
    mots = [m for m in re.findall(r"[a-zA-Z0-9\-]+", q.lower())
            if m not in MOTS_VIDES and len(m) > 3]
    trouves, couverts = [], set()
    for taille in (3, 2, 1):
        for deb in range(len(mots) - taille + 1):
            if any(i in couverts for i in range(deb, deb + taille)):
                continue
            cle = canon(" ".join(mots[deb:deb + taille]))
            if cle in aretes and len(cle) >= 4:
                trouves.append(cle); couverts.update(range(deb, deb + taille))
    return trouves

def classer(q, profondeur):
    ancres = ancrer(q); score = Counter(); vus = set(ancres); front = list(ancres)
    for saut in range(1, profondeur + 1):
        suiv = []
        for n in front:
            for a in aretes.get(n, []):
                poids = 1.0 / saut
                if a["s"] in ancres or a["t"] in ancres:
                    poids *= 2.0
                score[a["pmid"]] += poids
                v = a["t"] if a["s"] == n else a["s"]
                if v not in vus:
                    vus.add(v); suiv.append(v)
        front = suiv
    return [p for p, _ in score.most_common(K)]

jeu = json.load(open(D + "jeu_de_test.json", encoding="utf-8"))
courbe = json.load(open(D + "courbe_rappel.json", encoding="utf-8"))
vect = {l["id"]: l["vect"] for l in courbe["detail"]}

res = {1: [], 2: [], "v": []}
par_type = defaultdict(lambda: {1: [], 2: [], "v": []})
for q in jeu:
    att = set(q.get("pmids", []))
    if not att:
        continue
    for prof in (1, 2):
        r = len(att & set(classer(q["question"], prof))) / len(att)
        res[prof].append(r); par_type[q["type"]][prof].append(r)
    rv = len(att & set(vect[q["id"]][:K])) / len(att)
    res["v"].append(rv); par_type[q["type"]]["v"].append(rv)

m = lambda x: sum(x) / len(x)
print("=== ABLATION DE LA TRAVERSEE — rappel@5 ===\n")
print(f"{'':<16}{'vectoriel':>11}{'ancrage seul':>14}{'+ traversee':>13}")
print(f"{'Global':<16}{m(res['v']):>11.2f}{m(res[1]):>14.2f}{m(res[2]):>13.2f}")
for t in ("single-hop", "pont", "intersection"):
    d = par_type[t]
    print(f"{t:<16}{m(d['v']):>11.2f}{m(d[1]):>14.2f}{m(d[2]):>13.2f}")

ecart_total = m(res[2]) - m(res["v"])
ecart_ancrage = m(res[1]) - m(res["v"])
print(f"\nEcart total graphe - vectoriel      : {ecart_total:+.4f}")
print(f"Ecart obtenu par le seul ancrage    : {ecart_ancrage:+.4f}"
      f"   soit {100*ecart_ancrage/ecart_total:.0f} % de l'ecart")
print(f"Apport propre de la traversee       : {m(res[2])-m(res[1]):+.4f}"
      f"   soit {100*(m(res[2])-m(res[1]))/ecart_total:.0f} % de l'ecart")
