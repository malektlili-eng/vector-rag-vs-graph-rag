# Journal du pilote — semaine 1

## Test de couverture, appariement exact (scripts/12_test_couverture.py)

Corpus : 144 abstracts, 5 médicaments. Chaînes DrugMechDB concernées : 16.

Résultat : 0 chaîne entièrement couverte, 3 partiellement, 13 sans aucune étape.
18 entités sur ~23 introuvables par recherche de chaîne exacte.

Diagnostic : écart de nomenclature, non absence de contenu. DrugMechDB emploie les
désignations canoniques des bases de référence (UniProt, GO), la littérature emploie
les formes d'usage. Exemple vérifié : l'entité `serotonin uptake` est absente au sens
littéral, alors que l'abstract PMID 20048460 énonce « blocks the synaptic reuptake of
serotonin » — ordre inversé, préfixe re-, préposition intercalée.

Conséquence : une étape de normalisation d'entités (entity linking) est nécessaire.
Elle le sera également en aval, pour comparer les relations extraites par le LLM à
la vérité terrain, celui-ci produisant lui aussi des formes d'usage.

## Test de couverture, appariement relâché (scripts/13_couverture_souple.py)

Trois niveaux d'appariement testés : phrase exacte, deux derniers mots significatifs,
ensemble des tokens significatifs.

Entités détectées : 12/30 (exact), 13/30 (phrase), 18/30 (tokens).
Chaînes entièrement couvertes : 0/16 aux trois niveaux.

Trois modes d'échec distincts identifiés :
1. Décalage de granularité — `serotonin uptake` apparaît dans 26 abstracts,
   `Sodium-dependent serotonin transporter` dans aucun. La littérature
   pharmacologique décrit l'action et non la protéine qui la porte.
2. Qualificatifs canoniques absents de l'usage — les préfixes de nomenclature
   UniProt (« Sodium-dependent ») ne figurent jamais dans les résumés.
3. Absence de co-occurrence — chaîne Filgrastim : les quatre entités sont présentes
   individuellement mais jamais deux à deux dans un même abstract, condition
   nécessaire à l'extraction d'une relation.

Limite du test : le relâchement du critère introduit des faux positifs. L'entité
`Solute carrier family 12 member 3` obtient une correspondance au niveau « phrase »
via le fragment « family member », employé dans un abstract au sens familial.
Les chiffres du niveau tokens sont donc légèrement optimistes.

## Sondage de nomenclature (scripts/14_nomenclature_reelle.py)

Inspection inverse : au lieu de chercher les noms canoniques de DrugMechDB dans le
corpus, observation directe des désignations employées par la littérature.

Correspondances établies :
  Sodium-dependent serotonin transporter        → SERT, 5-HT transporter
  Sodium-dependent noradrenaline transporter    → NET, norepinephrine transporter
  Granulocyte colony-stimulating factor receptor → G-CSF receptor
  Solute carrier family 12 member 3             → sodium-chloride cotransporter
  serotonin uptake                              → serotonin reuptake

Trois formes de décalage : abréviation, nomenclature fonctionnelle contre
nomenclature génétique, variante lexicale. Aucune ne relève d'une absence de contenu.

Exception : Thyroid peroxidase est réellement absente du corpus propylthiouracil.
Les deux occurrences du terme « peroxidase » désignent la lactoperoxidase et la
myéloperoxidase, enzymes distinctes. Risque de faux amis en cas d'appariement
partiel : trois protéines différentes partagent ce fragment.

Correction méthodologique : le test de couverture par appariement littéral (scripts
12 et 13) mesurait une borne basse non représentative du pipeline réel. Celui-ci
n'exige pas que le LLM produise la forme canonique : il extrait la forme d'usage,
qu'une étape de normalisation associe ensuite à un identifiant de référence. La
question pertinente n'est donc pas « la forme canonique est-elle présente ? » mais
« la normalisation peut-elle relier forme d'usage et forme canonique ? ».

Conclusion du pilote : le présupposé fondateur est validé — les chaînes DrugMechDB
sont bien décrites dans les abstracts PubMed. Une étape de normalisation d'entités
est nécessaire et son périmètre est borné : environ 40 à 60 entités pour 25 à 30
questions, avec des synonymes disponibles dans UniProt et MeSH.

