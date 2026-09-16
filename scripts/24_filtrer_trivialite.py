# scripts/24_filtrer_trivialite.py
# Objectif : écarter les chaînes dont une entité pont est lexicalement contenue
# dans le médicament ou la maladie — elles ne constituent pas du multi-hop.

import json
import re
from collections import Counter

CRIBLAGE = "data/processed/criblage.json"
SORTIE = "data/processed/chaines_retenues.json"

SEUIL = 2
MOTS_VIDES = {"of", "the", "and", "in", "to", "for", "acid", "disorder",
              "disease", "deficiency", "syndrome"}

def tokens(texte):
    return {t for t in re.findall(r"[a-z]+", texte.lower())
            if t not in MOTS_VIDES and len(t) > 3}

def chevauche(pont, extremite):
    """Le pont est-il lexicalement présent dans l'extrémité (ou l'inverse) ?"""
    a, b = pont.lower(), extremite.lower()
    if len(a) >= 5 and (a in b or b in a):
        return True
    return bool(tokens(pont) & tokens(extremite))

with open(CRIBLAGE, "r", encoding="utf-8") as fichier:
    resultats = [r for r in json.load(fichier) if r["minimum"] >= SEUIL]

retenues, triviales = [], []
for chaine in resultats:
    medicament = chaine["etapes"][0]["source"]
    maladie = chaine["etapes"][-1]["cible"]
    ponts = [e["cible"] for e in chaine["etapes"][:-1]]

    fautifs = [p for p in ponts
               if chevauche(p, medicament) or chevauche(p, maladie)]
    if fautifs:
        triviales.append((chaine, fautifs))
    else:
        retenues.append(chaine)

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(retenues, fichier, ensure_ascii=False, indent=2)

print(f"Seuil de co-occurrence : {SEUIL}")
print(f"Chaînes examinées : {len(resultats)}")
print(f"  écartées pour trivialité lexicale : {len(triviales)}")
print(f"  retenues : {len(retenues)}\n")

print("=== ÉCARTÉES ===")
for chaine, fautifs in triviales:
    entites = " → ".join([chaine["etapes"][0]["source"]] +
                         [e["cible"] for e in chaine["etapes"]])
    print(f"  {entites[:88]}")
    print(f"     pont fautif : {', '.join(fautifs)}\n")

print("=== RETENUES ===")
for chaine in sorted(retenues, key=lambda c: -c["minimum"]):
    entites = " → ".join([chaine["etapes"][0]["source"]] +
                         [e["cible"] for e in chaine["etapes"]])
    print(f"  min {chaine['minimum']:>4} | {entites[:96]}")

print("\n=== MÉCANISMES CENTRAUX (redondance) ===")
noyaux = Counter(" → ".join(e["cible"] for e in c["etapes"][:-1])
                 for c in retenues)
for noyau, n in noyaux.most_common():
    print(f"  {n:>2} chaîne(s) : {noyau[:80]}")
print(f"\nMécanismes distincts : {len(noyaux)} pour {len(retenues)} chaînes")