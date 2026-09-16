# Recherche vectorielle et recherche par graphe pour l'inférence multi-hop sur corpus biomédical

**Rapport de stage — Laboratoire de recherche en Intelligence Artificielle et Ingénierie des Données, Faculté des Sciences de Bizerte**
*[English version](report.md)*
---

## Résumé

Ce travail compare deux architectures de génération augmentée par récupération — l'une fondée sur la recherche par similarité vectorielle, l'autre sur la traversée d'un graphe de connaissances — sur des questions exigeant la mise en relation de plusieurs documents. Le dispositif repose sur un corpus de 475 résumés d'articles PubMed, un graphe de 935 relations extraites automatiquement et formant 932 arêtes, et un jeu de vingt questions vérifiées manuellement.

Le pipeline par graphe obtient un rappel au rang 5 de 0,83 contre 0,55 pour le pipeline vectoriel, et une exactitude de réponse de 0,70 contre 0,30. L'écart s'établit à toutes les valeurs du budget documentaire testées : le graphe atteint avec cinq documents un niveau de rappel que la recherche vectorielle n'atteint pas avec cinquante.

Le travail produit par ailleurs trois résultats méthodologiques distincts de cette comparaison. D'abord, une base de mécanismes curée par des experts n'est pas reconstructible à partir de résumés d'articles : la littérature comprime les chaînes causales et présuppose les liens établis. Ensuite, l'avantage du graphe ne provient pas de sa capacité de traversée, contrairement à ce que l'argument théorique laisse attendre : l'écart est maximal sur les questions qui n'exigent qu'un seul document, et s'explique par l'absence de dilution. Enfin, la métrique de fidélité employée seule récompense le silence : le pipeline le moins performant y obtient le meilleur score, grâce à son taux d'abstention.

---

## 1. Introduction

### 1.1 Contexte

La génération augmentée par récupération associe un moteur de recherche documentaire à un modèle de langue : les documents jugés pertinents sont fournis au modèle, qui rédige sa réponse à partir d'eux. L'implémentation courante repose sur la similarité vectorielle — chaque document est représenté par un vecteur, chaque question également, et l'on retient les documents dont le vecteur est le plus proche.

Cette approche présente une faiblesse théorique connue sur les questions dites multi-hop, celles dont la réponse exige de combiner des informations dispersées dans plusieurs documents. La similarité vectorielle sélectionne les documents qui ressemblent globalement à la question ; elle n'a aucun mécanisme pour rassembler des documents complémentaires mais individuellement peu ressemblants.

Une alternative consiste à extraire du corpus un graphe de relations entre entités, puis à répondre par traversée de ce graphe. L'opération de jointure, absente de la recherche vectorielle, y devient native.

### 1.2 Question de recherche

L'énoncé du stage formule la question ainsi : *dans quelles conditions, et dans quelle mesure, l'architecture par graphe surpasse-t-elle l'architecture vectorielle sur des requêtes biomédicales multi-hop — et à quel coût en latence et en calcul ?*

Trois volets distincts s'y trouvent, traités séparément dans ce rapport.

Les **conditions** sont établies par l'analyse des modes d'échec propres à chaque architecture, exposée aux sections 8.1 et 8.2.

L'**ampleur de l'écart** est quantifiée par trois mesures indépendantes : le rappel de récupération, l'exactitude de la réponse et les métriques de jugement, aux sections 8.1 à 8.5.

Le **coût** est mesuré selon les deux dimensions demandées : la latence de requête à la section 8.4, le temps de calcul de construction et d'exploitation à la section 8.6.

### 1.3 Contraintes

Le travail s'inscrit dans un budget nul : aucun service payant, aucun modèle propriétaire distant. Les ressources de calcul se limitent à un poste dépourvu de GPU dédié et à un environnement Google Colab en offre gratuite. La durée impartie est de quatre semaines.

Ces contraintes ont orienté plusieurs décisions techniques, notamment le recours à un modèle de langue local de sept milliards de paramètres et la réimplémentation des métriques d'évaluation plutôt que l'emploi d'une bibliothèque supposant un accès distant.

---

## 2. Cadre conceptuel

### 2.1 Le raisonnement multi-hop

Une question est dite multi-hop lorsque sa réponse exige de franchir plusieurs relations. Deux formes ont été retenues dans ce travail.

Le **pont** est un chemin dirigé de trois entités : A agit sur B, B agit sur C. La question porte sur A et attend C ; l'entité B n'apparaît ni dans la question ni dans la réponse. Exemple retenu : l'amiloride inhibe la plasmine, laquelle est nécessaire à la myogenèse. La question demande quel processus musculaire dépend de la protéase inhibée par l'amiloride, sans jamais nommer la plasmine.

L'**intersection** fait converger deux entités vers une cible commune : A et C agissent tous deux sur B. La question demande quelle autre entité partage la cible de A. Exemple retenu : le ranibizumab et le ramucirumab inhibent tous deux l'angiogenèse, sans qu'aucun article ne les mentionne ensemble.

Dans les deux cas, l'entité intermédiaire — dite entité pont — doit demeurer invisible depuis les deux extrémités. Une chaîne dont le pont figure dans le nom d'une extrémité ne constitue pas un raisonnement multi-hop : elle se résout par simple lecture de la question.

### 2.2 Le faux multi-hop

Une question conçue comme multi-hop peut néanmoins se résoudre par une seule récupération si un document unique contient les deux extrémités du chemin. La recherche vectorielle le trouve alors sans traversée, et la question cesse de discriminer les deux architectures.

Ce phénomène s'est révélé massif sur le corpus étudié : les revues de synthèse énumèrent systématiquement les membres d'une classe thérapeutique. Une intersection entre deux médicaments de même classe constitue donc presque toujours un faux multi-hop.

### 2.3 Décomposition de la mesure

Un système de génération augmentée par récupération comporte deux étapes successives. La récupération sélectionne des documents ; la génération rédige une réponse à partir d'eux.

L'objet de l'étude étant la méthode de récupération, la mesure principale porte sur cette seule étape. Isoler les deux évite d'imputer à l'architecture un écart provenant du modèle générateur. La génération est mesurée séparément, avec le même modèle et le même prompt pour les deux pipelines : seuls les documents fournis diffèrent.

---

## 3. Constitution des données

### 3.1 Choix d'une référence structurée

Trois candidats ont été évalués selon un critère unique : le dataset doit permettre le chaînage de relations, condition nécessaire à l'objet de l'étude.

**DrugMechDB** a été retenu. Ce dataset rassemble 4 846 chemins mécanistiques reliant un médicament à une maladie, soit environ 32 641 relations pour 33 009 entités, au format YAML, typées selon le Biolink Model. Il est curé manuellement par des experts, publié sous licence CC0, et son test de chaînage est concluant. Sa connectivité est forte : l'entité « Glucocorticoid receptor » apparaît dans environ 670 chemins, ce qui permet de composer des chaînes traversant plusieurs enregistrements.

**SIDER** a été écarté. Il ne comporte que deux types de relations, tous deux issus du médicament : médicament vers effet secondaire, et médicament vers indication. Aucun objet ne réapparaît comme sujet ; la structure est une fourche et non une chaîne. Le dataset autorise un multi-hop dégénéré de type intersection, mais aucun chemin.

**SemMedDB** a été écarté sur base méthodologique, sans exploration approfondie. Cette base est construite par extraction automatique des titres et résumés MEDLINE au moyen de l'outil SemRep, sans curation manuelle. L'employer comme référence reviendrait à mesurer non la correction de l'extraction réalisée ici, mais son accord avec un autre système automatique : une erreur de la référence serait alors récompensée. SemMedDB resterait acceptable comme source de chaînes candidates vérifiées ensuite manuellement, mais DrugMechDB couvrant les deux usages, l'apport marginal était faible.

**Limite assumée du choix retenu.** DrugMechDB ne comporte aucun identifiant PubMed. L'alignement entre corpus et référence ne peut donc s'établir au niveau du document, mais seulement au niveau entité-relation. Ce compromis a été accepté au profit de la fiabilité de la référence.

