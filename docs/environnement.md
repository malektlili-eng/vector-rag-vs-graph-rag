# Environnement technique

## Poste de développement
- OS : Windows 11 Pro
- Processeur : Intel Core i5-6300U
- RAM : 16 GB
- GPU : aucun GPU dédié (Intel HD Graphics 520)
- Python : Python 3.12.10
- Isolation des dépendances : environnement virtuel Python (venv)
## Calcul intensif
- Google Colab (GPU) — extraction d'entités, embeddings, inférence LLM


## Dépendances

### Poste local (PC 1)
- PyYAML 6.0.3 — lecture du dataset DrugMechDB (format YAML)
- Biopython 1.88 — accès à l'API PubMed E-utilities
- transformers 5.15.0 — tokenisation, mesure de longueur en tokens
- Streamlit 1.62.0 — tableau de bord comparatif
- pip-system-certs 5.3 — résolution du problème de certificats SSL sous Windows
### Environnement Colab
- sentence-transformers 5.7.0 — modèles d'embedding
- torch 2.11.0+cu128 — support GPU
- transformers 5.15.0 — tokeniseurs des modèles d'embedding
- Ollama + qwen2.5:7b — extraction, génération et jugement
- GPU : Tesla T4, 15 360 Mo


## Organisation des données
- data/raw/ — données sources, en lecture seule (jamais modifiées)
- data/processed/ — sorties du pipeline

Source brute : indication_paths.yaml (DrugMechDB), téléchargé le 7/8/2026,
depuis https://github.com/SuLab/DrugMechDB

- Dataset chargé : 4 846 chemins mécanistiques (indication_paths.yaml, 7.89 MB)
- Structure racine : liste de dictionnaires
- Clés d'un enregistrement : directed, graph, links, multigraph, nodes
- Volume relationnel : ~32 641 arêtes, soit ≈ 6,74 arêtes par chemin
  (les deux mesures, obtenues indépendamment, sont cohérentes)

- Structure d'un chemin :
    graph  → métadonnées (clés : _id, disease, disease_mesh, drug, drug_mesh, drugbank)
    nodes  → liste d'entités (clés : id, label, name) — le TYPE Biolink est dans `label`
    links  → liste de relations (clés : key, source, target) — le TYPE de relation est dans `key`
             source et target référencent les `id` des nœuds



## Requête PubMed — pilote

Formulation retenue :
  "<médicament>"[Title/Abstract] AND hasabstract AND english[lang]
  AND (mechanism OR receptor OR inhibit* OR bind* OR pathway
       OR regulat* OR activat* OR express* OR "mode of action")[Title/Abstract]

Justification des composantes :
- [Title/Abstract] : sans ce filtre, le médicament est mentionné hors du corps de
  l'article dans la grande majorité des cas (epoprostenol : 13 851 → 1 079, soit -92 %).
- hasabstract : un article sans résumé est inexploitable par le pipeline.
- english[lang] : le modèle d'extraction est anglophone.
- Vocabulaire mécanistique : aligné sur les dix relations du schéma d'extraction,
  couvrant à la fois la liaison moléculaire (premier saut) et la régulation
  biologique (sauts suivants).

Disponibilité mesurée (script scripts/08_disponibilite_pubmed.py), colonne
mécanistique, filtre élargi :
  venlafaxine 2365 | propylthiouracil 1622 | filgrastim 351
  epoprostenol 335 | metolazone 96
Les cinq médicaments du pilote dépassent le seuil de 20-30 abstracts requis.

Calibrage du vocabulaire mécanistique : une première formulation limitée au
vocabulaire de liaison moléculaire (mechanism, receptor, inhibit*, bind*, pathway)
couvrait le premier maillon des chaînes (Drug → Protein) mais non les suivants
(Protein → BiologicalProcess → Disease). L'ajout des termes de régulation
(regulat*, activat*, express*, "mode of action") augmente la disponibilité de 75 %
pour filgrastim, dont le mécanisme est décrit en termes de régulation plutôt que
de liaison. Les quatre autres médicaments, agissant sur des récepteurs ou
transporteurs, gagnent de 8 à 27 %.

## Collecte pilote

Paramètres : 30 abstracts par médicament, 5 médicaments, classement par pertinence
(sort="relevance"), date de collecte 11 août 2026.
Sortie : data/raw/pubmed_pilote.json — le PMID de chaque abstract est conservé.

Justification du classement par pertinence : le pilote vise à établir si les chaînes
de DrugMechDB sont retrouvables dans les abstracts PubMed. Un échantillon aléatoire
ne permettrait pas de distinguer une absence réelle d'un défaut d'échantillonnage ;
le pilote teste donc le meilleur cas, où un résultat négatif serait décisif.
Le classement par pertinence de PubMed n'étant pas reproductible dans le temps,
la liste des PMID retenus est figée dans le fichier de sortie : la collecte est
ainsi rejouable à l'identique indépendamment de l'évolution de l'algorithme.

Résultat : 143 abstracts collectés sur 150 demandés (30 × 5 médicaments).
L'écart de 7 provient d'enregistrements PubMed sans article associé au moment
de la récupération ; aucun résumé vide n'a été rencontré.
Longueur des résumés : 222 mots en moyenne, de 24 à 709 mots.
Date de collecte : 11 août 2026

## Nettoyage du corpus pilote

Script scripts/11_nettoyer_corpus.py — entrée data/raw/pubmed_pilote.json,
sortie data/processed/corpus_pilote.json.

Opérations : suppression du balisage HTML autorisé par PubMed (<b>, <i>, <sup>,
<sub>), normalisation des espaces, filtrage des résumés de moins de 50 mots.

