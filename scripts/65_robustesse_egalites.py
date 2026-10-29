# -*- coding: utf-8 -*-
"""
65 - Robustesse des rappels du pipeline par graphe aux egalites de score.

Diagnostic en LECTURE SEULE. N'ecrit aucun fichier, ne modifie rien.

Le pipeline par graphe classe les documents par un score additif. Plusieurs
documents peuvent obtenir exactement le meme score ; s'ils se trouvent de
part et d'autre du rang K, celui qui entre dans le classement depend de
l'ordre dans lequel les relations sont lues, qui n'a aucune signification.

Pour chaque question, ce script calcule le rappel au rang K :
  - publie     : avec le departage effectivement utilise (scripts 48 et 57) ;
  - pire       : si les documents attendus sont departages en dernier ;
  - meilleur   : s'ils sont departages en premier ;
  - esperance  : moyenne sur un departage aleatoire uniforme.

Il reproduit la construction du graphe et le classement du script 57 a
l'identique, et verifie en fin d'execution qu'il retrouve ses chiffres.
"""

import json
import os
import re
from collections import defaultdict, Counter

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(DOSSIER, "data", "processed")

MOTS_VIDES = {
    "which","what","does","do","is","are","the","a","an","of","in","to","for","by","as",
    "other","another","besides","also","has","have","been","shown","reported","described",
    "cause","causes","inhibit","inhibits","activate","activates","upregulate","downregulate",
    "drug","compound","process","receptor","protein","enzyme","hormone","antidepressant",
    "same","that","this","with","and","or","name","currently","classified","selective",
    "potent","potently","patients",
}
GRECQUES = {"α":"alpha","β":"beta","γ":"gamma","δ":"delta","ε":"epsilon","ζ":"zeta",
            "η":"eta","θ":"theta","ι":"iota","κ":"kappa","λ":"lambda","μ":"mu","ν":"nu",
            "ξ":"xi","π":"pi","ρ":"rho","σ":"sigma","τ":"tau","φ":"phi","χ":"chi",
            "ψ":"psi","ω":"omega"}


def canon(texte):
    t = texte.lower().strip()
    for g, l in GRECQUES.items():
        t = t.replace(g, l)
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t


def charger(nom):
    with open(os.path.join(D, nom), encoding="utf-8") as f:
        return json.load(f)


aretes = defaultdict(list)
for r in charger("relations_nettoyees.json"):
    s, t = canon(r["source"]), canon(r["target"])
    if not s or not t or s == t:
        continue
    a = {"s": s, "t": t, "pmid": r["pmid"]}
    aretes[s].append(a)
    aretes[t].append(a)


def ancrer(q):
    mots = [m for m in re.findall(r"[a-zA-Z0-9\-]+", q.lower())
            if m not in MOTS_VIDES and len(m) > 3]
    trouves, couverts = [], set()
    for taille in (3, 2, 1):
        for deb in range(len(mots) - taille + 1):
            if any(i in couverts for i in range(deb, deb + taille)):
                continue
            cle = canon(" ".join(mots[deb:deb + taille]))
            if cle in aretes and len(cle) >= 4:
                trouves.append(cle)
                couverts.update(range(deb, deb + taille))
    return trouves


def scores(q, profondeur):
    """Scores du script 57, sans troncature au rang K."""
    ancres = ancrer(q)
    score = Counter()
    vus = set(ancres)
    front = list(ancres)
    for saut in range(1, profondeur + 1):
        suiv = []
        for n in front:
            for a in aretes.get(n, []):
                poids = 1.0 / saut
                if a["s"] in ancres or a["t"] in ancres:
                    poids *= 2.0
                score[a["pmid"]] += poids
                v = a["t"] if a["s"] == n else a["s"]
                if v not in vus:
                    vus.add(v)
                    suiv.append(v)
        front = suiv
    return score


def rappels(score, attendus, K):
    """(publie, pire, meilleur, esperance) du rappel au rang K."""
    ordre = [p for p, _ in score.most_common()]
    n = len(attendus)
    publie = len(attendus & set(ordre[:K])) / n
    if len(ordre) <= K:
        return publie, publie, publie, publie
    seuil = score[ordre[K - 1]]
    surs = [p for p in ordre if score[p] > seuil]
    egaux = [p for p in ordre if score[p] == seuil]
    places = K - len(surs)
    a_surs = len(attendus & set(surs))
    a_egaux = len(attendus & set(egaux))
    pire = (a_surs + max(0, a_egaux - (len(egaux) - places))) / n
    meilleur = (a_surs + min(a_egaux, places)) / n
    esperance = (a_surs + a_egaux * places / len(egaux)) / n
    return publie, pire, meilleur, esperance


