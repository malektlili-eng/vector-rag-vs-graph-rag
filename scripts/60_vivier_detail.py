# -*- coding: utf-8 -*-
"""
60 - Vivier de questions : arithmetique exacte.

Diagnostic en LECTURE SEULE. N'ecrit aucun fichier, ne modifie rien.

Le script 59 a montre l'entonnoir 350 -> 29 -> 16 -> 11 questions
multi-sauts, mais il comparait les chemins par leurs PMID, ce qui ne
distingue pas deux chemins differents reposant sur les deux memes
resumes. Ce script compare par les ENTITES, seule signature fiable :
les etiquettes de relation different d'un fichier a l'autre (le meme
chemin paroxetine -> CYP2D6 porte "negatively regulates" dans la liste
courte et "decreases activity of" dans le jeu de test), signe que les
fichiers proviennent d'executions differentes.

Question a laquelle il repond : combien de questions multi-sauts
supplementaires sont disponibles sans nouvelle collecte, et lesquelles.
"""

import json
import os
import re

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(DOSSIER, "data", "processed")

SEPARATEUR = re.compile(r"\s*(?:--[^-]*?-->|<--)\s*")


def charger(nom):
    chemin = os.path.join(PROC, nom)
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def signature_fichier(c):
    """Signature par entites d'un chemin issu des fichiers de selection."""
    d, p, a = norm(c.get("depart")), norm(c.get("pont")), norm(c.get("arrivee"))
    if c.get("type") == "intersection":
        # A -> B <- C : l'ordre de A et C est arbitraire
        return ("intersection", p, frozenset([d, a]))
    return ("pont", d, p, a)


def signatures_question(q):
    """Signatures possibles d'une question du jeu de test.

    Les intersections notent parfois deux extremites alternatives
    ("ramucirumab / nintedanib") : chacune donne une signature.
    """
    ch = q.get("chemin")
    if not ch:
        return []
    bouts = [x.strip() for x in SEPARATEUR.split(ch) if x.strip()]
    if len(bouts) < 3:
        return []
    if q.get("type") == "intersection":
        a, pont = norm(bouts[0]), norm(bouts[1])
        autres = [norm(x) for x in bouts[2].split("/") if x.strip()]
        return [("intersection", pont, frozenset([a, c])) for c in autres]
    return [("pont", norm(bouts[0]), norm(bouts[1]), norm(bouts[2]))]


def pmids_chemin(c):
    return frozenset(str(x) for x in (c.get("pmid_1"), c.get("pmid_2")) if x)


def decrire(c):
    fleche = "<--" if c.get("type") == "intersection" else "-->"
    return "%s --%s--> %s %s %s   [%s + %s]" % (
        c.get("depart"), c.get("relation_1"), c.get("pont"),
        fleche if c.get("type") == "intersection" else "--%s-->" % c.get("relation_2"),
        c.get("arrivee"), c.get("pmid_1"), c.get("pmid_2"))


# ------------------------------------------------------------------
jeu = charger("jeu_de_test.json") or []
shortlist = charger("chemins_shortlist.json") or []
filtres = charger("chemins_shortlist_filtres.json") or []
candidats = charger("chemins_candidats.json") or []

utilisees = set()
for q in jeu:
    for s in signatures_question(q):
        utilisees.add(s)

pmids_utilises = set()
for q in jeu:
    if q.get("pmids"):
        pmids_utilises.add(frozenset(str(x) for x in q["pmids"]))

sig_short = {signature_fichier(c): c for c in shortlist}
sig_filtres = {signature_fichier(c): c for c in filtres}

print("=" * 66)
print("1. CONTROLE DE L'ANALYSE PAR ENTITES")
print("=" * 66)
print()
print("  questions multi-sauts dans le jeu de test :",
      sum(1 for q in jeu if q.get("type") in ("pont", "intersection")))
print("  signatures extraites de ces questions     :", len(utilisees))
non_reconnues = [q["id"] for q in jeu
                 if q.get("type") in ("pont", "intersection")
                 and not signatures_question(q)]
if non_reconnues:
    print("  ATTENTION chemins non analysables :", non_reconnues)
else:
    print("  toutes les questions multi-sauts ont ete analysees")

retrouvees = sum(1 for s in utilisees if s in sig_short)
print()
print("  signatures de questions retrouvees dans la liste courte : %d / %d"
      % (retrouvees, len(utilisees)))
