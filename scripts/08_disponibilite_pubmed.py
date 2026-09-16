# scripts/08_disponibilite_pubmed.py
# Objectif : mesurer, pour chaque médicament du pilote, le nombre d'abstracts
# disponibles selon plusieurs formulations de requête.

import time
from Bio import Entrez

Entrez.email = "malektlili.eng@gmail.com"  

MEDICAMENTS = [
    "venlafaxine",
    "epoprostenol",
    "propylthiouracil",
    "filgrastim",
    "metolazone",
]

def compter(requete):
    """Retourne le nombre de résultats PubMed pour une requête donnée."""
    poignee = Entrez.esearch(db="pubmed", term=requete, retmax=0)
    resultat = Entrez.read(poignee)
    poignee.close()
    time.sleep(0.4)          # respect de la limite NCBI (3 requêtes/seconde)
    return int(resultat["Count"])

def variantes(medicament):
    return {
        "brut": f'"{medicament}"',
        "titre/résumé": f'"{medicament}"[Title/Abstract] AND hasabstract AND english[lang]',
        "mécanistique": (
            f'"{medicament}"[Title/Abstract] AND hasabstract AND english[lang] '
            f'AND (mechanism[Title/Abstract] OR receptor[Title/Abstract] '
            f'OR inhibit*[Title/Abstract] OR bind*[Title/Abstract] '
            f'OR pathway[Title/Abstract] OR regulat*[Title/Abstract] '
            f'OR activat*[Title/Abstract] OR express*[Title/Abstract] '
            f'OR "mode of action"[Title/Abstract])'
            ),
    }

print(f"{'Médicament':<20}{'Brut':>10}{'Titre/résumé':>15}{'Mécanistique':>15}")
for medicament in MEDICAMENTS:
    lignes = variantes(medicament)
    valeurs = {nom: compter(requete) for nom, requete in lignes.items()}
    print(f"{medicament:<20}{valeurs['brut']:>10}"
          f"{valeurs['titre/résumé']:>15}{valeurs['mécanistique']:>15}")