# Dry run — extraction sur échantillon

## Objectif
Trois questions à trancher avant l'extraction complète :
1. Le modèle produit-il un JSON structurellement exploitable ?
2. Respecte-t-il le schéma retenu (7 types d'entités, 10 relations) ?
3. Restitue-t-il correctement la polarité des relations ?

Une mesure complémentaire : le temps de traitement par abstract, qui détermine si
les 475 abstracts du corpus tiennent dans le budget de calcul disponible.

## Composition de l'échantillon
L'échantillon n'est pas tiré au hasard mais composé pour rendre les trois questions
testables : couverture des deux polarités (la question 3 étant indécidable si une
seule est représentée), diversité des types de relations, et inclusion d'un résumé
antérieur à 2000 — les résumés anciens étant moins structurés, leur traitement avait
été identifié comme un point de contrôle lors de la constitution du corpus.

Chaque abstract sélectionné porte une relation connue, issue de son champ de
provenance. La sortie du modèle sera confrontée à cette relation attendue, ce qui
fait du dry run une mesure et non une appréciation qualitative.

## Composition retenue

Huit abstracts couvrant sept relations distinctes (3 négatives, 4 positives),
condition nécessaire au test de polarité. Années : 1983, 2000, 2008, 2008, 2010,
2015, 2016, 2021 — le résumé de 1983 permettant de tester le traitement des formats
anciens, moins structurés.

Deux caractéristiques de l'échantillon relevées à la composition :

Un article (PMID 34540303) porte les deux premiers sauts des trois chaînes
venlafaxine, ces chaînes partageant le même mécanisme central. La redondance
mécanistique du jeu de chaînes se traduit donc par une redondance documentaire.

Trois articles sur huit mentionnent le médicament attendu comme comparateur et non
comme sujet principal (PMID 19108785 sur le nilotinib, 27217448 comparant dasatinib
et imatinib, 6225313 comparant zimelidine et desipramine). Cette configuration
introduit une quatrième question de contrôle : le modèle attribue-t-il correctement
la relation au médicament visé dans un texte discutant plusieurs molécules ? Une
confusion produirait une arête factuellement fausse.

## Configuration d'extraction

Modèle qwen2.5:7b, température 0, contexte 4096 tokens, sortie contrainte au format
JSON par l'option `format` d'Ollama.

Portée de la contrainte de format : elle garantit la validité syntaxique de la sortie
mais non sa conformité au schéma — un JSON bien formé peut contenir des types
d'entités ou de relations inventés. Le dry run mesure donc la conformité au schéma et
non la validité syntaxique.

Le prompt demande les noms d'entités tels qu'ils apparaissent dans le texte, sans
expansion des abréviations. La normalisation vers les identifiants de référence
constitue une étape distincte, appuyée sur les tables de synonymes UniProt et Gene
Ontology. Demander au modèle de produire directement les désignations canoniques
exposerait à des inventions, celles-ci n'étant pas déductibles du texte.

Le dry run est conduit sans exemple résolu (zero-shot), afin de mesurer si les
consignes de schéma suffisent à elles seules. L'ajout d'exemples constitue le premier
remède en cas d'échec, et son gain sera mesuré par comparaison.

## Résultats du dry run — première itération

Objectifs atteints :
- Validité syntaxique : 8 sorties JSON exploitables sur 8, aucun échec de parsing.
  La contrainte `format` d'Ollama remplit son rôle.
- Débit : 3,7 s par abstract en moyenne, soit environ 30 minutes pour les 475
  abstracts du corpus. La contrainte de calcul, identifiée comme risque majeur du
  projet, se révèle non contraignante.

Objectifs non atteints :
- Conformité au schéma : 3 relations sur 14 emploient un prédicat absent du schéma
  (`inhibits`), soit 21 %.
- Polarité : inversion caractérisée sur le PMID 21443098, dont le titre qualifie
  lafutidine d'antagoniste du récepteur H2 quand le modèle produit
  « increases activity of ».
- Attribution multi-médicaments : sur le PMID 6225313, la relation est attribuée au
  comparateur (zimelidine) et non au médicament visé (desipramine).
- Rappel : aucune des 12 relations attendues n'a été correctement extraite ; trois
  abstracts sur huit ne produisent aucune relation.

Le format ancien n'est pas en cause : le résumé de 1983 produit une sortie exploitable,
son échec relevant du défaut d'attribution et non de lisibilité.

Analyse : le modèle extrait le sujet principal de l'article et non la relation
mécanistique attendue. Les articles ciblés sont fréquemment des rapports d'effets
indésirables (PMID 19169095, 34540303), où la relation de mécanisme n'apparaît qu'en
incise. Cette observation met en évidence une limite du criblage : celui-ci mesure la
co-occurrence des noms d'entités dans un même texte, non l'énonciation d'une relation
entre elles. La co-occurrence constitue une condition nécessaire et non suffisante.

Décision sur la polarité, reportée : la mesure porte sur la combinaison d'un modèle et
d'un prompt dépourvu d'exemples, de verbes déclencheurs et d'ancrage sur le médicament.
Conclure à ce stade reviendrait à statuer sur une variable confondue. La décision est
reportée après correction du prompt et nouvelle mesure.

## Diagnostic — lecture des abstracts sans extraction

Les trois abstracts n'ayant produit aucune relation ont été lus manuellement pour
déterminer si la relation attendue y figure.

PMID 16597316 : l'abstract présente la fibrinolyse comme un traitement de l'embolie
pulmonaire ; il n'énonce pas de corrélation négative entre les deux.
PMID 19108785 : les entités BCR-ABL et LMC sont mentionnées séparément, la relation
causale entre elles n'est jamais formulée.
PMID 27217448 : l'abstract rapporte une réduction des transcrits BCR-ABL1 sous
traitement, résultat clinique attribué aux deux bras de l'essai, et non une action
du médicament sur l'activité de la protéine.

Aucune des trois relations attendues n'est énoncée. L'échec d'extraction n'est donc
pas imputable au prompt : aucune formulation ne permet d'extraire une relation absente
du texte.

Cause structurelle identifiée : un résumé scientifique énonce des résultats nouveaux
et présuppose les connaissances établies. Or DrugMechDB est constitué de mécanismes
consolidés, curés depuis DrugBank et la littérature de synthèse. Le savoir mécanistique
établi est précisément celui que les résumés ne réénoncent pas. Cette tension entre les
deux sources constitue une limite de fond de l'appariement corpus/référence.

Le phénomène n'est pas général : les PMID 21443098 et 34540303 énoncent explicitement
la relation attendue. La sélection des articles porteurs doit donc distinguer ceux qui
énoncent une relation de ceux qui se contentent de mentionner les entités.

Défaut de collecte identifié : la requête de collecte ciblée (scripts/25) ne comportait
pas le filtre de vocabulaire mécanistique appliqué aux distracteurs et calibré lors du
pilote. Les articles porteurs étaient donc moins filtrés que les distracteurs. La
correction consiste à appliquer ce filtre à la requête ciblée, puis à remesurer le
dry run avant toute modification du prompt, afin de ne pas confondre les deux effets.

## Deuxième itération — corpus corrigé, prompt inchangé

Effet du filtre mécanistique sur l'échantillon : cinq des huit abstracts sont
remplacés. Les substitutions déplacent l'échantillon des rapports de cas vers des
articles de pharmacologie (« Acute venous thromboembolism » remplacé par « Alteplase.
A reappraisal of its pharmacology » ; « Kleptomania Induced by Venlafaxine » par
« Psychopharmacological properties and therapeutic profile of venlafaxine »).

Effet du filtre mécanistique sur le corpus complet
(scripts/52_comparer_collectes.py) : le filtre renouvelle 12 % du corpus — 57
abstracts écartés, 48 ajoutés, 436 conservés sur 493. La nature des articles échangés
ne va toutefois pas uniformément dans le sens attendu. Plusieurs articles écartés sont
explicitement mécanistiques (« Pharmacology of fibrinolysis », « P2Y12 receptors:
structure and function », « SERT and NET occupancy by venlafaxine and milnacipran »)
tandis que certains articles ajoutés ne le sont pas (« Gastroretentive mucoadhesive
tablet of lafutidine for controlled release »).

Le filtre ne réalise donc pas un tri qualitatif : il modifie la requête et, par
conséquent, le classement par pertinence de PubMed, de sorte que les huit premiers
résultats de chaque saut changent. L'observation formulée sur l'échantillon de dry
run ne se généralise pas au corpus entier.

Un effet bénéfique demeure identifiable : parmi les articles écartés figurent des
comparaisons entre médicaments d'une même classe (« Comparison Between Ranibizumab
Biosimilar, Innovator Ranibizumab and Bevacizumab »), sources caractérisées de faux
multi-hop.

