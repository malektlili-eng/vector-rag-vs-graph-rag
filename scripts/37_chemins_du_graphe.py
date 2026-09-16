# scripts/37_chemins_du_graphe.py
# Objectif : construire le graphe à partir des relations extraites, y chercher
# les chemins multi-hop réellement présents, et les classer par robustesse.

import json
import re
from collections import defaultdict, Counter

RELATIONS = "data/processed/relations_nettoyees.json"
SORTIE = "data/processed/chemins_candidats.json"

MOTS_VIDES = {"of", "the", "and", "in", "to", "for", "a", "an"}

def canon(texte):
    """Forme canonique conservatrice : casse, ponctuation, parenthèses."""
    t = texte.lower().strip()
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def tokens(texte):
    return {m for m in re.findall(r"[a-z0-9]+", texte.lower())
            if m not in MOTS_VIDES and len(m) > 3}

def trivial(pont, extremite):
    """Le pont est-il lexicalement contenu dans l'extrémité ?"""
    a, b = pont.lower(), extremite.lower()
    if len(a) >= 5 and (a in b or b in a):
        return True
    return bool(tokens(pont) & tokens(extremite))

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

# ---------- Normalisation
formes = defaultdict(Counter)
for rel in relations:
    for champ in ("source", "target"):
        formes[canon(rel[champ])][rel[champ]] += 1

def libelle(cle):
    """Forme d'affichage la plus fréquente pour un nœud."""
    return formes[cle].most_common(1)[0][0]

fusions = {c: f for c, f in formes.items() if len(f) > 1}
print(f"Mentions distinctes : {sum(len(f) for f in formes.values())}")
print(f"Nœuds après fusion  : {len(formes)}")
print(f"Nœuds ayant fusionné plusieurs mentions : {len(fusions)}")
for cle, f in sorted(fusions.items(), key=lambda x: -sum(x[1].values()))[:8]:
    print(f"    {libelle(cle)[:38]:<40} ← {list(f)[:3]}")

# ---------- Graphe
sortantes = defaultdict(list)
entrantes = defaultdict(list)
types = {}
for rel in relations:
    s, t = canon(rel["source"]), canon(rel["target"])
    if not s or not t or s == t:
        continue
    arete = {"s": s, "t": t, "relation": rel["relation"],
             "pmid": rel["pmid"], "ts": rel["source_type"],
             "tt": rel["target_type"]}
    sortantes[s].append(arete)
    entrantes[t].append(arete)
    types[s] = rel["source_type"]
    types[t] = rel["target_type"]

print(f"\nNœuds : {len(types)} — arêtes : "
      f"{sum(len(v) for v in sortantes.values())}")

# ---------- Chemins de type PONT : A -> B -> C
ponts = []
for b in sortantes:
    for e1 in entrantes.get(b, []):
        for e2 in sortantes[b]:
            a, c = e1["s"], e2["t"]
            if a == c or a == b or b == c:
                continue
            if e1["pmid"] == e2["pmid"]:
                continue                      # même article : pas de multi-hop
            if trivial(libelle(b), libelle(a)) or trivial(libelle(b), libelle(c)):
                continue
            ponts.append({
                "type": "pont",
                "depart": libelle(a), "depart_type": types[a],
                "pont": libelle(b), "pont_type": types[b],
                "arrivee": libelle(c), "arrivee_type": types[c],
                "relation_1": e1["relation"], "relation_2": e2["relation"],
                "pmid_1": e1["pmid"], "pmid_2": e2["pmid"],
            })

# ---------- Chemins de type INTERSECTION : A -> B <- C
intersections = []
for b, arrivantes in entrantes.items():
    vus = set()
    for i, e1 in enumerate(arrivantes):
        for e2 in arrivantes[i + 1:]:
            a, c = e1["s"], e2["s"]
            if a == c or e1["pmid"] == e2["pmid"]:
                continue
            if (a, c) in vus or (c, a) in vus:
                continue
            if trivial(libelle(b), libelle(a)) or trivial(libelle(b), libelle(c)):
                continue
            vus.add((a, c))
            intersections.append({
                "type": "intersection",
                "depart": libelle(a), "depart_type": types[a],
                "pont": libelle(b), "pont_type": types[b],
                "arrivee": libelle(c), "arrivee_type": types[c],
                "relation_1": e1["relation"], "relation_2": e2["relation"],
                "pmid_1": e1["pmid"], "pmid_2": e2["pmid"],
            })

tous = ponts + intersections
with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(tous, fichier, ensure_ascii=False, indent=2)

print(f"\n=== CHEMINS TROUVÉS ===")
print(f"Ponts         : {len(ponts)}")
print(f"Intersections : {len(intersections)}")

def motifs(liste):
    return Counter(f"{c['depart_type']} → {c['pont_type']} → {c['arrivee_type']}"
                   for c in liste)

for nom, liste in (("PONTS", ponts), ("INTERSECTIONS", intersections)):
    if not liste:
        continue
    print(f"\n=== MOTIFS — {nom} ===")
    for motif, n in motifs(liste).most_common(8):
        print(f"{n:>5}   {motif}")

    print(f"\n=== EXEMPLES — {nom} ===")
    fleche = "→" if nom == "PONTS" else "←"
    for c in liste[:12]:
        print(f"  {c['depart'][:26]} --{c['relation_1'][:22]}--> "
              f"{c['pont'][:26]} {fleche} {c['arrivee'][:26]}")
        print(f"      PMID {c['pmid_1']} / {c['pmid_2']}")

print(f"\nFichier écrit : {SORTIE}")