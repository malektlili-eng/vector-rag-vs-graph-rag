# scripts/02_inspecter_structure.py
# Objectif : vérifier la forme réelle de graph, nodes et links
# avant d'écrire le script de comptage.

import yaml

CHEMIN = "data/raw/indication_paths.yaml"

print("Chargement en cours... (30 à 60 secondes)")

with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)

print("Chargement terminé.\n")

premier = donnees[0]

# --- 1. Le niveau "graph" : les métadonnées du chemin
#     C'est ici que devrait se trouver la clé "drug" que tu attendais.
print("=== graph ===")
print(premier["graph"])

# --- 2. Les nœuds : les entités traversées par le chemin
noeuds = premier["nodes"]
print("\n=== nodes ===")
print("Type             :", type(noeuds))
print("Nombre de nœuds  :", len(noeuds))
print("Clés d'un nœud   :", list(noeuds[0].keys()))
print("Premier nœud     :", noeuds[0])

# --- 3. Les liens : les relations entre ces entités
liens = premier["links"]
print("\n=== links ===")
print("Type             :", type(liens))
print("Nombre de liens  :", len(liens))
print("Clés d'un lien   :", list(liens[0].keys()))
print("Premier lien     :", liens[0])