Le mécanisme de complément non filtré n'a été mobilisé qu'une seule fois sur
318 sélections : le filtre suffit sur la quasi-totalité des sauts. Sa fonction est
d'éviter qu'un saut se retrouve sans aucun article, ce qui retirerait la chaîne de
l'étude sans possibilité de la tester — la distinction entre une chaîne non testée
et une chaîne testée et échouée étant nécessaire à l'analyse d'erreurs.

Limites persistantes : le PMID 19108785 demeure retenu pour la relation
BCR/ABL → causes → CML alors que sa lecture a établi qu'il ne l'énonce pas. Un filtre
lexical ne distingue pas la mention d'une entité de l'énonciation d'une relation.
Par ailleurs, deux abstracts sur huit portent sur l'asciminib quand la relation
attendue concerne l'imatinib, la difficulté d'attribution multi-médicaments restant
entière sur cette chaîne.

Hypothèse consignée avant mesure : la chaîne imatinib est structurellement
inexploitable, la relation BCR/ABL → causes → CML relevant du savoir de manuel qu'aucun
article de recherche ne réénonce. Cette hypothèse sera confrontée aux résultats de la
deuxième itération ; sa confirmation entraînerait le retrait de la chaîne du jeu de test.

## Résultats de la deuxième itération

Corpus corrigé, prompt inchangé. 18 relations extraites contre 14, aucun échec de
parsing, débit inchangé (4,4 s par abstract hors chargement initial du modèle).