## Construction de la table de normalisation

Étape préalable : le script d'extraction des chaînes ne conservait que les noms
d'entités, non leurs identifiants. Ceux-ci ont été rétablis (champs source_id et
cible_id), les identifiants étant ce qui relie DrugMechDB aux bases de référence.

Source des synonymes : API UniProt (rest.uniprot.org), champs recommendedName,
alternativeNames, shortNames, geneName et gene synonyms.
Sortie : data/processed/synonymes_proteines.json

Résultat : 7 protéines interrogées, 2 à 8 désignations chacune. Les formes relevées
dans le corpus lors du sondage de nomenclature sont toutes présentes dans UniProt
(SERT, NET, norepinephrine transporter, G-CSF receptor, sodium-chloride cotransporter).

Deux réserves sur la table obtenue :
- Une erreur d'annotation dans la source : SLC6A5 (transporteur de la glycine)
  figure parmi les synonymes du transporteur de la noradrénaline. La table est
  importée sans audit exhaustif des fiches UniProt.
- Six sigles de 3 à 4 caractères (TSC, NAT1, HTT, TPO, DAT1, NET1) sont ambigus en
  biomédecine. L'appariement est restreint aux mots entiers, et la casse est
  respectée pour les sigles de quatre caractères ou moins, afin de limiter les
  correspondances fortuites.

Les variantes lexicales des processus biologiques (uptake / reuptake) sont saisies
manuellement à partir des observations du script 14 : UniProt ne couvre que les
protéines.

## Remesure après normalisation des protéines (scripts/16_couverture_normalisee.py)

Résultat : 5 chaînes entièrement couvertes sur 16, contre 0 avant normalisation.
Le mécanisme de normalisation est validé : les chaînes DrugMechDB sont
reconstructibles à partir d'abstracts PubMed.

Réserve : les cinq chaînes couvertes proviennent toutes du même médicament
(venlafaxine). Quatre médicaments sur cinq produisent zéro chaîne exploitable.
Le taux global de 31 % masque une concentration sur un seul cas.

Diagnostic des 11 échecs, trois causes distinctes :
1. Appariement trop strict — la fonction exige la phrase entière du synonyme. UniProt
   fournit « Thiazide-sensitive sodium-chloride cotransporter » là où le corpus écrit
   « sodium-chloride cotransporter ». Défaut de mesure, non des données ; la
   couverture réelle est donc supérieure à la valeur mesurée.
2. Processus biologiques non normalisés — UniProt ne couvre que les protéines. Les
   entités BiologicalProcess n'ont reçu que trois variantes saisies manuellement.
3. Absence réelle de contenu — Thyroid peroxidase est absente du corpus
   propylthiouracil ; les indications d'epoprostenol retenues par DrugMechDB
   (rhinite allergique, rhume) ne correspondent pas au sujet de sa littérature.
   Ces chaînes sont définitivement inexploitables.

Les causes 1 et 2 sont réparables ; la cause 3 impose d'écarter les chaînes concernées.

## Normalisation des processus biologiques (scripts/17_synonymes_go.py)

Source : API QuickGO (EBI), synonymes de type « exact » et « narrow » uniquement.
Les types « related » et « broad » sont écartés : ils désignent des termes voisins
mais non équivalents, et produiraient des correspondances erronées.

Résultat : 7 processus interrogés, de 1 à 7 désignations. Apport significatif pour
norepinephrine uptake (7 formes) et Neutrophil differentiation (4 formes).

Incohérence relevée dans la source : Gene Ontology fournit « norepinephrine
reuptake » mais non « serotonin reuptake », alors que les deux termes ont un usage
équivalent dans la littérature. Comme l'erreur d'annotation observée dans UniProt
(SLC6A5), cela confirme qu'aucune base de référence n'est complète : les trois
sources — UniProt, Gene Ontology et variantes relevées manuellement — sont
complémentaires et nécessaires conjointement.

## Correction de l'appariement

La fonction d'appariement exigeait la phrase entière du synonyme. En nomenclature
biomédicale, les qualificatifs sont préfixés (« Sodium-dependent X »,
« Thiazide-sensitive X ») et le groupe nominal de tête porte l'identité. Les suffixes
des synonymes sont donc également acceptés, sous condition d'au moins deux mots et
vingt caractères — plancher destiné à écarter les fragments génériques (« factor
receptor ») susceptibles de produire des correspondances fortuites.

