# scripts/42_selection_chemins_v2.py
# Objectif : sélectionner les chemins candidats — validité d'abord,
# diversification ensuite — et produire le fichier de relecture manuelle.

import json
import re
from collections import Counter, defaultdict

CHEMINS = "data/processed/chemins_candidats.json"
RELATIONS = "data/processed/relations_nettoyees.json"
CORPUS = "data/processed/corpus.json"
SORTIE = "data/processed/chemins_shortlist.json"
RELECTURE = "docs/relecture-chemins.md"

MAX_PAR_PONT = 3
MAX_PAR_DEPART = 2


GENERIQUES = {
    "response", "responses", "symptoms", "symptom", "efficacy", "remission",
    "treatment", "therapy", "patients", "safety", "tolerability", "outcome",
    "outcomes", "effect", "effects", "effectiveness", "improvement",
    "adverse events", "clinical response", "disease", "activity", "levels",
    "risk", "invasion", "migration", "proliferation", "survival",
    "progression free survival", "growth", "tumor growth", "retinal thickness",
    "antidepressant", "antidepressants", "anticonvulsants", "antipsychotics",
    "protease inhibitors", "ssris", "tricyclics", "beta blockers",
}
# Relations jugées factuellement fausses lors de la relecture manuelle.
# L'exclusion porte sur la relation et non sur le chemin : une relation erronée
# invalide tout chemin qui l'emprunte, y compris ceux d'une génération ultérieure.
RELATIONS_FAUSSES = {
    ("venlafaxine", "cyp2d6"):
        "la venlafaxine est un substrat du CYP2D6 ; l'abstract précise "
        "qu'elle n'inhibe pas les CYP",
    ("reboxetine", "norepinephrinereuptake"):
        "polarité inversée : la reboxétine inhibe la recapture",
    ("sertraline", "depression"):
        "polarité inversée : la sertraline améliore la dépression",
    ("bromocriptine", "dopaminereceptor"):
        "polarité inversée : la bromocriptine est un agoniste",
    ("desipramine", "norepinephrinetransporter"):
        "polarité inversée : la désipramine inhibe le transporteur",
    ("clomipramine", "obsessivecompulsivedisorder"):
        "polarité inversée : la clomipramine traite le TOC",
    ("clomipraminehydrochloride", "serotoninuptake"):
        "polarité inversée : la clomipramine inhibe la recapture",
    ("sertraline", "serotoninuptake"):
        "polarité inversée : la sertraline inhibe la recapture",
    ("faricimabte", "retinalthickness"):
        "polarité inversée : le faricimab réduit l'épaisseur rétinienne",
    ("finasteride", "depression"):
        "relation contestée, et de sens opposé à celui de l'autre extrémité",
    ("nicergoline", "fibrosi"):
        "relation non énoncée : absence de cas rapportés ≠ corrélation négative",
}

# Rejets propres à un chemin donné, non généralisables à une relation.
CHEMINS_EXCLUS = {
    ("ergotamine", "5-HT2B receptors", "cabergoline"):
        "faux multi-hop non détecté : l'abstract source écrit « carbegoline »",
    ("P2Y 12 receptor", "apoptosis", "Bcr-Abl-expressing cells"):
        "domaines sans rapport, extrémité mal typée",
    ("Levomilnacipran", "serotonin reuptake", "clomipramine"):
        "doublon du chemin vers clomipramine hydrochloride — même molécule",
}


def canon_entite(texte):
    """Forme canonique d'un NOM D'ENTITÉ : le contenu entre parenthèses est
    une glose (abréviation, précision) et n'appartient pas au nom."""
    t = re.sub(r"\s*\([^)]*\)\s*", " ", texte.lower().strip())
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s\-]+", "", t)
    return t[:-1] if t.endswith("s") and len(t) > 4 else t


