# scripts/34_couverture_chaines.py
# Objectif : normaliser les entités extraites vers les identifiants de référence,
# puis mesurer combien de sauts de chaînes sont reconstructibles.

import json
import re
from collections import Counter, defaultdict

RELATIONS = "data/processed/relations_nettoyees.json"
CHAINES = "data/processed/chaines_retenues.json"
SYN_PROT = "data/processed/synonymes_toutes_proteines.json"
SYN_PROC = "data/processed/synonymes_tous_processus.json"
SORTIE = "data/processed/couverture_sauts.json"

NEGATIF = {"negatively regulates", "decreases activity of",
           "decreases abundance of", "negatively correlated with"}
POSITIF = {"positively regulates", "increases activity of",
           "increases abundance of", "positively correlated with"}

def classe(predicat):
    if predicat in NEGATIF:
        return "negatif"
    if predicat in POSITIF:
        return "positif"
    return predicat

def normaliser(texte):
    texte = re.sub(r"[^a-z0-9 ]+", " ", texte.lower())
    return re.sub(r"\s+", " ", texte).strip()

def variantes(texte):
    """Formes comparables d'une mention : entière, hors parenthèses,
    contenu des parenthèses, singulier approximatif."""
    brut = {texte.strip()}
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*(.*)$", texte.strip())
    if m:
        brut.add((m.group(1) + " " + m.group(3)).strip())
        brut.add(m.group(2).strip())
    for forme in list(brut):
        if forme.endswith("s") and len(forme) > 4:
            brut.add(forme[:-1])
    return {normaliser(f) for f in brut if f.strip()}

def suffixes(terme):
    mots = terme.split()
    return [" ".join(mots[i:]) for i in range(1, len(mots) - 1)
            if len(" ".join(mots[i:])) >= 20]

# ---------- 1. Formes acceptées par entité de référence
with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)

entites_ref = {}
for chaine in chaines:
    for etape in chaine["etapes"]:
        for nom, ident in ((etape["source"], etape["source_id"]),
                           (etape["cible"], etape["cible_id"])):
            entites_ref[ident] = nom

synonymes = {}
for fichier_syn in (SYN_PROT, SYN_PROC):
    with open(fichier_syn, "r", encoding="utf-8") as fichier:
        for ident, entree in json.load(fichier).items():
            synonymes[ident] = entree["synonymes"]

forme_vers_ref = defaultdict(set)
for ident, nom in entites_ref.items():
    termes = [nom] + synonymes.get(ident, [])
    for terme in list(termes):
        termes.extend(suffixes(terme))
    for terme in termes:
        for forme in variantes(terme):
            if len(forme) >= 3:
                forme_vers_ref[forme].add(ident)

collisions = {f: r for f, r in forme_vers_ref.items() if len(r) > 1}
print(f"Entités de référence : {len(entites_ref)}")
print(f"Formes acceptées     : {len(forme_vers_ref)}")
print(f"Formes ambiguës      : {len(collisions)}")
for forme, refs in list(collisions.items())[:8]:
    print(f"    « {forme} » → {[entites_ref[r][:28] for r in refs]}")

# ---------- 2. Appariement des entités extraites
with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

def apparier(mention):
    for forme in variantes(mention):
        refs = forme_vers_ref.get(forme)
        if refs and len(refs) == 1:
            return next(iter(refs))
    return None

mentions = Counter()
apparies = {}
for rel in relations:
    for champ in ("source", "target"):
        mentions[rel[champ]] += 1
for mention in mentions:
    apparies[mention] = apparier(mention)

n_app = sum(1 for m, r in apparies.items() if r)
occ_app = sum(n for m, n in mentions.items() if apparies[m])
print(f"\nMentions distinctes  : {len(mentions)}")
print(f"  appariées          : {n_app} "
      f"({n_app * 100 // len(mentions)} % des mentions distinctes, "
      f"{occ_app * 100 // sum(mentions.values())} % des occurrences)")

# ---------- 3. Couverture des sauts
index = defaultdict(list)
for rel in relations:
    s, t = apparies[rel["source"]], apparies[rel["target"]]
    if s and t:
        index[(s, t)].append(rel)

resultats, par_position = [], defaultdict(Counter)
print("\n=== COUVERTURE PAR CHAÎNE ===")
for chaine in chaines:
    medicament = chaine["etapes"][0]["source"]
    etats = []
    for i, etape in enumerate(chaine["etapes"], 1):
        cle = (etape["source_id"], etape["cible_id"])
        candidats = index.get(cle, [])
        exact = [r for r in candidats if r["relation"] == etape["relation"]]
        polarite = [r for r in candidats
                    if classe(r["relation"]) == classe(etape["relation"])]
        etat = ("exact" if exact else
                "polarité" if polarite else
                "entités" if candidats else "absent")
        etats.append(etat)
        position = "dernier" if i == len(chaine["etapes"]) else f"saut {i}"
        par_position[position][etat] += 1
        resultats.append({"chaine": chaine.get("id"), "medicament": medicament,
                          "saut": i, "position": position, "etat": etat,
                          "attendu": etape["relation"],
                          "trouves": sorted({r["relation"] for r in candidats}),
                          "pmids": sorted({r["pmid"] for r in candidats})})
    marques = {"exact": "OK", "polarité": "~ ", "entités": "P ", "absent": "--"}
    ligne = " ".join(marques[e] for e in etats)
    complet = all(e in ("exact", "polarité") for e in etats)
    print(f"[{ligne}] {'COMPLET' if complet else '       '} "
          f"{medicament} → {chaine['maladie'][:30]}")

print("\n  OK = prédicat exact | ~ = même polarité | "
      "P = entités reliées, polarité différente | -- = absent")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(resultats, fichier, ensure_ascii=False, indent=2)

print("\n=== PAR POSITION DE SAUT ===")
for position in sorted(par_position):
    compteur = par_position[position]
    total = sum(compteur.values())
    reussis = compteur["exact"] + compteur["polarité"]
    print(f"{position:<10} {reussis:>2}/{total:<3} reconstructibles   "
          f"(exact {compteur['exact']}, polarité {compteur['polarité']}, "
          f"partiel {compteur['entités']}, absent {compteur['absent']})")

complets = sum(1 for c in chaines
               if all(r["etat"] in ("exact", "polarité")
                      for r in resultats if r["chaine"] == c.get("id")))
print(f"\nChaînes entièrement reconstructibles : {complets}/{len(chaines)}")
print(f"Fichier écrit : {SORTIE}")