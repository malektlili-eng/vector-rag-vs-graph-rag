# scripts/39_selection_chemins.py
# Objectif : produire une liste courte et diversifiée de chemins candidats,
# accompagnée des abstracts sources pour vérification manuelle.

import json
import re
from collections import defaultdict, Counter

CHEMINS = "data/processed/chemins_candidats.json"
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

def generique(nom):
    n = re.sub(r"[^a-z ]", " ", nom.lower()).strip()
    if n in GENERIQUES:
        return True
    mots = n.split()
    return len(mots) == 1 and len(n) <= 4

with open(CHEMINS, "r", encoding="utf-8") as fichier:
    chemins = json.load(fichier)
with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}

avant = len(chemins)
chemins = [c for c in chemins
           if not generique(c["pont"])
           and not generique(c["depart"])
           and not generique(c["arrivee"])]
print(f"Chemins écartés pour entité générique : {avant - len(chemins)}")

# Diversification
par_pont, par_couple = Counter(), Counter()
retenus = []
for c in sorted(chemins, key=lambda x: (x["type"] != "pont", x["pont"])):
    cle_pont = c["pont"].lower()
    cle_couple = (cle_pont, c["depart"].lower())
    if par_pont[cle_pont] >= MAX_PAR_PONT:
        continue
    if par_couple[cle_couple] >= MAX_PAR_DEPART:
        continue
    par_pont[cle_pont] += 1
    par_couple[cle_couple] += 1
    retenus.append(c)

print(f"Chemins retenus après diversification : {len(retenus)}")
print(f"  ponts : {sum(1 for c in retenus if c['type'] == 'pont')}")
print(f"  intersections : {sum(1 for c in retenus if c['type'] == 'intersection')}")
print(f"Entités ponts distinctes : {len(par_pont)}")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(retenus, fichier, ensure_ascii=False, indent=2)

# Fichier de relecture
with open(RELECTURE, "w", encoding="utf-8") as fichier:
    fichier.write("# Relecture des chemins candidats\n\n")
    fichier.write("Pour chaque chemin : vérifier que les deux relations sont "
                  "réellement énoncées dans l'abstract cité, et que la polarité "
                  "est correcte. Cocher VALIDE ou ÉCARTÉ.\n\n---\n\n")
    for i, c in enumerate(retenus, 1):
        fleche = "→" if c["type"] == "pont" else "←"
        fichier.write(f"## {i}. [{c['type']}] {c['motif']}\n\n")
        fichier.write(f"**Chemin :** {c['depart']} --{c['relation_1']}--> "
                      f"**{c['pont']}** {fleche} {c['arrivee']}\n\n")
        fichier.write("**Décision :** [ ] VALIDE   [ ] ÉCARTÉ   —  motif :\n\n")
        for n, pmid in ((1, c["pmid_1"]), (2, c["pmid_2"])):
            article = corpus.get(pmid, {})
            fichier.write(f"### Relation {n} — PMID {pmid}\n\n")
            fichier.write(f"*{article.get('titre', '(titre absent)')}*\n\n")
            fichier.write(f"> {article.get('resume', '(résumé absent)')}\n\n")
        fichier.write("---\n\n")

print(f"\nFichiers écrits :\n  {SORTIE}\n  {RELECTURE}")

print("\n=== APERÇU ===")
for c in retenus[:25]:
    fleche = "→" if c["type"] == "pont" else "←"
    print(f"  [{c['type'][:4]}] {c['depart'][:22]} --{c['relation_1'][:18]}--> "
          f"{c['pont'][:22]} {fleche} {c['arrivee'][:22]}")