*[Version française](README.fr.md)*

# Vector RAG vs Graph RAG — multi-hop inference on a biomedical corpus

A controlled comparison of two retrieval-augmented generation architectures on questions that require combining several documents, together with the data engineering pipeline that feeds them.

Research internship — Artificial Intelligence, Data Engineering and Applications Laboratory (LR21ES23), Faculty of Sciences of Bizerte, University of Carthage.

---

## Result

On a corpus of 475 PubMed abstracts and a test set of 20 manually verified questions, graph traversal retrieval outperforms vector retrieval on every metric measured.

| | Vector | Graph |
|---|---|---|
| Recall at rank 5 (Context Recall) | 0.55 | **0.83** |
| Answer accuracy | 0.30 | **0.70** |
| Answer Relevance | 0.60 | **0.76** |
| Faithfulness | **0.86** | 0.81 |

**The graph reaches, with five documents, a recall level that vector search does not reach with fifty.** The gap holds at every document budget tested.

These figures set the graph against a standard vector baseline. Three more demanding baselines were added afterwards — a passage splitting, a BM25 lexical baseline, and LightRAG's retrieval run on our own graph. They locate the origin of the gap and bound its scope: sections 8.9 to 8.11 of the report set them out.

Three findings distinct from the comparison itself:

**A curated mechanism database is not reconstructible from article abstracts.** None of the fifteen DrugMechDB chains retained could be recovered from the extracted graph. The literature compresses causal chains and presupposes established links: out of 935 extracted relations, only 36 have a disease as their target.

**The graph's advantage does not come from traversal.** The gap is largest on single-hop questions, which require none, and an ablation attributes 91 % of it to anchoring alone. The dominant mechanism is the absence of dilution: what counts is retrieving documents by the entity rather than by a global vector. A lexical baseline recovers three quarters of the gap without any graph, and LightRAG, on our own graph, falls back to the vector level as soon as it ranks documents by resemblance.

**The faithfulness metric, taken in isolation, rewards silence.** The weaker pipeline scores highest on it, thanks to its 50 % abstention rate.

The [full report](docs/report.md) details the method, the results and their limitations.

---

## Architecture

```
Pipeline 0   PubMed collection → cleaning → LLM relation extraction
                                                    │
                         ┌──────────────────────────┴───────────────────┐
                         ▼                                              ▼
Pipeline A   Vector index (S-PubMedBert)             Pipeline B   Knowledge graph
             similarity search                                    anchoring + 2-hop traversal
                         │                                              │
                         └──────────────────────────┬───────────────────┘
                                                    ▼
                                          Comparative evaluation
                                     retrieval · generation · RAGAS
```

**Pipeline 0** collects abstracts through the NCBI E-utilities API, cleans them, then extracts entity-relation-entity triples using a local language model, following a schema of 7 entity types and 10 relations derived from DrugMechDB.

**Pipeline A** encodes each abstract in full and answers by cosine similarity.

**Pipeline B** builds a graph of 792 nodes and 932 edges, anchors the question on its nodes, traverses the two-hop neighbourhood and traces back to the source documents. It requires no GPU.

---

## Quick start

### Requirements

Python 3.12, about 2 GB of disk space. No paid service, no API key.

```bash
git clone https://github.com/malektlili-eng/stage-graphrag.git
cd stage-graphrag
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux and macOS
pip install -r requirements.txt
```

### Explore the results

```bash
streamlit run dashboard.py
```

For each of the twenty questions, the dashboard displays both pipelines' answers side by side, the documents each retrieved, and the associated metrics. Documents expected by the ground truth are flagged among those retrieved, which makes the mechanism behind the gap visible.

The interface replays precomputed results. Generation requires a GPU and was run separately.

### Reproduce a measurement

The graph pipeline runs without hardware acceleration:

```bash
python scripts/48_pipeline_graphe.py      # Pipeline B recall
python scripts/49_courbe_rappel.py        # recall by document budget
python scripts/62_comparaison_baselines.py  # all baselines and the paired tests
python scripts/65_robustesse_egalites.py    # sensitivity of recall to score ties
```

The GPU-dependent steps — relation extraction, vector encoding, generation, judging — are in `notebooks/`, ready to run on Google Colab's free tier.

---

## Data

### Contents

| File | Contents |
|---|---|
| `data/raw/indication_paths.yaml` | DrugMechDB, 4,846 mechanistic paths (CC0), downloaded 7 August 2026 |
| `data/raw/pubmed_corpus.json` | 475 PubMed abstracts collected 16 August 2026 |
| `data/processed/relations_nettoyees.json` | 935 extracted and normalised relations |
| `data/processed/baseline_*.json` | rankings of the further baselines (notebooks 61, 64 and 66, script 62) |
| `data/processed/jeu_de_test.json` | 20 questions with expected answers and source documents |

