# Journal d'exploration des datasets
Date : 2/8 — exploration conduite via l'interface web du dépôt et sa documentation,
avant le téléchargement du fichier de données, réalisé le 7/8.

Critère de sélection : le dataset doit permettre le chaînage de relations (multi-hop), condition nécessaire à l'objet de l'étude.

## Candidat 1 : DrugMechDB
- URL : https://github.com/SuLab/DrugMechDB
- Fichier de données : indication_paths.yaml (7,89 Mo)
- Volume : 4 846 chemins mécanistiques ; ~32 641 relations ; soit ≈ 6,74 relations par chemin
- Format : YAML
- Granularité : un enregistrement = un chemin complet médicament → maladie

- Types d'entités (14, standard Biolink Model) :
  BiologicalProcess, Cell, CellularComponent, ChemicalSubstance, Disease,
  Drug, GeneFamily, GrossAnatomicalStructure, MacromolecularComplex,
  MolecularActivity, OrganismTaxon, Pathway, PhenotypicFeature, Protein

- Types de relations observés (échantillon, non exhaustif) :
  increases activity of, decreases activity of, positively regulates,
  negatively regulates, increases abundance of, positively correlated with,
  negatively correlated with, causes, occurs in, located in, location of

- Écart documentation/données : le README annonce des relations en MAJUSCULES,
  les données sont en minuscules avec espaces.

- Test de chaînage : VALIDÉ
  Exemple : Drug → Protein → Protein → ChemicalSubstance → BiologicalProcess → Disease

- Remarque : chemins longs (5 sauts sur l'exemple) → extraire des sous-chaînes de 2-3 sauts

- Référence : Gonzalez-Cavazos et al. (2023), DrugMechDB: A Curated Database of
  Drug Mechanisms, Scientific Data 10(1), 632.

- Liens PubMed (PMID) : ABSENTS
  (2 occurrences de "pmid" trouvées = fragments d'URL Wikipédia, faux positifs)
- Conséquence : alignement corpus/référence impossible au niveau document,
  mais possible au niveau entité-relation.

- Licence : CC0 1.0 Universal (domaine public — usage académique et
  commercial libre, aucune restriction)

- Connectivité : VALIDÉE — l'entité "Glucocorticoid receptor" apparaît dans
  ~670 chemins. Les entités sont massivement partagées entre chemins,
  ce qui permet de composer des chaînes traversant plusieurs chemins.

- DÉCISION : DrugMechDB RETENU comme référence structurée.
  Justification : chaînage validé, connectivité forte, licence libre (CC0),
  typage standardisé (Biolink Model), curation experte.


## Candidat 2 : SIDER
- URL : https://sideeffects.embl.de
- Contenu : 8 fichiers, dont 3 dictionnaires, 2 doublons, 1 enrichissement
- Relations distinctes : seulement 2
    (Médicament → Effet secondaire)
    (Médicament → Indication)
- Test de chaînage : ÉCHOUÉ — aucun objet ne réapparaît comme sujet.
  Les deux relations partent du même type (fourche, pas chaîne).
- Nuance : permet un multi-hop dégénéré (deux médicaments partageant
  un effet secondaire) = type "intersection", pas type "pont".
- DÉCISION : ÉCARTÉ — inadapté au raisonnement multi-hop par traversée.

## Candidat 3 (envisagé, non exploré) : SemMedDB (Semantic MEDLINE Database)

- URL : https://lhncbc.nlm.nih.gov/ii/tools/SemRep_SemMedDB_SKR.html

- Intérêt potentiel : base construite à partir de MEDLINE/PubMed, donc chaque
  relation conserve un lien vers l'article source (PMID). Cela permettrait un
  alignement corpus/référence au niveau du document.

- Vérification effectuée : la documentation officielle indique que les
  prédications sémantiques sont extraites automatiquement des titres et résumés
  par traitement automatique du langage (outil SemRep). Aucune curation manuelle.

- Écarté sur base méthodologique, sans exploration approfondie :
  la référence étant elle-même produite par extraction automatique, une comparaison
  ne mesurerait pas la correction de notre extraction mais son accord avec un autre
  système automatique. Une erreur de la référence serait alors récompensée.
  DrugMechDB, curé par des experts humains, offre une fiabilité d'une autre nature.

- Distinction retenue : SemMedDB resterait acceptable comme source de chaînes
  candidates (vérifiées ensuite manuellement), mais pas comme référence de
  validation. DrugMechDB couvrant les deux usages, l'apport marginal est faible.

- Limite assumée du choix final : l'absence de PMID dans DrugMechDB restreint la
  validation au niveau entité-relation. Compromis accepté au profit de la fiabilité
  de la référence.