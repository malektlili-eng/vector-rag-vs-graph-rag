# scripts/33_recuperer_predicats.py
# Objectif : diagnostiquer les abstracts sans relation, récupérer les prédicats
# hors schéma récupérables, écarter les autres, et produire le jeu de relations
# nettoyé prêt pour la normalisation des entités.

import json
from collections import Counter, defaultdict

EXTRACTION = "data/processed/extraction.jsonl"
CORPUS = "data/processed/corpus.json"
SORTIE = "data/processed/relations_nettoyees.json"

TYPES = {"Drug", "Protein", "ChemicalSubstance", "BiologicalProcess",
         "PhenotypicFeature", "Disease", "OrganismTaxon"}
TYPES_ALIAS = {"Enzyme": "Protein"}

RELATIONS = {"positively regulates", "negatively regulates",
             "increases activity of", "decreases activity of",
             "increases abundance of", "decreases abundance of",
             "positively correlated with", "negatively correlated with",
             "participates in", "manifestation of", "causes"}

# Prédicat unique, quel que soit le type de la cible
DIRECT = {
    "negatively correlates with": "negatively correlated with",
    "positively correlates with": "positively correlated with",
    "is associated with higher levels or greater severity":
        "positively correlated with",
    "is associated with lower levels": "negatively correlated with",
    "protects against": "negatively correlated with",
    "is involved in": "participates in",
}

# Prédicat dépendant du type de la cible : (si Protein, si BiologicalProcess)
SELON_CIBLE = {
    "inhibits": ("decreases activity of", "negatively regulates"),
    "inhibits the activity of": ("decreases activity of", "negatively regulates"),
    "competitively inhibits": ("decreases activity of", "negatively regulates"),
    "blocks": ("decreases activity of", "negatively regulates"),
    "antagonizes": ("decreases activity of", "negatively regulates"),
    "attenuates": ("decreases activity of", "negatively regulates"),
    "activates": ("increases activity of", "positively regulates"),
    "stimulates": ("increases activity of", "positively regulates"),
    "augments": ("increases activity of", "positively regulates"),
    "augments activity of": ("increases activity of", "positively regulates"),
    "decreases": ("decreases activity of", "negatively regulates"),
    "increases": ("increases activity of", "positively regulates"),
}

NEGATIONS = {"does not affect", "does not mitigate", "does not inhibit",
             "has no effect on"}

def recuperer(predicat, type_cible):
    """Retourne (prédicat du schéma, motif) ou (None, motif de rejet)."""
    if predicat in RELATIONS:
        return predicat, "conforme"
    if predicat in NEGATIONS:
        return None, "négation"
    if predicat in DIRECT:
        return DIRECT[predicat], "récupéré"
    if predicat in SELON_CIBLE:
        proteine, processus = SELON_CIBLE[predicat]
        if type_cible in ("Protein", "ChemicalSubstance"):
            if predicat in ("decreases", "increases"):
                return ("decreases abundance of" if predicat == "decreases"
                        else "increases abundance of"), "récupéré"
            return proteine, "récupéré"
        return processus, "récupéré"
    return None, "sans équivalent"

# ---------- Chargement
enregistrements = []
with open(EXTRACTION, "r", encoding="utf-8") as fichier:
    for ligne in fichier:
        if ligne.strip():
            enregistrements.append(json.loads(ligne))

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}

# ---------- 1. Diagnostic des abstracts sans relation
vides = [e for e in enregistrements if not e["relations"]]
role_vides = Counter()
sauts_perdus = Counter()

for e in vides:
    article = corpus.get(e["pmid"])
    if not article:
        role_vides["absent du corpus"] += 1
        continue
    cibles = [p for p in article["provenance"] if p["role"] == "cible"]
    if cibles:
        role_vides["CIBLÉ"] += 1
        for p in cibles:
            sauts_perdus[(p["source"][:26], p["relation"], p["cible"][:26])] += 1
    else:
        role_vides["distracteur"] += 1

n_cibles = sum(1 for a in corpus.values()
               if any(p["role"] == "cible" for p in a["provenance"]))
n_distr = len(corpus) - n_cibles

print("=== ABSTRACTS SANS AUCUNE RELATION ===")
print(f"Total : {len(vides)} / {len(enregistrements)}")
for role, n in role_vides.most_common():
    base = n_cibles if role == "CIBLÉ" else n_distr
    print(f"  {role:<16} {n:>4}  ({n * 100 // max(base, 1)} % de cette catégorie)")

print("\n  Sauts dont un article porteur n'a rien produit :")
for (s, r, c), n in sauts_perdus.most_common(12):
    print(f"    {n:>2}x  {s} --{r}--> {c}")

# ---------- 2. Récupération des prédicats
propres, journal = [], Counter()
rejets = defaultdict(Counter)

for e in enregistrements:
    for rel in e["relations"]:
        ts = TYPES_ALIAS.get(rel.get("source_type"), rel.get("source_type"))
        tt = TYPES_ALIAS.get(rel.get("target_type"), rel.get("target_type"))
        origine = rel.get("relation")

        if ts not in TYPES or tt not in TYPES:
            journal["type d'entité invalide"] += 1
            rejets["type"][f"{ts} / {tt}"] += 1
            continue
        if not (isinstance(rel.get("source"), str)
                and isinstance(rel.get("target"), str)):
            journal["entité non textuelle"] += 1
            continue

        predicat, motif = recuperer(origine, tt)
        journal[motif] += 1
        if predicat is None:
            rejets[motif][origine] += 1
            continue

        propres.append({
            "pmid": e["pmid"],
            "source": rel["source"].strip(),
            "source_type": ts,
            "relation": predicat,
            "target": rel["target"].strip(),
            "target_type": tt,
            "predicat_origine": origine,
            "recupere": motif == "récupéré",
        })

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(propres, fichier, ensure_ascii=False, indent=2)

total_brut = sum(len(e["relations"]) for e in enregistrements)
print(f"\n=== RÉCUPÉRATION ===")
print(f"Relations en entrée : {total_brut}")
for motif, n in journal.most_common():
    print(f"  {motif:<26} {n:>5}")
print(f"Relations conservées : {len(propres)} "
      f"({len(propres) * 100 // total_brut} %)")
print(f"  dont récupérées    : {sum(1 for r in propres if r['recupere'])}")

print("\n=== PRÉDICATS ÉCARTÉS (sans équivalent) ===")
for predicat, n in rejets["sans équivalent"].most_common(20):
    print(f"{n:>4}   {predicat}")
if rejets["négation"]:
    print("\n=== NÉGATIONS ÉCARTÉES ===")
    for predicat, n in rejets["négation"].most_common():
        print(f"{n:>4}   {predicat}")
if rejets["type"]:
    print("\n=== TYPES INVALIDES ===")
    for paire, n in rejets["type"].most_common(8):
        print(f"{n:>4}   {paire}")

print(f"\nFichier écrit : {SORTIE}")