Filtrage par type de document : la requête restreint la collecte aux articles de
recherche ("journal article"[Publication Type]) et exclut commentaires, éditoriaux,
actualités et publications rétractées.

Ce filtre s'est révélé insuffisant sur le cas qui l'avait motivé : un avis
réglementaire de 24 mots (PMID 36813274) est indexé par PubMed comme "journal
article", ayant été publié en revue. Le critère de type de document ne recouvre
donc pas la distinction visée entre contenu scientifique et contenu réglementaire.

Le garde-fou de longueur (plancher de 50 mots) a écarté ce document. Le dispositif
retenu combine ainsi un filtre de principe sur le type de publication et un
garde-fou grossier destiné aux cas non couverts par ce filtre.

L'inspection de la distribution a par ailleurs montré que la longueur n'est pas un
indicateur de richesse en relations : plusieurs résumés de 76 à 115 mots contiennent
des énoncés mécanistiques explicites (ex. PMID 20048460, 111 mots : description du
blocage de la recapture de la sérotonine). Un plancher élevé aurait écarté 18 % du
corpus, dont une partie exploitable.

Répartition temporelle du corpus : 18 % des abstracts sont antérieurs à 2000.
Les résumés anciens étant moins structurés, la qualité d'extraction sur cette
tranche fera l'objet d'un contrôle lors du dry run.

## Collecte ciblée — corpus de travail

Script scripts/25_collecte_ciblee.py, sortie data/raw/pubmed_corpus.json.

Deux composantes :
- Articles ciblés — pour chaque saut de chaque chaîne retenue, les articles contenant
  simultanément le médicament et les deux entités du saut (plafond de 8 par saut),
  identifiés par la même requête que le criblage.
- Distracteurs — 20 articles supplémentaires par médicament, portant sur le même
  médicament sans contenir de saut de chaîne.

Justification du corpus mixte : sans articles ciblés, aucune chaîne n'est
reconstructible et les deux architectures échouent uniformément ; sans distracteurs,
la recherche devient triviale et ne discrimine pas davantage. Les deux pipelines
étant évalués sur un corpus identique, la comparaison demeure équitable. La
restriction porte sur la validité externe : l'étude mesure la performance sur un
corpus où les chaînes sont présentes, non la capacité à les retrouver dans l'ensemble
de la littérature.

Traçabilité : chaque abstract conserve un champ de provenance indiquant s'il porte un
saut de chaîne (et lequel) ou s'il constitue un distracteur. Cette métadonnée est
destinée à l'analyse d'erreurs et n'est exploitée par aucune étape du pipeline —
extraction, indexation, recherche et génération n'y ont pas accès. L'exposer
constituerait une fuite d'information absente en usage réel.

Résultat de la collecte : 526 articles identifiés, 493 récupérés. L'écart de 33
correspond à des enregistrements PubMed sans article associé au moment de la requête
(un seul résumé vide). Répartition : 227 articles porteurs de sauts, 266 distracteurs.
Longueur moyenne des résumés : 214 mots.

Vérification d'intégrité : la perte d'articles entre identification et récupération
peut rompre une chaîne dont un saut ne reposait que sur deux ou trois articles. Le
nombre d'articles effectivement présents est donc recompté saut par saut après
nettoyage (scripts/26_nettoyer_et_verifier.py), une chaîne dont un saut n'est plus
porté par aucun article n'étant plus reconstructible.

Résultat après nettoyage : 483 abstracts (226 porteurs de sauts, 257 distracteurs),
217 mots en moyenne. 63 abstracts contenaient du balisage HTML ; 10 ont été écartés
par le plancher de 50 mots, dont un article ciblé.

Intégrité des chaînes : aucune chaîne rompue. Sur les 16 chaînes retenues, 12
disposent d'au moins trois articles porteurs par saut ; 4 comportent un saut porté
par deux articles seulement (terguride saut 2, lafutidine saut 3, reboxetine saut 1,
desipramine saut 1).

Prédiction consignée avant extraction : les quatre chaînes fragiles présentent un
risque d'échec supérieur aux douze chaînes intactes, l'extracteur ne disposant que de
deux occurrences pour en tirer la relation contre huit dans le cas favorable. Cette
prédiction sera confrontée aux résultats après extraction.

## Environnement de calcul — Google Colab

Configuration : notebook Colab, GPU Tesla T4 (15 360 Mo de mémoire), Ollama installé à
chaque session, modèle qwen2.5:7b.

Justification du modèle : l'énoncé autorise Llama-3.1-8B ou Qwen-2.5-7B. Qwen 2.5 est
retenu pour sa meilleure conformité aux consignes de format, la tâche d'extraction
exigeant une sortie JSON strictement conforme à un schéma imposé.

Contrainte d'exécution : les sessions Colab gratuites ne persistent pas. L'installation
et le téléchargement du modèle (environ dix minutes) sont à refaire à chaque session,
et les scripts de traitement long doivent sauvegarder leur progression de manière
incrémentale afin de pouvoir reprendre après interruption.

Configuration observée lors du dry run : Tesla T4, 15 360 Mo de mémoire, pilote
NVIDIA 580.82.07, CUDA 13.0. GPU entièrement disponible (aucun processus concurrent).

Prérequis d'installation sur Colab : l'image ne fournit ni zstd (requis par le script
d'installation d'Ollama) ni pciutils/lshw (requis pour la détection du GPU au
démarrage du serveur). Ces trois paquets doivent être installés avant Ollama, faute
de quoi le serveur démarre en mode CPU sans erreur apparente. La bonne affectation
est vérifiée par `ollama ps`, dont la colonne PROCESSOR doit indiquer 100% GPU.

