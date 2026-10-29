# -*- coding: utf-8 -*-
"""
62 - Baseline lexicale BM25, et comparaison de toutes les baselines.

Question testee. Le pipeline vectoriel resume chaque texte en un seul
vecteur, qui reflete son sujet principal : une entite secondaire y pese
peu, meme dans un texte court (notebook 61). BM25 ne resume pas le texte :
il donne a chaque mot de la question son propre poids, le plus fort allant
au plus rare, c'est-a-dire le plus souvent au nom de l'entite. Si BM25
rejoint le graphe, l'avantage du graphe tient a ce que l'entite cherchee
n'est pas noyee dans une representation globale.

Protocole. Meme unite que la baseline vectorielle d'origine : le document
entier, titre + ligne vide + resume. Seule la representation change.
BM25 dans sa forme standard de Lucene et Elasticsearch :

    idf(t)    = ln(1 + (N - n_t + 0,5) / (n_t + 0,5))
    score(d)  = somme sur les termes t de la question de
                idf(t) * f * (k1 + 1) / (f + k1 * (1 - b + b * |d| / moy))

avec k1 = 1,2 et b = 0,75, leurs valeurs par defaut. Pretraitement :
minuscules, lettres grecques translitterees comme dans le graphe, mots
alphanumeriques, liste de mots vides anglais de Lucene, sans racinisation.
BM25 lit le document entier : il n'a pas de limite de longueur.

Le script compare ensuite, au rang 5 et selon le budget documentaire,
toutes les baselines disponibles au graphe, avec les memes tests que le
script 56 : Wilcoxon exact sur les ecarts apparies, et intervalle de
confiance bootstrap apparie (20 000 tirages, graine 42 reinitialisee a
chaque comparaison).

Entrees : corpus.json, jeu_de_test.json, courbe_rappel.json,
          baseline_passages.json (notebook 61, facultatif),
          baseline_lightrag.json (notebook 64, facultatif),
          baseline_lightrag_weight.json (notebook 66, facultatif)
Sortie  : data/processed/baseline_bm25.json

Les baselines LightRAG appliquent la recherche de LightRAG 1.5.7 a un graphe
identique au notre (792 entites, 856 paires reliees) : seule la methode de
recherche differe. Quatre configurations, deux facteurs croises.

  mode   : mix    = graphe et recherche vectorielle directe des passages
           hyb    = graphe seulement
  choix  : LR v   = les passages rattaches aux entites sont classes par
                    ressemblance vectorielle avec la question, avec le meme
                    encodeur et le meme texte que la baseline vectorielle
                    (kg_chunk_pick_method = VECTOR, reglage par defaut)
           LR p   = ils sont pris dans l'ordre des entites retrouvees
                    (kg_chunk_pick_method = WEIGHT)

Le notebook 66 rejoue les deux configurations VECTOR du notebook 64 : si les
deux fichiers sont presents, le script verifie qu'elles sont identiques avant
de s'en servir.

LightRAG ne produit pas de classement : l'ordre retenu est celui des documents
dans le contexte qu'il assemble (20 documents par question). Au rang 20, le
rappel ne depend donc pas de cet ordre.
"""

import json
import math
import os
import random
import re
from collections import Counter

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(DOSSIER, "data", "processed")

K1, B = 1.2, 0.75
BUDGETS = (1, 3, 5, 10, 20)
KMAX = max(BUDGETS)
CATEGORIES = ("single-hop", "pont", "intersection")

# Liste de mots vides anglais de Lucene (ENGLISH_STOP_WORDS_SET)
MOTS_VIDES = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in",
    "into", "is", "it", "no", "not", "of", "on", "or", "such", "that", "the",
    "their", "then", "there", "these", "they", "this", "to", "was", "will", "with",
}
GRECQUES = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
            "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
            "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "π": "pi", "ρ": "rho",
            "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega"}


def charger(nom):
    chemin = os.path.join(PROC, nom)
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def termes(texte):
    t = texte.lower()
    for g, l in GRECQUES.items():
        t = t.replace(g, l)
    return [m for m in re.findall(r"[a-z0-9]+", t) if m not in MOTS_VIDES]


class BM25:
    def __init__(self, documents, k1=K1, b=B):
        self.k1, self.b = k1, b
        self.freqs = [Counter(d) for d in documents]
        self.longueurs = [len(d) for d in documents]
        self.moyenne = sum(self.longueurs) / len(documents)
        n = Counter()
        for f in self.freqs:
            n.update(f.keys())
        N = len(documents)
        self.idf = {t: math.log(1 + (N - nt + 0.5) / (nt + 0.5)) for t, nt in n.items()}

    def scores(self, question):
        res = []
        for f, lg in zip(self.freqs, self.longueurs):
            norme = self.k1 * (1 - self.b + self.b * lg / self.moyenne)
            s = 0.0
            for t in question:
                ft = f.get(t, 0)
                if ft:
                    s += self.idf[t] * ft * (self.k1 + 1) / (ft + norme)
            res.append(s)
        return res


