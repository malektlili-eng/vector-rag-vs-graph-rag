# scripts/01_inspecter_donnees.py
# Objectif : vérifier la forme réelle des données avant tout traitement.

import yaml

CHEMIN = "data/raw/indication_paths.yaml"

print("Chargement en cours... (30 à 60 secondes, c'est normal)")

with open(CHEMIN, "r", encoding="utf-8") as fichier:
    donnees = yaml.safe_load(fichier)

print("Chargement terminé.\n")

# 1. Quelle est la forme globale de l'objet ?
print("Type de l'objet racine :", type(donnees))
print("Nombre d'éléments      :", len(donnees))

# 2. À quoi ressemble un élément ?
#    On ne présume pas que c'est une liste : c'est justement ce qu'on vérifie.
premier = donnees[0] if isinstance(donnees, list) else donnees

print("\nType d'un élément      :", type(premier))
print("Clés d'un élément      :", list(premier.keys()))