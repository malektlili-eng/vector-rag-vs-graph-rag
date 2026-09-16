# scripts/45_completer_pmids.py
# Objectif : renseigner les PMID des questions de contrôle en retrouvant,
# dans les relations extraites, l'arête dont chaque question est tirée.

import json
import re
import shutil

JEU = "data/processed/jeu_de_test.json"
RELATIONS = "data/processed/relations_nettoyees.json"

# id de la question -> (fragment du médicament, fragment de la cible)
SOURCES = {
    "SH01": ("corticosterone", "organic cation transporter"),
    "SH02": ("terguride", "5-ht(2a) receptor"),
    "SH03": ("prasugrel", "platelet aggregation"),
    "SH04": ("elemene", "ferroptosis"),
    "SH05": ("nilotinib", "3a4"),
    "SH06": ("sb204741", "5-ht2b receptor"),
    "SH07": ("sarpogrelate", "5-ht 2a receptor"),
    "SH08": ("capsaicin", "mucus secretion"),
    "SH09": ("azd6140", "p2y(12) receptor"),
}

def simplifie(texte):
    return re.sub(r"\s+", " ", texte.lower().replace("-", " ")).strip()

with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)
with open(JEU, "r", encoding="utf-8") as fichier:
    jeu = json.load(fichier)

shutil.copy(JEU, JEU.replace(".json", "_avant_pmids.json"))

trouves, manquants = 0, []
for question in jeu:
    cle = question.get("id")
    if cle not in SOURCES:
        continue
    frag_source, frag_cible = (simplifie(s) for s in SOURCES[cle])

    pmids = sorted({r["pmid"] for r in relations
                    if frag_source in simplifie(r["source"])
                    and frag_cible in simplifie(r["target"])})
    question["pmids"] = pmids
    if pmids:
        trouves += 1
        print(f"  {cle}  →  {', '.join(pmids)}")
    else:
        manquants.append(cle)
        print(f"  {cle}  →  AUCUN PMID TROUVÉ")

with open(JEU, "w", encoding="utf-8") as fichier:
    json.dump(jeu, fichier, ensure_ascii=False, indent=2)

print(f"\nQuestions renseignées : {trouves}/{len(SOURCES)}")
if manquants:
    print(f"À compléter à la main depuis docs/relecture-controle.md : "
          f"{', '.join(manquants)}")
print(f"Sauvegarde : {JEU.replace('.json', '_avant_pmids.json')}")