def classement(scores, pmids):
    ordre = sorted(range(len(scores)), key=lambda i: -scores[i])
    return [pmids[i] for i in ordre[:KMAX]]


def bornes_egalites(scores, pmids, attendus, K):
    """Rappel au rang K dans le pire et le meilleur departage des egalites."""
    tri = sorted(range(len(scores)), key=lambda i: -scores[i])
    seuil = scores[tri[K - 1]]
    surs = [pmids[i] for i in tri if scores[i] > seuil]
    egaux = [pmids[i] for i in tri if scores[i] == seuil]
    places = K - len(surs)
    a_s, a_e = len(attendus & set(surs)), len(attendus & set(egaux))
    n = len(attendus)
    return ((a_s + max(0, a_e - (len(egaux) - places))) / n,
            (a_s + min(a_e, places)) / n)


def rappel_q(liste, q, K):
    return len(set(q["pmids"]) & set(liste[:K])) / len(q["pmids"])


def rappel(cl, jeu, K, cat=None):
    qs = [q for q in jeu if cat is None or q["type"] == cat]
    return sum(rappel_q(cl[q["id"]], q, K) for q in qs) / len(qs)


def wilcoxon_exact(a, b):
    """Test des rangs signes exact, rangs moyens en cas d'ex aequo (script 56)."""
    d = [y - x for x, y in zip(a, b) if y != x]
    n = len(d)
    if n == 0:
        return 0, 0.0, 0.0, 1.0
    ordre = sorted(range(n), key=lambda i: abs(d[i]))
    rangs = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[ordre[j + 1]]) == abs(d[ordre[i]]):
            j += 1
        for k in range(i, j + 1):
            rangs[ordre[k]] = (i + j) / 2 + 1
        i = j + 1
    wp = sum(r for r, x in zip(rangs, d) if x > 0)
    wm = sum(r for r, x in zip(rangs, d) if x < 0)
    w, total, compte = min(wp, wm), sum(rangs), 0
    for masque in range(2 ** n):
        s = sum(rangs[i] for i in range(n) if masque >> i & 1)
        if s <= w + 1e-9 or s >= total - w - 1e-9:
            compte += 1
    return n, wp, wm, compte / 2 ** n


def bootstrap(a, b, tirages=20000, graine=42):
    random.seed(graine)
    paires = list(zip(a, b))
    n = len(paires)
    vals = []
    for _ in range(tirages):
        ech = [paires[random.randrange(n)] for _ in range(n)]
        vals.append(sum(y - x for x, y in ech) / n)
    vals.sort()
    return vals[int(0.025 * tirages)], vals[int(0.975 * tirages)]