Mesure de débit : le premier appel inclut le chargement du modèle en mémoire GPU
(41 s) et l'initialisation CUDA, et n'est pas représentatif. Le débit retenu est
mesuré à chaud, modèle déjà chargé : 34,5 tokens/s en génération.

Comportement à connaître : Ollama décharge le modèle après cinq minutes d'inactivité,
ce qui réintroduit le coût de chargement au appel suivant. Les traitements par lot
doivent donc être enchaînés sans interruption prolongée.

Fragilité du serveur Ollama sous Colab : lancé par subprocess.Popen depuis le noyau
du notebook, le serveur constitue un processus enfant et est terminé par toute
interruption de cellule. Il doit être démarré avec start_new_session=True afin d'être
détaché du groupe de processus du noyau. Le modèle téléchargé n'est pas affecté :
il persiste sur le disque de la machine virtuelle tant que celle-ci est active.

## Correction de la collecte ciblée

Le filtre de vocabulaire mécanistique, construit et calibré lors du pilote, n'avait
pas été reporté dans la requête de collecte ciblée. Les articles porteurs étaient donc
sélectionnés sur la seule co-occurrence des entités, sans garantie que l'article traite
d'un mécanisme. Le diagnostic du dry run a montré que les articles ainsi retenus sont
fréquemment des essais cliniques ou des rapports d'effets indésirables, mentionnant les
entités sans énoncer de relation entre elles.

Correction : la requête ciblée applique désormais le filtre mécanistique en priorité,
avec complément non filtré lorsque le nombre d'articles obtenus reste inférieur au
plafond. Ce dispositif privilégie la qualité sans exposer les chaînes peu documentées
à une rupture. Chaque article porteur conserve l'indication de son mode de sélection
(filtré ou complément), permettant de mesurer a posteriori l'effet du filtre sur la
qualité d'extraction.

Le corpus antérieur est conservé sous data/raw/pubmed_corpus_v1.json à fin de
comparaison. Le dry run sera relancé sur le nouveau corpus sans modification du prompt,
afin d'isoler l'effet de la correction de collecte de celui d'un éventuel ajustement
ultérieur du prompt.

Éphémérité constatée : une session Colab peut être recyclée sans notification, la
machine virtuelle étant remplacée. Les fichiers téléversés et le modèle téléchargé
sont alors perdus, alors même que le notebook et son noyau demeurent apparemment
actifs. La vérification préalable à tout traitement porte donc sur l'état effectif
de l'environnement (présence des fichiers, réponse du serveur Ollama) et non sur
l'apparence de la session.

Ordre d'installation vérifié : lorsque pciutils et lshw sont installés avant Ollama,
l'installeur détecte le GPU et l'annonce explicitement (« NVIDIA GPU installed. »),
là où l'installation dans l'ordre inverse produisait un avertissement de non-détection.
L'ordre des opérations conditionne donc l'affectation du GPU.

Résultat après correction : 475 abstracts (208 porteurs de sauts, 267 distracteurs),
collectés le 16 août 2026. Les chiffres antérieurs (526 identifiés, 493 récupérés,
483 après nettoyage) portent sur la collecte v1 du même jour, conservée sous
data/raw/pubmed_corpus_v1.json.

## Extraction complète

Prompt gelé dans la version validée par la troisième itération du dry run. Les
variantes de prédicat non couvertes par la table de correspondance (« competitively
inhibits », observée au contrôle imatinib) sont traitées par une étape de récupération
postérieure à l'extraction plutôt que par une modification du prompt : celle-ci
romprait la correspondance entre le prompt mesuré et le prompt exécuté, et n'anticiperait
que les variantes déjà rencontrées. La récupération ramène tout prédicat hors schéma
contenant un prédicat du schéma à ce dernier, et le nombre de relations ainsi
récupérées est comptabilisé.

Dispositif de reprise : les résultats sont écrits au format JSONL, une ligne ajoutée
après chaque abstract, sur Google Drive monté dans la session. Une interruption ne
perd que l'abstract en cours ; la relance détecte les identifiants déjà traités et
reprend à la suite. Le stockage sur Drive est nécessaire, le système de fichiers local
de Colab ne survivant pas à la fin de session.

Un appel de chauffe précède la boucle et n'est pas chronométré : le premier appel
inclut le chargement du modèle en mémoire GPU, mesuré à 97 secondes lors du contrôle
imatinib contre 2 à 10 secondes en régime établi.

Extraction complète réalisée en une session : 475 abstracts traités en 34,7 minutes,
soit 4,4 secondes par abstract, sans interruption. Le dispositif de reprise n'a pas
eu à être mobilisé. Le débit observé est conforme à l'estimation du dry run.

## Inventaire de l'extraction

985 relations extraites sur 475 abstracts, soit 2,1 par abstract. 177 abstracts
(37 %) n'ont produit aucune relation, 6 sorties JSON n'ont pu être analysées.
871 entités textuelles distinctes.

Conformité au schéma : 84 % (829 relations sur 985), mesure établie sur l'ensemble du
corpus. Le taux de 96 % observé au dry run portait sur huit abstracts et vingt-huit
relations, effectif trop faible pour être représentatif.

Les 156 relations non conformes se répartissent en trois familles :
- Variantes lexicales d'un prédicat du schéma (« inhibits », « blocks »,
  « competitively inhibits », « negatively correlates with ») : environ 90 relations,
  récupérables par correspondance.
- Reprise littérale de la colonne source de la table de correspondance du prompt
  (« is associated with higher levels or greater severity », « is involved in ») :
  environ 12 relations. Le modèle a produit la formulation à traduire au lieu de
  l'étiquette cible, la mise en forme de la table ne distinguant pas assez nettement
  les deux colonnes.