jeu = charger("jeu_de_test.json")
courbe = charger("courbe_rappel.json")
vect = {l["id"]: l["vect"] for l in courbe["detail"]}
N = len(jeu)
CATEGORIES = ("single-hop", "pont", "intersection")


def moyenne(valeurs):
    return sum(valeurs) / len(valeurs)


print("=" * 72)
print("1. QUESTIONS DONT LE RAPPEL@5 DEPEND DU DEPARTAGE DES EGALITES")
print("=" * 72)
print()
aucune = True
for prof in (1, 2):
    for q in jeu:
        pub, pire, meil, esp = rappels(scores(q["question"], prof), set(q["pmids"]), 5)
        if pire != meil:
            aucune = False
            print("  profondeur %d  %-5s  publie %.2f   pire %.2f   meilleur %.2f   esperance %.2f"
                  % (prof, q["id"], pub, pire, meil, esp))
if aucune:
    print("  aucune")

print()
print("=" * 72)
print("2. ABLATION AU RANG 5 SOUS LES QUATRE DEPARTAGES")
print("=" * 72)
print()
v_glob = moyenne([len(set(q["pmids"]) & set(vect[q["id"]][:5])) / len(q["pmids"]) for q in jeu])
tab = {}
for prof in (1, 2):
    par_q = [rappels(scores(q["question"], prof), set(q["pmids"]), 5) for q in jeu]
    tab[prof] = {"global": [moyenne([x[i] for x in par_q]) for i in range(4)]}
    for c in CATEGORIES:
        sel = [x for x, q in zip(par_q, jeu) if q["type"] == c]
        tab[prof][c] = [moyenne([x[i] for x in sel]) for i in range(4)]

print("  %-14s %-11s %9s %9s %9s %10s" % ("", "profondeur", "publie", "pire", "meilleur", "esperance"))
for ligne in ("global",) + CATEGORIES:
    for prof in (1, 2):
        pub, pire, meil, esp = tab[prof][ligne]
        print("  %-14s %-11d %9.4f %9.4f %9.4f %10.4f" % (ligne if prof == 1 else "", prof, pub, pire, meil, esp))

p2 = tab[2]["global"][0]
print()
print("  vectoriel global : %.4f   graphe complet : %.4f   ecart : %.4f" % (v_glob, p2, p2 - v_glob))
print()
for i, lib in enumerate(("publie", "pire", "meilleur", "esperance")):
    p1 = tab[1]["global"][i]
    print("  part de l'ecart obtenue par l'ancrage seul (%-9s) : %6.1f %%"
          % (lib, 100 * (p1 - v_glob) / (p2 - v_glob)))

print()
print("=" * 72)
print("3. DOCUMENTS QUI CHANGENT ENTRE PROFONDEUR 1 ET 2 (departage publie)")
print("=" * 72)
print()
for q in jeu:
    att = set(q["pmids"])
    t1 = [p for p, _ in scores(q["question"], 1).most_common(5)]
    t2 = [p for p, _ in scores(q["question"], 2).most_common(5)]
    gagnes = sorted(att & (set(t2) - set(t1)))
    perdus = sorted(att & (set(t1) - set(t2)))
    if gagnes or perdus:
        print("  %-5s %-13s gagnes %s   perdus %s" % (q["id"], q["type"], gagnes, perdus))

print()
print("=" * 72)
print("4. COURBE DU PIPELINE COMPLET (PROFONDEUR 2) SELON K")
print("=" * 72)
print()
print("  %-14s %4s %9s %9s %9s %10s" % ("", "K", "publie", "pire", "meilleur", "esperance"))
for ligne in ("global",) + CATEGORIES:
    qs = jeu if ligne == "global" else [q for q in jeu if q["type"] == ligne]
    for K in (1, 3, 5, 10, 20):
        par_q = [rappels(scores(q["question"], 2), set(q["pmids"]), K) for q in qs]
        vals = [moyenne([x[i] for x in par_q]) for i in range(4)]
        print("  %-14s %4d %9.4f %9.4f %9.4f %10.4f" % (ligne if K == 1 else "", K, *vals))

print()
print("=" * 72)
print("5. CONTROLE : CONCORDANCE AVEC LE SCRIPT 57")
print("=" * 72)
print()
attendu = {1: 0.8083, 2: 0.8333}
ok = all(abs(tab[p]["global"][0] - attendu[p]) < 5e-5 for p in (1, 2)) and abs(v_glob - 0.55) < 5e-5
print("  vectoriel 0.5500, profondeur 1 0.8083, profondeur 2 0.8333 :",
      "RETROUVES" if ok else "ECART - NE PAS UTILISER CES CHIFFRES")
print()
print("AUCUN FICHIER N'A ETE MODIFIE.")