Le nombre de relations attendues correctement extraites demeure nul, mais la nature
des échecs a changé.

Cas déterminant — PMID 22049464 : le modèle produit « terguride blocks 5-HT(2B)
receptors » là où la référence indique « terguride decreases activity of
5-Hydroxytryptamine receptor 2B ». Source, cible et polarité coïncident ; seul le
prédicat diffère. L'échec relève désormais du vocabulaire et non de la compréhension.
Même configuration au PMID 8521760 (« alteplase stimulates fibrinolysis »).

Le taux de non-conformité au schéma passe de 21 % à 39 %. Cette dégradation apparente
s'explique par l'amélioration du corpus : les articles mécanistiques emploient
davantage de verbes d'action, que le modèle recopie au lieu de les traduire vers le
schéma. La faiblesse du prompt était masquée par la pauvreté du corpus antérieur.

Polarité — résultat nuancé : le modèle restitue correctement la polarité lorsqu'il
emploie son propre vocabulaire (« blocks » pour un antagoniste) et l'inverse
lorsqu'il doit la traduire en étiquette de schéma (« increases activity of » pour
lafutidine, dont le titre indique l'action antagoniste). L'erreur se situe donc à
l'étape de correspondance verbe-étiquette et non à la compréhension du texte. La
décision sur la fusion des couples de polarité reste reportée, le remède approprié
étant une table de correspondance explicite.

L'inversion observée sur le PMID 21443098 est identique à celle de la première
itération, confirmant le déterminisme du dispositif à température nulle.

Hypothèse imatinib confirmée : trois articles distincts ont été soumis pour la
relation BCR/ABL → causes → CML sans qu'aucun ne la produise. Cette relation relève
du savoir établi qu'aucun article de recherche ne réénonce. La chaîne imatinib est
retirée du jeu de test sur cette base mesurée.

## Retrait de la chaîne imatinib

La chaîne imatinib → BCR/ABL → CML (ph+) est retirée du jeu de test. Trois articles
distincts ont été soumis pour la relation BCR/ABL → causes → CML sans qu'aucun ne la
produise ; la lecture manuelle a établi qu'aucun ne l'énonce. Cette relation relève
du savoir établi qu'un article de recherche présuppose sans le reformuler.