- Prédicats sans équivalent dans le schéma : relations cliniques volontairement
  exclues (« treats », « improves », « prevents ») et énoncés de négation
  (« does not affect », « does not mitigate »).

Les énoncés de négation révèlent une limite de conception du schéma : les dix
prédicats retenus expriment tous un lien effectif, positif ou négatif, sans permettre
de représenter une absence de relation. Ces relations sont supprimées et non
converties, une conversion inversant le sens du texte source.

Deux difficultés de normalisation apparaissent dès l'inventaire : la casse sépare une
même entité en deux occurrences distinctes (« finasteride » et « Finasteride »), et
les mentions parenthétiques (« serotonin transporter (SERT) ») ne correspondent à
aucune forme des tables de synonymes.

Trois définitions de la conformité coexistent dans ce journal, et les trois chiffres
correspondants sont exacts sous leur propre définition
(scripts/55_trancher_conformite.py) :

  829  prédicat au schéma, sans considération des types d'entités  (script 32)
  822  prédicat au schéma et aucun type manquant                    (script 33)
  820  prédicat au schéma et les deux types parmi les sept retenus  (contrôle 55)

Le chiffre retenu est 822, soit 83 %, définition employée par l'étape de récupération
qui produit le fichier exploité en aval. Les mentions de 829 relations conformes et de
156 non conformes figurant plus haut dans cette section relèvent de la première
définition et doivent être lues comme telles.

Les neuf relations séparant la définition la plus large de la plus stricte révèlent
deux défauts du modèle que le contrôle de conformité ne détecte pas.

Types inventés : deux relations portent le type « Enzyme », absent du schéma
(finasteride et dutasteride vers la 5α-réductase). Leur type étant présent, elles sont
conservées dans le graphe. Le filtre excluant les arêtes reliant deux médicaments
s'appuyant sur les types, une entité typée hors schéma lui échappe par construction.

Nom du type recopié à la place du nom de l'entité : trois relations ont pour source le
mot littéral « Drug ». C'est le même défaut que la reprise de la colonne source de la
table de correspondance, transposé au champ entité. Ces trois relations sont écartées
par le contrôle de type manquant.

## Récupération des prédicats

Trois mécanismes appliqués aux 156 relations non conformes :
- Correspondance directe pour les variantes de conjugaison et les formulations
  reprises de la colonne source de la table du prompt ;
- Correspondance conditionnée par le type de la cible pour les verbes d'action, selon
  la même règle que le prompt : activity of pour une protéine, regulates pour un
  processus, abundance of pour une substance ;
- Suppression pour les énoncés de négation et les prédicats cliniques sans équivalent
  dans le schéma.

Aucun prédicat n'est rattaché par approximation : ce qui n'est pas explicitement
recensé est écarté et journalisé. Chaque relation conservée mémorise son prédicat
d'origine, ce qui permet de retracer toute arête du graphe et de mesurer l'apport de
la récupération.

Récupération des prédicats : 113 relations récupérées sur 156 non conformes, portant
le taux de conservation de 84 % à 94 % (935 relations sur 985). Écartées : 36 relations
à prédicat sans équivalent dans le schéma (« treats », « targets », « improves »,
majoritairement de nature clinique), 4 énoncés de négation, 10 relations à type
d'entité manquant.

Diagnostic des abstracts sans relation : 177 au total, dont 120 distracteurs (44 % de
cette catégorie) et 57 articles ciblés (27 %). L'écart confirme l'effet du ciblage,
les articles sélectionnés pour porter un saut produisant nettement plus de relations
que les distracteurs.

Les sauts dont les articles porteurs sont restés vides relèvent majoritairement du
schéma « processus biologique vers maladie » avec le prédicat « positively correlated
with » — configuration identique à celle qui a fait échouer la chaîne imatinib. Ce
constat porte toutefois sur le nombre d'articles vides et non sur la reconstructibilité
effective des sauts, mesurée séparément.

## Pipeline A — RAG vectoriel

Unité de récupération : l'abstract entier, titre et résumé concaténés. Aucun découpage
n'est appliqué : la longueur moyenne des résumés, estimée à ce stade à environ
300 tokens et mesurée ultérieurement à 385, tient largement dans la fenêtre de
contexte, et l'abstract constitue une unité sémantique cohérente qu'un découpage
fragmenterait. Ce choix rend en outre la comparaison à la vérité terrain directe, une
unité récupérée correspondant exactement à un identifiant PubMed.

Modèles d'embedding comparés : pritamdeka/S-PubMedBert-MS-MARCO, version de PubMedBERT
entraînée pour la recherche sémantique, et sentence-transformers/all-MiniLM-L6-v2,
modèle généraliste de référence. PubMedBERT dans sa version d'origine est un modèle de
langue et non un encodeur de phrases ; son emploi direct produirait des représentations
inadaptées à la recherche.

Les vecteurs sont normalisés, la similarité cosinus se réduisant alors à un produit
scalaire.

Métrique retenue à ce stade : le rappel de récupération au rang 5, mesuré avant toute
génération. L'étude portant sur la méthode de récupération, l'isoler de l'étape de
génération évite d'imputer à l'architecture un écart provenant du modèle générateur.

## Pipeline A — premiers résultats de récupération

Index construits sur 475 abstracts, sans découpage. Modèle biomédical
(S-PubMedBert-MS-MARCO) : 768 dimensions, 23 secondes. Modèle généraliste
(all-MiniLM-L6-v2) : 384 dimensions, 10 secondes.