### 3.2 Schéma d'extraction

Un premier relevé manuel de huit chemins a permis d'identifier un motif candidat. Ce relevé s'est révélé biaisé — quatre des huit chemins concernaient le même médicament — et a été validé par comptage sur l'intégralité du dataset.

**Types d'entités.** Le seuil retenu est de 500 médicaments distincts, valeur correspondant à une rupture nette de la distribution (546 vers 343) et non fixée a priori. Sept types ont été conservés : Drug, Disease, BiologicalProcess, Protein, ChemicalSubstance, PhenotypicFeature, OrganismTaxon.

Trois types ont été fusionnés vers un parent sémantiquement valide : MolecularActivity et Pathway vers BiologicalProcess, GeneFamily vers Protein. Une fusion n'a été appliquée que lorsqu'un tel parent existait parmi les types conservés ; elle supprime alors une distinction à frontière graduelle sans altérer le sens du nœud.

Quatre types ont été exclus : CellularComponent, Cell, GrossAnatomicalStructure, MacromolecularComplex. Aucun parent valide n'existait pour eux ; les fusionner aurait produit un étiquetage délibérément faux.

**Une révision documentée.** OrganismTaxon avait d'abord été exclu par application du seuil, n'apparaissant que chez 343 médicaments comme nœud. Le comptage des relations typées a révélé que ce type est l'extrémité dominante de la relation `causes`, présente chez 484 médicaments, et de `in taxon`, présente chez 208. Son exclusion réduisait `causes` de 68 % et supprimait entièrement `in taxon`, retirant de fait les mécanismes infectieux de l'objet d'étude. Le type a été rétabli.

Cette révision a mis au jour une limite de méthode : un critère de sélection portant sur la fréquence des entités comme nœuds ne tient pas compte de leur rôle d'extrémité dans les relations. Un type peu fréquent comme nœud peut ancrer une relation majeure. Un seuil portant sur les seules entités est donc insuffisant et doit être complété par une vérification des relations qu'il conditionne.

**Types de relations.** Le seuil retenu est de 300 médicaments distincts, situé à la plus forte discontinuité de la distribution (306 vers 191, soit une chute de 38 %) à l'intérieur de la fourchette exploitable par un modèle local, estimée entre huit et douze types. Dix relations ont été retenues.

La polarité a été conservée : les trois couples opposés — regulates, correlated with, activity of — n'ont pas été fusionnés. Ils portent le signal dominant du dataset, et « inhibe » n'équivaut pas à « active ». Cette décision comportait un risque assumé, une polarité mal extraite produisant un fait faux et non un simple défaut de typage. Elle a été soumise à un point de contrôle explicite lors du dry run, décrit en section 4.

**Chaînes candidates.** Après application du schéma et d'un filtre de longueur de deux à trois sauts, 193 chemins demeurent compatibles sur 4 846, portant sur 130 médicaments distincts. Le motif dominant est Drug → Protein → BiologicalProcess → Disease, avec 77 occurrences, soit 40 % de l'ensemble.

La contrainte dominante est la longueur : le filtre de profondeur écarte 4 463 chemins, contre 190 pour l'ensemble des filtres de schéma. Les filtres étant appliqués en cascade, ces effectifs sont conditionnels.

### 3.3 Constitution du corpus

Le corpus est constitué de résumés d'articles PubMed, récupérés par l'API E-utilities du NCBI.

**Formulation de la requête.** La requête restreint la recherche au titre et au résumé, exige la présence d'un résumé, se limite à l'anglais, et impose un vocabulaire mécanistique. Le filtre de champ est déterminant : sans lui, le médicament est mentionné hors du corps de l'article dans la grande majorité des cas — l'epoprostenol passe de 13 851 à 1 079 résultats, soit une réduction de 92 %.

Le vocabulaire mécanistique a fait l'objet d'un calibrage. Une première formulation limitée aux termes de liaison moléculaire couvrait le premier maillon des chaînes mais non les suivants. L'ajout des termes de régulation augmente la disponibilité de 75 % pour le filgrastim, dont le mécanisme se décrit en termes de régulation plutôt que de liaison.

**Sélection des médicaments.** Un pilote de cinq médicaments, choisis sur une estimation qualitative de la richesse mécanistique de leur littérature, a conduit à un résultat instructif : quatre estimations sur cinq se sont révélées fausses. Un seul médicament produisait des chaînes exploitables.

La sélection a donc été refondée sur une mesure. Pour chaque chaîne candidate, la co-occurrence des entités de chaque saut a été mesurée directement par requête PubMed, sans téléchargement ni inférence. L'instrument a d'abord été appliqué aux cinq médicaments du pilote, dont le résultat était connu, avant d'être étendu aux 130 candidats : un instrument de mesure dont on ne vérifie pas qu'il reproduit un résultat établi ne peut fonder aucune sélection.

Le criblage a retenu 16 chaînes portant sur onze mécanismes distincts, après application d'un seuil minimal de co-occurrence et élimination des chaînes à entité pont lexicalement triviale. L'une d'elles, la chaîne imatinib, a été retirée ultérieurement sur mesure — le motif est exposé en section 5.2 — ce qui porte à quinze le nombre de chaînes servant à l'analyse du décalage entre référence et corpus.

**Composition mixte.** Le corpus associe deux composantes. Les articles ciblés portent, pour chaque saut de chaque chaîne, les entités concernées. Les distracteurs portent sur le même médicament sans contenir de saut de chaîne.

Cette composition répond à une double contrainte. Sans articles ciblés, aucune chaîne n'est reconstructible et les deux architectures échouent uniformément. Sans distracteurs, la recherche devient triviale et ne discrimine pas davantage.

**Portée de ce choix.** Les deux pipelines étant évalués sur un corpus identique, la comparaison demeure équitable. La restriction porte sur la validité externe : l'étude mesure la performance sur un corpus où les chaînes sont présentes, non la capacité à les retrouver dans l'ensemble de la littérature.

**Traçabilité.** Chaque abstract conserve un champ de provenance indiquant s'il porte un saut de chaîne, et lequel, ou s'il constitue un distracteur. Cette métadonnée est destinée à l'analyse d'erreurs et n'est exploitée par aucune étape du pipeline : ni l'extraction, ni l'indexation, ni la recherche, ni la génération n'y ont accès. L'exposer constituerait une fuite d'information absente en usage réel.

**Corpus final.** 475 abstracts, dont 208 porteurs de sauts et 267 distracteurs. Longueur moyenne de 217 mots, soit 385 tokens mesurés.

Une vérification d'intégrité a été conduite saut par saut après nettoyage. Trente-trois articles identifiés n'ont pu être récupérés ; les compteurs globaux restaient normaux, mais certains sauts ne reposaient que sur deux articles, dont la perte aurait rendu une chaîne inutilisable sans qu'aucun indicateur ne le signale. Aucune chaîne n'a été rompue.

---

## 4. Extraction des relations

### 4.1 Dispositif

L'extraction emploie qwen2.5:7b, exécuté localement via Ollama sur GPU Tesla T4. La température est nulle, la fenêtre de contexte de 4096 tokens, et la sortie contrainte au format JSON.

Le choix du modèle est justifié par sa meilleure conformité aux consignes de format, la tâche exigeant une sortie strictement conforme à un schéma imposé.

La portée de la contrainte de format mérite d'être précisée : elle garantit la validité syntaxique de la sortie mais non sa conformité au schéma. Un JSON bien formé peut contenir des types d'entités ou de relations inventés.

### 4.2 Validation par dry run

Trois itérations ont été conduites sur un échantillon de huit abstracts, composé pour rendre testables les questions posées plutôt que tiré au hasard : couverture des deux polarités, diversité des types de relations, inclusion d'un résumé antérieur à 2000.

**Première itération.** Validité syntaxique parfaite, mais aucune des douze relations attendues correctement extraite. La lecture manuelle des abstracts a établi que trois d'entre eux n'énonçaient tout simplement pas la relation attendue. L'échec n'était donc pas imputable au prompt.

