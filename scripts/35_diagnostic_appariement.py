# scripts/35_diagnostic_appariement.py
# Objectif : déterminer si l'échec des derniers sauts vient d'un défaut de
# normalisation des entités ou d'une absence réelle de la relation.

import json
import re
from collections import Counter, defaultdict

RELATIONS = "data/processed/relations_nettoyees.json"
CHAINES = "data/processed/chaines_retenues.json"
SYN_PROT = "data/processed/synonymes_toutes_proteines.json"
SYN_PROC = "data/processed/synonymes_tous_processus.json"

MOTS_VIDES = {"of", "the", "and", "in", "to", "for", "disease", "disorder",
              "syndrome", "acute", "chronic", "primary", "type"}

def tokens(texte):
    return {t for t in re.findall(r"[a-z0-9]+", texte.lower())
            if t not in MOTS_VIDES and len(t) > 3}

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)
with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

# Entités de référence, par type
ref = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        ref[etape["source_id"]] = (etape["source"], etape["source_type"])
        ref[etape["cible_id"]] = (etape["cible"], etape["cible_type"])

synonymes = {}
for f in (SYN_PROT, SYN_PROC):
    with open(f, "r", encoding="utf-8") as fichier:
        for ident, entree in json.load(fichier).items():
            synonymes[ident] = entree["synonymes"]

print("=== FORMES DISPONIBLES PAR TYPE D'ENTITÉ DE RÉFÉRENCE ===")
par_type = defaultdict(list)
for ident, (nom, type_e) in ref.items():
    par_type[type_e].append(len(synonymes.get(ident, [])) or 1)
for type_e, n in sorted(par_type.items()):
    print(f"  {type_e:<20} {len(n):>2} entités, "
          f"{sum(n)/len(n):.1f} formes en moyenne")

# Mentions extraites
mentions = Counter()
for rel in relations:
    mentions[rel["source"]] += 1
    mentions[rel["target"]] += 1

print("\n=== CANDIDATS NON APPARIÉS, PAR ENTITÉ DE RÉFÉRENCE ===")
print("(mentions extraites partageant des mots avec l'entité attendue)\n")

for ident, (nom, type_e) in sorted(ref.items(), key=lambda x: x[1][1]):
    if type_e not in ("Disease", "PhenotypicFeature", "ChemicalSubstance"):
        continue
    mots_ref = tokens(nom)
    proches = [(m, n) for m, n in mentions.items()
               if mots_ref & tokens(m)]
    proches.sort(key=lambda x: -x[1])
    if proches:
        print(f"  [{type_e}] « {nom} »")
        for m, n in proches[:5]:
            marque = "  = exact" if m.lower() == nom.lower() else ""
            print(f"        {n:>3}x  {m[:56]}{marque}")
        print()

print("\n=== DERNIERS SAUTS : QU'A PRODUIT LA SOURCE ? ===\n")
for chaine in chaines:
    dernier = chaine["etapes"][-1]
    source_nom = dernier["source"]
    formes = {source_nom} | set(synonymes.get(dernier["source_id"], []))
    formes = {f.lower() for f in formes}
    sortantes = [r for r in relations if r["source"].lower() in formes]
    print(f"{chaine['etapes'][0]['source']} → {chaine['maladie'][:28]}")
    print(f"  attendu : {source_nom[:34]} --{dernier['relation']}--> "
          f"{dernier['cible'][:28]}")
    if not sortantes:
        print("  aucune relation extraite partant de cette source\n")
        continue
    for r in sortantes[:6]:
        print(f"    {r['source'][:26]} --{r['relation']}--> {r['target'][:32]}")
    print()