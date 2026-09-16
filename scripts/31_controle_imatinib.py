# scripts/31_controle_imatinib.py
# Objectif : rassembler tous les articles portant les sauts de la chaîne imatinib,
# afin de les soumettre au prompt corrigé et statuer sur le retrait.

import json

CHAINES = "data/processed/chaines_retenues_avant_retrait.json"
CORPUS = "data/processed/corpus_avant_retrait.json"
SORTIE = "data/processed/controle_imatinib.json"

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

chaine = next(c for c in chaines
              if c["etapes"][0]["source"].lower() == "imatinib")
ident = chaine.get("id")

print("Chaîne contrôlée :")
for i, etape in enumerate(chaine["etapes"], 1):
    print(f"  saut {i} : {etape['source']} --{etape['relation']}--> {etape['cible']}")

with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)

echantillon = [a for a in corpus
               if any(p["role"] == "cible" and p.get("chaine") == ident
                      for p in a["provenance"])]

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(echantillon, fichier, ensure_ascii=False, indent=2)

print(f"\nArticles portant cette chaîne : {len(echantillon)}")
for article in echantillon:
    sauts = sorted({p["saut"] for p in article["provenance"]
                    if p["role"] == "cible" and p.get("chaine") == ident})
    print(f"  saut(s) {sauts}  PMID {article['pmid']} ({article['annee']}) "
          f"— {article['titre'][:60]}")
print(f"\nFichier écrit : {SORTIE}")