Ce diagnostic a révélé un défaut de collecte : le filtre de vocabulaire mécanistique, construit et calibré lors du pilote, n'avait pas été reporté dans la requête de collecte ciblée. Les articles porteurs étaient sélectionnés sur la seule co-occurrence des entités, sans garantie que l'article traite d'un mécanisme.

La correction de ce défaut a été mesurée sur le corpus complet par comparaison des deux collectes. Le filtre renouvelle 12 % du corpus — 57 abstracts écartés, 48 ajoutés, 436 conservés sur 493. La nature des articles échangés ne va toutefois pas uniformément dans le sens attendu : plusieurs articles écartés sont explicitement mécanistiques, tandis que certains articles ajoutés relèvent de la galénique ou de l'épidémiologie. Le filtre ne réalise donc pas un tri qualitatif mais modifie la requête et, par conséquent, le classement par pertinence de PubMed. Un effet bénéfique demeure identifiable : parmi les articles écartés figurent des comparaisons entre médicaments d'une même classe, sources caractérisées de faux multi-hop.

**Deuxième itération**, corpus corrigé et prompt inchangé. Le score demeure nul mais la nature des échecs change. Le modèle produit désormais « terguride blocks 5-HT(2B) receptors » là où la référence indique « decreases activity of ». Source, cible et polarité coïncident ; seul le prédicat diffère. L'échec relève du vocabulaire et non de la compréhension.

Le taux de non-conformité au schéma passe paradoxalement de 21 % à 39 %. Cette dégradation apparente s'explique par l'amélioration du corpus : les articles mécanistiques emploient davantage de verbes d'action, que le modèle recopie au lieu de les traduire vers le schéma. La faiblesse du prompt était masquée par la pauvreté du corpus antérieur.

**Troisième itération**, modification unique : ajout d'une table de correspondance verbe-étiquette, assortie d'une règle d'affectation selon le type de la cible. La non-conformité passe de six relations à une, à texte identique — conclusion établie sur les cinq abstracts communs aux deux itérations, l'échantillon ayant partiellement changé par ailleurs.

**Décision sur la polarité.** L'inversion observée à la deuxième itération est corrigée : le modèle produit désormais « lafutidine decreases activity of histamine H2 receptor » là où le titre qualifie la molécule d'antagoniste. L'erreur portait sur la traduction du verbe en étiquette et non sur la compréhension du texte. La décision de conserver les couples de polarité distincts est donc maintenue, sans fusion.

### 4.3 Extraction complète

475 abstracts traités en 34,7 minutes, soit 4,4 secondes par abstract, sans interruption. Un dispositif de reprise incrémentale au format JSONL avait été prévu ; il n'a pas eu à être mobilisé.

**Volume produit.** 985 relations, soit 2,1 par abstract, portant sur 871 entités textuelles distinctes. 177 abstracts n'ont produit aucune relation, dont 120 distracteurs et 57 articles ciblés. L'écart entre ces deux taux — 44 % contre 27 % — confirme l'effet du ciblage.

**Conformité.** La mesure dépend de la définition retenue, et trois définitions coexistent dans les journaux du projet. Sur les 985 relations extraites : 829 emploient un prédicat du schéma sans considération des types d'entités ; 822 y ajoutent la condition qu'aucun type ne soit manquant ; 820 exigent en outre que les deux types appartiennent aux sept types du schéma.

Le chiffre retenu ici est **822 sur 985, soit 83 %**, définition employée par l'étape de récupération qui produit le fichier de relations effectivement exploité en aval.

Les 163 relations non conformes se répartissent en quatre familles : variantes lexicales d'un prédicat du schéma, reprise littérale de la colonne source de la table de correspondance, prédicats sans équivalent, et relations dont un type d'entité est absent.

Une étape de récupération, postérieure à l'extraction, ramène tout prédicat non conforme au prédicat du schéma qu'il contient. Elle récupère 113 relations et porte le taux de conservation de 83 % à 94 %, soit 935 relations. Sont écartées 36 relations à prédicat sans équivalent — majoritairement cliniques : `treats`, `targets`, `improves`, `prevents` —, 10 relations à type d'entité manquant et 4 énoncés de négation. Aucun prédicat n'est rattaché par approximation : ce qui n'est pas explicitement recensé est écarté et journalisé.

**Deux défauts que le contrôle de conformité laisse passer.** L'examen des neuf relations séparant les définitions les plus larges et les plus strictes en révèle deux, tous deux imputables au modèle et non au dispositif.

Le modèle invente des types d'entités absents du schéma : deux relations portent le type « Enzyme », qui n'y figure pas, et sont néanmoins conservées dans le graphe puisque leur type est présent. Ce constat a une conséquence pratique, le filtre excluant les arêtes reliant deux médicaments s'appuyant sur les types : une entité typée hors schéma lui échappe par construction.

Le modèle recopie en outre parfois le nom du type au lieu du nom de l'entité : trois relations ont pour source le mot littéral « Drug ». Il s'agit du même défaut que la reprise de la colonne source de la table de correspondance, transposé au champ entité. Ces trois relations ont été écartées par le contrôle de type d'entité.

**Une limite de conception du schéma.** Quatre relations extraites étaient des énoncés de négation — « does not affect », « does not mitigate ». Les dix prédicats du schéma expriment tous un lien effectif, positif ou négatif, sans permettre de représenter une absence de relation. Ces relations ont été supprimées et non converties, une conversion inversant le sens du texte source.

---

## 5. Le décalage entre référence et corpus

Ce résultat n'était pas anticipé et constitue l'apport principal du travail au-delà de la comparaison des architectures.

### 5.1 Constat

Les chaînes de DrugMechDB ne sont pas reconstructibles à partir des résumés PubMed. Sur les quinze chaînes retenues, aucune n'a pu être retrouvée dans le graphe extrait. Le maillon défaillant est constant : la relation reliant un processus biologique à une maladie.

**Mesure décisive.** Sur 935 relations conservées après récupération des prédicats, 36 seulement ont une maladie pour cible, dont 33 partent d'un médicament. La relation processus vers maladie, qui constitue le dernier saut de toutes les chaînes retenues, est pratiquement absente du corpus.

**Répartition des processus biologiques selon leur position.** La recapture de la noradrénaline et de la sérotonine apparaît 15 fois comme source contre 93 fois comme cible ; l'agrégation plaquettaire jamais comme source contre 17 fois comme cible ; l'angiogenèse une fois contre 29 ; la sécrétion acide gastrique jamais contre 8.

**Un contre-exemple, et il est instructif.** La fibrinolyse échappe à ce motif : elle apparaît 15 fois comme source contre 11 fois comme cible. Les entités de cette famille — plasmine, plasminogène, activateur du plasminogène — sont décrites comme agissant sur d'autres entités, et non seulement comme subissant l'action d'un médicament.

Cette exception explique un fait autrement surprenant. Le seul chemin de type pont proprement mécanistique retenu dans le jeu de test final, `amiloride → plasmine → myogenèse`, appartient précisément à cette famille. Là où les autres processus ne relancent jamais la chaîne, la fibrinolyse le fait — et c'est le seul endroit du corpus où un pont mécanistique authentique a pu être construit.

La généralisation doit donc être formulée avec précaution : les processus biologiques sont majoritairement des points d'arrivée, mais non universellement, et les exceptions sont exactement les endroits où la topologie en chemin subsiste.

### 5.2 Caractérisation

Les résumés produisent une **topologie en étoile** centrée sur le médicament : chaque arête part de celui-ci vers sa cible protéique, son processus ou son effet clinique. DrugMechDB modélise une **topologie en chemin**, où chaque entité intermédiaire relance la chaîne.

Deux mécanismes concourent à ce décalage.

**La littérature comprime.** Là où DrugMechDB décompose « venlafaxine → transporteur de la noradrénaline → recapture de la noradrénaline », un article écrit en une phrase que la venlafaxine inhibe la recapture de la noradrénaline. L'entité intermédiaire disparaît.

