# Structures observées dans DrugMechDB

Méthode : relevé de 8 chemins pris dans l'ordre d'affichage de l'interface web
de DrugMechDB, abstraits en suites de types d'entités (Biolink Model), afin
d'identifier les motifs structurels récurrents.

Limite de l'échantillon : 4 des 8 chemins relevés concernent le même médicament
(Aminobenzoic acid, associé à 4 maladies différentes). L'échantillon n'est donc
pas indépendant et sur-représente les motifs propres à ce médicament.

---

## 1. Aminobenzoic acid → Dermatomyositis   (chemin ramifié)
   Branche A : Drug → BiologicalProcess → Disease   (2 sauts)
   Branche B : Drug → Protein → ChemicalSubstance → BiologicalProcess → Disease   (4 sauts)

## 2. Etanercept → Juvenile idiopathic arthritis   (ramifié)
   Drug → Protein → Pathway → BiologicalProcess → PhenotypicFeature → Disease   (5 sauts)

## 3. Denileukin diftitox → Primary cutaneous T-cell lymphoma   (ramifié à l'entrée)
   Drug → Protein → BiologicalProcess → BiologicalProcess → ChemicalSubstance
        → Protein → BiologicalProcess → Disease   (7 sauts)

## 4. Dornase alfa → Cystic fibrosis   (linéaire)
   Drug → BiologicalProcess → ChemicalSubstance → GrossAnatomicalStructure → Disease   (4 sauts)

## 5. Cetuximab → Malignant tumor of colon   (ramifié)
   Drug → Protein → MolecularActivity → BiologicalProcess → Disease   (4 sauts)

## 6. Aminobenzoic acid → Morphea   (ramifié)
   Branche A : Drug → BiologicalProcess → Disease   (2 sauts)
   Branche B : Drug → Protein → ChemicalSubstance → BiologicalProcess → Disease   (4 sauts)

## 7. Aminobenzoic acid → Induratio penis plastica   (ramifié)
   Branche A : Drug → BiologicalProcess → Disease   (2 sauts)
   Branche B : Drug → Protein → ChemicalSubstance → PhenotypicFeature → Disease   (4 sauts)

## 8. Aminobenzoic acid → Pemphigus   (ramifié, 3 branches)
   Branche A : Drug → BiologicalProcess → Disease   (2 sauts)
   Branche B : Drug → Protein → ChemicalSubstance → BiologicalProcess → Disease   (4 sauts)
   Branche C : Drug → ChemicalSubstance → Disease   (2 sauts)



## Analyse de l'échantillon

Propriété structurelle : tout chemin commence par Drug et se termine par Disease.
Ce n'est pas une régularité empirique mais une contrainte de conception du dataset
(chaque entrée est une indication médicament → maladie).

Contrôle du biais — paires de types consécutifs, comptées en médicaments distincts :
  Drug → Protein ................... 4 médicaments  → robuste
  BiologicalProcess → Disease ...... 3 médicaments  → robuste
  Drug → BiologicalProcess ......... 2 médicaments  → fragile
  Protein → ChemicalSubstance ...... 1 médicament   → biaisé, écarté
  ChemicalSubstance → BiologicalProcess ... 1 médicament → biaisé, écarté

Résultat : le premier saut (Drug → Protein) est stable, mais le second diverge
selon le médicament (ChemicalSubstance, Pathway, BiologicalProcess, MolecularActivity).
Un échantillon de 8 chemins ne permet pas de trancher une structure à 3 sauts.

Décision provisoire — noyau de types à extraire :
  Drug, Protein, BiologicalProcess, Disease
Motif cible : Drug → Protein → BiologicalProcess → Disease
À valider en semaine 1 par comptage sur l'intégralité du dataset.





## Validation sur données complètes

Comptage sur l'intégralité du dataset (4 846 chemins, 33 009 nœuds, 32 641 liens,
1 643 médicaments distincts) — script scripts/03_compter_types.py.

