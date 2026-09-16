# scripts/44_questions_controle.py
# Objectif : proposer des questions single-hop de contrôle, répondables par un seul
# abstract, à partir des relations les mieux attestées du graphe.

import json
import re
from collections import Counter, defaultdict

RELATIONS = "data/processed/relations_nettoyees.json"
CORPUS = "data/processed/corpus.json"
MULTIHOP = "data/processed/jeu_de_test.json"
SORTIE = "docs/relecture-controle.md"

# Formulations par prédicat : (gabarit, ce que la réponse désigne)
GABARITS = {
    "decreases activity of":
        "Which {type_cible} does {source} inhibit?",
    "increases activity of":
        "Which {type_cible} does {source} activate?",
    "negatively regulates":
        "Which process does {source} downregulate?",
    "positively regulates":
        "Which process does {source} upregulate?",
    "increases abundance of":
        "Which substance does {source} increase the level of?",
    "decreases abundance of":
        "Which substance does {source} decrease the level of?",
}

LIBELLE_TYPE = {
    "Protein": "protein or receptor",
    "ChemicalSubstance": "substance",
    "BiologicalProcess": "process",
    "Disease": "disease",
    "PhenotypicFeature": "clinical feature",
    "OrganismTaxon": "organism",
    "Drug": "drug",
}

def canon(t):
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t.lower().strip())
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[\s\-]+", "", t)

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)
with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}
with open(MULTIHOP, "r", encoding="utf-8") as fichier:
    multihop = json.load(fichier)

# Entités déjà mobilisées par le multi-hop : à éviter pour garder l'indépendance
deja = set()
for q in multihop:
    deja.add(canon(q["entite_pont"]))
    for r in q["reponses_acceptables"]:
        deja.add(canon(r))

# Attestation : une relation vue dans plusieurs abstracts est plus sûre
support = Counter()
for r in relations:
    support[(canon(r["source"]), r["relation"], canon(r["target"]))] += 1

candidats, vus_source = [], Counter()
for r in relations:
    if r["relation"] not in GABARITS:
        continue
    if r["source_type"] != "Drug":
        continue
    cs, ct = canon(r["source"]), canon(r["target"])
    if cs in deja or ct in deja:
        continue
    if len(cs) < 4 or len(ct) < 4 or vus_source[cs] >= 1:
        continue

    cle = (cs, r["relation"], ct)
    candidats.append({
        "source": r["source"], "relation": r["relation"],
        "cible": r["target"], "type_cible": r["target_type"],
        "pmid": r["pmid"], "support": support[cle],
        "question": GABARITS[r["relation"]].format(
            source=r["source"],
            type_cible=LIBELLE_TYPE.get(r["target_type"], "entity")),
    })
    vus_source[cs] += 1

candidats.sort(key=lambda c: -c["support"])
candidats = candidats[:20]

with open(SORTIE, "w", encoding="utf-8") as fichier:
    fichier.write("# Relecture des questions de contrôle (single-hop)\n\n")
    fichier.write("Objectif : retenir 8 à 10 questions répondables par un seul "
                  "abstract. Vérifier que la relation est énoncée, que la polarité "
                  "est correcte, et que la question a une réponse claire.\n\n---\n\n")
    for i, c in enumerate(candidats, 1):
        a = corpus.get(c["pmid"], {})
        fichier.write(f"## SH{i:02d}  (attestée dans {c['support']} relation(s))\n\n")
        fichier.write(f"**Question :** {c['question']}\n\n")
        fichier.write(f"**Réponse attendue :** {c['cible']}\n\n")
        fichier.write(f"**Relation :** {c['source']} --{c['relation']}--> "
                      f"{c['cible']}\n\n")
        fichier.write("**Décision :** [ ] VALIDE   [ ] ÉCARTÉ   —  motif :\n\n")
        fichier.write(f"### PMID {c['pmid']}\n\n*{a.get('titre', '(absent)')}*\n\n")
        fichier.write(f"> {a.get('resume', '(absent)')}\n\n---\n\n")

print(f"Candidats proposés : {len(candidats)}")
print(f"Fichier écrit : {SORTIE}\n")
for i, c in enumerate(candidats, 1):
    print(f"  SH{i:02d}  [{c['support']}]  {c['question'][:60]}")
    print(f"          → {c['cible'][:50]}")