### Provenance and rights

The corpus gathers 475 article abstracts retrieved through the NCBI E-utilities API. These abstracts are redistributed here solely to make the study reproducible. The National Library of Medicine does not hold the rights to PubMed abstracts, which remain the property of their respective publishers. No commercial use is intended or permitted. Any publisher wishing to have content removed may request it through the repository issues.

Since the PubMed identifiers for the whole corpus are fixed in `data/raw/`, the collection remains reproducible without relying on this file.

DrugMechDB is released under CC0 1.0 Universal — public domain, no restrictions.

> Gonzalez-Cavazos et al. (2023). *DrugMechDB: A Curated Database of Drug Mechanisms.* Scientific Data 10(1), 632.

---

## The test set

Twenty questions in English, of which eleven require two distinct documents and nine are single-hop, serving as controls.

Each question derives from a path actually present in the extracted graph, and **each was manually verified** against its source abstracts: the review discarded thirteen paths for polarity inversion — schema-compliant and syntactically valid, yet semantically false.

Two forms of multi-hop reasoning are represented.

**Bridge** — A acts on B, B acts on C. Amiloride inhibits plasmin, which is required for myogenesis. The question asks which muscular process depends on the protease inhibited by amiloride, without ever naming plasmin.

**Intersection** — A and C both act on B. Ranibizumab and ramucirumab both inhibit angiogenesis, without any single article mentioning them together.

In both cases the intermediate entity is invisible from the question as from the answer. An automated filter further discards any path whose two endpoints appear in a single corpus abstract, a case solvable by one retrieval.

The test set is reusable independently of this work.

---

## Decision journals

The `docs/` folder holds the journals kept throughout the internship. They record the decisions, the measurements that grounded them, and those that overturned them. The analytical report is available in both languages, as are two of the journals; **the remaining journals are in French**.

| File | Subject |
|---|---|
| `report.md` | full analytical report in English |
| `rapport-stage.md` | full analytical report in French |
| `exploration-datasets.md` | choice of the structured reference, rejected candidates |
| `structures-observees.md` | derivation of the extraction schema |
| `journal-pilote.md` | five-drug pilot and its refutation |
| `pilot-journal.md` | English version of the pilot journal |
| `dry-run.md` | three iterations of extraction prompt tuning |
| `contraintes-jeu-de-test.md` | ground truth construction constraints |
| `environnement.md` | technical environment and detailed results |
| `points-soutenance.md` | methodological findings retained for the defence |
| `defence-points.md` | English version of the findings retained for the defence |

These journals also record what did not work: a pilot in which four estimates out of five proved wrong, a truncation hypothesis refuted by measurement, a filter rendered ineffective by a typing defect located elsewhere.

---

## Limitations

The test set comprises twenty questions resting on ten distinct bridge entities. This size limits the statistical precision of the observed gaps and rules out any fine-grained subcategory analysis.

The corpus is built to contain the chains being tested. The study measures performance on a corpus where the information is present, not the ability to find it across the literature at large.

The graph is built entirely by automatic extraction, whereas the vector index uses no language model. A random sample of 40 relations reveals on the order of 10 % polarity inversions. This bias works against the hypothesis under test, the graph prevailing despite the handicap.

The vector baseline keeps the whole abstract as its retrieval unit: a standard implementation, not an optimised opponent. Three more demanding baselines were measured after the fact. They change none of the figures above, but they bound their scope, and they were measured on retrieval only, never on answers.

These limitations and several others are set out in detail in section 10 of the report.

---

## Environment

Development took place on a machine without a dedicated GPU, under Windows 11, with Python 3.12.10. Steps requiring hardware acceleration were run on Google Colab's free tier: relation extraction with Ollama and qwen2.5:7b, vector encoding with `pritamdeka/S-PubMedBert-MS-MARCO`, generation and judging.

The `requirements.txt` file pins the exact versions of the local dependencies.

The project budget is zero: no paid service, no remote proprietary model, no API key.

### Note on the collection scripts

The scripts that query PubMed carry a placeholder email address in the `Entrez.email` field. NCBI uses it to identify the caller. Replace it with your own address before running any new collection.

---

## Layout

```
stage-graphrag/
├── data/
│   ├── raw/                 sources, read-only
│   └── processed/           pipeline outputs
├── scripts/                 scripts numbered in execution order
├── notebooks/               GPU-dependent steps (Colab)
├── docs/                    decision journals and report
├── dashboard.py             demonstration interface
└── requirements.txt
```

Scripts are numbered in their execution order, local machine and Colab combined, so that the repository reflects the chronology of the work.

---

## Author

Malek Tlili — fifth year of the engineering programme, software engineering and data engineering, Faculty of Sciences of Bizerte.

Work carried out at the LR21ES23 laboratory over four weeks.