def canon_texte(texte):
    """Forme canonique d'un TEXTE LIBRE : les parenthèses contiennent du contenu
    (listes de molécules, abréviations) et doivent être conservées."""
    t = re.sub(r"[^a-z0-9 \-]+", " ", texte.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[\s\-]+", "", t)


def tokens(texte):
    return {m for m in re.findall(r"[a-z0-9]+", texte.lower()) if len(m) > 3}


def generique(nom):
    n = re.sub(r"[^a-z ]", " ", nom.lower())
    n = re.sub(r"\s+", " ", n).strip()
    return n in GENERIQUES or (len(n.split()) == 1 and len(n) <= 4)


def malformee(nom):
    n = nom.lower()
    return (" and " in n or " or " in n
            or len(n.split()) > 5
            or n.startswith("active metabolites"))


def meme_entite(a, b):
    ca, cb = canon_entite(a), canon_entite(b)
    if ca == cb:
        return True
    court, long = sorted((ca, cb), key=len)
    return len(court) >= 6 and court in long


def variantes_entite(nom):
    """Formes sous lesquelles une entité peut apparaître dans un texte :
    forme complète, forme sans glose parenthétique, glose seule."""
    brut = nom.lower().strip()
    formes = {canon_texte(brut), canon_entite(brut)}
    glose = re.search(r"\(([^)]+)\)", brut)
    if glose:
        formes.add(canon_texte(glose.group(1)))
    return {f for f in formes if len(f) >= 4}


def dans_texte(entite, texte_canon):
    return any(f in texte_canon for f in variantes_entite(entite))


# ---------- Type majoritaire par nœud
with open(RELATIONS, "r", encoding="utf-8") as fichier:
    relations = json.load(fichier)

votes = defaultdict(Counter)
for rel in relations:
    votes[canon_entite(rel["source"])][rel["source_type"]] += 1
    votes[canon_entite(rel["target"])][rel["target_type"]] += 1


def type_reel(nom):
    c = votes.get(canon_entite(nom))
    return c.most_common(1)[0][0] if c else None


# ---------- Corpus pré-canonicalisé
with open(CORPUS, "r", encoding="utf-8") as fichier:
    corpus = json.load(fichier)
textes = [(a["pmid"], canon_texte(a["titre"] + " " + a["resume"]))
          for a in corpus]

# ---------- Filtres de validité
with open(CHEMINS, "r", encoding="utf-8") as fichier:
    chemins = json.load(fichier)

journal = Counter()
valides = []

for c in chemins:
    td, tp, ta = (type_reel(c["depart"]), type_reel(c["pont"]),
                  type_reel(c["arrivee"]))

    if tp == "Drug" and c["type"] == "pont":
        journal["pont de type Drug"] += 1
        continue
    if any(generique(c[k]) for k in ("depart", "pont", "arrivee")):
        journal["entité générique"] += 1
        continue
    if any(malformee(c[k]) for k in ("depart", "pont", "arrivee")):
        journal["entité malformée"] += 1
        continue
    if meme_entite(c["depart"], c["arrivee"]):
        journal["extrémités identiques"] += 1
        continue
    if meme_entite(c["pont"], c["depart"]) or meme_entite(c["pont"], c["arrivee"]):
        journal["pont trivial"] += 1
        continue
    if (c["depart"], c["pont"], c["arrivee"]) in CHEMINS_EXCLUS:
        journal["exclusion manuelle"] += 1
        continue

    paires = [(canon_entite(c["depart"]), canon_entite(c["pont"]))]
    if c["type"] == "intersection":
        paires.append((canon_entite(c["arrivee"]), canon_entite(c["pont"])))
    else:
        paires.append((canon_entite(c["pont"]), canon_entite(c["arrivee"])))
    if any(p in RELATIONS_FAUSSES for p in paires):
        journal["relation fausse (relecture)"] += 1
        continue

    coupables = [pmid for pmid, texte in textes
                 if dans_texte(c["depart"], texte)
                 and dans_texte(c["arrivee"], texte)]
    if coupables:
        journal["faux multi-hop"] += 1
        continue

    c["motif"] = f"{td} → {tp} → {ta}"
    valides.append(c)

print(f"Chemins en entrée : {len(chemins)}")
for motif, n in journal.most_common():
    print(f"  écartés — {motif:<28} {n:>4}")
print(f"Chemins valides : {len(valides)}")

# ---------- Déduplication
vus, uniques = set(), []
for c in valides:
    cle = tuple(sorted((canon_entite(c["depart"]), canon_entite(c["arrivee"])))) \
          + (canon_entite(c["pont"]), c["type"])
    if cle not in vus:
        vus.add(cle)
        uniques.append(c)
print(f"Après déduplication : {len(uniques)}")

# ---------- Diversification
par_pont, par_couple = Counter(), Counter()
retenus = []
for c in sorted(uniques, key=lambda x: (x["type"] != "pont", x["pont"])):
    cp = canon_entite(c["pont"])
    cc = (cp, canon_entite(c["depart"]))
    if par_pont[cp] >= MAX_PAR_PONT or par_couple[cc] >= MAX_PAR_DEPART:
        continue
    par_pont[cp] += 1
    par_couple[cc] += 1
    retenus.append(c)

ponts = sum(1 for c in retenus if c["type"] == "pont")
print(f"Après diversification : {len(retenus)}"
      f"  (ponts {ponts}, intersections {len(retenus) - ponts})")
print(f"Entités ponts distinctes : {len(par_pont)}")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(retenus, fichier, ensure_ascii=False, indent=2)

# ---------- Fichier de relecture
index = {a["pmid"]: a for a in corpus}
with open(RELECTURE, "w", encoding="utf-8") as fichier:
    fichier.write("# Relecture des chemins candidats\n\n")
    fichier.write("Vérifier pour chaque chemin :\n"
                  "1. les deux relations sont énoncées dans les abstracts cités ;\n"
                  "2. la polarité est correcte (inhibe / active) ;\n"
                  "3. les trois entités relèvent du même domaine ;\n"
                  "4. une question naturelle peut être formulée.\n\n---\n\n")
    for i, c in enumerate(retenus, 1):
        fleche = "→" if c["type"] == "pont" else "←"
        fichier.write(f"## {i}. [{c['type']}] {c['motif']}\n\n")
        fichier.write(f"**Chemin :** {c['depart']} --{c['relation_1']}--> "
                      f"**{c['pont']}** {fleche} {c['arrivee']}\n\n")
        fichier.write("**Décision :** [ ] VALIDE   [ ] ÉCARTÉ   —  motif :\n\n")
        for n, pmid in ((1, c["pmid_1"]), (2, c["pmid_2"])):
            a = index.get(pmid, {})
            fichier.write(f"### Relation {n} — PMID {pmid}\n\n")
            fichier.write(f"*{a.get('titre', '(absent)')}*\n\n")
            fichier.write(f"> {a.get('resume', '(absent)')}\n\n")
        fichier.write("---\n\n")

print(f"\nFichiers écrits :\n  {SORTIE}\n  {RELECTURE}")
print("\n=== APERÇU ===")
for c in retenus[:40]:
    fleche = "→" if c["type"] == "pont" else "←"
    print(f"  [{c['type'][:4]}] {c['depart'][:22]} --{c['relation_1'][:18]}--> "
          f"{c['pont'][:22]} {fleche} {c['arrivee'][:22]}")