Rappel au rang 5 :
                     biomédical   généraliste
  global                0,55         0,49
  single-hop            0,67         0,67
  pont                  0,50         0,33
  intersection          0,44         0,35

Deux observations. Le modèle biomédical n'apporte aucun gain sur les questions à un
saut mais un écart net sur les questions multi-hop, où le vocabulaire spécialisé
paraît déterminant. Et le rappel décroît du single-hop au multi-hop pour les deux
modèles, conformément à l'hypothèse sur la faiblesse de la recherche par similarité
face aux requêtes exigeant plusieurs documents.

Le rappel de 0,67 sur les questions de contrôle demeure toutefois inférieur à ce
qu'on attend d'un témoin : une question à un saut porte sur un document unique et
connu, que cinq résultats devraient presque toujours contenir. Trois causes sont à
départager avant toute comparaison avec le Pipeline B : une faiblesse réelle de la
récupération, une troncature des abstracts dépassant la fenêtre de 512 tokens des
modèles d'embedding, ou une vérité terrain trop étroite, plusieurs abstracts pouvant
attester la même relation sans que tous soient enregistrés.

Mesure de la longueur des abstracts en tokens (scripts/46_mesurer_tokens.py) :
385 tokens en moyenne, 1729 au maximum, pour un ratio de 1,67 token par mot. Ce ratio
est supérieur à celui de l'anglais courant, la nomenclature biomédicale, les
abréviations et les valeurs numériques se décomposant en plusieurs tokens.

82 abstracts sur 475, soit 17 % du corpus, dépassent la fenêtre de 512 tokens des
modèles d'embedding et sont donc tronqués silencieusement à l'indexation. Le plus long
perd environ 70 % de son contenu. Aucun n'atteint la fenêtre de 4096 tokens employée
pour l'extraction, ce qui confirme que le choix de ne pas découper était fondé pour
cette étape et ne l'est pas nécessairement pour l'indexation vectorielle.

Précision méthodologique : ce comptage emploie le tokeniseur de Qwen, celui de
l'extraction. Le tokeniseur des modèles d'embedding, qui détermine effectivement la
troncature à l'indexation, en dénombre environ 10 %. La proportion pertinente pour le
pipeline vectoriel est donc cette dernière ; chaque modèle segmente le texte selon son
propre vocabulaire.

Révision ultérieure (notebook 61) : la fenêtre du modèle d'encodage retenu n'est pas de
512 tokens mais de 350, valeur inscrite dans sa configuration. Mesurée avec son propre
tokeniseur, la longueur moyenne des résumés est de 330 tokens, et 166 d'entre eux sur
475 — soit 35 % — dépassent la limite. Les chiffres ci-dessus, 385 tokens en moyenne et
82 abstracts au-delà de 512, relèvent du tokeniseur de Qwen et d'une fenêtre supposée ;
ils sont conservés comme trace de l'état des connaissances à cette étape.

## Diagnostic des échecs de récupération

L'hypothèse d'une troncature à 512 tokens est écartée. Les documents attendus mais non
récupérés comptent 358 tokens en moyenne contre 348 pour ceux qui le sont, et 5 % sont
tronqués contre 6 %. Les deux populations sont indiscernables sur ce critère.

Révision ultérieure : cette comparaison repose sur une fenêtre supposée de 512 tokens,
qui est erronée : la configuration du modèle d'encodage fixe max_seq_length à 350. Le
tokeniseur employé est en revanche le bon — le script 47 compte avec celui de
l'encodage, et c'est le script 46 qui compte avec celui de Qwen. La réfutation a été
refaite par intervention
directe (notebook 61) : en restreignant l'indexation à la partie que la baseline lisait
réellement, le rappel au rang 5 demeure inchangé. La conclusion tient ; son fondement a
changé.

La lecture des cas d'échec fait apparaître une autre cause. Les documents manqués sont
ceux dont l'entité recherchée n'est pas le sujet principal : la question SH07 porte sur
le sarpogrelate, absent du titre du document attendu et cité deux fois dans le
corps du résumé parmi d'autres antagonistes. Les trois documents attendus de la question
MH05 ne nomment ni le ranibizumab ni le ramucirumab dans leur titre.

Une entité mentionnée une fois dans un texte de 350 tokens contribue faiblement au
vecteur qui représente ce texte. La recherche vectorielle sélectionne les documents
dont le sujet global ressemble à la question, non ceux qui contiennent l'information
cherchée. Ce phénomène de dilution constitue une limite structurelle de l'indexation
par document entier, et non un défaut d'implémentation.

Choix de conception assumé : la baseline conserve l'abstract entier comme unité de
récupération. Un découpage en passages plus courts améliorerait vraisemblablement le
rappel, une entité isolée pesant davantage dans un segment de cent tokens que dans un
abstract complet. Ce découpage n'est pas mis en œuvre, la baseline visant une
implémentation standard telle qu'un praticien la réaliserait par défaut ; l'écart
correspondant est signalé comme limite plutôt que dissimulé.

Révision ultérieure : ce découpage a été mis en œuvre après coup, comme mesure séparée
(notebook 61). Il porte le rappel au rang 5 de 0,55 à 0,60 et 0,62 selon la granularité,
sans combler l'écart au graphe. La baseline de la comparaison principale demeure
l'abstract entier.

## Pipeline B — Graph RAG

Le graphe est construit à partir des 935 relations extraites, chaque entité canonisée
formant un nœud et chaque relation une arête portant son identifiant PubMed d'origine.
L'exécution ne requiert aucun GPU : le graphe est une structure de données et la
traversée un parcours d'index, là où le pipeline vectoriel exige le calcul
d'embeddings.