print("  (un chiffre bas signifierait que la liste courte provient")
print("   d'une execution differente de celle du jeu de test)")

print()
print("=" * 66)
print("2. RECOUVREMENT ENTRE LES DEUX FICHIERS DE SELECTION")
print("=" * 66)
print()
communs = set(sig_short) & set(sig_filtres)
print("  liste courte (chemins_shortlist)          :", len(sig_short))
print("  apres filtres (chemins_shortlist_filtres) :", len(sig_filtres))
print("  communs aux deux                          :", len(communs))
print("  dans la liste courte seulement            :", len(set(sig_short) - set(sig_filtres)))
print("  dans les filtres seulement                :", len(set(sig_filtres) - set(sig_short)))
print()
print("  Si 'liste courte seulement' est proche de 0, la liste courte")
print("  est bien le sous-ensemble retenu apres revue manuelle, et")
print("  'filtres seulement' correspond aux chemins ecartes.")

print()
print("=" * 66)
print("3. DISPONIBLE : RETENU EN REVUE, JAMAIS UTILISE")
print("=" * 66)
print()
dispo_short = [c for s, c in sig_short.items() if s not in utilisees]
print("  chemins de la liste courte non utilises :", len(dispo_short))
print()
for c in dispo_short:
    doublon = " (memes resumes qu'une question existante)" if pmids_chemin(c) in pmids_utilises else ""
    print("   .", decrire(c) + doublon)

print()
print("=" * 66)
print("4. ECARTE EN REVUE MANUELLE - NE PAS REUTILISER")
print("=" * 66)
print()
ecartes = [c for s, c in sig_filtres.items() if s not in sig_short]
print("  chemins presents apres filtres mais absents de la liste courte :", len(ecartes))
print("  (le rapport indique 13 chemins ecartes pour inversion de polarite)")
print()
for c in ecartes:
    print("   x", decrire(c))

print()
print("=" * 66)
print("5. INDEPENDANCE DES CHEMINS DISPONIBLES")
print("=" * 66)
print()
ponts_utilises = set(norm(q.get("entite_pont")) for q in jeu if q.get("entite_pont"))
ponts_dispo = set(norm(c.get("pont")) for c in dispo_short)
print("  entites pont deja utilisees   :", len(ponts_utilises))
print("  entites pont des disponibles  :", len(ponts_dispo))
print("  dont nouvelles                :", len(ponts_dispo - ponts_utilises))
print("  ->", sorted(ponts_dispo - ponts_utilises))
nouveaux_resumes = sum(1 for c in dispo_short if pmids_chemin(c) not in pmids_utilises)
print()
print("  chemins reposant sur un couple de resumes inedit :", nouveaux_resumes)

print()
print("=" * 66)
print("6. VIVIER SINGLE-HOP")
print("=" * 66)
print()
rels = charger("relations_nettoyees.json") or []
pmids_jeu = set()
for q in jeu:
    pmids_jeu.update(str(x) for x in q.get("pmids", []))
libres = [r for r in rels if str(r.get("pmid")) not in pmids_jeu]
print("  relations totales                        :", len(rels))
print("  relations sur un resume deja utilise     :", len(rels) - len(libres))
print("  relations sur un resume inedit           :", len(libres))
print("  resumes distincts parmi celles-ci        :", len(set(str(r.get("pmid")) for r in libres)))
print()
compte = {}
for r in libres:
    k = str(r.get("relation"))
    compte[k] = compte.get(k, 0) + 1
print("  par predicat :")
for k in sorted(compte, key=lambda x: -compte[x])[:12]:
    print("    %-32s %4d" % (k, compte[k]))

print()
print("=" * 66)
print("7. VIVIER BRUT NON EXPLOITE")
print("=" * 66)
print()
sig_cand = {}
for c in candidats:
    sig_cand.setdefault(signature_fichier(c), c)
jamais_vus = set(sig_cand) - set(sig_filtres) - set(sig_short) - utilisees
print("  candidats bruts (signatures distinctes) :", len(sig_cand))
print("  jamais passes par les filtres            :", len(jamais_vus))
print()
print("  Ces chemins ont ete ecartes par les filtres automatiques")
print("  (endpoints coexistant dans un meme resume, types non")
print("  admissibles, etc.). Les reintegrer exigerait de relacher")
print("  un critere, ce qui doit etre justifie explicitement.")

print()
print("AUCUN FICHIER N'A ETE MODIFIE.")