Ce seuil est une heuristique et non une règle exacte ; les formes générées sont
imprimées pour inspection manuelle.

Contrôle des formes générées par suffixe : deux d'entre elles sont écartées après
inspection. « cell differentiation », issu de « neutrophil cell differentiation »,
est un terme générique de biologie cellulaire. « colony-stimulating factor receptor »,
issu du récepteur du G-CSF, correspond également aux récepteurs du GM-CSF et du M-CSF,
protéines distinctes. Le plancher de vingt caractères ne discrimine pas ces cas :
la longueur d'un terme ne mesure pas sa spécificité.

## Verdict du pilote

Résultat final : 5 chaînes exploitables sur 16, toutes issues d'un même médicament
(venlafaxine). Les quatre autres médicaments n'en produisent aucune.

Le diagnostic de la chaîne metolazone (scripts/19_diagnostic_chaine.py) confirme une
absence réelle de contenu et non un défaut de mesure : la protéine cible n'apparaît
que dans un abstract sur 29, lequel ne mentionne pas le médicament ; le processus
biologique de l'étape suivante n'apparaît dans aucun abstract.

Conclusions :
1. Le présupposé fondateur est validé — les chaînes DrugMechDB sont reconstructibles
   à partir d'abstracts PubMed, sous réserve d'une normalisation des entités.
2. La sélection des médicaments du pilote était fondée sur une estimation qualitative
   de la richesse mécanistique de leur littérature, non sur une mesure. Quatre
   estimations sur cinq se sont révélées fausses.
3. Le facteur discriminant est la nature de la littérature du médicament : venlafaxine
   dispose d'une littérature pharmacologique moléculaire, les quatre autres d'une
   littérature majoritairement clinique.

Conséquence méthodologique : la sélection des médicaments de la collecte complète
sera fondée sur une mesure préalable de co-occurrence médicament–protéine cible,
obtenue directement par requête PubMed sans téléchargement ni inférence.

Conclusion révisée : ce verdict, établi sur cinq médicaments et par appariement lexical,
a été infirmé par la mesure sur corpus complet. La couverture d'entités mesurée ici ne
préjuge pas de l'extractibilité des relations, la co-occurrence de deux entités
n'impliquant pas que le texte énonce un lien entre elles. Voir docs/dry-run.md,
section « Caractérisation du décalage entre référence et corpus ».

## Pré-criblage des médicaments candidats

Principe : plutôt que de collecter puis tester, la co-occurrence médicament–protéine
cible est mesurée directement par requête PubMed, sans téléchargement ni inférence.
Une requête retourne le nombre d'articles mentionnant les deux entités dans leur
titre ou résumé.

Étape préalable : récupération des synonymes UniProt de l'ensemble des protéines
des 193 chaînes candidates (scripts/20_synonymes_masse.py).

Portée du test : le criblage évalue le premier saut des chaînes (Drug → Protein).
Il constitue une condition nécessaire et non suffisante — le pilote a montré qu'une
chaîne peut franchir ce premier saut et échouer sur le maillon suivant (Filgrastim).
Sa fonction est d'éliminer les médicaments dont la littérature ne descend pas au
niveau moléculaire, non de garantir la reconstructibilité complète.

Révision du criblage : le criblage devait initialement porter sur le seul premier
saut des chaînes (Drug → Protein). Confronté aux résultats du pilote, ce critère
s'avère peu précis : trois des cinq médicaments franchissent ce premier saut, un
seul produit une chaîne exploitable. Le criblage porte donc sur l'ensemble des sauts
de chaque chaîne.

Sources de normalisation par type d'entité :
  Protein            → UniProt (46 entités distinctes, toutes avec ≥ 2 désignations)
  BiologicalProcess  → Gene Ontology, synonymes exacts et étroits
  Disease, ChemicalSubstance, PhenotypicFeature → nom DrugMechDB employé tel quel

Limite assumée : les noms de maladies et de substances de DrugMechDB sont des formes
d'usage courantes, vérifiées lors du pilote (Hypertension détectée dans 8 abstracts,
Major depressive disorder dans 4). Aucune normalisation n'est appliquée à ces trois
types faute de source unifiée mobilisable dans le temps imparti ; le criblage les
sous-estime donc dans les cas où la littérature emploie une désignation alternative.