Trois étapes : ancrage de la question sur les nœuds du graphe par appariement des
groupes de mots, du plus long au plus court ; traversée du voisinage à deux sauts ;
remontée des arêtes atteintes vers les documents qui les portent, ce qui permet
d'évaluer les deux pipelines sur le même étalon.

La traversée ignore l'orientation des arêtes. Les chemins de type intersection
exigent en effet de remonter du médicament vers la cible partagée puis de redescendre
vers un second médicament, ce qu'un parcours orienté interdirait.

Pondération du classement des documents : une arête atteinte au premier saut compte
pour 1, au second pour 0,5 ; une arête incidente à un nœud d'ancrage voit son poids
doublé. Ces valeurs constituent un choix de conception et non une propriété du
dispositif ; elles n'ont pas été optimisées sur le jeu de test, ce qui reviendrait à
ajuster le système aux questions servant à l'évaluer.

L'ancrage constitue le point de fragilité du pipeline : une question dont aucune
entité n'est appariée à un nœud produit un rappel nul indépendamment de la qualité du
graphe. Le nombre de questions non ancrées est donc rapporté séparément.

## Résultats comparés de récupération (rappel au rang 5)

                      Vectoriel    Graphe
  Global                 0,55       0,83
  Single-hop             0,67       1,00
  Pont                   0,50       0,67
  Intersection           0,44       0,71

Le pipeline par graphe surpasse le pipeline vectoriel sur les trois catégories de
questions. L'écart est maximal sur les intersections, où il atteint 0,27 point, soit
une amélioration relative de 61 %.

L'avantage n'est toutefois pas imputable à la seule capacité de traversée : le graphe
l'emporte également sur les questions à un saut, qui n'en requièrent aucune. Deux
mécanismes distincts y contribuent. L'absence de dilution joue sur toutes les
catégories : le graphe indexe des relations et non des documents, de sorte qu'une
entité citée une seule fois dans un résumé conserve le même poids qu'une entité
centrale. La capacité de traversée joue spécifiquement sur les questions multi-hop et
explique que l'écart y soit plus marqué. Attribuer l'intégralité de l'écart à la
traversée constituerait une erreur d'interprétation.

Révision ultérieure : deux points de ce paragraphe ont été corrigés depuis. L'écart
maximal n'est pas celui des intersections mais celui des questions à un saut (+0,33),
la mesure ci-dessus étant antérieure à la correction de la translittération. Et une
entité citée une fois ne conserve pas « le même poids » qu'une entité centrale : elle
reste atteignable par son nom, ce qui suffit à expliquer l'écart. L'ablation rapportée
en section 8.8 du rapport attribue 91 % de l'écart à l'ancrage seul, là où ce paragraphe
proposait une attribution partagée entre dilution et traversée.

Modes d'échec propres à chaque architecture :
- Le pipeline vectoriel échoue lorsque l'entité recherchée n'est pas le sujet
  principal du document, son vecteur reflétant le contenu global du texte.
- Le pipeline par graphe échoue lorsque l'ancrage de la question ne parvient pas à
  identifier de nœud (question SH04, dont l'entité s'écrit « β-elemene » dans le
  graphe et « beta-elemene » dans la question), lorsque l'ancrage porte sur une entité
  différente de celle qui conduit à la réponse (MH01, ancrée sur la paroxétine sans
  apparier le CYP2D6), ou lorsque le nœud d'ancrage présente un degré très élevé et
  noie les documents pertinents sous le volume d'arêtes atteintes (MH08, 195 arêtes).

Les deux architectures présentent donc des faiblesses structurelles distinctes, ce qui
constitue un résultat d'analyse au-delà de la seule comparaison des scores.

## Rappel selon le nombre de documents récupérés

  K        Vectoriel    Graphe    Écart
   1          0,38       0,45     +0,08
   3          0,53       0,78     +0,26
   5          0,55       0,83     +0,28
  10          0,60       0,88     +0,28
  20          0,77       0,95     +0,18

Mesure établie après correction de la translittération des caractères grecs.

Le pipeline par graphe domine à toutes les valeurs de K. Le résultat ne dépend donc
pas du choix du budget documentaire, ce qui écarte l'objection d'un écart obtenu par
un réglage favorable.

Budget documentaire équivalent : le graphe atteint un rappel de 0,83 avec cinq
documents, niveau que le pipeline vectoriel n'atteint pas même en récupérant cinquante
documents. Les documents manqués ne sont pas mal classés mais absents du classement :
la dilution les rend invisibles à la recherche par similarité plutôt qu'elle ne les
relègue.

L'écart culmine entre K = 5 et K = 10, à 0,28 point, et se resserre de part et d'autre.
À K = 1, le budget documentaire est trop restreint pour qu'une question multi-hop soit
résoluble par l'une ou l'autre architecture. À K = 20, le pipeline vectoriel finit par
rattraper une partie de son retard.

Comportement contrasté selon la catégorie de question : à K = 1, les deux pipelines
obtiennent des scores strictement identiques sur les intersections (0,25) mais non sur
les questions à un saut, où le graphe l'emporte déjà de 0,11 point.

Cette dissociation est instructive. Sur les intersections, aucune des deux architectures
ne peut réussir avec un document unique, la question exigeant par construction deux
documents distincts : l'égalité y traduit une impossibilité commune. Sur les questions
à un saut, en revanche, un document suffit, et le graphe le place mieux — non par
capacité de traversée, qui n'est pas sollicitée, mais par absence de dilution.

Sur les questions de type pont, l'écart demeure rigoureusement constant à 0,17 point
pour toutes les valeurs de K testées : le pipeline vectoriel ne rattrape jamais son
retard, quel que soit le nombre de documents qu'on lui accorde. Cette régularité a
survécu à la correction de la translittération, ce qui la rend moins susceptible d'être
un artefact de mesure. L'observation porte néanmoins sur trois questions et appelle
réserve.

