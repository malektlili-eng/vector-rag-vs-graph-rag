# -*- coding: utf-8 -*-
"""
59 - Vivier de questions encore disponible.

Diagnostic en LECTURE SEULE. N'ecrit aucun fichier, ne modifie rien.

Objectif : mesurer combien de questions supplementaires sont atteignables
sans nouvelle collecte PubMed. Le jeu de test compte 20 questions (3 ponts,
8 intersections, 9 controles single-hop) issues d'un vivier plus large.
Ce script compte ce qui n'a jamais servi.

Il ne suppose pas la structure des fichiers : il l'affiche.
"""

import json
import os

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(DOSSIER, "data", "processed")

FICHIERS = [
    "chemins_candidats.json",
    "chemins_shortlist_filtres.json",
    "chemins_shortlist.json",
    "jeu_de_test.json",
]


def charger(nom):
    chemin = os.path.join(PROC, nom)
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def elements(donnees):
    """Rend la liste d'elements, que la racine soit une liste ou un dict."""
    if donnees is None:
        return []
    if isinstance(donnees, list):
        return donnees
    if isinstance(donnees, dict):
        for cle in ("chemins", "candidats", "shortlist", "resultats",
                    "questions", "detail", "items"):
            if cle in donnees and isinstance(donnees[cle], list):
                return donnees[cle]
        for v in donnees.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def apercu(obj, limite=420):
    t = json.dumps(obj, ensure_ascii=False)
    return t if len(t) <= limite else t[:limite] + " ..."


def pmids_de(element):
    """Extrait un ensemble de PMID d'un element, quel que soit le champ."""
    trouves = set()

    def creuser(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if "pmid" in k.lower():
                    if isinstance(v, str):
                        trouves.add(v)
                    elif isinstance(v, list):
                        trouves.update(str(i) for i in v if isinstance(i, (str, int)))
                    elif isinstance(v, int):
                        trouves.add(str(v))
                else:
                    creuser(v)
        elif isinstance(x, list):
            for i in x:
                creuser(i)

    creuser(element)
    return trouves


print("=" * 62)
print("1. STRUCTURE DES FICHIERS")
print("=" * 62)

charges = {}
for nom in FICHIERS:
    d = charger(nom)
    charges[nom] = d
    print()
    print("--- %s" % nom)
    if d is None:
        print("    ABSENT")
        continue
    if isinstance(d, dict):
        print("    racine : dict, cles =", list(d.keys())[:12])
    els = elements(d)
    print("    elements :", len(els))
    if els and isinstance(els[0], dict):
        print("    champs   :", list(els[0].keys()))
        print("    exemple  :", apercu(els[0]))

print()
print("=" * 62)
print("2. ENTONNOIR")
print("=" * 62)
print()
for nom in FICHIERS:
    els = elements(charges.get(nom))
    print("    %-32s %5d" % (nom, len(els)))

print()
print("=" * 62)
print("3. REPARTITION PAR TYPE")
print("=" * 62)
for nom in FICHIERS:
    els = elements(charges.get(nom))
    if not els or not isinstance(els[0], dict):
        continue
    champ = None
    for c in ("type", "forme", "categorie", "type_chemin"):
        if c in els[0]:
            champ = c
            break
    print()
    print("--- %s  (champ '%s')" % (nom, champ))
    if champ is None:
        print("    aucun champ de type identifie")
        continue
    compte = {}
    for e in els:
        v = str(e.get(champ))
        compte[v] = compte.get(v, 0) + 1
    for k in sorted(compte, key=lambda x: -compte[x]):
        print("    %-28s %4d" % (k, compte[k]))

print()
print("=" * 62)
print("4. CE QUI N'A JAMAIS SERVI")
print("=" * 62)

jeu = elements(charges.get("jeu_de_test.json"))
utilises = set()
for q in jeu:
    p = pmids_de(q)
    if p:
        utilises.add(frozenset(p))
print()
print("    questions dans le jeu de test :", len(jeu))
print("    signatures PMID utilisees     :", len(utilises))

for nom in ("chemins_shortlist.json", "chemins_shortlist_filtres.json"):
    els = elements(charges.get(nom))
    if not els:
        continue
    inutilises = []
    for e in els:
        p = pmids_de(e)
        if not p:
            continue
        # non utilise si aucune question ne repose exactement sur ces PMID,
        # et si les PMID du chemin ne sont pas tous couverts par une question
        if frozenset(p) in utilises:
            continue
        if any(p <= u for u in utilises):
            continue
        inutilises.append(e)
    print()
    print("--- %s" % nom)
    print("    total            :", len(els))
    print("    jamais utilises  :", len(inutilises))
    champ = None
    if els and isinstance(els[0], dict):
        for c in ("type", "forme", "categorie", "type_chemin"):
            if c in els[0]:
                champ = c
                break
    if champ:
        compte = {}
        for e in inutilises:
            v = str(e.get(champ))
            compte[v] = compte.get(v, 0) + 1
        for k in sorted(compte, key=lambda x: -compte[x]):
            print("      %-26s %4d" % (k, compte[k]))
    for e in inutilises[:6]:
        print("      .", apercu(e, 240))

print()
print("=" * 62)
print("5. VIVIER SINGLE-HOP")
print("=" * 62)
rel = charger("relations_nettoyees.json")
rels = elements(rel)
print()
print("    relations disponibles :", len(rels))
if rels and isinstance(rels[0], dict):
    print("    champs                :", list(rels[0].keys()))
print()
print("    Les questions single-hop derivent d'une relation unique :")
print("    le vivier n'est pas limitant, seule la verification")
print("    manuelle l'est.")
print()
print("AUCUN FICHIER N'A ETE MODIFIE.")
