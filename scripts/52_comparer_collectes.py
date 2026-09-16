# scripts/52_comparer_collectes.py
# Objectif : mesurer l'effet du filtre mécanistique sur la composition du corpus.

import json

def charger(chemin):
    with open(chemin, "r", encoding="utf-8") as fichier:
        return {a["pmid"]: a for a in json.load(fichier)}

v1 = charger("data/raw/pubmed_corpus_v1.json")
v2 = charger("data/raw/pubmed_corpus.json")

communs = set(v1) & set(v2)
partis = set(v1) - set(v2)
arrives = set(v2) - set(v1)

print(f"Collecte v1 : {len(v1)} abstracts")
print(f"Collecte v2 : {len(v2)} abstracts")
print(f"  conservés : {len(communs)} ({len(communs) * 100 // len(v1)} % de v1)")
print(f"  écartés   : {len(partis)}")
print(f"  ajoutés   : {len(arrives)}")

print("\n=== ÉCARTÉS (10 premiers) ===")
for pmid in list(partis)[:10]:
    print(f"  {v1[pmid]['titre'][:76]}")

print("\n=== AJOUTÉS (10 premiers) ===")
for pmid in list(arrives)[:10]:
    print(f"  {v2[pmid]['titre'][:76]}")