Les articles collectés pour cette chaîne sont conservés dans le corpus et reclassés
en distracteurs : traitant de leucémie et d'inhibiteurs de kinase, ils constituent un
bruit thématiquement proche sans porter de relation testée. Les versions antérieures
des deux fichiers sont conservées sous le suffixe _avant_retrait.

Vigilance associée : ce mode d'échec — une relation de manuel jamais réénoncée — n'est
pas propre à cette chaîne. Les maillons reliant une protéine ou un processus à une
maladie par un lien de longue date admis sont exposés au même phénomène.

## Incohérence d'étiquetage dans la référence

DrugMechDB emploie deux prédicats distincts pour une même configuration : « terguride
decreases activity of 5-HT2B receptor » et « venlafaxine negatively regulates
noradrenaline transporter » décrivent toutes deux l'inhibition d'une protéine par un
médicament. Aucune règle ne permet de prédire laquelle la référence retient dans un
cas donné.

Conséquence pour l'évaluation : exiger la correspondance exacte du prédicat
sous-estimerait la performance du système. Les prédicats de même direction et de même
polarité seront considérés comme équivalents lors de la comparaison à la vérité terrain.
Cette décision porte sur l'évaluation et non sur l'extraction.

## Troisième itération — correction du prompt

Modification unique : ajout d'une table de correspondance verbe-étiquette, assortie
d'une règle d'affectation selon le type de la cible (activity of pour une protéine,
regulates pour un processus). Ni exemples résolus ni ancrage sur le médicament ne sont
introduits à ce stade, afin de mesurer isolément l'effet de la table.

Défaut de composition détecté et corrigé : le retrait de la chaîne imatinib a
supprimé la relation `causes` du jeu, réduisant à six le nombre de relations
distinctes couvrables. L'étape de complément de l'échantillon prenant les articles
dans l'ordre du fichier, quatre des huit abstracts portaient la même relation. Une
contrainte de diversité par médicament a été ajoutée : l'échantillon privilégie les
médicaments non encore représentés avant d'accepter un doublon.

Portée du jeu de test : les quinze chaînes retenues n'exercent que six des dix
relations du schéma d'extraction. Les relations `increases activity of`,
`participates in`, `manifestation of` et `causes` ne sont testées par aucune question.
Le schéma d'extraction est donc plus large que le périmètre évalué.

Mesure planifiée : le taux de réussite d'extraction sera calculé par position de saut.
Les derniers sauts des chaînes relient un processus biologique à une maladie par des
liens admis de longue date, profil identique à celui qui a fait échouer la chaîne
imatinib. Un échec systématique des derniers sauts contrastant avec la réussite des
premiers confirmerait que le savoir mécanistique proximal est énoncé dans la
littérature tandis que le savoir consolidé ne l'est pas.

## Résultats de la troisième itération — table de correspondance verbe-étiquette

Échantillon et corpus identiques à l'itération précédente, seul le prompt modifié.
L'isolement de la variable est donc complet.

Non-conformité au schéma : 7 relations sur 18 (39 %) avant, 1 sur 28 (4 %) après.
La table de correspondance est le facteur déterminant.

Inversion de polarité corrigée : le PMID 21443098 produit désormais
« lafutidine decreases activity of histamine H2 receptor » là où l'itération
précédente donnait « increases activity of », alors que le titre qualifie la molécule
d'antagoniste. L'hypothèse formulée après la deuxième itération est confirmée :
l'erreur portait sur la traduction du verbe en étiquette et non sur la compréhension
du texte. La décision de conserver les couples de polarité distincts est donc
maintenue, sans fusion.

Premières extractions conformes à la référence :
- venlafaxine decreases activity of NET (référence : negatively regulates
  Sodium-dependent noradrenaline transporter) — correspondance établie après
  normalisation de l'abréviation et équivalence par classe de polarité ;
- terguride decreases activity of 5-HT(2B) receptors, identique à la référence.

Le taux de relations attendues correctement extraites passe de 0 sur 11 à 2 ou 3.