L'échantillon manuel de 8 chemins ne couvrait que 9 des 14 types et omettait
OrganismTaxon (343 médicaments), GeneFamily (243), CellularComponent (108),
Cell (100) et MacromolecularComplex (3). Deux de ces types omis sont plus
fréquents que des types retenus sur la base de l'échantillon.

Observation structurelle : 33 009 nœuds pour 32 641 liens. Une arborescence simple
impliquerait un écart de 4 846 (un par chemin) ; l'écart observé de 368 indique que
la plupart des chemins comportent des branches convergentes plutôt qu'une chaîne unique.

Seuil retenu : 500 médicaments distincts, correspondant à une rupture nette de la
distribution (546 → 343). Ce seuil est dérivé des données et non fixé a priori.
Une exception documentée y est apportée (voir « Révision du schéma » ci-dessous).

Schéma final : 7 types — Drug, Disease, BiologicalProcess, Protein,
ChemicalSubstance, PhenotypicFeature, OrganismTaxon.

Fusions : MolecularActivity et Pathway → BiologicalProcess ; GeneFamily → Protein.
Une fusion n'est appliquée que lorsqu'il existe un parent sémantiquement valide
parmi les types conservés : elle supprime alors une distinction à frontière graduelle
sans altérer le sens du nœud.

Exclusions : CellularComponent, Cell, GrossAnatomicalStructure,
MacromolecularComplex. Ces types n'admettent aucun parent valide parmi les types
conservés ; les fusionner reviendrait à produire un étiquetage délibérément faux.

Conséquence assumée : la construction du jeu de test est restreinte aux chaînes
composées des sept types retenus. Le schéma d'extraction et le jeu d'évaluation
restent ainsi cohérents, au prix d'une réduction du volume de chaînes exploitables.

Ce choix privilégie la fiabilité de l'étiquetage sur la finesse du typage : un type
confondu produit une arête silencieusement fausse, non détectable à l'exécution, et
constitue une variable confondante dans la comparaison des deux architectures.

### Révision du schéma — rétablissement d'OrganismTaxon

Décision initiale : OrganismTaxon avait été exclu par application du seuil de
500 médicaments distincts, n'apparaissant que chez 343 médicaments en tant que nœud.

Élément nouveau : le comptage des relations typées (script 04) a révélé que ce type
est l'extrémité dominante de `causes` (484 médicaments, 5e relation du dataset par
nombre de médicaments distincts) et de `in taxon` (208 médicaments). Son exclusion
réduisait `causes` à 155 médicaments (-68 %) et supprimait entièrement `in taxon`,
retirant de fait les mécanismes infectieux de l'objet d'étude.

Décision révisée : OrganismTaxon est rétabli ; le schéma passe à 7 types. Le coût
est faible, ce type n'ayant aucun voisin ambigu parmi les types conservés — son
ajout n'introduit donc pas de risque de confusion à l'étiquetage.

Limite de méthode identifiée : le critère de sélection appliqué aux entités mesurait
leur fréquence en tant que nœuds, sans tenir compte de leur rôle d'extrémité dans les
relations. Un type peu fréquent comme nœud peut ancrer une relation majeure. Un seuil
portant sur les seules entités est donc insuffisant : il doit être complété par une
vérification des relations qu'il conditionne.

Conséquence mesurée sur les relations, schéma révisé (script scripts/04_relations_typees.py) :
64 des 67 types de relations restent exploitables. Les trois types perdus
(`expresses`, `increases expression of`, `decreases synthesis of`) n'apparaissent
chacun que chez un seul médicament — perte négligeable.

Le rétablissement d'OrganismTaxon a restauré `causes` (155 → 477 médicaments) et
`in taxon` (0 → 186), confirmant le diagnostic qui avait motivé la révision.