def main():
    corpus = charger("corpus.json")
    jeu = charger("jeu_de_test.json")
    courbe = charger("courbe_rappel.json")
    passages = charger("baseline_passages.json")
    lightrag = charger("baseline_lightrag.json")
    poids = charger("baseline_lightrag_weight.json")

    pmids = [a["pmid"] for a in corpus]
    docs = [termes(a["titre"] + "\n\n" + a["resume"]) for a in corpus]

    print("=" * 74)
    print("1. BASELINE BM25 - DOCUMENT ENTIER")
    print("=" * 74)
    print()
    print("  documents indexes : %d   termes distincts : %d   longueur moyenne : %.0f termes"
          % (len(docs), len({t for d in docs for t in d}), sum(map(len, docs)) / len(docs)))

    moteur = BM25(docs)
    bm25, dependants = {}, []
    for q in jeu:
        s = moteur.scores(termes(q["question"]))
        bm25[q["id"]] = classement(s, pmids)
        for K in BUDGETS:
            pire, meil = bornes_egalites(s, pmids, set(q["pmids"]), K)
            if pire != meil:
                dependants.append((q["id"], K, pire, meil))

    with open(os.path.join(PROC, "baseline_bm25.json"), "w", encoding="utf-8") as f:
        json.dump({"k1": K1, "b": B, "classements": bm25}, f, ensure_ascii=False, indent=1)
    print("  ecrit : baseline_bm25.json")
    print()
    if dependants:
        print("  rappels dependant du departage des egalites :")
        for qid, K, pire, meil in dependants:
            print("    %s  K=%-2d pire %.2f  meilleur %.2f" % (qid, K, pire, meil))
    else:
        print("  aucun rappel ne depend du departage des egalites, a aucun rang")

    print()
    print("  sensibilite du rappel@5 aux parametres (k1, b) :")
    valeurs = []
    for k1 in (0.9, 1.2, 1.5, 2.0):
        for b in (0.4, 0.75, 1.0):
            m = BM25(docs, k1, b)
            cl = {q["id"]: classement(m.scores(termes(q["question"])), pmids) for q in jeu}
            valeurs.append((rappel(cl, jeu, 5), k1, b))
    print("    %d reglages : de %.4f a %.4f (reglage par defaut k1=%.1f, b=%.2f : %.4f)"
          % (len(valeurs), min(v[0] for v in valeurs), max(v[0] for v in valeurs),
             K1, B, rappel(bm25, jeu, 5)))

    print()
    colonnes = [("dense doc", {l["id"]: l["vect"] for l in courbe["detail"]})]
    if passages:
        colonnes += [("dense 3p", passages["classements"]["passages_3p"]),
                     ("dense 2p", passages["classements"]["passages_2p"])]
    else:
        print("  baseline_passages.json absent : colonnes des passages omises")
    colonnes += [("BM25 doc", bm25)]
    if poids:
        c = poids["classements"]
        colonnes += [("LR v mix", c["VECTOR mix"]), ("LR v hyb", c["VECTOR hybrid"]),
                     ("LR p mix", c["WEIGHT mix"]), ("LR p hyb", c["WEIGHT hybrid"])]
        if lightrag:
            ecarts = [mode for mode, cle in (("mix", "VECTOR mix"), ("hybrid", "VECTOR hybrid"))
                      if c[cle] != lightrag["classements"][mode]]
            print("  controle VECTOR, notebook 66 contre notebook 64 : "
                  + ("identique" if not ecarts else "DIFFERENT en mode " + ", ".join(ecarts)))
    elif lightrag:
        colonnes += [("LR v mix", lightrag["classements"]["mix"]),
                     ("LR v hyb", lightrag["classements"]["hybrid"])]
        print("  baseline_lightrag_weight.json absent : colonnes WEIGHT omises")
    else:
        print("  baselines LightRAG absentes : colonnes omises")
    colonnes += [("graphe", {l["id"]: l["graphe"] for l in courbe["detail"]})]
    graphe = colonnes[-1][1]

    print()
    print("=" * 74)
    print("2. RAPPEL SELON LE BUDGET DOCUMENTAIRE")
    print("=" * 74)
    print()
    noms = [n for n, _ in colonnes]
    if any(n.startswith("LR ") for n in noms):
        print("  LR v : LightRAG, passages classes par ressemblance vectorielle (VECTOR)")
        if any(n.startswith("LR p") for n in noms):
            print("  LR p : LightRAG, passages pris dans l'ordre des entites (WEIGHT)")
        print("  mix  : graphe et recherche vectorielle directe ; hyb : graphe seulement")
        print()
    print("  %-12s" % "K" + "".join("%10s" % n for n, _ in colonnes))
    for K in BUDGETS:
        print("  %-12d" % K + "".join("%10.4f" % rappel(c, jeu, K) for _, c in colonnes))
    print()
    print("  rappel@5 par categorie")
    for cat in CATEGORIES:
        print("  %-12s" % cat + "".join("%10.4f" % rappel(c, jeu, 5, cat) for _, c in colonnes))

    print()
    print("=" * 74)
    print("3. TESTS APPARIES AU RANG 5 (Wilcoxon exact, bootstrap 20 000, graine 42)")
    print("=" * 74)
    print()

    def comparer(nom_a, a, nom_b, b):
        """Ecart nom_b - nom_a, question par question."""
        x = [rappel_q(a[q["id"]], q, 5) for q in jeu]
        y = [rappel_q(b[q["id"]], q, 5) for q in jeu]
        n, wp, wm, p = wilcoxon_exact(x, y)
        lo, hi = bootstrap(x, y)
        print("  %-9s - %-9s ecart %+.4f  n=%2d  W+=%5.1f  W-=%5.1f  p=%.6f  IC95 [%+.4f ; %+.4f]"
              % (nom_b, nom_a, sum(y) / len(y) - sum(x) / len(x), n, wp, wm, p, lo, hi))

    for nom, c in colonnes[:-1]:
        comparer(nom, c, "graphe", graphe)
    dico = dict(colonnes)
    print()
    for a, b in (("dense doc", "BM25 doc"), ("LR v mix", "LR p mix"), ("LR v hyb", "LR p hyb")):
        if a in dico and b in dico:
            comparer(a, dico[a], b, dico[b])

    print()
    print("=" * 74)
    print("4. RAPPEL@5 PAR QUESTION")
    print("=" * 74)
    print()
    print("  %-5s %-12s" % ("", "") + "".join("%10s" % n for n, _ in colonnes))
    for q in jeu:
        print("  %-5s %-12s" % (q["id"], q["type"])
              + "".join("%10.2f" % rappel_q(c[q["id"]], q, 5) for _, c in colonnes))

    print()
    print("Seul baseline_bm25.json a ete ecrit.")


if __name__ == "__main__":
    main()