Défauts résiduels : un cas de vocabulaire non traduit (« stimulates » vers un
processus, qui appelait « positively regulates ») ; l'attribution multi-médicaments
demeure défaillante (PMID 25712664 et 25667920) ; le PMID 19169095 continue de ne
produire que des effets indésirables, l'abstract étant un rapport de cas ne
mentionnant pas le mécanisme.

## Contrôle du retrait de la chaîne imatinib

Le retrait a été décidé sur la lecture manuelle de trois abstracts, mais également
sur des extractions obtenues avec le prompt défectueux. Les quatre articles portant
le saut BCR/ABL → causes → CML sont resoumis au prompt corrigé afin de confirmer ou
d'infirmer le retrait sur l'ensemble des articles disponibles.

Correction sur l'isolement de la variable : le retrait de la chaîne imatinib ayant
recomposé l'échantillon, trois abstracts sur huit diffèrent entre les itérations 2
et 3, en plus du prompt. La comparaison globale entre ces deux itérations n'isole
donc pas la variable.

L'effet de la table de correspondance est établi sur les cinq abstracts communs aux
deux itérations : six relations non conformes au schéma avant, une après, à texte
identique. C'est sur ce sous-ensemble que porte la conclusion.

Le défaut de composition de l'échantillon persiste après correction : trois abstracts
sur huit portent le même médicament, la contrainte de diversité s'appuyant sur un
champ de provenance qui désigne une protéine lorsque l'article porte un saut
intermédiaire. Aucune itération supplémentaire du dry run n'est conduite : le taux de
non-conformité de 4 % est jugé suffisant pour un passage à l'échelle, et poursuivre
l'ajustement du prompt sur huit abstracts reviendrait à l'optimiser sur l'échantillon
d'évaluation.

Une part des défauts résiduels relève du corpus et non du prompt : le PMID 25712664,
intitulé « Ergotamine and nicergoline », ne discute le terguride qu'incidemment ;
l'attribution de la relation à l'ergotamine constitue une extraction correcte d'un
article mal ciblé.

## Contrôle du retrait de la chaîne imatinib — résultat

Les quatre articles portant le saut BCR/ABL → causes → CML ont été soumis au prompt
corrigé. Aucun ne produit cette relation.

Le PMID 17284091, revue consacrée à l'usage de l'imatinib dans la leucémie myéloïde
chronique, constituait le candidat le plus favorable : la fonction d'une revue est de
rappeler les données établies. Il produit une unique relation, « Imatinib inhibits
BCR-Abelson fusion protein », correspondant au saut 1 de la chaîne. Le saut 2 en est
absent.

Le retrait est confirmé sur l'ensemble des articles disponibles et avec l'instrument
corrigé. L'hypothèse consignée avant mesure est validée.

Contraste structurant, observé sur un même article : le saut décrivant l'action du
médicament sur sa cible est extrait, celui reliant la cible à la maladie ne l'est pas.
Le premier constitue l'objet de la publication, le second son présupposé. L'échec ne
relève donc pas de la difficulté d'extraction mais de ce qu'un article scientifique
énonce. Ce résultat constitue une première confirmation de l'hypothèse à vérifier par
la mesure du taux de réussite par position de saut sur l'extraction complète.

Observation résiduelle : le modèle produit « competitively inhibits », variante non
prévue par la table de correspondance, qui recense « inhibits » sans ses modificateurs
adverbiaux.

## Caractérisation du décalage entre référence et corpus

Mesure décisive : sur 935 relations extraites, 36 ont une maladie pour cible, dont 33
partent d'un médicament. La relation processus → maladie, qui constitue le dernier
saut de toutes les chaînes retenues, est pratiquement absente du corpus.

Répartition des processus biologiques selon leur position : recapture de la
noradrénaline et de la sérotonine, 15 occurrences comme source contre 93 comme cible ;
agrégation plaquettaire, 0 contre 17 ; angiogenèse, 1 contre 29 ; sécrétion acide
gastrique, 0 contre 8. Les processus sont des points d'arrivée et non des points de
départ.

