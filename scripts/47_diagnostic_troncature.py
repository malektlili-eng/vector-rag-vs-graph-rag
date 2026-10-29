# scripts/47_diagnostic_troncature.py
# Objectif : déterminer si les échecs de récupération portent préférentiellement
# sur des abstracts tronqués par la fenêtre de 512 tokens.
#
# Révision ultérieure : la fenêtre de 512 tokens retenue ici est erronée. La
# configuration du modèle d'encodage fixe max_seq_length à 350 ; mesurée à cette
# limite, la proportion d'abstracts tronqués passe de 5 à 6 % à 35 %. La réfutation
# de l'hypothèse de troncature a été refaite par intervention dans le notebook 61,
# en n'indexant que la partie que la baseline lisait réellement : le rappel au rang 5
# ne bouge pas. C'est cette mesure qui fait référence. Ce script est conservé comme
# trace de l'état des connaissances à cette étape.

import json
from transformers import AutoTokenizer

CORPUS = "data/processed/corpus.json"
JEU = "data/processed/jeu_de_test.json"
RESULTATS = "data/processed/recuperation_vectorielle.json"
LIMITE = 512

tokeniseur = AutoTokenizer.from_pretrained(
    "pritamdeka/S-PubMedBert-MS-MARCO")

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = {a["pmid"]: a for a in json.load(fichier)}
with open(JEU, "r", encoding="utf-8") as fichier:
    jeu = {q["id"]: q for q in json.load(fichier)}
with open(RESULTATS, "r", encoding="utf-8") as fichier:
    resultats = json.load(fichier)["biomed"]

longueurs = {}
for pmid, a in corpus.items():
    texte = a["titre"] + "\n\n" + a["resume"]
    longueurs[pmid] = len(tokeniseur.encode(texte, truncation=False))

trouves, manques = [], []
for ligne in resultats:
    for pmid in ligne["attendus"]:
        (trouves if pmid in ligne["recuperes"] else manques).append(pmid)

def profil(liste, nom):
    if not liste:
        print(f"{nom} : aucun")
        return
    tronques = sum(1 for p in liste if longueurs.get(p, 0) > LIMITE)
    moyenne = sum(longueurs.get(p, 0) for p in liste) / len(liste)
    print(f"{nom} : {len(liste)} documents")
    print(f"   longueur moyenne : {moyenne:.0f} tokens")
    print(f"   tronqués (> {LIMITE}) : {tronques} "
          f"({tronques * 100 // len(liste)} %)")

print("=== DOCUMENTS ATTENDUS ===")
profil(trouves, "Retrouvés  ")
profil(manques, "Manqués    ")

print(f"\nRéférence corpus entier : "
      f"{sum(1 for v in longueurs.values() if v > LIMITE) * 100 // len(longueurs)} % tronqués")

print("\n=== DÉTAIL DES DOCUMENTS MANQUÉS ===")
for ligne in resultats:
    absents = [p for p in ligne["attendus"] if p not in ligne["recuperes"]]
    if not absents:
        continue
    q = jeu.get(ligne["id"], {})
    print(f"\n{ligne['id']} [{ligne['type']}] — rappel {ligne['rappel']:.2f}")
    print(f"  {q.get('question', '')[:78]}")
    for pmid in absents:
        n = longueurs.get(pmid, 0)
        marque = "TRONQUÉ" if n > LIMITE else "       "
        print(f"  manqué : PMID {pmid}  {n:>5} tokens  {marque}")
        print(f"           {corpus.get(pmid, {}).get('titre', '')[:66]}")