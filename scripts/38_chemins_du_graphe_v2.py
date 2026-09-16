# scripts/38_chemins_du_graphe_v2.py
# Objectif : normalisation étendue, exclusion des arêtes médicament → médicament,
# et affichage des chemins groupés par motif.

import json
import re
from collections import defaultdict, Counter

RELATIONS = "data/processed/relations_nettoyees.json"
SORTIE = "data/processed/chemins_candidats.json"

MOTS_VIDES = {"of", "the", "and", "in", "to", "for", "a", "an"}

def conservateur(texte):
    t = texte.lower().strip()
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def agressif(cle):
    """Clé insensible aux espaces internes, aux tirets et au pluriel final."""
    t = re.sub(r"[\s\-]+", "", cle)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t

def tokens(texte):
    return {m for m in re.findall(r"[a-z0-9]+", texte.lower())
            if m not in MOTS_VIDES and len(m) > 3}

def trivial(pont, extremite):
    a, b = pont.lower(), extremite.lower()
    if len(a) >= 5 and (a in b or b in a):
        return True
    return bool(tokens(pont) & tokens(extremite))

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

# ---------- Exclusion des arêtes médicament → médicament
avant = len(relations)
relations = [r for r in relations
             if not (r["source_type"] == "Drug" and r["target_type"] == "Drug")]
print(f"Arêtes Drug → Drug écartées : {avant - len(relations)} "
      f"({len(relations)} conservées)")

# ---------- Normalisation en deux passes
brut = defaultdict(Counter)
for rel in relations:
    for champ in ("source", "target"):
        brut[conservateur(rel[champ])][rel[champ]] += 1

groupes = defaultdict(list)
for cle in brut:
    groupes[agressif(cle)].append(cle)

vers_canon, fusions_etendues = {}, []
for cle_agressive, membres in groupes.items():
    principal = max(membres, key=lambda c: sum(brut[c].values()))
    for membre in membres:
        vers_canon[membre] = principal
    if len(membres) > 1:
        fusions_etendues.append(membres)

formes = defaultdict(Counter)
for cle, compteur in brut.items():
    formes[vers_canon[cle]].update(compteur)

def libelle(cle):
    return formes[cle].most_common(1)[0][0]

print(f"\nMentions distinctes : {sum(sum(c.values()) for c in brut.values())}")
print(f"Nœuds après normalisation : {len(formes)}")
print(f"Fusions au-delà de la casse : {len(fusions_etendues)}")
for membres in sorted(fusions_etendues, key=len, reverse=True)[:10]:
    print(f"    {membres}")

# ---------- Graphe
sortantes, entrantes, types = defaultdict(list), defaultdict(list), {}
for rel in relations:
    s = vers_canon[conservateur(rel["source"])]
    t = vers_canon[conservateur(rel["target"])]
    if not s or not t or s == t:
        continue
    arete = {"s": s, "t": t, "relation": rel["relation"], "pmid": rel["pmid"]}
    sortantes[s].append(arete)
    entrantes[t].append(arete)
    types[s] = rel["source_type"]
    types[t] = rel["target_type"]

print(f"\nNœuds : {len(types)} — arêtes : {sum(len(v) for v in sortantes.values())}")

def enregistrer(a, b, c, e1, e2, forme):
    return {"type": forme,
            "depart": libelle(a), "depart_type": types[a],
            "pont": libelle(b), "pont_type": types[b],
            "arrivee": libelle(c), "arrivee_type": types[c],
            "relation_1": e1["relation"], "relation_2": e2["relation"],
            "pmid_1": e1["pmid"], "pmid_2": e2["pmid"],
            "motif": f"{types[a]} → {types[b]} → {types[c]}"}

ponts = []
for b in list(sortantes):
    for e1 in entrantes.get(b, []):
        for e2 in sortantes[b]:
            a, c = e1["s"], e2["t"]
            if len({a, b, c}) < 3 or e1["pmid"] == e2["pmid"]:
                continue
            if trivial(libelle(b), libelle(a)) or trivial(libelle(b), libelle(c)):
                continue
            ponts.append(enregistrer(a, b, c, e1, e2, "pont"))

intersections = []
for b, arrivantes in entrantes.items():
    vus = set()
    for i, e1 in enumerate(arrivantes):
        for e2 in arrivantes[i + 1:]:
            a, c = e1["s"], e2["s"]
            if len({a, b, c}) < 3 or e1["pmid"] == e2["pmid"]:
                continue
            if (a, c) in vus or (c, a) in vus:
                continue
            if trivial(libelle(b), libelle(a)) or trivial(libelle(b), libelle(c)):
                continue
            vus.add((a, c))
            intersections.append(enregistrer(a, b, c, e1, e2, "intersection"))

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(ponts + intersections, fichier, ensure_ascii=False, indent=2)

print(f"\n=== CHEMINS ===\nPonts : {len(ponts)}   Intersections : {len(intersections)}")

for nom, liste, fleche in (("PONTS", ponts, "→"),
                           ("INTERSECTIONS", intersections, "←")):
    if not liste:
        continue
    par_motif = defaultdict(list)
    for c in liste:
        par_motif[c["motif"]].append(c)
    print(f"\n{'=' * 72}\n  {nom}\n{'=' * 72}")
    for motif, groupe in sorted(par_motif.items(), key=lambda x: -len(x[1]))[:6]:
        print(f"\n  {motif}  —  {len(groupe)} chemin(s)")
        for c in groupe[:4]:
            print(f"      {c['depart'][:24]} --{c['relation_1'][:20]}--> "
                  f"{c['pont'][:24]} {fleche} {c['arrivee'][:24]}")
            print(f"          PMID {c['pmid_1']} / {c['pmid_2']}")

print(f"\nFichier écrit : {SORTIE}")