Un contre-exemple : la fibrinolyse. Ce processus apparaît 15 fois comme source contre
11 fois comme cible, à rebours du motif observé sur les quatre autres. Les entités de
cette famille — plasmine, plasminogène, activateur du plasminogène — sont décrites
comme agissant sur d'autres entités et non seulement comme subissant l'action d'un
médicament.

Cette exception n'est pas anecdotique : le seul chemin de type pont proprement
mécanistique retenu dans le jeu de test final, amiloride → plasmine → myogenèse,
appartient précisément à cette famille. Là où les autres processus ne relancent jamais
la chaîne, la fibrinolyse le fait, et c'est le seul endroit du corpus où un pont
mécanistique authentique a pu être construit.

La généralisation doit donc être formulée avec précaution : les processus biologiques
sont majoritairement des points d'arrivée, mais non universellement, et les exceptions
sont exactement les endroits où la topologie en chemin subsiste.

Caractérisation : les résumés produisent une topologie en étoile centrée sur le
médicament, chaque arête partant de celui-ci vers sa cible protéique, son processus ou
son effet clinique. DrugMechDB modélise une topologie en chemin, où chaque entité
intermédiaire relance la chaîne. Ce décalage de topologie explique l'ensemble des
échecs observés depuis le pilote et non les seuls derniers sauts.