Pertes partielles résiduelles, imputables aux exclusions maintenues (CellularComponent,
Cell, GrossAnatomicalStructure) : `occurs in` 183 → 127 (-31 %), `part of` 46 → 32 (-30 %),
`disrupts` 88 → 71 (-19 %). Ces pertes portent sur des relations de rang moyen et
n'affectent pas les dix relations les plus fréquentes du schéma.

### Schéma des relations

Seuil : 300 médicaments distincts (colonne « utilisable »), retenu à la plus forte
discontinuité de la distribution (306 → 191, soit -38 %) située à l'intérieur de la
fourchette exploitable par un modèle local (8 à 12 types de relations). Une
discontinuité comparable existe au rang 4 (-36 %) mais ne laisserait que trois
relations, insuffisant pour former des chaînes variées.

Normalisation des relations inverses : appliquée avant le seuil par principe, elle
s'avère sans effet ici — `caused by` ajouterait 32 médicaments à `causes` (477 → 509)
et `has participant` 6 à `participates in`, sans modifier aucun rang.

Dix relations retenues :
  positively regulates (1055)      negatively correlated with (467)
  positively correlated with (999) participates in (415)
  decreases activity of (851)      increases activity of (349)
  negatively regulates (543)       manifestation of (327)
  causes (477)                     increases abundance of (306)

Polarité conservée. Les trois couples opposés (positively/negatively regulates,
positively/negatively correlated with, increases/decreases activity of) ne sont pas
fusionnés : ils portent le signal dominant du dataset, et « inhibe » n'est pas
équivalent à « active ». Le budget de dix relations reste dans la fourchette
exploitable, aucune réduction n'est donc contrainte.

Risque assumé et point de contrôle : une polarité mal extraite produit un fait faux,
non un simple défaut de typage. Les petits modèles gèrent mal la négation. La qualité
de l'extraction de polarité constitue donc un critère explicite du dry run de la
semaine 1, sur 5 à 10 abstracts. Si le modèle inverse les signes, les trois couples
seront fusionnés — décision reportée jusqu'à cette mesure.

### Chaînes candidates après application du schéma

Script scripts/05_chaines_candidates.py. Filtres appliqués en cascade : longueur
2-3 sauts, absence d'arête `treats`, types et relations dans le schéma retenu.

Résultat : 193 chemins compatibles sur 4 846, portant sur 130 médicaments distincts
(1,5 chemin par médicament). Répartition : ~55 chaînes à 2 sauts, ~137 à 3 sauts.

Motif dominant : Drug → Protein → BiologicalProcess → Disease (77 occurrences, 40 %).
Ce motif correspond à celui identifié provisoirement sur l'échantillon manuel de
8 chemins, confirmé ici sur données complètes.

Contrainte dominante : la longueur. Le filtre 2-3 sauts écarte 4 463 chemins (92 %),
contre 190 pour l'ensemble des filtres de schéma. Les filtres étant appliqués en
cascade, ces effectifs sont conditionnels : parmi les chemins de 2-3 sauts, environ
la moitié passe les filtres de schéma.

Décalage relevé entre schéma d'extraction et jeu d'évaluation : OrganismTaxon
n'apparaît dans aucun des motifs de chaînes candidates. Les mécanismes infectieux
empruntent des chemins longs, éliminés par le filtre de profondeur. Le type reste
justifié dans le schéma d'extraction appliqué aux abstracts, mais aucune question
de test ne le mobilisera. Une décision validée au niveau des relations peut ainsi
demeurer sans effet au niveau des chaînes courtes.

Validation de linéarité : les 193 chemins candidats ont été vérifiés comme formant
une chaîne simple Drug → ... → Disease (script scripts/06_extraire_chaines.py :
un seul nœud de départ, un seul successeur par nœud, aucun cycle, tous les liens
parcourus). Aucun rejet — la contrainte de 2-3 sauts exclut mécaniquement les
ramifications, qui requièrent au minimum quatre arêtes. Les chaînes sont
matérialisées dans data/processed/chaines_candidates.json avec leurs entités ponts
et leurs relations ordonnées.