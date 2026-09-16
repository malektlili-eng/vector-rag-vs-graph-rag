# scripts/46_mesurer_tokens.py
# Objectif : mesurer la longueur réelle des abstracts en tokens, pour vérifier
# qu'ils tiennent dans la fenêtre de contexte sans découpage.

import json
from transformers import AutoTokenizer

CORPUS = "data/processed/corpus.json"

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

tokeniseur = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B")

longueurs_mots, longueurs_tokens = [], []
for article in corpus:
    texte = article["titre"] + "\n\n" + article["resume"]
    longueurs_mots.append(len(texte.split()))
    longueurs_tokens.append(len(tokeniseur.encode(texte)))

n = len(corpus)
moy_mots = sum(longueurs_mots) / n
moy_tokens = sum(longueurs_tokens) / n

print(f"Abstracts        : {n}")
print(f"Mots   — moyenne : {moy_mots:.0f}   max : {max(longueurs_mots)}")
print(f"Tokens — moyenne : {moy_tokens:.0f}   max : {max(longueurs_tokens)}")
print(f"Ratio tokens/mots : {moy_tokens / moy_mots:.2f}")
print(f"Dépassant 512 tokens  : {sum(1 for t in longueurs_tokens if t > 512)}")
print(f"Dépassant 4096 tokens : {sum(1 for t in longueurs_tokens if t > 4096)}")