Révision ultérieure (script 65) : au rang 10, cette constance dépend du départage des
égalités. Selon l'ordre retenu entre documents de même poids, le rappel du graphe y vaut
de 0,83 à 1,00, soit un écart compris entre 0,17 et 0,33. La valeur publiée est celle du
cas le moins favorable au graphe.

Portée pratique : l'avantage du graphe est pour une part un avantage d'efficacité. Il
obtient avec peu de documents ce que le pipeline vectoriel n'obtient qu'avec beaucoup,
voire jamais. Cette nuance importe, vingt abstracts de 385 tokens excédant la fenêtre
exploitable d'un modèle de sept milliards de paramètres.

## Coût de construction et d'exploitation

                            Vectoriel        Graphe
  Extraction des relations       —          35 min GPU
  Indexation                  1 min GPU      quelques secondes, sans GPU
  Requête                     GPU requis     parcours d'index, sans GPU
  Total de construction       1 min          35 min

Le pipeline par graphe exige trente-cinq fois plus de calcul à la construction, cette
charge provenant intégralement de l'extraction des relations, qui requiert un appel au
modèle de langue par document. Cette étape appartient au pipeline de données en amont
et doit être imputée au coût du graphe, faute de quoi la comparaison omettrait
l'essentiel de son surcoût.

En contrepartie, le graphe s'interroge sans accélérateur matériel, là où le pipeline
vectoriel requiert un GPU pour encoder chaque question, et atteint avec cinq documents
un rappel que le pipeline vectoriel n'atteint pas avec cinquante.

L'arbitrage est donc celui d'un coût initial élevé contre un coût d'exploitation
faible : le surcoût du graphe se justifie pour un corpus stable et fréquemment
interrogé, et ne se justifie pas pour un corpus renouvelé en permanence, dont la
reconstruction du graphe devrait être répétée.

## Asymétrie du recours au modèle de langue

Le modèle de langue n'intervient pas de façon symétrique dans les deux pipelines. Le
graphe est intégralement construit par extraction automatique au moyen de Qwen 2.5 7B,
tandis que l'index vectoriel n'en fait aucun usage : il repose sur un modèle
d'embedding, qui produit des représentations et ne génère pas de texte.

La performance du pipeline par graphe dépend donc de la qualité de cette extraction,
dont la relecture manuelle a établi qu'elle comporte 21 % d'inversions de polarité sur
les chemins examinés. Un extracteur différent produirait un graphe différent et,
vraisemblablement, un résultat différent.

Portée du résultat : la comparaison établie porte sur un couple architecture-extracteur
— un graphe extrait par un modèle local de sept milliards de paramètres, opposé à un
index vectoriel construit sur S-PubMedBert — et non sur les architectures considérées
indépendamment de leur mise en œuvre.

Sens du biais : une extraction imparfaite dégrade le graphe en y introduisant des
arêtes erronées, sans affecter l'index vectoriel. Le biais joue donc contre l'hypothèse
testée. Le pipeline par graphe l'emporte malgré ce handicap, ce qui rend la mesure
conservatrice : un extracteur plus fiable creuserait vraisemblablement l'écart plutôt
qu'il ne le réduirait.

Le recours symétrique au modèle de langue concerne les deux étapes ultérieures — la
génération des réponses et l'évaluation automatique par RAGAS — où le même modèle est
appliqué aux sorties des deux pipelines, seuls les documents fournis différant.

## Correction — translittération des caractères grecs

La fonction de canonisation des noms d'entités ne translittérait pas les caractères
grecs. Une entité écrite « β-elemene » dans le graphe et « beta-elemene » dans une
question produisait deux formes canoniques distinctes, empêchant tout appariement.
Ce défaut a été identifié à l'analyse de la question SH04, pour laquelle le pipeline
par graphe ne récupérait aucun document.

Correction appliquée à l'étape d'ancrage : la fonction translittère désormais
l'alphabet grec complet avant toute autre normalisation, l'ordre important puisque le
filtrage ultérieur des caractères non latins supprimerait sinon la lettre grecque.

Portée de la correction : elle est limitée à l'ancrage des questions sur le graphe,
étape située en aval de la constitution du jeu de test. La vérité terrain demeure donc
inchangée, ce qui distingue cette correction d'un ajustement du système aux questions
servant à l'évaluer. Le défaut corrigé existait indépendamment du jeu de test employé.

Différence structurelle mise en évidence : le pipeline par graphe repose sur un
appariement exact de chaînes de caractères et se trouve donc sensible aux variations
orthographiques, là où le pipeline vectoriel opère sur des représentations continues
qui absorbent ces variations. Aucune correction symétrique n'est applicable au pipeline
vectoriel, qui n'emploie pas de canonisation.

Résultats avant et après correction de la translittération :
  Rappel@5 du pipeline par graphe, sans translittération : 0,78
  Rappel@5 du pipeline par graphe, avec translittération : 0,83
  Rappel@5 sur les questions à un saut : 0,89 puis 1,00
Le graphe compte 792 nœuds après correction contre 794 auparavant, deux paires
d'entités ayant fusionné.

## Résultats de génération

Le même modèle (qwen2.5:7b, température nulle, fenêtre de 8192 tokens) est appliqué
aux documents récupérés par chacun des deux pipelines, seul le contexte fourni
différant.

                    Vectoriel    Graphe
  Exactitude           0,30       0,70
  Abstention           0,50       0,15
  Latence moyenne      2,8 s      2,9 s

  single-hop           0,44       0,78
  pont                 0,00       0,67
  intersection         0,25       0,62