**La littérature présuppose.** Le lien final n'est jamais réénoncé. Le cas le plus net concerne la relation « BCR-ABL cause la leucémie myéloïde chronique », fait de manuel depuis quarante ans. Quatre articles ont été soumis, dont une revue de synthèse consacrée à l'usage de l'imatinib dans cette pathologie — le candidat le plus favorable, la fonction d'une revue étant de rappeler les données établies. Aucun ne produit cette relation. La revue produit en revanche le saut précédent, « Imatinib inhibits BCR-Abelson fusion protein ».

Le contraste, observé sur un même article, est structurant : le saut décrivant l'action du médicament sur sa cible est extrait, celui reliant la cible à la maladie ne l'est pas. Le premier constitue l'objet de la publication, le second son présupposé.

### 5.3 Conséquence méthodologique

Une base de connaissances curée et un corpus d'articles ne décrivent pas le monde au même niveau de détail. Le savoir mécanistique consolidé est précisément celui que les résumés ne réénoncent pas.

Ce constat a imposé un changement de méthode. Trois voies s'ouvraient : raccourcir les chaînes, dériver les questions du graphe extrait, ou faire du décalage le résultat unique de l'étude. La deuxième a été retenue.

**DrugMechDB change de rôle.** Il cesse d'être la source des questions et devient la référence de qualité d'extraction. Les questions sont dérivées des chemins réellement présents dans le graphe extrait, chacun vérifié manuellement contre ses abstracts sources.

**Sur l'équité de ce choix.** Les relations provenant des textes du corpus, les passages existent et le pipeline vectoriel peut les retrouver. Les questions emploient en outre les noms d'entités tels que le modèle les a lus dans le texte, ce qui facilite la recherche par similarité. Le biais résiduel penche donc contre l'hypothèse testée, direction préférable pour un dispositif expérimental.

---

## 6. Construction du jeu de test

### 6.1 Recherche des chemins

Le graphe extrait a été parcouru à la recherche de chemins de type pont et de type intersection. La recherche a produit 350 chemins bruts, ramenés à 23 valides après filtrage puis à 16 après diversification.

Cette réduction considérable est instructive.

**Propagation combinatoire d'une erreur.** La première recherche produisait 230 ponts, dont 115 empruntaient un médicament comme entité pont. Les exemples relevés font tous apparaître la même arête erronée en entrée : « asciminib increases activity of imatinib », convertie depuis un énoncé d'association thérapeutique. Le nœud imatinib présentant un degré sortant élevé, cette arête entrante fausse s'est combinée à ses arêtes sortantes.

La sortie du script de recherche établit le décompte de 115 ponts à entité pont médicamenteuse ; elle n'établit pas qu'ils procèdent tous de cette unique arête, plusieurs autres arêtes reliant deux médicaments existant dans le graphe. L'ordre de grandeur demeure : une arête entrante fausse sur un nœud très connecté engendre des dizaines de chemins candidats.

Une erreur d'extraction ne demeure donc pas locale dans un graphe : son effet est multiplié par le degré du nœud qu'elle atteint. Le phénomène est structurel et non lié à la qualité de l'extraction. Après exclusion des arêtes reliant deux médicaments, 89 des 149 ponts restants relèvent d'un même motif, `Drug → ChemicalSubstance → BiologicalProcess`, dont les exemples relevés font tous apparaître la même arête entrante — correcte cette fois — sur un nœud très connecté. Ici encore, la sortie du script fournit un décompte par motif et non une attribution par arête.

**Le filtre de types n'était pas encore effectif à ce stade.** L'exclusion des arêtes reliant deux médicaments n'en a écarté que treize, et vingt-trois ponts continuent d'emprunter une telle arête. La cause est un défaut de typage identifié ultérieurement : le type d'un nœud était fixé par la dernière relation traitée et non par son type majoritaire, de sorte qu'un nœud mal typé échappait à un filtre reposant sur les types. Le défaut a été corrigé, et la sélection finale écarte trente-sept chemins pour ce motif.

Ce constat prolonge le précédent : non seulement une arête erronée se propage, mais le mécanisme censé la contenir peut lui-même être neutralisé par une erreur d'étiquetage située ailleurs.

**Plafond structurel du corpus.** Le nombre de chemins multi-hop authentiques demeure faible. Le corpus portant sur quatorze médicaments dont plusieurs relèvent de mêmes classes thérapeutiques, et la littérature de synthèse énumérant systématiquement les membres d'une classe, la proportion de chemins non résolubles par une unique récupération est intrinsèquement limitée. Ce plafond constitue une propriété du domaine documentaire et non un défaut de méthode.

### 6.2 Filtres appliqués

Six critères ont été appliqués, dans un ordre plaçant la validation avant la diversification. Cet ordre a lui-même fait l'objet d'une correction : la diversification, appliquée en premier, écartait des chemins valides au profit de chemins ultérieurement invalidés.