Le corpus contient néanmoins des structures multi-hop, de deux formes : des
intersections, plusieurs médicaments partageant une même cible (venlafaxine,
duloxétine et milnacipran vers la recapture de la noradrénaline ; clopidogrel,
prasugrel et ticagrelor vers l'agrégation plaquettaire), et des chemins de type pont
(uPA vers plasminogène, plasmine vers myogenèse). Les chaînes multi-hop existent donc
dans le graphe extrait, mais ne coïncident pas avec celles que prescrit la référence.

## Qualité résiduelle de la polarité

Trois inversions caractérisées subsistent après correction du prompt :
« Venlafaxine positively regulates NE reuptake » (la molécule inhibe la recapture),
« lafutidine positively regulates gastric acid secretion » (elle la réduit) et
« venlafaxine increases activity of social phobia » (elle la traite). La construction
en nom composé « X reuptake inhibitor » paraît en cause, le modèle attribuant mal le
signe porté par le nom lui-même. Le taux d'inversion résiduel devra être quantifié :
il conditionne la validité des questions dérivées du graphe et rend la vérification
manuelle de chaque question obligatoire.

Quantification (scripts/54_echantillon_polarite.py, graine fixée à 42) : un échantillon
aléatoire de 40 relations tirées parmi les 807 porteuses de polarité a été confronté
aux phrases de ses abstracts sources. Onze relations n'ont pu être tranchées, les
phrases extraites ne portant pas l'information. Sur les 29 restantes, trois inversions
caractérisées et trois énoncés à direction non soutenue, soit de l'ordre de 10 %
d'inversions et 20 % d'énoncés incorrects au sens large. L'intervalle de confiance à
95 % pour les inversions s'étend approximativement de 2 % à 27 %.

Révision ultérieure : lors de la rédaction du rapport, une relation initialement comptée
comme tranchée a été reclassée en non tranchée. Le dépouillement y est donc de douze
relations non tranchées et vingt-huit jugeables, et c'est sur vingt-huit que sont calculés
les intervalles publiés en section 6.3 — 2 % à 28 % pour les inversions, 8 % à 41 % pour
les énoncés incorrects au sens large. Les chiffres ci-dessus relèvent de l'étape du dry
run et sont conservés à ce titre. Les erreurs relevées sont les mêmes dans les deux
dépouillements, trois inversions et trois énoncés à direction non soutenue : seul le
dénominateur change, et aucune conclusion n'en dépend.

Les trois inversions, vérifiables sur le seul texte des abstracts :
  venlafaxine increases activity of NET (l'article la décrit comme un inhibiteur)
  Selexipag positively regulates pulmonary arterial hypertension (il la traite)
  lafutidine negatively regulates gastric acid elimination (le titre dit « enhanced »)

Les erreurs se regroupent par article source : sept des relations ciblant une maladie
constituent la même inversion, issue d'un seul article recensant les traitements de la
phobie sociale, où sept molécules sont décrites comme augmentant l'activité de la
pathologie qu'elles traitent. Un échantillonnage aléatoire de relations sous-estime
donc la variance réelle du taux d'erreur.

## Propagation combinatoire d'une erreur d'extraction

La première recherche de chemins dans le graphe extrait a produit 230 ponts, dont 115 empruntant un médicament comme entité pont, les exemples relevés faisant tous apparaître la même arête erronée en entrée : « asciminib increases activity of imatinib »,
convertie depuis un énoncé d'association thérapeutique (« asciminib add-on to
imatinib »). Le nœud imatinib présentant un degré sortant élevé, cette arête entrante
fausse s'est combinée à l'ensemble de ses arêtes sortantes.
La sortie du script établit le décompte de 115 ponts à entité pont médicamenteuse ;
elle n'établit pas qu'ils procèdent tous de cette unique arête, plusieurs arêtes
reliant deux médicaments existant dans le graphe.

Une erreur d'extraction ne demeure donc pas locale dans un graphe : son effet est
multiplié par le degré du nœud qu'elle atteint. Ce constat justifie la vérification
manuelle des questions dérivées et constitue un argument mesuré en faveur d'un
contrôle de qualité en amont de la construction du graphe.

Décision : les arêtes reliant deux entités de type Drug sont exclues. Aucune chaîne de
la référence ne comporte deux médicaments consécutifs, et dans les résumés cette
configuration relève de la comparaison ou de l'association clinique, non du mécanisme.

Domination par les nœuds de fort degré : après exclusion des arêtes médicament vers
médicament, 89 des 149 ponts relèvent d'un même motif, Drug → ChemicalSubstance →
BiologicalProcess, dont les exemples relevés font tous apparaître la même arête
entrante — « tocilizumab decreases activity of IL-6 », correcte cette fois — sur un
nœud très connecté. La sortie du script fournit un décompte par motif et non une
attribution par arête ; l'ordre de grandeur demeure. Le phénomène observé avec l'arête
erronée asciminib est donc structurel et non lié à la qualité de l'extraction : une
entité pont de fort degré engendre mécaniquement des chemins redondants. La sélection
des chemins candidats plafonne en conséquence le nombre de chemins par entité pont.

Le filtre d'exclusion des arêtes médicament vers médicament s'avère par ailleurs
inopérant à ce stade : il n'en écarte que treize, et vingt-trois ponts continuent
d'emprunter une telle arête (metformine vers imatinib). La cause est le défaut de
typage décrit ci-dessous — le type d'un nœud était fixé par la dernière relation
traitée — qui neutralise un filtre reposant sur les types. Après correction, la
sélection finale écarte trente-sept chemins pour ce motif.

Entités ponts génériques écartées : certaines entités extraites relèvent du vocabulaire
d'essai clinique (« response », « symptoms », « efficacy ») et non du domaine
biomédical. Une question construite sur une telle entité pont n'aurait pas de sens ;
ces chemins sont exclus par liste explicite.

Correction d'un défaut de typage : le type d'un nœud était fixé par la dernière
relation traitée, un même nœud pouvant recevoir des types différents selon les
relations. Le type majoritaire est désormais retenu, ce qui rend effectif le filtre
sur les arêtes médicament vers médicament.

## Filtrage du faux multi-hop à l'échelle du corpus

Le contrôle manuel comparait chaque chemin à ses deux abstracts sources ; le contrôle
automatisé le compare aux 475 abstracts du corpus. La seconde portée est la bonne :
la recherche vectorielle interroge l'ensemble du corpus, et tout article contenant
les deux extrémités permet une résolution en une seule récupération.

Résultat : 32 chemins écartés sur 61, dont 11 que la relecture manuelle avait validés.
Le contrôle automatisé et le contrôle humain sont complémentaires — le premier détecte
ce qui est vérifiable mécaniquement à grande échelle, le second ce qui relève du sens.
Un cas illustre cette complémentarité en sens inverse : le chemin ergotamine →
5-HT2B ← cabergoline échappe au filtre parce que l'abstract source orthographie
« carbegoline » ; il est écarté manuellement.

Constat structurel : les intersections entre médicaments d'une même classe
thérapeutique constituent presque toujours un faux multi-hop, les revues de synthèse
énumérant systématiquement les membres d'une classe. Survivent les chemins de type
pont, dont les extrémités sont de types différents et donc rarement co-mentionnées,
ainsi que les intersections entre classes éloignées — insuline et maprotiline vers la
recapture de la noradrénaline, aucune revue ne réunissant une hormone et un
antidépresseur.

Défaut d'ordonnancement du pipeline : la diversification, qui plafonne le nombre de
chemins par entité pont, était appliquée avant les filtres de validité. Elle écartait
donc des chemins valides au profit de chemins ultérieurement invalidés. L'ordre correct
place la validation avant la diversification.

Réordonnancement du pipeline : les filtres de validité sont désormais appliqués avant
la diversification. Sur 350 chemins bruts, 55 restent valides, 54 après déduplication,
36 après diversification, contre 11 exploitables par l'ordre précédent.

Les décisions de relecture sont remontées dans le code sous deux formes. Les relations
identifiées comme factuellement fausses sont inscrites dans une liste d'exclusion
portant sur la relation et non sur le chemin : une relation erronée invalide tout
chemin qui l'emprunte, y compris ceux qu'une génération ultérieure produirait. Les
rejets propres à un chemin donné — domaines sans rapport, artefact d'orthographe dans
la source — sont inscrits séparément.

Trois défauts de filtrage corrigés à cette occasion : le terme « effectiveness »
absent de la liste des entités génériques, une comparaison rendue inopérante par la
normalisation des traits d'union, et l'absence de détection des entités malformées
(fragments de phrase, énumérations de deux médicaments).

Faille de normalisation identifiée : une même fonction canonisait les noms d'entités
et les textes d'abstracts. Cette fonction supprimait le contenu entre parenthèses,
traitement correct pour un nom d'entité — « serotonin transporter (SERT) » se réduit
à « serotonin transporter » — mais destructeur pour un texte libre, où les parenthèses
portent des listes de molécules et des précisions. Toute entité citée entre
parenthèses échappait ainsi au filtre de faux multi-hop.

Cas révélateur : le chemin indatraline → transporteur de la sérotonine ← fluoxétine
n'était pas rejeté alors que le PMID 18801947 cite les deux, la fluoxétine
n'apparaissant que dans une énumération parenthétique. Deux fonctions de
normalisation distinctes sont désormais employées, selon que l'objet traité est un
nom d'entité ou un texte libre.

Asymétrie de normalisation, corrigée : la distinction entre canonisation d'un nom
d'entité et canonisation d'un texte libre a introduit une incompatibilité de
comparaison. Une entité comportant une glose parenthétique — « PI3 kinase (PI3K)
pathway » — était réduite à « pi3kinasepathway » tandis que le texte conservait
« pi3kinasepi3kpathway », rendant la recherche infructueuse. Des chemins constituant
des faux multi-hop caractérisés redevenaient ainsi valides.

Correction : la recherche d'une entité dans un texte teste désormais l'ensemble de
ses formes possibles — forme complète, forme sans glose, glose isolée. Deux
normalisations distinctes exigent un pont explicite dès lors qu'on compare leurs
sorties.

Plafond structurel du corpus : le nombre de chemins multi-hop authentiques demeure
faible (une vingtaine sur 350 candidats bruts). Le corpus portant sur quatorze
médicaments dont plusieurs relèvent de mêmes classes thérapeutiques, et la littérature
de synthèse énumérant systématiquement les membres d'une classe, la proportion de
chemins non résolubles par une unique récupération est intrinsèquement limitée. Ce
plafond constitue une propriété du domaine documentaire et non un défaut de méthode.

Quantification postérieure (scripts 59 et 60) : sur les seize chemins retenus après
diversification, treize correspondent aux onze questions multi-hop construites, certaines
intersections admettant deux extrémités alternatives. Les trois chemins restants reposent
tous sur un couple de résumés déjà mobilisé par une question retenue : aucun n'apporte de
source nouvelle. Élargir le bras multi-hop sans élargir le corpus reviendrait donc à
ajouter des questions dépendantes des mêmes documents.