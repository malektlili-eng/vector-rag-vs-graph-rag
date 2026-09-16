# scripts/22_criblage_pubmed.py
# Objectif : mesurer, pour chaque chaîne, la co-occurrence PubMed de chaque saut,
# sans téléchargement. Calibré d'abord sur les 5 médicaments du pilote.

import json
import re
import time
from Bio import Entrez

Entrez.email = "malektlili.eng@gmail.com"      # ← ton adresse réelle

CHAINES = "data/processed/chaines_candidates.json"
SYN_PROT = "data/processed/synonymes_toutes_proteines.json"
SYN_PROC = "data/processed/synonymes_tous_processus.json"
SORTIE = "data/processed/criblage.json"

# Phase 1 : validation sur les médicaments du pilote.
# Phase 2 : mettre à None pour cribler les 130.
FILTRE = None

SYNONYMES_MAX = 8
LONGUEUR_MIN = 3

# --- Table des formes acceptées
formes = {}
for fichier_syn in (SYN_PROT, SYN_PROC):
    with open(fichier_syn, "r", encoding="utf-8") as fichier:
        for entree in json.load(fichier).values():
            formes[entree["nom_drugmechdb"]] = entree["synonymes"]

def nettoyer(terme):
    """PubMed n'accepte pas certains caractères dans une phrase entre guillemets."""
    return re.sub(r'["\[\]()]', " ", terme).strip()

def bloc(nom):
    """Construit le fragment de requête pour une entité."""
    liste = formes.get(nom, [nom]) or [nom]
    retenus, vus = [], set()
    for terme in liste:
        propre = nettoyer(terme)
        if len(propre) < LONGUEUR_MIN or propre.lower() in vus:
            continue
        vus.add(propre.lower())
        retenus.append(f'"{propre}"[Title/Abstract]')
        if len(retenus) >= SYNONYMES_MAX:
            break
    return "(" + " OR ".join(retenus) + ")"

cache = {}
def compter(medicament, source, cible):
    cle = (medicament.lower(), source, cible)
    if cle in cache:
        return cache[cle]
    requete = (f'"{nettoyer(medicament)}"[Title/Abstract] AND hasabstract '
               f'AND english[lang] AND {bloc(source)} AND {bloc(cible)}')
    try:
        poignee = Entrez.esearch(db="pubmed", term=requete, retmax=0)
        n = int(Entrez.read(poignee)["Count"])
        poignee.close()
    except Exception as erreur:
        print(f"    ÉCHEC : {erreur}")
        n = -1
    time.sleep(0.4)
    cache[cle] = n
    return n

with open(CHAINES, "r", encoding="utf-8") as fichier:
    chaines = json.load(fichier)
if FILTRE:
    chaines = [c for c in chaines if c["medicament"].lower() in FILTRE]

print(f"Chaînes à cribler : {len(chaines)}")
print(f"Requêtes estimées : ~{sum(len(c['etapes']) for c in chaines)}\n")

resultats = []
for i, chaine in enumerate(chaines, 1):
    scores = [compter(chaine["medicament"], e["source"], e["cible"])
              for e in chaine["etapes"]]
    complete = all(n > 0 for n in scores)
    resultats.append({**chaine, "scores": scores, "complete": complete,
                      "minimum": min(scores)})
    if i % 20 == 0:
        print(f"  {i}/{len(chaines)}...")

with open(SORTIE, "w", encoding="utf-8") as fichier:
    json.dump(resultats, fichier, ensure_ascii=False, indent=2)

resultats.sort(key=lambda r: (-r["minimum"], r["medicament"]))

print("\n=== RÉSULTAT PAR CHAÎNE ===")
print(f"{'sauts':<16}{'min':>5}  médicament → maladie")
for r in resultats:
    marque = " ".join(f"{n:>4}" if n >= 0 else "  ??" for n in r["scores"])
    etat = "OK" if r["complete"] else "  "
    print(f"{marque:<16}{r['minimum']:>5} {etat} "
          f"{r['medicament']} → {r['maladie'][:34]}")

exploitables = [r for r in resultats if r["complete"]]
medicaments = {r["medicament"] for r in exploitables}
print(f"\nChaînes exploitables : {len(exploitables)}/{len(resultats)}")
print(f"Médicaments concernés : {len(medicaments)}")
for medicament in sorted(medicaments):
    n = sum(1 for r in exploitables if r["medicament"] == medicament)
    print(f"   {medicament} ({n} chaîne{'s' if n > 1 else ''})")