| Critère | Chemins écartés |
|---|---|
| Entité générique (vocabulaire d'essai clinique) | 179 |
| Faux multi-hop à l'échelle du corpus | 70 |
| Pont de type Drug | 37 |
| Relation identifiée comme fausse à la relecture | 28 |
| Entité malformée | 6 |
| Extrémités identiques | 4 |
| Exclusion manuelle décidée à la relecture | 3 |
| **Total écarté** | **327** |

Le filtre de faux multi-hop compare chaque chemin aux 475 abstracts du corpus et non à ses seuls abstracts sources. La portée est déterminante : la recherche vectorielle interroge l'ensemble du corpus, et tout article contenant les deux extrémités permet une résolution en une seule récupération.

### 6.3 Vérification manuelle

Les questions étant dérivées du graphe extrait, une erreur d'extraction produirait une question à réponse fausse. Chaque chemin retenu a donc été confronté à ses abstracts sources. Cette relecture a écarté treize chemins pour inversion de polarité — conformes au schéma, syntaxiquement valides, sémantiquement faux. Trois exemples : la venlafaxine décrite comme augmentant la recapture de la noradrénaline, la lafutidine comme augmentant la sécrétion acide gastrique, la bromocriptine comme diminuant l'activité des récepteurs dopaminergiques alors qu'elle en est un agoniste. Aucun contrôle automatique n'aurait pu les détecter.

**Quantification du taux d'inversion.** Cette relecture portant sur des chemins retenus par le filtrage, elle ne fournit pas un taux d'erreur représentatif du graphe. Une mesure distincte a donc été conduite sur un échantillon aléatoire reproductible de 40 relations tirées parmi les 807 relations porteuses de polarité que compte le graphe, chacune confrontée aux phrases de son abstract source.

Douze relations n'ont pu être tranchées, les phrases extraites automatiquement ne portant pas l'information nécessaire. Sur les 28 restantes : trois inversions de polarité caractérisées et trois énoncés dont la direction n'est pas soutenue par le texte, soit de l'ordre de 10 % d'inversions et 21 % d'énoncés incorrects au sens large.

Le critère de jugement retenu est strict : une relation n'est comptée correcte que si une phrase du corpus l'établit. Un énoncé pharmacologiquement exact mais non attesté par le texte source est classé indécidable, puisque la mesure porte sur la fidélité de l'extraction au texte et non sur la véracité de l'énoncé.

Les trois inversions sont vérifiables sur le seul texte de l'abstract. « Venlafaxine increases activity of NET » là où l'article la décrit comme un inhibiteur de recapture. « Selexipag positively regulates pulmonary arterial hypertension » là où le médicament est approuvé pour traiter cette pathologie. « Lafutidine negatively regulates gastric acid elimination » là où le titre indique que cette élimination est accrue par la molécule.

**Portée de cette mesure.** Trois inversions sur 28 observations correspondent à un intervalle de confiance à 95 % s'étendant approximativement de 2 % à 28 %. Ces valeurs donnent un ordre de grandeur, non une estimation précise.

Une observation complémentaire limite en outre la portée de tout échantillonnage aléatoire : les erreurs se regroupent par article. Sept des relations ciblant une maladie constituent la même inversion, issue d'un seul article recensant les traitements de la phobie sociale, où sept molécules distinctes sont décrites comme augmentant l'activité de la pathologie qu'elles traitent. Un échantillon de relations sous-estime donc la variance réelle, plusieurs erreurs pouvant partager une source unique.

Le contrôle automatisé et le contrôle humain se sont révélés complémentaires dans les deux sens. Le premier a détecté 32 faux multi-hop sur 61, dont 11 que la relecture avait validés, en comparant chaque chemin à l'ensemble du corpus. Le second a détecté un cas que le filtre laissait passer, l'abstract source orthographiant « carbegoline » au lieu de « cabergoline ».

### 6.4 Composition finale

**Vingt questions**, réparties en onze questions multi-hop portant sur dix entités ponts distinctes, et neuf questions à un saut servant de contrôle.

Les questions de contrôle jouent le rôle de témoin. Si les deux architectures les réussissent, le dispositif fonctionne. Si le pipeline par graphe y échouait là où le vectoriel réussit, il y aurait un problème d'implémentation et non un résultat sur le multi-hop.

**Effectif nominal et effectif effectif.** Les onze questions multi-hop reposent sur dix entités ponts distinctes : une seule paire, portant sur le transporteur de la noradrénaline, partage son entité pont et ne constitue donc pas deux observations indépendantes. Les résultats sont rapportés en mentionnant les deux effectifs, l'effectif nominal surestimant légèrement la précision atteignable.

**Décision de périmètre.** Une question porte sur un effet indésirable partagé plutôt que sur un mécanisme d'action. Elle a été conservée et marquée comme catégorie distincte : la question de recherche porte sur la capacité à retrouver une information exigeant deux documents, non sur la nature mécanistique de cette information. Cet effectif d'une seule question interdit toute analyse séparée de cette catégorie.

**Séparation des données.** Le jeu de test contient, pour chaque question, la réponse attendue, les identifiants des documents sources et le chemin d'origine. Seul le champ `question` est transmis aux pipelines ; le reste sert exclusivement à l'évaluation, exécutée après que le système a répondu.

---

## 7. Les deux pipelines

### 7.1 Pipeline A — recherche vectorielle

**Unité de récupération.** L'abstract entier, titre et résumé concaténés. Aucun découpage n'est appliqué : l'abstract constitue une unité sémantique cohérente qu'un découpage fragmenterait, et ce choix rend la comparaison à la vérité terrain directe, une unité récupérée correspondant exactement à un identifiant PubMed.

**Modèles comparés.** `pritamdeka/S-PubMedBert-MS-MARCO`, version de PubMedBERT entraînée pour la recherche sémantique, et `sentence-transformers/all-MiniLM-L6-v2`, modèle généraliste de référence. PubMedBERT dans sa version d'origine est un modèle de langue et non un encodeur de phrases ; son emploi direct produirait des représentations inadaptées à la recherche.

Le modèle biomédical n'apporte aucun gain sur les questions à un saut mais un écart net sur les questions multi-hop, où le vocabulaire spécialisé paraît déterminant. Il a été retenu pour la suite.

**Choix de conception assumé.** Un découpage en passages plus courts améliorerait vraisemblablement le rappel, une entité isolée pesant davantage dans un segment de cent tokens que dans un abstract complet. Ce découpage n'a pas été mis en œuvre, la baseline visant une implémentation standard telle qu'un praticien la réaliserait par défaut. L'écart correspondant est signalé comme limite plutôt que dissimulé.

### 7.2 Pipeline B — traversée de graphe

Le graphe compte 792 nœuds et 932 arêtes, chaque arête portant son identifiant PubMed d'origine. Son exécution ne requiert aucun GPU.

**Trois étapes.** L'ancrage identifie dans la question les entités présentes dans le graphe, par appariement des groupes de mots du plus long au plus court. La traversée explore le voisinage à deux sauts. La remontée associe les arêtes atteintes aux documents qui les portent, ce qui permet d'évaluer les deux pipelines sur le même étalon.

**La traversée ignore l'orientation des arêtes.** Les chemins de type intersection exigent de remonter du médicament vers la cible partagée puis de redescendre vers un second médicament, ce qu'un parcours orienté interdirait.

**Pondération.** Une arête atteinte au premier saut compte pour 1, au second pour 0,5 ; une arête incidente à un nœud d'ancrage voit son poids doublé. Ces valeurs constituent un choix de conception et n'ont pas été optimisées sur le jeu de test, ce qui reviendrait à ajuster le système aux questions servant à l'évaluer.

**Point de fragilité.** L'ancrage conditionne tout le reste : une question dont aucune entité n'est appariée produit un rappel nul indépendamment de la qualité du graphe.

### 7.3 Une correction en aval du jeu de test

L'analyse de la question SH04 a révélé que la fonction de canonisation ne translittérait pas les caractères grecs. Une entité écrite « β-elemene » dans le graphe et « beta-elemene » dans une question produisait deux formes distinctes, empêchant tout appariement.

La correction porte sur l'étape d'ancrage, située en aval de la constitution du jeu de test. La vérité terrain demeure inchangée, ce qui distingue cette correction d'un ajustement du système aux questions servant à l'évaluer : le défaut corrigé existait indépendamment du jeu de test employé.

Les deux mesures sont rapportées. Le rappel au rang 5 passe de 0,78 à 0,83, celui des questions à un saut de 0,89 à 1,00. Le graphe compte 792 nœuds après correction contre 794 auparavant, deux paires d'entités ayant fusionné.

**Différence structurelle mise en évidence.** Le pipeline par graphe repose sur un appariement exact de chaînes de caractères et se trouve sensible aux variations orthographiques, là où le pipeline vectoriel opère sur des représentations continues qui les absorbent. Aucune correction symétrique n'est applicable au pipeline vectoriel, qui n'emploie pas de canonisation.

---

## 8. Résultats

### 8.1 Récupération

Rappel au rang 5, sur les vingt questions du jeu de test. Cette mesure correspond à la métrique **Context Recall** de RAGAS : parmi les documents nécessaires à la réponse, quelle proportion figure dans les documents récupérés ? Elle est calculée directement sur les identifiants PubMed de la vérité terrain, sans recours à un juge, et constitue donc la plus fiable des trois métriques rapportées.

| | Vectoriel | Graphe | Écart |
|---|---|---|---|
| Global | 0,55 | **0,83** | +0,28 |
| Questions à un saut | 0,67 | **1,00** | +0,33 |
| Pont | 0,50 | **0,67** | +0,17 |
| Intersection | 0,44 | **0,71** | +0,27 |

Le pipeline par graphe surpasse le pipeline vectoriel sur les trois catégories.

**L'écart est maximal là où la traversée ne sert pas.** Il atteint 0,33 point sur les questions à un saut, qui n'exigent qu'un seul document, contre 0,27 sur les intersections et 0,17 sur les ponts. Cette hiérarchie contredit l'attribution que l'on aurait attendue et invite à la réviser.

Une objection doit être levée avant d'en tirer une conclusion : les trois catégories ne partent pas du même niveau, et le pipeline par graphe atteint 1,00 sur les questions à un saut. L'écart y est donc borné par construction, puisque le pipeline vectoriel y atteignait déjà 0,67. Comparer des écarts bruts entre catégories de difficulté inégale n'est pas légitime en soi. La comparaison a donc été refaite en proportion d'erreur comblée, c'est-à-dire en rapportant l'écart à la marge disponible.

| Catégorie | Écart brut | Erreur comblée |
|---|---|---|
| Questions à un saut | +0,33 | 100 % |
| Intersection | +0,27 | 48 % |
| Pont | +0,17 | 34 % |

La hiérarchie est inchangée sous les deux mesures. La conclusion ne relève donc pas d'un artefact de plafond.

Le mécanisme dominant n'est donc pas la capacité de traversée, mais l'**absence de dilution**. Le graphe indexe des relations et non des documents : une entité citée une seule fois dans un résumé y conserve le même poids qu'une entité centrale, là où le vecteur d'un document reflète son sujet global. Ce mécanisme joue sur toutes les catégories de questions et suffit à expliquer l'essentiel de l'écart mesuré.

La **capacité de traversée** n'apporte pas de gain supplémentaire mesurable sur ce jeu de test. Deux lectures demeurent possibles. Sa contribution peut être faible en regard de celle de la dilution. Son apport peut aussi être masqué par la difficulté intrinsèquement plus grande des questions multi-hop, sur lesquelles les deux architectures partent d'un niveau inférieur. L'effectif — trois questions de type pont, huit intersections — ne permet pas de trancher entre ces deux lectures.

Attribuer l'écart à la traversée constituerait donc une erreur d'interprétation que les données ne soutiennent pas.

### 8.2 Diagnostic des échecs du pipeline vectoriel

Le rappel de 0,67 initialement mesuré sur les questions de contrôle demeurait inférieur à ce qu'on attend d'un témoin. Trois causes ont été envisagées.

L'hypothèse d'une **troncature** des abstracts dépassant la fenêtre de 512 tokens des modèles d'embedding a été testée et écartée. Les documents attendus mais non récupérés comptent 358 tokens en moyenne contre 348 pour ceux qui le sont, et 5 % sont tronqués contre 6 %. Les deux populations sont indiscernables sur ce critère.

La cause réelle est la **dilution**. Les documents manqués sont ceux dont l'entité recherchée n'est pas le sujet principal. La question SH07 porte sur le sarpogrelate, absent du titre du document attendu et cité une seule fois dans le corps du résumé parmi d'autres antagonistes. Les trois documents attendus de la question MH05 ne nomment ni le ranibizumab ni le ramucirumab dans leur titre.

Une entité mentionnée une fois dans un texte de 350 tokens contribue faiblement au vecteur qui représente ce texte. La recherche vectorielle sélectionne les documents dont le sujet global ressemble à la question, non ceux qui contiennent l'information cherchée. Ce phénomène constitue une limite structurelle de l'indexation par document entier, et non un défaut d'implémentation.

### 8.3 Rappel selon le budget documentaire

| K | Vectoriel | Graphe | Écart |
|---|---|---|---|
| 1 | 0,38 | 0,45 | +0,08 |
| 3 | 0,53 | 0,78 | +0,26 |
| 5 | 0,55 | **0,83** | +0,28 |
| 10 | 0,60 | 0,88 | +0,28 |
| 20 | 0,77 | 0,95 | +0,18 |

Le pipeline par graphe domine à toutes les valeurs de K. Le résultat ne dépend donc pas du choix du budget documentaire, ce qui écarte l'objection d'un écart obtenu par un réglage favorable.

**Budget documentaire équivalent.** Le graphe atteint un rappel de 0,83 avec cinq documents, niveau que le pipeline vectoriel n'atteint pas même en récupérant cinquante documents. Les documents manqués ne sont pas mal classés mais absents du classement : la dilution les rend invisibles à la recherche par similarité plutôt qu'elle ne les relègue.

**L'écart culmine entre K = 5 et K = 10**, à 0,28 point, et se resserre de part et d'autre. À K = 1, le budget documentaire est trop restreint pour qu'une question multi-hop soit résoluble par l'une ou l'autre architecture. À K = 20, le pipeline vectoriel finit par rattraper une partie de son retard.

**Un comportement contrasté selon la catégorie de question.** À K = 1, les deux pipelines obtiennent des scores strictement identiques sur les intersections (0,25) mais non sur les questions à un saut, où le graphe l'emporte déjà de 0,11 point.

Cette dissociation est instructive. Sur les intersections, aucune des deux architectures ne peut réussir avec un document unique, la question exigeant par construction deux documents distincts : l'égalité y traduit une impossibilité commune. Sur les questions à un saut, en revanche, un document suffit, et le graphe le place mieux — non par capacité de traversée, qui n'est pas sollicitée, mais par absence de dilution.

**Sur les questions de type pont, l'écart demeure rigoureusement constant** à 0,17 point pour toutes les valeurs de K testées : le pipeline vectoriel ne rattrape jamais son retard, quel que soit le nombre de documents qu'on lui accorde. Cette régularité a survécu à la correction de la translittération, ce qui la rend moins susceptible d'être un artefact de mesure. L'observation porte néanmoins sur trois questions et appelle réserve.

**Portée pratique.** L'avantage du graphe est pour une part un avantage d'efficacité : il obtient avec peu de documents ce que le pipeline vectoriel n'obtient qu'avec beaucoup, voire jamais. Cette nuance importe, vingt abstracts de 385 tokens excédant la fenêtre exploitable d'un modèle de sept milliards de paramètres.

### 8.4 Génération

Le même modèle est appliqué aux documents récupérés par chacun des deux pipelines, avec le même prompt et la même température : seul le contexte fourni diffère. Le prompt prévoit une réponse explicite d'abstention lorsque les documents ne contiennent pas l'information.

| | Vectoriel | Graphe |
|---|---|---|
| Exactitude | 0,30 | **0,70** |
| Abstention | 0,50 | 0,15 |
| Latence moyenne | 2,8 s | 2,9 s |
| Questions à un saut | 0,44 | **0,78** |
| Pont | 0,00 | **0,67** |
| Intersection | 0,25 | **0,62** |

**L'écart d'exactitude (0,40) excède l'écart de rappel (0,28).** Un défaut de récupération ne se rattrape pas à la génération : le pipeline vectoriel s'abstient dans la moitié des cas, non par erreur mais faute de disposer des documents nécessaires. Aucune qualité de rédaction ne compense un document absent.

Les latences sont équivalentes. L'avantage du graphe ne porte donc pas sur le coût de génération.

**Portée de la métrique.** Une réponse est comptée correcte dès lors qu'elle contient l'une des formulations acceptables, y compris dans sa justification. La mesure est donc permissive. Cette tolérance s'applique identiquement aux deux pipelines et ne fausse pas la comparaison, mais elle gonfle vraisemblablement les deux scores.

**Deux cas d'analyse.** La question SH04 illustre une erreur de génération et non de récupération : les deux pipelines récupèrent le document attendu et produisent tous deux une réponse erronée. Le dispositif distingue donc bien les deux étapes.

La question MH09 constitue le seul cas où le pipeline vectoriel l'emporte nettement. La question ne nomme aucun médicament — elle demande quel inhibiteur sélectif de la recapture de la sérotonine agit également sur le transporteur de la noradrénaline. Le graphe s'ancre sur deux processus et n'atteint jamais le document pertinent. Ce mode d'échec est propre à l'architecture par graphe : lorsqu'une question ne comporte que des concepts et aucune entité nommée saillante, l'ancrage oriente la traversée dans une direction improductive.

### 8.5 Évaluation par juge

Les métriques de fidélité et de pertinence suivent les définitions de RAGAS mais sont réimplémentées plutôt qu'importées de la bibliothèque. Celle-ci suppose l'accès à un modèle distant, ce que la contrainte de budget nul interdit, et masque le prompt de jugement employé. Une réimplémentation rend ce prompt explicite et donc rapportable.

Le jugement est produit sur une échelle discrète à cinq niveaux, ramenée à l'intervalle [0,1]. Un modèle de sept milliards de paramètres ne produit pas de score continu de façon reproductible ; restreindre la granularité à ce que le juge peut effectivement tenir évite de recueillir du bruit.

**Stabilité du juge.** Chaque réponse a été évaluée trois fois. L'écart maximal entre les trois jugements est en moyenne de 0,01 pour la fidélité et nul pour la pertinence ; 39 jugements sur 40 sont parfaitement stables pour la première, 40 sur 40 pour la seconde. La réserve formulée a priori sur l'instabilité d'un juge de petite taille n'est pas confirmée par la mesure.

| | Vectoriel | Graphe |
|---|---|---|
| Fidélité | **0,86** | 0,81 |
| Pertinence | 0,60 | **0,76** |
| Exactitude | 0,30 | **0,70** |

**Le pipeline vectoriel obtient une meilleure fidélité.** Ce résultat s'explique par son taux d'abstention : s'abstenir lorsque les documents ne contiennent pas l'information constitue un comportement fidèle et reçoit la note maximale. Un système qui répond rarement est mécaniquement fidèle.

**La métrique de fidélité, prise isolément, récompense donc le silence.** Les questions de type pont l'illustrent : le pipeline vectoriel y obtient sa meilleure fidélité, 0,92, alors que son exactitude y est nulle. Cette observation porte sur trois questions et vaut comme illustration, non comme mesure.

Les trois métriques doivent être lues conjointement. Le pipeline vectoriel apparaît **prudent** — il n'invente pas mais répond peu ; le pipeline par graphe **utile** — il répond plus souvent et plus souvent correctement.

### 8.6 Coûts

| | Vectoriel | Graphe |
|---|---|---|
| Extraction des relations | — | 35 min GPU |
| Indexation | moins d'une minute GPU | quelques secondes, sans GPU |
| Requête | GPU requis | parcours d'index, sans GPU |
| **Total de construction** | **moins d'une minute** | **35 min** |

Le pipeline par graphe exige environ deux ordres de grandeur de calcul supplémentaire à la construction. Cette charge provient intégralement de l'extraction des relations, qui requiert un appel au modèle de langue par document. Cette étape appartient au pipeline de données en amont et doit être imputée au coût du graphe, faute de quoi la comparaison omettrait l'essentiel de son surcoût.

**Précision sur la mesure du coût d'indexation.** Le chronométrage de l'indexation vectorielle englobe le chargement du modèle d'embedding en mémoire et l'encodage du corpus, soit 23 secondes au total, dont environ 8 secondes d'encodage proprement dit. Il n'inclut pas le téléchargement initial du modèle. Cette omission est symétrique de celle appliquée au pipeline par graphe, dont les 35 minutes excluent l'installation d'Ollama et le téléchargement du modèle de langue. Aucune des deux mesures n'isolant proprement ses composantes, le rapport entre les deux n'est donné qu'en ordre de grandeur.

En contrepartie, le graphe s'interroge sans accélérateur matériel, là où le pipeline vectoriel requiert un GPU pour encoder chaque question.

**L'arbitrage est celui d'un coût initial élevé contre un coût d'exploitation faible.** Le surcoût du graphe se justifie pour un corpus stable et fréquemment interrogé ; il ne se justifie pas pour un corpus renouvelé en permanence, dont la reconstruction devrait être répétée.

Sur un système recevant un volume important de requêtes, l'arbitrage bascule nettement en faveur du graphe.

---

## 9. Livrable de démonstration

Une interface Streamlit permet la consultation des résultats. Elle comporte deux vues : une comparaison question par question, affichant côte à côte la réponse de chaque pipeline, ses métriques et les documents qu'il a récupérés, et une vue d'ensemble reprenant les agrégats globaux et par catégorie.

L'interface restitue des résultats précalculés plutôt que de les générer à la demande. La génération requiert un accélérateur matériel absent du poste de démonstration, et cette conception garantit en outre que les valeurs affichées coïncident exactement avec celles du présent rapport.

Les documents attendus par la vérité terrain sont signalés parmi les documents récupérés, ce qui rend visible le mécanisme de l'écart : le pipeline vectoriel affiche fréquemment cinq documents dont aucun n'est attendu, tandis que le pipeline par graphe en place généralement un ou deux en tête de classement.

---

## 10. Limites

### 10.1 Effectifs

Le jeu de test compte vingt questions, dont onze multi-hop reposant sur dix entités ponts distinctes. Cet effectif limite la précision statistique des écarts observés et interdit toute analyse par sous-catégorie fine — les résultats sur les questions de type pont, au nombre de trois, sont rapportés à titre illustratif, de même que l'unique question portant sur un effet indésirable.

Ce plafond résulte d'une propriété du corpus et non d'un manque d'effort : la littérature de synthèse énumérant systématiquement les membres d'une classe thérapeutique, la proportion de chemins non résolubles par une unique récupération est intrinsèquement limitée sur un corpus portant sur quatorze médicaments.

### 10.2 Validité externe

Le corpus est construit pour contenir les chaînes testées. L'étude mesure donc la performance sur un corpus où l'information est présente, non la capacité à la retrouver dans l'ensemble de la littérature.

Ce choix est nécessaire : sans articles porteurs, les deux pipelines échoueraient uniformément et le dispositif ne discriminerait rien.

### 10.3 Asymétrie du recours au modèle de langue

Le graphe est intégralement construit par extraction automatique au moyen d'un modèle de langue, tandis que l'index vectoriel n'en fait aucun usage.

La performance du pipeline par graphe dépend donc de la qualité de cette extraction. Un échantillon aléatoire de 40 relations porteuses de polarité, confronté aux abstracts sources, fait apparaître de l'ordre de 10 % d'inversions caractérisées et 21 % d'énoncés incorrects au sens large, sur les 28 relations que les phrases extraites permettaient de trancher. L'intervalle de confiance est large et ces valeurs ne constituent qu'un ordre de grandeur.

**Portée du résultat.** La comparaison porte sur un couple architecture-extracteur — un graphe extrait par un modèle local de sept milliards de paramètres, opposé à un index vectoriel construit sur S-PubMedBert — et non sur les architectures considérées indépendamment de leur mise en œuvre.

**Sens du biais.** Une extraction imparfaite dégrade le graphe en y introduisant des arêtes erronées, sans affecter l'index vectoriel. Le biais joue donc contre l'hypothèse testée. Le pipeline par graphe l'emporte malgré ce handicap, ce qui rend la mesure conservatrice : un extracteur plus fiable creuserait vraisemblablement l'écart plutôt qu'il ne le réduirait.

### 10.4 Baseline non optimisée

Le pipeline vectoriel conserve l'abstract entier comme unité de récupération. Un découpage en passages plus courts améliorerait vraisemblablement son rappel. Cette optimisation n'a pas été mise en œuvre, la baseline visant une implémentation standard.

### 10.5 Périmètre du schéma d'extraction

Les quinze chaînes retenues n'exercent que six des dix relations du schéma. Les relations `increases activity of`, `participates in`, `manifestation of` et `causes` ne sont testées par aucune question. Le schéma d'extraction est donc plus large que le périmètre évalué.

Par ailleurs, le type OrganismTaxon, rétabli dans le schéma d'extraction après mesure, n'apparaît dans aucun motif de chaîne candidate : les mécanismes infectieux empruntent des chemins longs, éliminés par le filtre de profondeur. Une décision validée au niveau des relations peut ainsi demeurer sans effet au niveau des chaînes courtes.

---

## 11. Conclusion

Sur les questions d'inférence multi-hop en domaine biomédical, la recherche par traversée de graphe surpasse la recherche vectorielle sur l'ensemble des métriques de récupération et de génération mesurées. Le graphe atteint avec cinq documents un niveau de rappel que la recherche vectorielle n'atteint pas avec cinquante, et son avantage se maintient à toutes les valeurs du budget documentaire testées.

L'avantage tient principalement à un mécanisme unique, et non à celui que l'on attendait. L'écart est maximal sur les questions à un saut, qui n'exigent aucune traversée : c'est donc l'absence de dilution qui domine. Le graphe indexe des relations et non des documents, de sorte qu'une entité citée une seule fois y pèse autant qu'une entité centrale. La capacité de traversée, présentée comme l'argument théorique en faveur de l'architecture par graphe, ne produit pas de gain supplémentaire mesurable sur ce jeu de test — sans qu'il soit possible de déterminer si sa contribution est faible ou masquée par la difficulté supérieure des questions multi-hop.

**Sur la question de recherche.** Le surcoût du graphe est réel — environ deux ordres de grandeur de calcul supplémentaire à la construction — mais il est intégralement payé une fois. À l'exploitation, le graphe est le moins coûteux des deux : il s'interroge sans accélérateur matériel là où le pipeline vectoriel en exige un pour chaque question, et les latences de génération sont équivalentes. L'arbitrage se résout donc en faveur du graphe pour un corpus stable et fréquemment interrogé, et en sa défaveur pour un corpus renouvelé en permanence.

**Trois résultats distincts de cette comparaison** méritent d'être retenus.

Une base de mécanismes curée par des experts n'est pas reconstructible à partir de résumés d'articles. La littérature comprime les chaînes causales et présuppose les liens établis : le savoir mécanistique consolidé est précisément celui que les résumés ne réénoncent pas. Ce constat, qui a imposé une refonte de la méthode en cours d'étude, constitue une limite de fond de tout appariement entre base curée et corpus documentaire.

Une erreur d'extraction ne demeure pas locale dans un graphe : son effet est multiplié par le degré du nœud qu'elle atteint. Une arête entrante fausse sur un nœud très connecté a contribué à faire passer le nombre de chemins candidats de quelques dizaines à plus de deux cents. Ce constat plaide pour un contrôle de qualité en amont de la construction du graphe plutôt qu'en aval.

Les erreurs d'extraction se regroupent en outre par article source, ce qui a une conséquence pratique : un échantillon aléatoire de relations sous-estime la variance réelle du taux d'erreur, plusieurs erreurs pouvant partager une même origine documentaire.

La métrique de fidélité, employée seule, récompense le silence. Le pipeline le moins performant y obtient le meilleur score grâce à son taux d'abstention. Cette métrique n'a de sens que lue conjointement avec la pertinence et l'exactitude.

### Perspectives

Trois directions prolongeraient naturellement ce travail.

**Élargir le corpus.** Le plafond de chemins multi-hop authentiques résulte du nombre restreint de médicaments couverts. Un corpus portant sur plusieurs centaines de molécules issues de classes thérapeutiques éloignées augmenterait mécaniquement la proportion d'intersections non résolubles par une unique récupération.

**Renforcer l'extracteur.** Le taux d'inversion de polarité, de l'ordre de 10 % sur l'échantillon mesuré, constitue le principal handicap du pipeline par graphe. Un modèle plus grand, ou un dispositif de vérification automatique de la polarité, creuserait vraisemblablement l'écart mesuré.

**Traiter l'ancrage.** Le mode d'échec propre à l'architecture par graphe — une question ne comportant que des concepts et aucune entité nommée saillante — appelle un mécanisme d'ancrage plus robuste, par exemple fondé sur une recherche vectorielle appliquée aux nœuds du graphe plutôt que sur un appariement exact de chaînes de caractères. Une telle hybridation combinerait les forces des deux architectures.

---

## Annexe A — Environnement technique

**Poste de développement.** Windows 11 Pro, Intel Core i5-6300U, 16 Go de mémoire vive, sans GPU dédié. Python 3.12.10, dépendances isolées dans un environnement virtuel.

**Calcul intensif.** Google Colab, GPU Tesla T4 (15 360 Mo), Ollama, modèle qwen2.5:7b.

**Dépendances principales.** PyYAML 6.0.3, Biopython 1.88, transformers 5.15.0, sentence-transformers 5.7.0, torch 2.11.0+cu128, Streamlit 1.62.0, pip-system-certs 5.3.

Le fichier `requirements.txt`, à la racine du dépôt, fige les versions exactes et permet de reconstituer l'environnement à l'identique.

## Annexe B — Organisation du dépôt

```
stage-graphrag/
├── data/
│   ├── raw/          données sources, en lecture seule
│   └── processed/    sorties du pipeline
├── scripts/          scripts numérotés dans l'ordre d'exécution
├── notebooks/        notebooks Colab (extraction, indexation, génération)
├── docs/             journaux de décision et d'exploration
├── dashboard.py      interface de démonstration
└── requirements.txt
```

Les scripts sont numérotés dans leur ordre d'exécution, poste local et Colab confondus, de sorte que le dépôt restitue la chronologie complète du travail.

## Annexe C — Contraintes de reproductibilité

**Sources brutes.** `indication_paths.yaml` (DrugMechDB), téléchargé depuis le dépôt SuLab/DrugMechDB. Les abstracts PubMed sont récupérés par l'API E-utilities ; la liste des identifiants collectés est figée dans les fichiers de sortie, ce qui rend la collecte rejouable à l'identique indépendamment de l'évolution de l'algorithme de classement de PubMed.

**Dates de collecte.** Corpus pilote le 11 août 2026, corpus de travail le 16 août 2026. Ces dates importent : le classement par pertinence de PubMed n'étant pas reproductible dans le temps, seule la liste figée des identifiants garantit la rejouabilité.

**Déterminisme.** Température nulle sur l'ensemble des appels au modèle de langue. Le déterminisme du dispositif a été vérifié : une même inversion de polarité a été reproduite à l'identique entre deux itérations du dry run.

**Prérequis Colab.** L'image Colab ne fournit ni `zstd`, requis par le script d'installation d'Ollama, ni `pciutils`/`lshw`, requis pour la détection du GPU au démarrage du serveur. Ces trois paquets doivent être installés avant Ollama, faute de quoi le serveur démarre en mode CPU sans erreur apparente.

**Éphémérité des sessions.** Une session Colab peut être recyclée sans notification. Les fichiers téléversés et le modèle téléchargé sont alors perdus, alors même que le notebook demeure apparemment actif. Les traitements longs sauvegardent leur progression de manière incrémentale sur un espace de stockage persistant.

## Annexe D — Correspondance avec le cahier des charges

### Livrables prescrits

| Livrable | État | Section |
|---|---|---|
| Pipeline 0 — collecte, nettoyage, extraction | réalisé | 3.3 et 4 |
| Pipeline A — baseline vectorielle | réalisé | 7.1 |
| Pipeline B — architecture par graphe | réalisé | 7.2 |
| Tableau de bord comparatif | réalisé | 9 |

### Métriques d'évaluation

Les trois métriques RAGAS prescrites sont mesurées.

| Métrique RAGAS | Nom employé dans ce rapport | Valeur (vectoriel / graphe) |
|---|---|---|
| Context Recall | Rappel au rang 5 | 0,55 / 0,83 |
| Faithfulness | Fidélité | 0,86 / 0,81 |
| Answer Relevance | Pertinence | 0,60 / 0,76 |

Une quatrième mesure, l'exactitude de la réponse, a été ajoutée. Déterministe et sans recours à un juge, elle sert de référence aux deux métriques jugées et permet d'établir que la fidélité, prise isolément, récompense l'abstention.

### Écarts aux outils prescrits

Trois substitutions ont été opérées par rapport aux outils mentionnés dans le cahier des charges. Elles sont énoncées ici plutôt que passées sous silence.

**Architecture par graphe.** Le cahier des charges mentionne les cadriciels GraphRAG de Microsoft ou LightRAG. La traversée a été implémentée directement. Ce choix garantit le contrôle des paramètres du dispositif — pondération des sauts, méthode d'ancrage, profondeur — qui sont explicités dans ce rapport et auraient été masqués par un cadriciel. Il supprime en outre une dépendance lourde dans un environnement de calcul reconstruit à chaque session.

**Base vectorielle.** Le cahier des charges mentionne ChromaDB ou FAISS. Les vecteurs sont conservés sous forme de tenseurs normalisés et la recherche s'effectue par produit scalaire. Sur 475 documents, un index approché n'apporte aucun gain : la recherche exhaustive s'exécute en quelques millisecondes et évite l'approximation introduite par les structures de voisinage.

**Matériel de calcul.** Le cahier des charges prévoit un poste GPU du département ou un portable disposant d'au moins 8 Go de mémoire vidéo. Le poste de travail disponible étant dépourvu de GPU dédié, l'inférence a été portée sur Google Colab en offre gratuite. Cette substitution respecte la contrainte de budget nul mais introduit l'éphémérité des sessions, dont les conséquences pratiques sont documentées ci-dessus.

### Réductions de périmètre prévues au cahier des charges

Le cahier des charges prévoit explicitement plusieurs réductions pour tenir la durée de quatre semaines. Toutes ont été respectées : un seul dataset structuré (DrugMechDB, le choix étant justifié en section 3.1), un corpus de quelques centaines d'abstracts (475), un jeu de test de vingt à trente questions (vingt), une validation automatisée sans évaluation par expert, une baseline vectorielle volontairement standard, et un tableau de bord fonctionnel plutôt que finalisé.