Normalisation des processus biologiques à l'échelle : 75 processus distincts
interrogés via Gene Ontology, dont 32 (42 %) ne disposent que d'une seule désignation,
contre 0 sur 46 pour les protéines via UniProt. La couche BiologicalProcess est donc
structurellement la plus fragile de la chaîne de normalisation, ce que confirmait
déjà le pilote : les chaînes Filgrastim et epoprostenol franchissaient le saut
Drug → Protein et échouaient sur le maillon Protein → BiologicalProcess.

Calibration du criblage : l'instrument est d'abord appliqué aux cinq médicaments du
pilote, dont le résultat est connu, avant d'être étendu aux 130 candidats. Un
instrument de mesure dont on ne vérifie pas qu'il reproduit un résultat établi ne
peut fonder aucune sélection.

Limite du criblage : la recherche PubMed est insensible à la casse, ce qui expose les
sigles courts (NET, DAT, TSC) à des correspondances fortuites. Le criblage produit
donc des faux positifs. Sa fonction est l'élimination et non la confirmation : un
médicament échouant malgré un appariement permissif est écarté avec certitude, tandis
qu'un médicament retenu demeure à vérifier après collecte.

## Validation du criblage

L'instrument a été appliqué aux cinq médicaments du pilote, dont le résultat était
connu. Il retrouve le même verdict : seul venlafaxine produit des chaînes
exploitables (4 chaînes contre 5 au pilote). Le criblage est légèrement plus strict,
exigeant la mention du médicament à chaque saut — contrainte conforme au pipeline
réel, la collecte s'effectuant par médicament.

Goulot d'étranglement confirmé : le premier saut (Drug → Protein) est franchi par la
plupart des chaînes, y compris celles ayant échoué au pilote (propylthiouracil :
89 articles associant le médicament et la thyroperoxydase dans PubMed, contre 0 dans
les 30 abstracts collectés). L'échec se produit au maillon suivant, vers le processus
biologique.

