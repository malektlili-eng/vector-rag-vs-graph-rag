# scripts/40_nettoyer_shortlist.py
# Objectif : corriger le typage des nœuds, écarter les chemins à extrémités
# identiques et dédupliquer par triplet d'entités.

import json
import re
from collections import Counter, defaultdict

CHEMINS = "data/processed/chemins_candidats.json"
RELATIONS = "data/processed/relations_nettoyees.json"
CORPUS = "data/processed/corpus.json"
SORTIE = "data/processed/chemins_shortlist.json"
RELECTURE = "docs/relecture-chemins.md"

MAX_PAR_PONT = 3
MAX_PAR_DEPART = 2

GENERIQUES = {
    "response", "responses", "symptoms", "symptom", "efficacy", "remission",
    "treatment", "therapy", "patients", "safety", "tolerability", "outcome",
    "outcomes", "effect", "effects", "improvement", "adverse events",
    "clinical response", "disease", "activity", "levels", "risk",
}

def canon(texte):
    t = texte.lower().strip()
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t

def generique(nom):
    n = re.sub(r"[^a-z ]", " ", nom.lower()).strip()
    return n in GENERIQUES or (len(n.split()) == 1 and len(n) <= 4)

def meme_entite(a, b):
    """Deux libellés désignent-ils la même entité ?"""
    ca, cb = canon(a), canon(b)
    if ca == cb:
        return True
    court, long = sorted((ca, cb), key=len)
    return len(court) >= 6 and court in long

# ---------- Type majoritaire par nœud
with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

votes = defaultdict(Counter)
for rel in relations:
    votes[canon(rel["source"])][rel["source_type"]] += 1
    votes[canon(rel["target"])][rel["target_type"]] += 1

def type_reel(nom):
    compteur = votes.get(canon(nom))
    return compteur.most_common(1)[0][0] if compteur else None

# ---------- Filtrage
with open(CHEMINS, "r", encoding="utf-8") as fichier:
    chemins = json.load(fichier)

journal = Counter()
gardes = []
for c in chemins:
    td, tp, ta = (type_reel(c["depart"]), type_reel(c["pont"]),
                  type_reel(c["arrivee"]))

    if tp == "Drug" and c["type"] == "pont":
        journal["pont de type Drug"] += 1
        continue
    if any(generique(c[k]) for k in ("depart", "pont", "arrivee")):
        journal["entité générique"] += 1
        continue
    if meme_entite(c["depart"], c["arrivee"]):
        journal["extrémités identiques"] += 1
        continue
    if meme_entite(c["pont"], c["depart"]) or meme_entite(c["pont"], c["arrivee"]):
        journal["pont trivial"] += 1
        continue

    c["motif"] = f"{td} → {tp} → {ta}"
    gardes.append(c)

print(f"Chemins en entrée : {len(chemins)}")
for motif, n in journal.most_common():
    print(f"  écartés — {motif:<24} {n:>4}")
print(f"Chemins conservés : {len(gardes)}")

# ---------- Déduplication par triplet, puis diversification
vus, uniques = set(), []
for c in gardes:
    cle = tuple(sorted((canon(c["depart"]), canon(c["arrivee"])))) \
          + (canon(c["pont"]), c["type"])
    if cle in vus:
        continue
    vus.add(cle)
    uniques.append(c)
print(f"Après déduplication par triplet : {len(uniques)}")

par_pont, par_couple = Counter(), Counter()
retenus = []
for c in sorted(uniques, key=lambda x: (x["type"] != "pont", x["pont"])):
    cp = canon(c["pont"])
    cc = (cp, canon(c["depart"]))
    if par_pont[cp] >= MAX_PAR_PONT or par_couple[cc] >= MAX_PAR_DEPART:
        continue
    par_pont[cp] += 1
    par_couple[cc] += 1
    retenus.append(c)

print(f"Après diversification : {len(retenus)}"
      f"  (ponts {sum(1 for c in retenus if c['type'] == 'pont')}, "
      f"intersections {sum(1 for c in retenus if c['type'] == 'intersection')})")
print(f"Entités ponts distinctes : {len(par_pont)}")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(retenus, fichier, ensure_ascii=False, indent=2)

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}

with open(RELECTURE, "w", encoding="utf-8") as fichier:
    fichier.write("# Relecture des chemins candidats\n\n")
    fichier.write("Pour chaque chemin, vérifier dans les abstracts cités :\n"
                  "1. les deux relations sont réellement énoncées ;\n"
                  "2. la polarité est correcte (inhibe / active) ;\n"
                  "3. les entités désignent bien ce que le chemin prétend ;\n"
                  "4. une question sensée peut être formulée dessus.\n\n---\n\n")
    for i, c in enumerate(retenus, 1):
        fleche = "→" if c["type"] == "pont" else "←"
        fichier.write(f"## {i}. [{c['type']}] {c['motif']}\n\n")
        fichier.write(f"**Chemin :** {c['depart']} --{c['relation_1']}--> "
                      f"**{c['pont']}** {fleche} {c['arrivee']}\n\n")
        fichier.write("**Décision :** [ ] VALIDE   [ ] ÉCARTÉ   —  motif :\n\n")
        for n, pmid in ((1, c["pmid_1"]), (2, c["pmid_2"])):
            article = corpus.get(pmid, {})
            fichier.write(f"### Relation {n} — PMID {pmid}\n\n")
            fichier.write(f"*{article.get('titre', '(absent)')}*\n\n")
            fichier.write(f"> {article.get('resume', '(absent)')}\n\n")
        fichier.write("---\n\n")

print(f"\nFichiers écrits :\n  {SORTIE}\n  {RELECTURE}")
print("\n=== APERÇU ===")
for c in retenus[:30]:
    fleche = "→" if c["type"] == "pont" else "←"
    print(f"  [{c['type'][:4]}] {c['depart'][:22]} --{c['relation_1'][:18]}--> "
          f"{c['pont'][:22]} {fleche} {c['arrivee'][:22]}")