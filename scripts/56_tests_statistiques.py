# scripts/56_tests_statistiques.py
# Objectif : mesurer la significativite des ecarts entre les deux pipelines,
# sur un plan apparie — les memes vingt questions passent dans les deux.
# McNemar exact pour l exactitude (binaire), Wilcoxon signe pour le rappel
# (continu), bootstrap apparie pour les intervalles de confiance.

import json, random
from math import comb
from collections import defaultdict

D = "data/processed/"
courbe = json.load(open(D + "courbe_rappel.json", encoding="utf-8"))
ragas = json.load(open(D + "evaluation_ragas.json", encoding="utf-8"))

# ---- rappel@5 par question
K = 5
rap = []
for l in courbe["detail"]:
    att = set(l["attendus"])
    if not att:
        continue
    rv = len(att & set(l["vect"][:K])) / len(att)
    rg = len(att & set(l["graphe"][:K])) / len(att)
    rap.append((l["id"], l["type"], rv, rg))

print(f"Questions : {len(rap)}")
print(f"Rappel@5 moyen  vectoriel {sum(x[2] for x in rap)/len(rap):.4f}"
      f"   graphe {sum(x[3] for x in rap)/len(rap):.4f}")

# ---- exactitude par question
ex = defaultdict(dict)
for r in ragas:
    ex[r["id"]][r["pipeline"]] = bool(r["correct"])
exact = [(i, ex[i]["vectoriel"], ex[i]["graphe"]) for i in ex]
print(f"Exactitude moyenne  vectoriel {sum(x[1] for x in exact)/len(exact):.4f}"
      f"   graphe {sum(x[2] for x in exact)/len(exact):.4f}")
print()

# ---- McNemar exact (exactitude, binaire apparie)
b = sum(1 for _, v, g in exact if g and not v)   # graphe seul correct
c = sum(1 for _, v, g in exact if v and not g)   # vectoriel seul correct
n = b + c
p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) * 0.5**n for k in range(min(b, c) + 1)))
print("=== McNEMAR EXACT — EXACTITUDE ===")
print(f"  graphe seul correct  b = {b}")
print(f"  vectoriel seul       c = {c}")
print(f"  discordants          n = {n}")
print(f"  p (bilateral)          = {p:.6f}")
print()

# ---- Wilcoxon signe des rangs (rappel, continu apparie)
diffs = [g - v for _, _, v, g in rap if g != v]
n_w = len(diffs)
absd = sorted((abs(d), i) for i, d in enumerate(diffs))
rangs = [0.0] * n_w
i = 0
while i < len(absd):
    j = i
    while j + 1 < len(absd) and absd[j + 1][0] == absd[i][0]:
        j += 1
    r = (i + j + 2) / 2
    for k in range(i, j + 1):
        rangs[absd[k][1]] = r
    i = j + 1
Wp = sum(rangs[i] for i, d in enumerate(diffs) if d > 0)
Wm = sum(rangs[i] for i, d in enumerate(diffs) if d < 0)
print("=== WILCOXON SIGNE DES RANGS — RAPPEL@5 ===")
print(f"  paires non nulles n = {n_w}")
print(f"  W+ = {Wp}   W- = {Wm}")

# p exact par enumeration des signes (n_w petit)
W = min(Wp, Wm)
cnt = 0
tot = 2 ** n_w
for masque in range(tot):
    s = sum(rangs[i] for i in range(n_w) if masque >> i & 1)
    if s <= W or s >= sum(rangs) - W:
        cnt += 1
print(f"  p (bilateral, exact)   = {cnt/tot:.6f}")
print()

# ---- bootstrap apparie
random.seed(42)
B = 20000
def boot(paires, f):
    n = len(paires)
    vals = []
    for _ in range(B):
        ech = [paires[random.randrange(n)] for _ in range(n)]
        vals.append(f(ech))
    vals.sort()
    return vals[int(0.025 * B)], vals[int(0.975 * B)]

d_rap = [(v, g) for _, _, v, g in rap]
lo1, hi1 = boot(d_rap, lambda e: sum(g - v for v, g in e) / len(e))
obs1 = sum(g - v for v, g in d_rap) / len(d_rap)

d_ex = [(v, g) for _, v, g in exact]
lo2, hi2 = boot(d_ex, lambda e: sum(g - v for v, g in e) / len(e))
obs2 = sum(g - v for v, g in d_ex) / len(d_ex)

print("=== BOOTSTRAP APPARIE (20 000 reechantillons, graine 42) ===")
print(f"  ecart de rappel@5    {obs1:+.4f}   IC 95 % [{lo1:+.4f}, {hi1:+.4f}]")
print(f"  ecart d'exactitude   {obs2:+.4f}   IC 95 % [{lo2:+.4f}, {hi2:+.4f}]")