Biais assumé du critère de sélection : le criblage dépend de la richesse en synonymes
des entités, elle-même inégale (0 % des protéines contre 42 % des processus n'ont
qu'une désignation). Il mesure donc partiellement la qualité de la normalisation et
non la seule disponibilité de la littérature. Ce biais est toutefois identique à
celui du pipeline d'évaluation, qui emploiera la même table de synonymes pour
confronter les relations extraites à la vérité terrain : une chaîne non détectable
au criblage ne serait pas davantage validable à l'évaluation. La sélection retient
ainsi les chaînes que le dispositif est capable de mesurer, ce qui constitue une
restriction de périmètre explicite et non un défaut de méthode.

## Criblage complet

193 chaînes criblées, environ 524 requêtes PubMed. Résultat brut : 27 chaînes
présentant une co-occurrence non nulle à chacun de leurs sauts, sur 23 médicaments.

Le critère binaire (co-occurrence > 0) s'avère insuffisant : six chaînes retenues
reposent sur un unique article dans l'ensemble de PubMed. Une collecte par pertinence
générale n'a pas de garantie de l'inclure. Un seuil minimal est donc appliqué à la
plus faible co-occurrence de la chaîne.

Effet du seuil : 27 chaînes / 23 médicaments (> 0), 21 / 18 (≥ 2), 16 / 14 (≥ 4),
12 / 11 (≥ 10). Le seuil de 4 est retenu comme point d'équilibre entre le volume
requis (15 à 20 chaînes multi-hop) et la probabilité que la collecte atteigne les
articles porteurs.

Conséquence sur la stratégie de collecte : les co-occurrences étant parfois limitées
à quelques articles sur plusieurs milliers, une collecte par pertinence générale ne
garantit pas leur présence dans le corpus. La collecte sera donc mixte — articles
ciblés par les requêtes de co-occurrence, complétés d'articles généraux sur le même
médicament servant de distracteurs.

Portée de ce choix : les deux architectures étant évaluées sur un corpus identique,
la comparaison demeure équitable. La restriction porte sur la validité externe :
l'étude mesure la performance sur un corpus où les chaînes sont présentes, et non la
capacité à les retrouver dans l'ensemble de la littérature. Sans articles-réponses,
les deux pipelines échoueraient uniformément et le dispositif ne discriminerait rien ;
sans distracteurs, la recherche deviendrait triviale et ne discriminerait pas davantage.

## Analyse des chaînes criblées

Deux défauts identifiés au seuil de 4 :

Trivialité lexicale — quatre chaînes sur seize comportent une entité pont contenue
dans le nom du médicament ou de la maladie, ce qui contrevient à la définition du
raisonnement multi-hop. Toutes appartiennent au motif Drug → ChemicalSubstance →
Disease. Ces chaînes ne discrimineraient pas les deux architectures et réduiraient
artificiellement l'écart mesuré.

Redondance mécanistique — cinq chaînes partagent le couple protéine-processus
« transporteur de la noradrénaline → recapture de la noradrénaline », deux le couple
sérotoninergique équivalent. Ces chaînes ne constituent pas des mesures indépendantes :
un système réussissant l'une réussira vraisemblablement les autres. L'effectif effectif
du jeu de test est donc inférieur à son effectif nominal, ce qui doit être pris en
compte dans l'interprétation de la variance.

Diversité des motifs — aucune chaîne des motifs Drug → BiologicalProcess → Disease
(32 candidates) et Drug → Protein → PhenotypicFeature → Disease (13 candidates) ne
franchit le seuil. Le jeu de test portera donc majoritairement sur le motif
Drug → Protein → BiologicalProcess → Disease. Cette restriction découle de la
faiblesse de la normalisation des processus biologiques (42 % sans synonyme).

## Jeu de chaînes retenu

Seuil de co-occurrence 3, après élimination des chaînes à entité pont lexicalement
triviale : 14 chaînes retenues sur 18, portant sur 9 mécanismes distincts.

Quatre chaînes écartées pour trivialité (Calcium Chloride → Calcium → Hypocalcemia ;
Potassium chloride → Potassium → Hypokalemia ; potassium citrate → Potassium →
Hypokalemia ; hydroxocobalamin → cobalamin → Cobalamin deficiency), toutes du motif
Drug → ChemicalSubstance → Disease.

Effectif nominal et effectif effectif : les 14 chaînes reposent sur 9 mécanismes,
cinq d'entre elles partageant le couple transporteur de la noradrénaline / recapture
de la noradrénaline et deux le couple sérotoninergique équivalent. Ces chaînes ne
constituent pas des observations indépendantes. Les résultats seront rapportés en
mentionnant les deux effectifs, l'effectif nominal surestimant la précision atteignable.

Deux risques identifiés, à traiter par le test à vide lors de la construction du jeu
de test :
- Fuite par pré-entraînement : la chaîne imatinib → BCR/ABL → leucémie myéloïde
  chronique est l'exemple canonique de la thérapie ciblée et figure dans la
  littérature pédagogique standard ; Clopidogrel → P2Y12 présente un risque analogue.
- Trivialité partielle : la désignation étendue d'urokinase (« urokinase-type
  plasminogen activator ») contient l'entité pont Plasminogen, sans que le nom
  DrugMechDB ne la révèle.

Volume atteignable : 12 chaînes à trois sauts comportent chacune deux entités ponts
et permettent donc deux questions distinctes, portant sur des traversées différentes.
Le potentiel s'établit à environ 26 questions, dont l'indépendance reste bornée par
les 9 mécanismes sous-jacents.

Seuil définitif : 2. Le seuil est fixé sur le gain en mécanismes distincts et non en
nombre de chaînes. Le passage de 3 à 2 ajoute deux chaînes portant deux mécanismes
entièrement nouveaux (terguride → récepteur 5-HT2B ; lafutidine → récepteur H2 →
sécrétion acide gastrique), portant l'effectif effectif de 9 à 11 mécanismes pour
16 chaînes.

La collecte étant ciblée sur les articles porteurs de chaque co-occurrence, les
chaînes à faible effectif restent atteignables. Le risque résiduel porte sur
l'extraction : un maillon documenté par deux articles seulement n'offre que deux
occasions au modèle d'en extraire la relation. Les chaînes à faible co-occurrence
sont donc plus fragiles, ce qui sera vérifié après extraction.