L'écart d'exactitude (0,40) excède l'écart de rappel mesuré à l'étape de récupération
(0,28). Un défaut de récupération ne se rattrape pas à la génération : le pipeline
vectoriel s'abstient dans la moitié des cas, non par erreur mais faute de disposer des
documents nécessaires. Le prompt prévoyant une réponse explicite d'abstention, le
modèle signale l'absence d'information plutôt que de l'inventer.

Les latences sont équivalentes, les deux pipelines fournissant un volume de contexte
comparable. L'avantage du graphe ne porte donc pas sur le coût de génération.

Portée de la métrique d'exactitude : une réponse est comptée correcte dès lors qu'elle
contient l'une des formulations acceptables, y compris dans sa justification. La
mesure est donc permissive : la réponse SH03 du pipeline par graphe est validée par la
présence de « platelet aggregation » dans la phrase de justification et non dans la
réponse principale. Ce choix évite de pénaliser des reformulations correctes, au prix
d'une tolérance qu'il convient d'énoncer.

Deux cas d'analyse :

La question SH04 illustre une erreur de génération et non de récupération : les deux
pipelines récupèrent le document attendu et produisent tous deux une réponse erronée
(voie de signalisation NRF2/HMOX1 au lieu de la ferroptose). Le dispositif distingue
donc bien les deux étapes.

La question MH09 constitue le seul cas où le pipeline vectoriel l'emporte nettement.
La question ne nomme aucun médicament — elle demande quel inhibiteur sélectif de la
recapture de la sérotonine agit également sur le transporteur de la noradrénaline. Le
graphe s'ancre sur deux processus et n'atteint jamais le document pertinent. Ce mode
d'échec est propre à l'architecture par graphe : lorsqu'une question ne comporte que
des concepts et aucune entité nommée saillante, l'ancrage oriente la traversée dans
une direction improductive.

## Évaluation par juge — fidélité et pertinence

Les deux métriques suivent les définitions de RAGAS mais sont réimplémentées plutôt
qu'importées de la bibliothèque. Celle-ci suppose l'accès à un modèle distant, ce que
la contrainte de budget nul interdit, et masque le prompt de jugement employé. Une
réimplémentation rend ce prompt explicite et donc rapportable.

Le jugement est produit sur une échelle discrète à cinq niveaux, ramenée à l'intervalle
[0,1] par division par quatre. Un modèle de sept milliards de paramètres ne produit pas
de score continu de façon reproductible ; restreindre la granularité à ce que le juge
peut effectivement tenir évite de recueillir du bruit.

Stabilité du juge : chaque réponse a été évaluée trois fois. L'écart maximal entre les
trois jugements est en moyenne de 0,01 pour la fidélité et nul pour la pertinence ;
39 jugements sur 40 sont parfaitement stables pour la première, 40 sur 40 pour la
seconde. La réserve formulée a priori sur l'instabilité d'un juge de petite taille
n'est pas confirmée par la mesure.

                    Vectoriel    Graphe
  Fidélité             0,86       0,81
  Pertinence           0,60       0,76
  Exactitude           0,30       0,70

  single-hop  fidélité 0,81       0,81
              pertinence 0,69     0,86
  pont        fidélité 0,92       0,75
              pertinence 0,42     0,58
  intersection fidélité 0,91      0,83
              pertinence 0,56     0,72

Le pipeline vectoriel obtient une fidélité supérieure à celle du pipeline par graphe.
Ce résultat s'explique par son taux d'abstention : s'abstenir lorsque les documents ne
contiennent pas l'information constitue un comportement fidèle et reçoit la note
maximale. Un système qui répond rarement est mécaniquement fidèle.

La métrique de fidélité, prise isolément, récompense donc le silence. Les questions de
type pont l'illustrent : le pipeline vectoriel y obtient sa meilleure fidélité (0,92)
alors que son exactitude y est nulle. Cette observation porte sur trois questions et
vaut comme illustration, non comme mesure.

Les trois métriques doivent être lues conjointement : la fidélité mesure l'absence
d'invention, la pertinence l'adéquation à la question, l'exactitude la justesse de la
réponse. Le pipeline vectoriel apparaît prudent — il n'invente pas mais répond peu — et
le pipeline par graphe utile : il répond plus souvent et plus souvent correctement.

## Tableau de bord comparatif

Interface Streamlit (dashboard.py, à la racine du dépôt), lancée par
`streamlit run dashboard.py`. Deux vues : une comparaison question par question,
affichant côte à côte la réponse de chaque pipeline, ses métriques et les documents
qu'il a récupérés, et une vue d'ensemble reprenant les agrégats globaux et par
catégorie.

L'interface restitue des résultats précalculés plutôt que de les générer à la demande.
La génération requiert un accélérateur matériel absent du poste de démonstration, et
cette conception garantit en outre que les valeurs affichées coïncident exactement avec
celles du rapport.

Les documents attendus par la vérité terrain sont signalés parmi les documents
récupérés, ce qui rend visible le mécanisme de l'écart : le pipeline vectoriel affiche
fréquemment cinq documents dont aucun n'est attendu, tandis que le pipeline par graphe
en place généralement un ou deux en tête de classement.

Le fichier requirements.txt, généré à la racine du dépôt, fige les versions exactes
de l'ensemble des dépendances et permet de reconstituer l'environnement à l'identique.
Les dépendances propres à l'exécution sur Colab (sentence-transformers, torch) y
figurent lorsqu'elles ont également été installées localement ; celles installées
uniquement dans les notebooks sont mentionnées dans la section relative à
l'environnement de calcul.