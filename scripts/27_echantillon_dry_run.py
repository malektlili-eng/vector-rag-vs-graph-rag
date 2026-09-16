# scripts/27_echantillon_dry_run.py
# Objectif : composer un échantillon de dry run couvrant les deux polarités,
# plusieurs types de relations et un abstract ancien, avec la relation attendue
# pour chacun — grille de vérification manuelle.

import json
from collections import Counter, defaultdict

CORPUS = "data/processed/corpus.json"
SORTIE = "data/processed/dry_run_sample.json"

TAILLE = 8

NEGATIVES = {"negatively regulates", "decreases activity of",
             "negatively correlated with"}

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

cibles = [a for a in corpus
          if any(p["role"] == "cible" for p in a["provenance"])]

# --- Distribution des relations portées
relations = Counter()
for article in cibles:
    for p in article["provenance"]:
        if p["role"] == "cible":
            relations[p["relation"]] += 1

print("=== RELATIONS PORTÉES PAR LES ARTICLES CIBLÉS ===")
for relation, n in relations.most_common():
    signe = "négative" if relation in NEGATIVES else "positive"
    print(f"{n:>4}   {relation:<32} ({signe})")

print(f"\nRelations négatives : "
      f"{sum(n for r, n in relations.items() if r in NEGATIVES)}")
print(f"Relations positives : "
      f"{sum(n for r, n in relations.items() if r not in NEGATIVES)}")

# --- Sélection : couvrir un maximum de relations distinctes
par_relation = defaultdict(list)
for article in cibles:
    for p in article["provenance"]:
        if p["role"] == "cible":
            par_relation[p["relation"]].append(article)

echantillon, vus = [], set()

def ajouter(article):
    if article["pmid"] in vus:
        return False
    vus.add(article["pmid"])
    echantillon.append(article)
    return True

# 1. un article par relation distincte, en commençant par les plus rares
for relation in sorted(par_relation, key=lambda r: len(par_relation[r])):
    if len(echantillon) >= TAILLE:
        break
    for article in par_relation[relation]:
        if ajouter(article):
            break

# 2. forcer la présence d'un abstract ancien
if not any(a["annee"] and a["annee"] < "2000" for a in echantillon):
    anciens = sorted((a for a in cibles if a["annee"] and a["annee"] < "2000"),
                     key=lambda a: a["annee"])
    if anciens:
        if len(echantillon) >= TAILLE:
            echantillon.pop()
        ajouter(anciens[0])

# 3. compléter en privilégiant les médicaments non représentés
#def medicament(article):
#    for p in article["provenance"]:
#        if p["role"] == "cible":
#            return p["source"] if p["saut"] == 1 else None
#    return None

representes = {a["provenance"][0].get("source") for a in echantillon}
restants = sorted(cibles, key=lambda a: a["pmid"] in vus)
for tour in (1, 2):
    for article in restants:
        if len(echantillon) >= TAILLE:
            break
        med = next((p.get("source") for p in article["provenance"]
                    if p["role"] == "cible" and p["saut"] == 1), None)
        if tour == 1 and med in representes:
            continue
        if ajouter(article):
            representes.add(med)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(echantillon, fichier, ensure_ascii=False, indent=2)

print(f"\n=== GRILLE DE VÉRIFICATION ({len(echantillon)} abstracts) ===")
for i, article in enumerate(echantillon, 1):
    attendues = [p for p in article["provenance"] if p["role"] == "cible"]
    print(f"\n{i}. PMID {article['pmid']} ({article['annee']}) — "
          f"{len(article['resume'].split())} mots")
    print(f"   {article['titre'][:82]}")
    for p in attendues:
        signe = "NEG" if p["relation"] in NEGATIVES else "POS"
        print(f"   [{signe}] {p['source'][:30]} --{p['relation']}--> {p['cible'][:30]}")

couvertes = {p["relation"] for a in echantillon
             for p in a["provenance"] if p["role"] == "cible"}
neg = sum(1 for r in couvertes if r in NEGATIVES)
print(f"\nRelations distinctes couvertes : {len(couvertes)} "
      f"({neg} négative(s), {len(couvertes) - neg} positive(s))")
print(f"Années : {sorted(a['annee'] for a in echantillon if a['annee'])}")
print(f"Fichier écrit : {SORTIE}")
