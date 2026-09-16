# scripts/41_filtre_faux_multihop.py
# Objectif : écarter les chemins dont les deux extrémités figurent dans un même
# abstract du corpus — un tel chemin est résoluble par une seule récupération.

import json
import re
from collections import Counter

CHEMINS = "data/processed/chemins_shortlist.json"
CORPUS = "data/processed/corpus.json"
SORTIE = "data/processed/chemins_shortlist_filtres.json"

def canon(texte):
    t = texte.lower().strip()
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[\s\-]+", "", t)

def present(entite, texte_canon):
    c = canon(entite)
    if len(c) < 4:
        return False
    if c.endswith("s") and len(c) > 5:
        c = c[:-1]
    return c in texte_canon

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)
textes = [(a["pmid"], canon(a["titre"] + " " + a["resume"])) for a in corpus]

with open(CHEMINS, "r", encoding="utf-8") as fichier:
    chemins = json.load(fichier)

gardes, rejets = [], []
for c in chemins:
    coupables = [pmid for pmid, texte in textes
                 if present(c["depart"], texte) and present(c["arrivee"], texte)]
    if coupables:
        rejets.append((c, coupables))
    else:
        gardes.append(c)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(gardes, fichier, ensure_ascii=False, indent=2)

print(f"Chemins en entrée : {len(chemins)}")
print(f"  écartés (faux multi-hop) : {len(rejets)}")
print(f"  conservés : {len(gardes)}\n")

print("=== ÉCARTÉS ===")
for c, coupables in rejets:
    fleche = "→" if c["type"] == "pont" else "←"
    print(f"  {c['depart'][:24]} ... {c['pont'][:22]} {fleche} {c['arrivee'][:24]}")
    print(f"      les deux extrémités dans : {', '.join(coupables[:3])}")

ponts = Counter(c["pont"] for c in gardes)
print(f"\nEntités ponts distinctes conservées : {len(ponts)}")