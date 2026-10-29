*[English version](README.md)*
# Vector RAG vs Graph RAG — inférence multi-hop sur corpus biomédical

**[Démonstration en ligne](https://vector-rag-vs-graph-rag.streamlit.app)** — le tableau de bord comparatif, sans installation. Hébergé sur Streamlit Community Cloud ; l'application s'endort après quelques jours sans visite et met quelques secondes à se réveiller.

Comparaison contrôlée de deux architectures de génération augmentée par récupération sur des questions exigeant la mise en relation de plusieurs documents, avec le pipeline d'ingénierie de données qui les alimente.

Stage de recherche — Laboratoire d'Intelligence Artificielle, Ingénierie des Données et Applications (LR21ES23), Faculté des Sciences de Bizerte, Université de Carthage.

---

## Résultat

Sur un corpus de 475 résumés PubMed et un jeu de 20 questions vérifiées manuellement, la recherche par traversée de graphe surpasse la recherche vectorielle sur toutes les métriques mesurées.

| | Vectoriel | Graphe |
|---|---|---|
| Rappel au rang 5 (Context Recall) | 0,55 | **0,83** |
| Exactitude de la réponse | 0,30 | **0,70** |
| Pertinence (Answer Relevance) | 0,60 | **0,76** |
| Fidélité (Faithfulness) | **0,86** | 0,81 |

**Le graphe atteint avec cinq documents un niveau de rappel que la recherche vectorielle n'atteint pas avec cinquante.** L'écart se maintient à toutes les valeurs du budget documentaire testées.

Ces chiffres opposent le graphe à une baseline vectorielle standard. Trois baselines plus exigeantes ont été ajoutées ensuite — un découpage en passages, une baseline lexicale BM25, et la recherche de LightRAG conduite sur notre propre graphe. Elles situent l'origine de l'écart et en bornent la portée : les sections 8.9 à 8.11 du rapport les détaillent.

Trois résultats distincts de cette comparaison :

**Une base de mécanismes curée n'est pas reconstructible à partir de résumés d'articles.** Aucune des quinze chaînes de DrugMechDB retenues n'a pu être retrouvée dans le graphe extrait. La littérature comprime les chaînes causales et présuppose les liens établis : sur 935 relations extraites, 36 seulement ont une maladie pour cible.

**L'avantage du graphe ne vient pas de la traversée.** L'écart est maximal sur les questions à un saut, qui n'en requièrent aucune, et une ablation attribue 91 % de cet écart à l'ancrage seul. Le mécanisme dominant est l'absence de dilution : ce qui compte est d'aller chercher les documents par l'entité plutôt que par un vecteur global. Une baseline lexicale en récupère les trois quarts sans aucun graphe, et LightRAG, sur notre propre graphe, retombe au niveau vectoriel dès qu'il classe les documents par ressemblance.

**La métrique de fidélité, employée seule, récompense le silence.** Le pipeline le moins performant y obtient le meilleur score, grâce à son taux d'abstention de 50 %.

Le [rapport complet](docs/rapport-stage.md) détaille la méthode, les résultats et leurs limites.

---

## Architecture

```
Pipeline 0   Collecte PubMed → nettoyage → extraction de relations par LLM
                                                    │
                         ┌──────────────────────────┴───────────────────┐
                         ▼                                              ▼
Pipeline A   Index vectoriel (S-PubMedBert)          Pipeline B   Graphe de connaissances
             recherche par similarité                             ancrage + traversée à 2 sauts
                         │                                              │
                         └──────────────────────────┬───────────────────┘
                                                    ▼
                                         Évaluation comparative
                                    récupération · génération · RAGAS
```

**Pipeline 0** collecte les résumés via l'API E-utilities du NCBI, les nettoie, puis en extrait des triplets entité-relation-entité au moyen d'un modèle de langue local, selon un schéma de 7 types d'entités et 10 relations dérivé de DrugMechDB.

**Pipeline A** encode chaque abstract entier et répond par similarité cosinus.

**Pipeline B** construit un graphe de 792 nœuds et 932 arêtes, ancre la question sur ses nœuds, traverse le voisinage à deux sauts et remonte aux documents porteurs. Il ne requiert aucun GPU.

---

## Démarrage rapide

### Prérequis

Python 3.12, environ 2 Go d'espace disque. Aucun service payant ni clé d'API.

```bash
git clone https://github.com/malektlili-eng/stage-graphrag.git
cd stage-graphrag
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux et macOS
pip install -r requirements.txt
```

### Explorer les résultats

```bash
streamlit run dashboard.py
```

Le tableau de bord affiche, pour chacune des vingt questions, les réponses des deux pipelines côte à côte, les documents que chacun a récupérés, et les métriques associées. Les documents attendus par la vérité terrain y sont signalés, ce qui rend visible le mécanisme de l'écart.

L'interface restitue des résultats précalculés. La génération requiert un GPU et a été exécutée séparément.

### Rejouer une mesure

Le pipeline par graphe s'exécute sans accélérateur matériel :

```bash
python scripts/48_pipeline_graphe.py      # rappel du Pipeline B
python scripts/49_courbe_rappel.py        # rappel selon le budget documentaire
python scripts/62_comparaison_baselines.py  # toutes les baselines et les tests appariés
python scripts/65_robustesse_egalites.py    # sensibilité des rappels aux égalités de score
```

Les étapes exigeant un GPU — extraction des relations, encodage vectoriel, génération, jugement — se trouvent dans `notebooks/`, prêtes à être exécutées sur Google Colab en offre gratuite.

---

## Données

### Contenu

| Fichier | Contenu |
|---|---|
| `data/raw/indication_paths.yaml` | DrugMechDB, 4 846 chemins mécanistiques (CC0), téléchargé le 7 août 2026 |
| `data/raw/pubmed_corpus.json` | 475 résumés PubMed collectés le 16 août 2026 |
| `data/processed/relations_nettoyees.json` | 935 relations extraites et normalisées |
| `data/processed/baseline_*.json` | classements des baselines supplémentaires (notebooks 61, 64 et 66, script 62) |
| `data/processed/jeu_de_test.json` | 20 questions avec réponses attendues et documents sources |

### Provenance et droits

Le corpus rassemble 475 résumés d'articles récupérés via l'API E-utilities du NCBI. Ces résumés sont redistribués ici à seule fin de reproductibilité de l'étude. La National Library of Medicine ne détient pas les droits sur les résumés PubMed, qui demeurent la propriété de leurs éditeurs respectifs. Aucun usage commercial n'est prévu ni autorisé. Tout éditeur souhaitant le retrait d'un contenu peut en faire la demande via les issues du dépôt.

Les identifiants PubMed de l'ensemble du corpus étant figés dans `data/raw/`, la collecte demeure rejouable à l'identique sans recourir à ce fichier.

DrugMechDB est publié sous licence CC0 1.0 Universal — domaine public, aucune restriction.

> Gonzalez-Cavazos et al. (2023). *DrugMechDB: A Curated Database of Drug Mechanisms.* Scientific Data 10(1), 632.

---

## Le jeu de test

Vingt questions en anglais, dont onze exigeant deux documents distincts et neuf à un seul saut servant de témoin.

Chaque question est dérivée d'un chemin réellement présent dans le graphe extrait, et **chacune a été vérifiée manuellement** contre ses abstracts sources : la relecture a écarté treize chemins pour inversion de polarité, conformes au schéma et syntaxiquement valides mais sémantiquement faux.

Deux formes de raisonnement multi-hop sont représentées.

**Pont** — A agit sur B, B agit sur C. L'amiloride inhibe la plasmine, laquelle est nécessaire à la myogenèse. La question demande quel processus musculaire dépend de la protéase inhibée par l'amiloride, sans jamais nommer la plasmine.

**Intersection** — A et C agissent tous deux sur B. Le ranibizumab et le ramucirumab inhibent tous deux l'angiogenèse, sans qu'aucun article ne les mentionne ensemble.

Dans les deux cas, l'entité intermédiaire est invisible depuis la question comme depuis la réponse. Un filtre automatisé écarte en outre tout chemin dont les deux extrémités figurent dans un même abstract du corpus, cas résoluble par une unique récupération.

Le jeu de test est réutilisable indépendamment de ce travail.

---

## Journaux de décision

Le dossier `docs/` contient les journaux tenus au fil du stage. Ils documentent les décisions, les mesures qui les ont fondées, et celles qui les ont infirmées. Le rapport analytique est disponible dans les deux langues, ainsi que deux des journaux ; les autres sont en français.

| Fichier | Objet |
|---|---|
| `rapport-stage.md` | rapport analytique complet |
| `report.md` | version anglaise du rapport |
| `exploration-datasets.md` | choix de la référence structurée, candidats écartés |
| `structures-observees.md` | dérivation du schéma d'extraction |
| `journal-pilote.md` | pilote sur cinq médicaments et sa réfutation |
| `pilot-journal.md` | version anglaise du journal du pilote |
| `dry-run.md` | trois itérations d'ajustement du prompt d'extraction |
| `contraintes-jeu-de-test.md` | contraintes de construction de la vérité terrain |
| `environnement.md` | environnement technique et résultats détaillés |
| `points-soutenance.md` | constats méthodologiques retenus pour l'oral |
| `defence-points.md` | version anglaise des constats retenus pour l'oral |

Ces journaux consignent aussi ce qui n'a pas fonctionné : un pilote dont quatre estimations sur cinq se sont révélées fausses, une hypothèse de troncature réfutée par la mesure, un filtre rendu inopérant par un défaut de typage situé ailleurs.

---

## Limites

Le jeu de test compte vingt questions reposant sur dix entités ponts distinctes. Cet effectif limite la précision statistique des écarts et interdit toute analyse par sous-catégorie fine.

Le corpus est construit pour contenir les chaînes testées. L'étude mesure la performance sur un corpus où l'information est présente, non la capacité à la retrouver dans l'ensemble de la littérature.

Le graphe est intégralement construit par extraction automatique, tandis que l'index vectoriel n'emploie aucun modèle de langue. Un échantillon aléatoire de 40 relations révèle de l'ordre de 10 % d'inversions de polarité. Ce biais joue contre l'hypothèse testée, le graphe l'emportant malgré ce handicap.

La baseline vectorielle conserve l'abstract entier comme unité de récupération : c'est une implémentation standard, et non un adversaire optimisé. Trois baselines plus exigeantes ont été mesurées après coup. Elles ne changent aucun des chiffres ci-dessus, mais elles en bornent la portée, et elles n'ont été mesurées qu'en récupération, jamais en réponses.

Ces limites et plusieurs autres sont exposées en détail dans la section 10 du rapport.

---

## Environnement

Le développement s'est effectué sur un poste dépourvu de GPU dédié, sous Windows 11, avec Python 3.12.10. Les étapes exigeant un accélérateur matériel ont été portées sur Google Colab en offre gratuite : extraction des relations avec Ollama et qwen2.5:7b, encodage vectoriel avec `pritamdeka/S-PubMedBert-MS-MARCO`, génération et jugement.

Le fichier `requirements.txt` fige les versions exactes des dépendances locales.

Le budget du projet est nul : aucun service payant, aucun modèle propriétaire distant, aucune clé d'API.

### Note sur les scripts de collecte

Les scripts interrogeant PubMed portent une adresse électronique d'exemple dans le champ `Entrez.email`. Le NCBI l'emploie pour identifier l'appelant. Remplacez-la par votre adresse avant toute nouvelle collecte.

---

## Organisation

```
stage-graphrag/
├── data/
│   ├── raw/                 sources, en lecture seule
│   └── processed/           sorties du pipeline
├── scripts/                 scripts numérotés dans l'ordre d'exécution
├── notebooks/               étapes exigeant un GPU (Colab)
├── docs/                    journaux de décision et rapport
├── dashboard.py             interface de démonstration
└── requirements.txt
```

Les scripts sont numérotés dans leur ordre d'exécution, poste local et Colab confondus, de sorte que le dépôt restitue la chronologie du travail.

---

## Auteur

Malek Tlili — 5ᵉ année du cycle ingénieur, génie logiciel et ingénierie des données, Faculté des Sciences de Bizerte.

Travail conduit au laboratoire LR21ES23 sur une durée de quatre semaines.
