# scripts/30_retirer_chaine.py
# Objectif : retirer du jeu de test une chaîne dont une relation n'est énoncée
# par aucun article, et reclasser ses articles porteurs en distracteurs.

import json
import shutil

CHAINES = "data/processed/chaines_retenues.json"
CORPUS = "data/processed/corpus.json"
MEDICAMENT_RETIRE = "imatinib"

shutil.copy(CHAINES, CHAINES.replace(".json", "_avant_retrait.json"))
shutil.copy(CORPUS, CORPUS.replace(".json", "_avant_retrait.json"))

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

retirees = [c for c in chaines
            if c["etapes"][0]["source"].lower() == MEDICAMENT_RETIRE.lower()]
gardees = [c for c in chaines if c not in retirees]
ids_retires = {c.get("id") for c in retirees}

with open(CHAINES, "w", encoding="utf-8") as fichier:
    json.dump(gardees, fichier, ensure_ascii=False, indent=2)

print(f"Chaînes retirées : {len(retirees)}")
for c in retirees:
    entites = " → ".join([c["etapes"][0]["source"]] +
                         [e["cible"] for e in c["etapes"]])
    print(f"   {entites}")
print(f"Chaînes conservées : {len(gardees)}")

# --- Reclassement des articles porteurs
with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

reclasses = 0
for article in corpus:
    reste = [p for p in article["provenance"]
             if not (p["role"] == "cible" and p.get("chaine") in ids_retires)]
    if len(reste) == len(article["provenance"]):
        continue
    if not any(p["role"] == "cible" for p in reste):
        reste.append({"role": "distracteur", "medicament": MEDICAMENT_RETIRE,
                      "note": "porteur d'une chaîne retirée"})
        reclasses += 1
    article["provenance"] = reste

with open(CORPUS, "w", encoding="utf-8") as fichier:
    json.dump(corpus, fichier, ensure_ascii=False, indent=2)

n_cibles = sum(1 for a in corpus
               if any(p["role"] == "cible" for p in a["provenance"]))
mecanismes = {" → ".join(e["cible"] for e in c["etapes"][:-1]) for c in gardees}

print(f"\nArticles reclassés en distracteurs : {reclasses}")
print(f"Corpus : {len(corpus)} abstracts "
      f"({n_cibles} ciblés / {len(corpus) - n_cibles} distracteurs)")
print(f"Mécanismes distincts : {len(mecanismes)} pour {len(gardees)} chaînes")