# Vector retrieval and graph retrieval for multi-hop inference on a biomedical corpus

**Internship report — Artificial Intelligence and Data Engineering Research Laboratory, Faculty of Sciences of Bizerte**

*[Version française](rapport-stage.md)*

---

## Abstract

This work compares two retrieval-augmented generation architectures — one based on vector similarity search, the other on knowledge graph traversal — on questions that require combining several documents. The setup rests on a corpus of 475 PubMed abstracts, a graph of 935 automatically extracted relations forming 932 edges, and a test set of twenty manually verified questions.

The graph pipeline achieves a recall at rank 5 of 0.83 against 0.55 for the vector pipeline, and an answer accuracy of 0.70 against 0.30. The gap holds at every document budget tested: the graph reaches, with five documents, a recall level that vector search does not reach with fifty.  Both gaps are statistically significant on this paired design (p = 0.039 for accuracy, p = 0.014 for recall). An ablation establishes that 91 % of the gap comes from anchoring alone, without traversal.

The work also produces three methodological findings distinct from this comparison. First, an expert-curated mechanism database is not reconstructible from article abstracts: the literature compresses causal chains and presupposes established links. Second, the graph's advantage does not come from its traversal capability, contrary to what the theoretical argument leads one to expect: the gap is largest on questions requiring a single document, and is explained by the absence of dilution. Third, the faithfulness metric used in isolation rewards silence: the weaker pipeline scores highest on it, thanks to its abstention rate.

---

## 1. Introduction

### 1.1 Context

Retrieval-augmented generation couples a document search engine with a language model: the documents deemed relevant are supplied to the model, which writes its answer from them. The common implementation rests on vector similarity — each document is represented by a vector, each question likewise, and the documents whose vector is closest are retained.

This approach has a known theoretical weakness on so-called multi-hop questions, those whose answer requires combining information scattered across several documents. Vector similarity selects documents that resemble the question as a whole; it has no mechanism for gathering documents that are complementary but individually dissimilar.

An alternative consists in extracting from the corpus a graph of relations between entities, then answering by traversing that graph. The join operation, absent from vector search, becomes native.

### 1.2 Research question

The internship specification frames the question as follows: *under what conditions, and by how much, does the graph architecture outperform the vector architecture on multi-hop biomedical queries — and at what cost in latency and compute?*

Three distinct strands are present, treated separately in this report.

The **conditions** are established through the analysis of the failure modes specific to each architecture, set out in sections 8.1 and 8.2.

The **magnitude of the gap** is quantified by three independent measurements: retrieval recall, answer accuracy and the judged metrics, in sections 8.1 to 8.5.

The **cost** is measured along the two dimensions requested: query latency in section 8.4, construction and operation compute time in section 8.6.

### 1.3 Constraints

The work is bound to a zero budget: no paid service, no remote proprietary model. Compute resources are limited to a machine without a dedicated GPU and to a Google Colab free-tier environment. The allotted duration is four weeks.

These constraints shaped several technical decisions, notably the use of a local seven-billion-parameter language model and the reimplementation of the evaluation metrics rather than the use of a library presupposing remote access.

---

## 2. Conceptual framework

### 2.1 Multi-hop reasoning

A question is called multi-hop when its answer requires crossing several relations. Two forms were retained in this work.

The **bridge** is a directed path of three entities: A acts on B, B acts on C. The question concerns A and expects C; entity B appears neither in the question nor in the answer. Example retained: amiloride inhibits plasmin, which is required for myogenesis. The question asks which muscular process depends on the protease inhibited by amiloride, without ever naming plasmin.

The **intersection** makes two entities converge on a shared target: A and C both act on B. The question asks which other entity shares A's target. Example retained: ranibizumab and ramucirumab both inhibit angiogenesis, without any article mentioning them together.

In both cases the intermediate entity — the bridge entity — must remain invisible from both endpoints. A chain whose bridge appears in the name of an endpoint does not constitute multi-hop reasoning: it is solved by simply reading the question.

### 2.2 The false multi-hop

A question designed as multi-hop can nevertheless be solved by a single retrieval if one document contains both endpoints of the path. Vector search then finds it without traversal, and the question ceases to discriminate between the two architectures.

This phenomenon proved pervasive in the corpus studied: review articles systematically enumerate the members of a therapeutic class. An intersection between two drugs of the same class is therefore almost always a false multi-hop.

### 2.3 Decomposition of the measurement

A retrieval-augmented generation system comprises two successive stages. Retrieval selects documents; generation writes an answer from them.

Since the object of the study is the retrieval method, the primary measurement bears on that stage alone. Isolating the two avoids attributing to the architecture a gap arising from the generating model. Generation is measured separately, with the same model and the same prompt for both pipelines: only the documents supplied differ.

---

## 3. Data construction

### 3.1 Choice of a structured reference

Three candidates were evaluated against a single criterion: the dataset must allow relation chaining, a necessary condition for the object of the study.

**DrugMechDB** was retained. This dataset gathers 4,846 mechanistic paths linking a drug to a disease, amounting to roughly 32,641 relations across 33,009 entities, in YAML format, typed according to the Biolink Model. It is manually curated by experts, published under a CC0 licence, and its chaining test is conclusive. Its connectivity is strong: the entity "Glucocorticoid receptor" appears in roughly 670 paths, which makes it possible to compose chains spanning several records.

**SIDER** was set aside. It comprises only two relation types, both originating from the drug: drug to side effect, and drug to indication. No object reappears as a subject; the structure is a fork, not a chain. The dataset permits a degenerate multi-hop of the intersection type, but no path.

**SemMedDB** was set aside on methodological grounds, without in-depth exploration. This database is built by automatic extraction from MEDLINE titles and abstracts using the SemRep tool, without manual curation. Using it as a reference would amount to measuring not the correctness of the extraction carried out here, but its agreement with another automatic system: an error in the reference would then be rewarded. SemMedDB would remain acceptable as a source of candidate chains subsequently verified by hand, but since DrugMechDB covers both uses, the marginal benefit was low.

**Acknowledged limitation of the choice made.** DrugMechDB carries no PubMed identifier. Alignment between corpus and reference therefore cannot be established at the document level, only at the entity-relation level. This trade-off was accepted in favour of the reliability of the reference.

### 3.2 Extraction schema

An initial manual survey of eight paths identified a candidate pattern. This survey proved biased — four of the eight paths concerned the same drug — and was validated by counting across the whole dataset.

**Entity types.** The threshold retained is 500 distinct drugs, a value corresponding to a clear break in the distribution (546 down to 343) and not set a priori. Seven types were kept: Drug, Disease, BiologicalProcess, Protein, ChemicalSubstance, PhenotypicFeature, OrganismTaxon.

Three types were merged into a semantically valid parent: MolecularActivity and Pathway into BiologicalProcess, GeneFamily into Protein. A merge was applied only where such a parent existed among the retained types; it then removes a distinction with a gradual boundary without altering the meaning of the node.

Four types were excluded: CellularComponent, Cell, GrossAnatomicalStructure, MacromolecularComplex. No valid parent existed for them; merging them would have produced deliberately false labelling.

**A documented revision.** OrganismTaxon had first been excluded by application of the threshold, appearing in only 343 drugs as a node. Counting typed relations revealed that this type is the dominant endpoint of the `causes` relation, present in 484 drugs, and of `in taxon`, present in 208. Its exclusion reduced `causes` by 68 % and removed `in taxon` entirely, thereby withdrawing infectious mechanisms from the object of study. The type was reinstated.

This revision brought to light a methodological limitation: a selection criterion bearing on the frequency of entities as nodes does not account for their role as relation endpoints. A type that is infrequent as a node may anchor a major relation. A threshold bearing on entities alone is therefore insufficient and must be complemented by a check on the relations it conditions.

**Relation types.** The threshold retained is 300 distinct drugs, located at the sharpest discontinuity in the distribution (306 down to 191, a 38 % drop) within the range workable by a local model, estimated at between eight and twelve types. Ten relations were retained.

Polarity was preserved: the three opposing pairs — regulates, correlated with, activity of — were not merged. They carry the dataset's dominant signal, and "inhibits" is not equivalent to "activates". This decision carried an acknowledged risk, since a mis-extracted polarity produces a false fact rather than a mere typing defect. It was subjected to an explicit checkpoint during the dry run, described in section 4.

**Candidate chains.** After applying the schema and a length filter of two to three hops, 193 paths remain compatible out of 4,846, spanning 130 distinct drugs. The dominant pattern is Drug → Protein → BiologicalProcess → Disease, with 77 occurrences, or 40 % of the total.

The dominant constraint is length: the depth filter discards 4,463 paths, against 190 for all schema filters combined. Since the filters are applied in cascade, these counts are conditional.

### 3.3 Corpus construction

The corpus consists of PubMed article abstracts, retrieved through the NCBI E-utilities API.

**Query formulation.** The query restricts the search to title and abstract, requires the presence of an abstract, limits results to English, and imposes a mechanistic vocabulary. The field filter is decisive: without it, the drug is mentioned outside the body of the article in the vast majority of cases — epoprostenol drops from 13,851 to 1,079 results, a reduction of 92 %.

The mechanistic vocabulary was calibrated. An initial formulation limited to molecular binding terms covered the first link of the chains but not the subsequent ones. Adding regulation terms increases availability by 75 % for filgrastim, whose mechanism is described in terms of regulation rather than binding.

**Drug selection.** A pilot on five drugs, chosen on a qualitative estimate of the mechanistic richness of their literature, led to an instructive result: four estimates out of five proved wrong. Only one drug yielded usable chains.

Selection was therefore refounded on a measurement. For each candidate chain, the co-occurrence of the entities of each hop was measured directly by PubMed query, without download or inference. The instrument was first applied to the five pilot drugs, whose outcome was known, before being extended to the 130 candidates: a measuring instrument that is not verified to reproduce an established result cannot ground any selection.

The screening retained 16 chains spanning eleven distinct mechanisms, after applying a minimum co-occurrence threshold and removing chains with a lexically trivial bridge entity. One of them, the imatinib chain, was withdrawn subsequently on the basis of measurement — the reason is set out in section 5.2 — bringing to fifteen the number of chains used in the analysis of the reference-corpus mismatch.

**Mixed composition.** The corpus combines two components. Targeted articles carry, for each hop of each chain, the entities concerned. Distractors concern the same drug without containing any chain hop.

This composition answers a twofold constraint. Without targeted articles, no chain is reconstructible and both architectures fail uniformly. Without distractors, retrieval becomes trivial and discriminates no better.

**Scope of this choice.** Since both pipelines are evaluated on an identical corpus, the comparison remains fair. The restriction bears on external validity: the study measures performance on a corpus where the chains are present, not the ability to find them across the literature at large.

**Traceability.** Each abstract carries a provenance field indicating whether it bears a chain hop, and which, or whether it is a distractor. This metadata is intended for error analysis and is used by no stage of the pipeline: neither extraction, nor indexing, nor retrieval, nor generation has access to it. Exposing it would constitute a leak of information absent from real use.

**Final corpus.** 475 abstracts, of which 208 bear hops and 267 are distractors. Mean length of 217 words, or 385 measured tokens.

An integrity check was carried out hop by hop after cleaning. Thirty-three identified articles could not be retrieved; global counters remained normal, but some hops rested on only two articles, whose loss would have rendered a chain unusable without any indicator signalling it. No chain was broken.

---

## 4. Relation extraction

### 4.1 Setup

Extraction uses qwen2.5:7b, run locally through Ollama on a Tesla T4 GPU. Temperature is zero, the context window 4,096 tokens, and the output constrained to JSON format.

The choice of model is justified by its better compliance with format instructions, the task requiring output strictly conforming to an imposed schema.

The scope of the format constraint deserves clarification: it guarantees the syntactic validity of the output but not its schema compliance. A well-formed JSON may contain invented entity or relation types.

### 4.2 Validation by dry run

Three iterations were conducted on a sample of eight abstracts, composed so as to make the questions posed testable rather than drawn at random: coverage of both polarities, diversity of relation types, inclusion of an abstract predating 2000.

**First iteration.** Perfect syntactic validity, but none of the twelve expected relations correctly extracted. Manual reading of the abstracts established that three of them simply did not state the expected relation. The failure was therefore not attributable to the prompt.

This diagnosis revealed a collection defect: the mechanistic vocabulary filter, built and calibrated during the pilot, had not been carried over into the targeted collection query. Targeted articles were selected on entity co-occurrence alone, with no guarantee that the article dealt with a mechanism.

Correcting this defect was measured on the full corpus by comparing the two collections. The filter renews 12 % of the corpus — 57 abstracts discarded, 48 added, 436 retained out of 493. The nature of the exchanged articles does not, however, run uniformly in the expected direction: several discarded articles are explicitly mechanistic, while some added articles belong to pharmaceutical formulation or epidemiology. The filter therefore does not perform a qualitative sort but modifies the query and, consequently, PubMed's relevance ranking. One beneficial effect remains identifiable: among the discarded articles are comparisons between drugs of a same class, characterised sources of false multi-hop.

**Second iteration**, corrected corpus and unchanged prompt. The score remains nil but the nature of the failures changes. The model now produces "terguride blocks 5-HT(2B) receptors" where the reference states "decreases activity of". Source, target and polarity coincide; only the predicate differs. The failure is one of vocabulary, not of comprehension.

The schema non-compliance rate rises paradoxically from 21 % to 39 %. This apparent degradation is explained by the improvement of the corpus: mechanistic articles use more action verbs, which the model copies rather than translating them into the schema. The weakness of the prompt had been masked by the poverty of the earlier corpus.

**Third iteration**, single modification: addition of a verb-to-label mapping table, together with an assignment rule based on the type of the target. Non-compliance drops from six relations to one, on identical text — a conclusion established on the five abstracts common to both iterations, the sample having partly changed otherwise.

**Decision on polarity.** The inversion observed at the second iteration is corrected: the model now produces "lafutidine decreases activity of histamine H2 receptor" where the title describes the molecule as an antagonist. The error lay in translating the verb into a label, not in comprehending the text. The decision to keep the polarity pairs distinct is therefore maintained, without merging.

### 4.3 Full extraction

475 abstracts processed in 34.7 minutes, or 4.4 seconds per abstract, without interruption. An incremental resume mechanism in JSONL format had been provided; it did not need to be used.

**Volume produced.** 985 relations, or 2.1 per abstract, spanning 871 distinct textual entities. 177 abstracts produced no relation, of which 120 distractors and 57 targeted articles. The gap between these two rates — 44 % against 27 % — confirms the effect of targeting.

**Compliance.** The measurement depends on the definition adopted, and three definitions coexist in the project journals. Out of the 985 extracted relations: 829 use a schema predicate without regard to entity types; 822 add the condition that no type be missing; 820 further require both types to belong to the seven schema types.

The figure retained here is **822 out of 985, or 83 %**, the definition used by the recovery stage that produces the relation file actually exploited downstream.

The 163 non-compliant relations fall into four families: lexical variants of a schema predicate, literal reproduction of the source column of the mapping table, predicates without equivalent, and relations with a missing entity type.

A recovery stage, subsequent to extraction, maps any non-compliant predicate to the schema predicate it contains. It recovers 113 relations and raises the retention rate from 83 % to 94 %, that is 935 relations. Discarded are 36 relations whose predicate has no equivalent — mostly clinical: `treats`, `targets`, `improves`, `prevents` —, 10 relations with a missing entity type, and 4 negation statements. No predicate is attached by approximation: whatever is not explicitly listed is discarded and logged.

**Two defects that the compliance check lets through.** Examining the nine relations separating the broadest and strictest definitions reveals two, both attributable to the model and not to the setup.

The model invents entity types absent from the schema: two relations carry the type "Enzyme", which does not appear in it, and are nevertheless kept in the graph since their type is present. This has a practical consequence, as the filter excluding edges linking two drugs relies on types: an entity typed outside the schema escapes it by construction.

The model also sometimes copies the name of the type instead of the name of the entity: three relations have the literal word "Drug" as their source. This is the same defect as the reproduction of the source column of the mapping table, transposed to the entity field. These three relations were discarded by the entity type check.

**A design limitation of the schema.** Four extracted relations were negation statements — "does not affect", "does not mitigate". The ten schema predicates all express an effective link, positive or negative, without allowing an absence of relation to be represented. These relations were deleted rather than converted, since a conversion would invert the meaning of the source text.

---

## 5. The mismatch between reference and corpus

This result was not anticipated and constitutes the work's principal contribution beyond the comparison of architectures.

### 5.1 Finding

DrugMechDB chains are not reconstructible from PubMed abstracts. Of the fifteen chains retained, none could be recovered from the extracted graph. The failing link is constant: the relation connecting a biological process to a disease.

**Decisive measurement.** Out of 935 relations retained after predicate recovery, only 36 have a disease as their target, of which 33 originate from a drug. The process-to-disease relation, which constitutes the final hop of every chain retained, is practically absent from the corpus.

**Distribution of biological processes by position.** Norepinephrine and serotonin reuptake appears 15 times as a source against 93 times as a target; platelet aggregation never as a source against 17 times as a target; angiogenesis once against 29; gastric acid secretion never against 8.

**A counter-example, and an instructive one.** Fibrinolysis escapes this pattern: it appears 15 times as a source against 11 times as a target. Entities of this family — plasmin, plasminogen, plasminogen activator — are described as acting on other entities, and not merely as undergoing the action of a drug.

This exception explains an otherwise surprising fact. The only properly mechanistic bridge path retained in the final test set, `amiloride → plasmin → myogenesis`, belongs precisely to this family. Where the other processes never restart the chain, fibrinolysis does — and it is the only place in the corpus where an authentic mechanistic bridge could be built.

The generalisation must therefore be stated with care: biological processes are predominantly endpoints, but not universally so, and the exceptions are exactly the places where the path topology survives.

### 5.2 Characterisation

Abstracts produce a **star topology** centred on the drug: each edge runs from it towards its protein target, its process or its clinical effect. DrugMechDB models a **path topology**, where each intermediate entity restarts the chain.

Two mechanisms contribute to this mismatch.

**The literature compresses.** Where DrugMechDB decomposes "venlafaxine → norepinephrine transporter → norepinephrine reuptake", an article writes in a single sentence that venlafaxine inhibits norepinephrine reuptake. The intermediate entity disappears.

**The literature presupposes.** The final link is never restated. The clearest case concerns the relation "BCR-ABL causes chronic myeloid leukaemia", a textbook fact for forty years. Four articles were submitted, including a review devoted to the use of imatinib in this pathology — the most favourable candidate, the function of a review being to recall established data. None produces this relation. The review does, however, produce the preceding hop, "Imatinib inhibits BCR-Abelson fusion protein".

The contrast, observed within one and the same article, is structuring: the hop describing the drug's action on its target is extracted, the one connecting the target to the disease is not. The first is the object of the publication, the second its presupposition.

### 5.3 Methodological consequence

A curated knowledge base and a corpus of articles do not describe the world at the same level of detail. Consolidated mechanistic knowledge is precisely what abstracts do not restate.

This finding forced a change of method. Three routes were open: shortening the chains, deriving the questions from the extracted graph, or making the mismatch the sole result of the study. The second was retained.

**DrugMechDB changes role.** It ceases to be the source of the questions and becomes the extraction quality reference. The questions are derived from paths actually present in the extracted graph, each manually verified against its source abstracts.

**On the fairness of this choice.** Since the relations come from the corpus texts, the passages exist and the vector pipeline can find them. The questions moreover use entity names as the model read them in the text, which facilitates similarity search. The residual bias therefore works against the hypothesis under test, a preferable direction for an experimental setup.

---

## 6. Construction of the test set

### 6.1 Path search

The extracted graph was traversed in search of bridge-type and intersection-type paths. The search produced 350 raw paths, reduced to 23 valid ones after filtering and then to 16 after diversification.

This considerable reduction is instructive.

**Combinatorial propagation of an error.** The first search produced 230 bridges, of which 115 used a drug as bridge entity. The examples observed all show the same erroneous incoming edge: "asciminib increases activity of imatinib", converted from a statement of therapeutic combination. The imatinib node having a high out-degree, this false incoming edge combined with its outgoing edges.

The search script's output establishes the count of 115 bridges with a drug bridge entity; it does not establish that they all stem from this single edge, several other edges linking two drugs existing in the graph. The order of magnitude stands: one false incoming edge on a highly connected node generates dozens of candidate paths.

An extraction error therefore does not remain local in a graph: its effect is multiplied by the degree of the node it reaches. The phenomenon is structural and not tied to extraction quality. After excluding edges linking two drugs, 89 of the 149 remaining bridges belong to a single pattern, `Drug → ChemicalSubstance → BiologicalProcess`, whose observed examples all show the same incoming edge — correct this time — on a highly connected node. Here again, the script's output provides a count by pattern and not an attribution by edge.

**The type filter was not yet effective at this stage.** Excluding edges linking two drugs discarded only thirteen of them, and twenty-three bridges still travel through such an edge. The cause is a typing defect identified subsequently: a node's type was set by the last relation processed rather than by its majority type, so that a mistyped node escaped a filter relying on types. The defect was corrected, and the final selection discards thirty-seven paths on this ground.

This finding extends the previous one: not only does an erroneous edge propagate, but the mechanism meant to contain it can itself be neutralised by a labelling error located elsewhere.

**Structural ceiling of the corpus.** The number of authentic multi-hop paths remains low. Since the corpus covers fourteen drugs, several of which belong to the same therapeutic classes, and since review literature systematically enumerates the members of a class, the proportion of paths not solvable by a single retrieval is intrinsically limited. This ceiling is a property of the documentary domain and not a defect of method.

### 6.2 Filters applied

Six criteria were applied, in an order placing validation before diversification. This order was itself the object of a correction: diversification, applied first, discarded valid paths in favour of paths subsequently invalidated.

| Criterion | Paths discarded |
|---|---|
| Generic entity (clinical trial vocabulary) | 179 |
| False multi-hop at corpus scale | 70 |
| Drug-type bridge | 37 |
| Relation identified as false during review | 28 |
| Malformed entity | 6 |
| Identical endpoints | 4 |
| Manual exclusion decided during review | 3 |
| **Total discarded** | **327** |

The false multi-hop filter compares each path against the 475 abstracts of the corpus and not merely against its source abstracts. The scope is decisive: vector search queries the whole corpus, and any article containing both endpoints allows resolution in a single retrieval.

### 6.3 Manual verification

Since the questions are derived from the extracted graph, an extraction error would produce a question with a false answer. Each retained path was therefore confronted with its source abstracts. This review discarded thirteen paths for polarity inversion — schema-compliant, syntactically valid, semantically false. Three examples: venlafaxine described as increasing norepinephrine reuptake, lafutidine as increasing gastric acid secretion, bromocriptine as decreasing the activity of dopamine receptors when it is an agonist of them. No automated check could have detected them.

**Quantifying the inversion rate.** Since this review bore on paths retained by the filtering, it does not provide an error rate representative of the graph. A separate measurement was therefore conducted on a reproducible random sample of 40 relations drawn from the 807 polarity-bearing relations the graph contains, each confronted with the sentences of its source abstract.

Twelve relations could not be adjudicated, the automatically extracted sentences not carrying the necessary information. Of the 28 remaining: three characterised polarity inversions and three statements whose direction is not supported by the text, that is, on the order of 10 % inversions and 21 % incorrect statements in the broad sense.

The judging criterion adopted is strict: a relation is counted correct only if a sentence from the corpus establishes it. A statement that is pharmacologically accurate but not attested by the source text is classed as undecidable, since the measurement bears on the fidelity of the extraction to the text and not on the truth of the statement.

The three inversions are verifiable from the abstract text alone. "Venlafaxine increases activity of NET" where the article describes it as a reuptake inhibitor. "Selexipag positively regulates pulmonary arterial hypertension" where the drug is approved to treat that pathology. "Lafutidine negatively regulates gastric acid elimination" where the title states that this elimination is enhanced by the molecule.

**Scope of this measurement.** Three inversions out of 28 observations correspond to a 95 % confidence interval extending approximately from 2 % to 28 %. These values give an order of magnitude, not a precise estimate.

A further observation limits the scope of any random sampling: errors cluster by article. Seven of the relations targeting a disease constitute the same inversion, arising from a single article surveying treatments for social phobia, where seven distinct molecules are described as increasing the activity of the pathology they treat. A sample of relations therefore underestimates the true variance, several errors possibly sharing a single source.

Automated control and human control proved complementary in both directions. The former detected 32 false multi-hops out of 61, including 11 that the review had validated, by comparing each path against the whole corpus. The latter detected a case the filter let through, the source abstract spelling "carbegoline" instead of "cabergoline".

### 6.4 Final composition

**Twenty questions**, split into eleven multi-hop questions spanning ten distinct bridge entities, and nine single-hop questions serving as controls.

The control questions act as a witness. If both architectures succeed on them, the setup works. If the graph pipeline failed on them where the vector pipeline succeeds, there would be an implementation problem and not a result about multi-hop.

**Nominal and effective sample size.** The eleven multi-hop questions rest on ten distinct bridge entities: a single pair, bearing on the norepinephrine transporter, shares its bridge entity and therefore does not constitute two independent observations. Results are reported mentioning both counts, the nominal count slightly overstating the precision attainable.

**Scope decision.** One question bears on a shared adverse effect rather than on a mechanism of action. It was retained and marked as a distinct category: the research question concerns the ability to retrieve information requiring two documents, not the mechanistic nature of that information. This sample size of a single question rules out any separate analysis of the category.

**Data separation.** The test set contains, for each question, the expected answer, the identifiers of the source documents and the originating path. Only the `question` field is passed to the pipelines; the rest serves solely for evaluation, run after the system has answered.

---

## 7. The two pipelines

### 7.1 Pipeline A — vector search

**Retrieval unit.** The whole abstract, title and body concatenated. No splitting is applied: the abstract constitutes a coherent semantic unit that splitting would fragment, and this choice makes the comparison against the ground truth direct, a retrieved unit corresponding exactly to a PubMed identifier.

**Models compared.** `pritamdeka/S-PubMedBert-MS-MARCO`, a version of PubMedBERT trained for semantic search, and `sentence-transformers/all-MiniLM-L6-v2`, a general-purpose reference model. PubMedBERT in its original version is a language model and not a sentence encoder; using it directly would produce representations unsuited to search.

The biomedical model brings no gain on single-hop questions but a clear gap on multi-hop questions, where specialised vocabulary appears decisive. It was retained for the remainder.

**Acknowledged design choice.** Splitting into shorter passages would likely improve recall, an isolated entity weighing more in a hundred-token segment than in a full abstract. This splitting was not implemented, the baseline aiming at a standard implementation such as a competent practitioner would produce by default. The corresponding gap is flagged as a limitation rather than concealed.

### 7.2 Pipeline B — graph traversal

The graph has 792 nodes and 932 edges, each edge carrying its PubMed identifier of origin. Running it requires no GPU.

**Three stages.** Anchoring identifies in the question the entities present in the graph, by matching word groups from longest to shortest. Traversal explores the two-hop neighbourhood. Tracing back associates the reached edges with the documents that carry them, which allows both pipelines to be evaluated against the same yardstick.

**Traversal ignores edge direction.** Intersection-type paths require going up from the drug to the shared target and then back down to a second drug, which a directed walk would forbid.

**Weighting.** An edge reached at the first hop counts for 1, at the second for 0.5; an edge incident to an anchor node has its weight doubled. These values are a design choice and were not optimised on the test set, which would amount to tuning the system to the questions used to evaluate it.

**Point of fragility.** Anchoring conditions everything else: a question none of whose entities is matched produces zero recall regardless of the quality of the graph.

### 7.3 A correction downstream of the test set

Analysis of question SH04 revealed that the canonicalisation function did not transliterate Greek characters. An entity written "β-elemene" in the graph and "beta-elemene" in a question produced two distinct forms, preventing any match.

The correction bears on the anchoring stage, situated downstream of the construction of the test set. The ground truth remains unchanged, which distinguishes this correction from tuning the system to the questions used to evaluate it: the defect corrected existed independently of the test set employed.

Both measurements are reported. Recall at rank 5 rises from 0.78 to 0.83, that of single-hop questions from 0.89 to 1.00. The graph has 792 nodes after correction against 794 before, two pairs of entities having merged.

**A structural difference brought to light.** The graph pipeline rests on exact string matching and is therefore sensitive to spelling variations, whereas the vector pipeline operates on continuous representations that absorb them. No symmetrical correction applies to the vector pipeline, which uses no canonicalisation.

---

## 8. Results

### 8.1 Retrieval

Recall at rank 5, over the twenty questions of the test set. This measurement corresponds to the **Context Recall** metric of RAGAS: among the documents needed for the answer, what proportion appears among the documents retrieved? It is computed directly on the PubMed identifiers of the ground truth, without recourse to a judge, and is therefore the most reliable of the three metrics reported.

| | Vector | Graph | Gap |
|---|---|---|---|
| Overall | 0.55 | **0.83** | +0.28 |
| Single-hop questions | 0.67 | **1.00** | +0.33 |
| Bridge | 0.50 | **0.67** | +0.17 |
| Intersection | 0.44 | **0.71** | +0.27 |

The graph pipeline outperforms the vector pipeline on all three categories.

**The gap is largest where traversal is of no use.** It reaches 0.33 points on single-hop questions, which require only one document, against 0.27 on intersections and 0.17 on bridges. This hierarchy contradicts the attribution one would have expected and calls for it to be revised.

An objection must be dispelled before drawing a conclusion: the three categories do not start from the same level, and the graph pipeline reaches 1.00 on single-hop questions. The gap is therefore bounded by construction, since the vector pipeline already reached 0.67 there. Comparing raw gaps across categories of unequal difficulty is not legitimate in itself. The comparison was therefore redone in terms of the proportion of error closed, that is, by relating the gap to the available margin.

| Category | Raw gap | Error closed |
|---|---|---|
| Single-hop questions | +0.33 | 100 % |
| Intersection | +0.27 | 48 % |
| Bridge | +0.17 | 34 % |

The hierarchy is unchanged under both measures. The conclusion is therefore not a ceiling artefact.

The dominant mechanism is therefore not the traversal capability, but the **absence of dilution**. The graph indexes relations and not documents: an entity cited once in an abstract retains the same weight there as a central entity, whereas a document's vector reflects its overall topic. This mechanism operates across all question categories and suffices to explain most of the measured gap.

The **traversal capability** brings no measurable additional gain on this test set. Two readings remain possible. Its contribution may be small relative to that of dilution. Its contribution may also be masked by the intrinsically greater difficulty of multi-hop questions, on which both architectures start from a lower level. The sample size — three bridge questions, eight intersections — does not allow these two readings to be told apart.

Attributing the gap to traversal would therefore be an interpretive error that the data do not support.

### 8.2 Diagnosis of the vector pipeline's failures

The recall of 0.67 initially measured on the control questions remained below what one expects of a witness. Three causes were considered.

The hypothesis of **truncation** of abstracts exceeding the 512-token window of the embedding models was tested and rejected. Documents expected but not retrieved average 358 tokens against 348 for those that are, and 5 % are truncated against 6 %. The two populations are indistinguishable on this criterion.

The real cause is **dilution**. The documents missed are those in which the entity sought is not the main topic. Question SH07 concerns sarpogrelate, absent from the title of the expected document and cited once in the body of the abstract among other antagonists. The three documents expected for question MH05 name neither ranibizumab nor ramucirumab in their titles.

An entity mentioned once in a 350-token text contributes weakly to the vector representing that text. Vector search selects documents whose overall topic resembles the question, not those containing the information sought. This phenomenon is a structural limitation of whole-document indexing, and not an implementation defect.

### 8.3 Recall by document budget

| K | Vector | Graph | Gap |
|---|---|---|---|
| 1 | 0.38 | 0.45 | +0.08 |
| 3 | 0.53 | 0.78 | +0.26 |
| 5 | 0.55 | **0.83** | +0.28 |
| 10 | 0.60 | 0.88 | +0.28 |
| 20 | 0.77 | 0.95 | +0.18 |

The graph pipeline dominates at every value of K. The result therefore does not depend on the choice of document budget, which dispels the objection of a gap obtained through a favourable setting.

**Equivalent document budget.** The graph reaches a recall of 0.83 with five documents, a level the vector pipeline does not reach even when retrieving fifty. The documents missed are not poorly ranked but absent from the ranking: dilution makes them invisible to similarity search rather than relegating them.

**The gap peaks between K = 5 and K = 10**, at 0.28 points, and narrows on either side. At K = 1, the document budget is too small for a multi-hop question to be solvable by either architecture. At K = 20, the vector pipeline eventually recovers part of its lag.

**A contrasting behaviour by question category.** At K = 1, both pipelines obtain strictly identical scores on intersections (0.25) but not on single-hop questions, where the graph already leads by 0.11 points.

This dissociation is instructive. On intersections, neither architecture can succeed with a single document, the question requiring two distinct documents by construction: the equality reflects a shared impossibility. On single-hop questions, by contrast, one document suffices, and the graph ranks it better — not through traversal capability, which is not called upon, but through the absence of dilution.

**On bridge-type questions, the gap remains rigorously constant** at 0.17 points across every value of K tested: the vector pipeline never recovers its lag, whatever number of documents it is granted. This regularity survived the transliteration correction, which makes it less likely to be a measurement artefact. The observation nevertheless bears on three questions and calls for reservation.

**Practical scope.** The graph's advantage is in part an advantage of efficiency: it obtains with few documents what the vector pipeline obtains only with many, or never. This nuance matters, twenty abstracts of 385 tokens exceeding the usable context window of a seven-billion-parameter model.

### 8.4 Generation

The same model is applied to the documents retrieved by each of the two pipelines, with the same prompt and the same temperature: only the context supplied differs. The prompt provides for an explicit abstention answer when the documents do not contain the information.

| | Vector | Graph |
|---|---|---|
| Accuracy | 0.30 | **0.70** |
| Abstention | 0.50 | 0.15 |
| Mean latency | 2.8 s | 2.9 s |
| Single-hop questions | 0.44 | **0.78** |
| Bridge | 0.00 | **0.67** |
| Intersection | 0.25 | **0.62** |

**The accuracy gap (0.40) exceeds the recall gap (0.28).** A retrieval failure is not recovered at generation: the vector pipeline abstains in half the cases, not through error but for want of the necessary documents. No quality of writing compensates for an absent document.

Latencies are equivalent. The graph's advantage therefore does not bear on generation cost.

**Scope of the metric.** An answer is counted correct as soon as it contains one of the acceptable formulations, including within its justification. The measure is therefore permissive. This tolerance applies identically to both pipelines and does not distort the comparison, but it likely inflates both scores.

**Two analytical cases.** Question SH04 illustrates a generation error and not a retrieval error: both pipelines retrieve the expected document and both produce a wrong answer. The setup therefore does distinguish the two stages.

Question MH09 is the only case where the vector pipeline clearly prevails. The question names no drug — it asks which selective serotonin reuptake inhibitor also acts on the norepinephrine transporter. The graph anchors on two processes and never reaches the relevant document. This failure mode is specific to the graph architecture: when a question comprises only concepts and no salient named entity, anchoring steers the traversal in an unproductive direction.

### 8.5 Judged evaluation

The faithfulness and relevance metrics follow the RAGAS definitions but are reimplemented rather than imported from the library. The latter presupposes access to a remote model, which the zero-budget constraint forbids, and conceals the judging prompt used. A reimplementation makes that prompt explicit and therefore reportable.

Judgement is produced on a discrete five-level scale, mapped onto the interval [0,1]. A seven-billion-parameter model does not produce a continuous score reproducibly; restricting granularity to what the judge can actually sustain avoids collecting noise.

**Judge stability.** Each answer was evaluated three times. The maximum spread between the three judgements averages 0.01 for faithfulness and is nil for relevance; 39 judgements out of 40 are perfectly stable for the former, 40 out of 40 for the latter. The reservation formulated a priori about the instability of a small judge is not confirmed by measurement.

| | Vector | Graph |
|---|---|---|
| Faithfulness | **0.86** | 0.81 |
| Relevance | 0.60 | **0.76** |
| Accuracy | 0.30 | **0.70** |

**The vector pipeline obtains better faithfulness.** This result is explained by its abstention rate: abstaining when the documents do not contain the information is faithful behaviour and receives the maximum score. A system that rarely answers is mechanically faithful.

**The faithfulness metric, taken in isolation, therefore rewards silence.** Bridge-type questions illustrate this: the vector pipeline obtains its best faithfulness there, 0.92, while its accuracy there is nil. This observation bears on three questions and stands as an illustration, not as a measurement.

The three metrics must be read together. The vector pipeline appears **cautious** — it does not invent but answers little; the graph pipeline **useful** — it answers more often and more often correctly.

### 8.6 Costs

| | Vector | Graph |
|---|---|---|
| Relation extraction | — | 35 min GPU |
| Indexing | under one minute GPU | a few seconds, no GPU |
| Query | GPU required | index walk, no GPU |
| **Construction total** | **under one minute** | **35 min** |

The graph pipeline requires roughly two orders of magnitude more compute at construction. This load comes entirely from relation extraction, which requires one call to the language model per document. This stage belongs to the upstream data pipeline and must be charged to the cost of the graph, failing which the comparison would omit the essential part of its overhead.

**A note on measuring the indexing cost.** The timing of vector indexing encompasses loading the embedding model into memory and encoding the corpus, that is 23 seconds in total, of which roughly 8 seconds of encoding proper. It does not include the initial download of the model. This omission is symmetrical to the one applied to the graph pipeline, whose 35 minutes exclude the installation of Ollama and the download of the language model. Since neither measurement cleanly isolates its components, the ratio between the two is given only as an order of magnitude.

In return, the graph is queried without hardware acceleration, where the vector pipeline requires a GPU to encode each question.

**The trade-off is one of high initial cost against low operating cost.** The graph's overhead is justified for a stable, frequently queried corpus; it is not justified for a continuously renewed corpus, whose graph would have to be rebuilt repeatedly.

On a system receiving a high volume of queries, the trade-off tips clearly in favour of the graph.

---
### 8.7 Statistical significance of the gaps

The twenty questions pass through both pipelines, which makes this a paired design: each
observation is a couple, not two independent measurements. The tests used account for
this.

**Accuracy — McNemar's exact test.** Since accuracy is binary per question, the test
bears on discordant pairs alone. The graph pipeline answers correctly where the vector
pipeline fails in ten cases, the reverse occurring twice, giving twelve discordant pairs.
The probability of observing so unbalanced a split under the hypothesis that the two
pipelines are equivalent is **p = 0.039**.

**Recall — Wilcoxon signed-rank test.** Since recall is continuous, the test bears on the
non-zero differences, ten in number. The sum of positive ranks is 51.5 against 3.5 for
negative ranks, giving **p = 0.014** by exact enumeration of sign configurations.

**Confidence intervals by paired bootstrap**, 20,000 resamples, seed fixed at 42:

  Recall@5 difference     +0.28   95 % CI [+0.11, +0.47]
  Accuracy difference     +0.40   95 % CI [+0.10, +0.70]

Both gaps are significant at the 5 % level and both intervals exclude zero. The sample
size of twenty questions, flagged as a limitation in section 10.1, therefore does not
prevent a conclusion about the overall gap: it limits the precision of the estimate, not
its sign. The lower bounds of the intervals — eleven points of recall, ten points of
accuracy — constitute the minimum gap the data support.

This conclusion does not extend to the per-category analyses, whose sample sizes of three
to nine questions remain too small for any test.

### 8.8 Ablation: the specific contribution of traversal

Section 8.1 attributes the gap to the absence of dilution rather than to traversal, on
the basis of the hierarchy of per-category gaps. That attribution remained an
interpretation. It is tested directly here by neutralising traversal: the graph pipeline
is rerun at depth 1, that is, retaining only the edges incident to the anchor nodes,
without exploring the neighbourhood. A single parameter changes.

                     Vector    Anchoring only   Anchoring + traversal
  Overall             0.55          0.81                 0.83
  single-hop          0.67          1.00                 1.00
  bridge              0.50          0.33                 0.67
  intersection        0.44          0.77                 0.71

**Anchoring alone produces 91 % of the gap.** Of the 0.283 points separating the two
pipelines, 0.258 are obtained with no traversal at all. The hypothesis formulated in
section 8.1 is therefore established by measurement and no longer merely by analysis of
the gaps.

The mechanism is the one described in section 8.2: simply indexing relations rather than
documents suffices to recover the abstracts in which the entity sought is not the main
topic, which vector search misses through dilution.

**Traversal is not without effect, however, and its profile is revealing.** It doubles
recall on bridge-type questions, from 0.33 to 0.67 — the only category where a directed
path must be followed end to end. It slightly degrades intersections, from 0.77 to 0.71,
by introducing into the ranking documents reached at the second hop that compete with the
relevant ones.

Traversal therefore acts where it is structurally required and harms elsewhere. Its net
contribution of 9 % across the test set results from these two opposing effects
cancelling, and not from a uniformly small contribution. A pipeline activating traversal
only on bridge-type questions would outperform both configurations tested here;
determining this automatically constitutes an immediate improvement path.

This measurement bears on three bridge questions and eight intersections. The direction of
both effects is clear, their magnitude is not.


## 9. Demonstration deliverable

A Streamlit interface allows the results to be consulted. It comprises two views: a question-by-question comparison, displaying side by side each pipeline's answer, its metrics and the documents it retrieved, and an overview presenting the global and per-category aggregates.

The interface replays precomputed results rather than generating them on demand. Generation requires hardware acceleration absent from the demonstration machine, and this design further guarantees that the values displayed coincide exactly with those of this report.

The documents expected by the ground truth are flagged among the documents retrieved, which makes the mechanism behind the gap visible: the vector pipeline frequently displays five documents none of which is expected, whereas the graph pipeline generally places one or two at the top of the ranking.

---

## 10. Limitations

### 10.1 Sample sizes

The test set comprises twenty questions, of which eleven are multi-hop resting on ten distinct bridge entities. This size limits the statistical precision of the gaps observed and rules out any fine-grained subcategory analysis — the results on bridge-type questions, three in number, are reported for illustration, as is the single question bearing on an adverse effect.

This ceiling results from a property of the corpus and not from a lack of effort: since review literature systematically enumerates the members of a therapeutic class, the proportion of paths not solvable by a single retrieval is intrinsically limited on a corpus covering fourteen drugs.

### 10.2 External validity

The corpus is built to contain the chains being tested. The study therefore measures performance on a corpus where the information is present, not the ability to find it across the literature at large.

This choice is necessary: without carrier articles, both pipelines would fail uniformly and the setup would discriminate nothing.

### 10.3 Asymmetry in the use of the language model

The graph is built entirely by automatic extraction using a language model, whereas the vector index makes no use of one.

The performance of the graph pipeline therefore depends on the quality of this extraction. A random sample of 40 polarity-bearing relations, confronted with the source abstracts, reveals on the order of 10 % characterised inversions and 21 % incorrect statements in the broad sense, over the 28 relations that the extracted sentences allowed to be adjudicated. The confidence interval is wide and these values constitute only an order of magnitude.

**Scope of the result.** The comparison bears on an architecture-extractor pair — a graph extracted by a local seven-billion-parameter model, set against a vector index built on S-PubMedBert — and not on the architectures considered independently of their implementation.

**Direction of the bias.** Imperfect extraction degrades the graph by introducing erroneous edges into it, without affecting the vector index. The bias therefore works against the hypothesis under test. The graph pipeline prevails despite this handicap, which makes the measurement conservative: a more reliable extractor would likely widen the gap rather than narrow it.

### 10.4 Unoptimised baseline

The vector pipeline keeps the whole abstract as its retrieval unit. Splitting into shorter passages would likely improve its recall. This optimisation was not implemented, the baseline aiming at a standard implementation.

### 10.5 Scope of the extraction schema

The fifteen chains retained exercise only six of the ten schema relations. The relations `increases activity of`, `participates in`, `manifestation of` and `causes` are tested by no question. The extraction schema is therefore broader than the scope evaluated.

Furthermore, the OrganismTaxon type, reinstated in the extraction schema after measurement, appears in no candidate chain pattern: infectious mechanisms take long paths, eliminated by the depth filter. A decision validated at the relation level can thus remain without effect at the level of short chains.

---

## 11. Conclusion

On multi-hop inference questions in the biomedical domain, graph traversal retrieval outperforms vector retrieval on every retrieval and generation metric measured. The graph reaches, with five documents, a recall level that vector search does not reach with fifty, and its advantage holds at every document budget tested.

The advantage rests principally on a single mechanism, and not on the one expected. The gap is largest on single-hop questions, which require no traversal: it is therefore the absence of dilution that dominates. The graph indexes relations and not documents, so that an entity cited once weighs as much there as a central entity. The traversal capability, presented as the theoretical argument in favour of the graph architecture, produces no measurable additional gain on this test set — without it being possible to determine whether its contribution is small or masked by the greater difficulty of multi-hop questions.

**On the research question.** The graph's overhead is real — roughly two orders of magnitude more compute at construction — but it is paid in full once. In operation, the graph is the cheaper of the two: it is queried without hardware acceleration where the vector pipeline requires it for every question, and generation latencies are equivalent. The trade-off therefore resolves in favour of the graph for a stable, frequently queried corpus, and against it for a continuously renewed corpus.

**Three findings distinct from this comparison** deserve to be retained.

An expert-curated mechanism database is not reconstructible from article abstracts. The literature compresses causal chains and presupposes established links: consolidated mechanistic knowledge is precisely what abstracts do not restate. This finding, which forced a redesign of the method mid-study, constitutes a fundamental limitation of any pairing between a curated database and a documentary corpus.

An extraction error does not remain local in a graph: its effect is multiplied by the degree of the node it reaches. A false incoming edge on a highly connected node contributed to raising the number of candidate paths from a few dozen to more than two hundred. This finding argues for quality control upstream of graph construction rather than downstream.

Extraction errors moreover cluster by source article, which has a practical consequence: a random sample of relations underestimates the true variance of the error rate, several errors possibly sharing a common documentary origin.

The faithfulness metric, used alone, rewards silence. The weaker pipeline scores highest on it thanks to its abstention rate. This metric only makes sense read together with relevance and accuracy.

### Future directions

Three directions would naturally extend this work.

**Broadening the corpus.** The ceiling on authentic multi-hop paths results from the small number of drugs covered. A corpus spanning several hundred molecules from distant therapeutic classes would mechanically increase the proportion of intersections not solvable by a single retrieval.

**Strengthening the extractor.** The polarity inversion rate, on the order of 10 % on the sample measured, constitutes the main handicap of the graph pipeline. A larger model, or an automatic polarity verification mechanism, would likely widen the measured gap.

**Addressing anchoring.** The failure mode specific to the graph architecture — a question comprising only concepts and no salient named entity — calls for a more robust anchoring mechanism, for instance based on vector search applied to the graph's nodes rather than on exact string matching. Such a hybridisation would combine the strengths of both architectures.

---

## Appendix A — Technical environment

**Development machine.** Windows 11 Pro, Intel Core i5-6300U, 16 GB of RAM, no dedicated GPU. Python 3.12.10, dependencies isolated in a virtual environment.

**Intensive compute.** Google Colab, Tesla T4 GPU (15,360 MB), Ollama, qwen2.5:7b model.

**Main dependencies.** PyYAML 6.0.3, Biopython 1.88, transformers 5.15.0, sentence-transformers 5.7.0, torch 2.11.0+cu128, Streamlit 1.62.0, pip-system-certs 5.3.

The `requirements.txt` file, at the root of the repository, pins the exact versions and allows the environment to be reconstituted identically.

## Appendix B — Repository layout

```
stage-graphrag/
├── data/
│   ├── raw/          source data, read-only
│   └── processed/    pipeline outputs
├── scripts/          scripts numbered in execution order
├── notebooks/        Colab notebooks (extraction, indexing, generation)
├── docs/             decision and exploration journals
├── dashboard.py      demonstration interface
└── requirements.txt
```

Scripts are numbered in their execution order, local machine and Colab combined, so that the repository reflects the complete chronology of the work.

## Appendix C — Reproducibility constraints

**Raw sources.** `indication_paths.yaml` (DrugMechDB), downloaded from the SuLab/DrugMechDB repository. PubMed abstracts are retrieved through the E-utilities API; the list of collected identifiers is fixed in the output files, which makes the collection replayable identically regardless of how PubMed's ranking algorithm evolves.

**Collection dates.** Pilot corpus on 11 August 2026, working corpus on 16 August 2026. These dates matter: since PubMed's relevance ranking is not reproducible over time, only the fixed list of identifiers guarantees replayability.

**Determinism.** Zero temperature on all calls to the language model. The determinism of the setup was verified: the same polarity inversion was reproduced identically across two dry run iterations.

**Colab prerequisites.** The Colab image provides neither `zstd`, required by the Ollama installation script, nor `pciutils`/`lshw`, required for GPU detection when the server starts. These three packages must be installed before Ollama, failing which the server starts in CPU mode with no apparent error.

**Ephemerality of sessions.** A Colab session may be recycled without notification. Uploaded files and the downloaded model are then lost, even though the notebook appears to remain active. Long-running jobs save their progress incrementally to persistent storage.

## Appendix D — Correspondence with the project specification

### Prescribed deliverables

| Deliverable | Status | Section |
|---|---|---|
| Pipeline 0 — collection, cleaning, extraction | delivered | 3.3 and 4 |
| Pipeline A — vector baseline | delivered | 7.1 |
| Pipeline B — graph architecture | delivered | 7.2 |
| Comparative dashboard | delivered | 9 |

### Evaluation metrics

The three prescribed RAGAS metrics are measured.

| RAGAS metric | Name used in this report | Value (vector / graph) |
|---|---|---|
| Context Recall | Recall at rank 5 | 0.55 / 0.83 |
| Faithfulness | Faithfulness | 0.86 / 0.81 |
| Answer Relevance | Relevance | 0.60 / 0.76 |

A fourth measurement, answer accuracy, was added. Deterministic and requiring no judge, it serves as a reference for the two judged metrics and makes it possible to establish that faithfulness, taken in isolation, rewards abstention.

### Departures from the prescribed tools

Three substitutions were made relative to the tools mentioned in the project specification. They are stated here rather than passed over in silence.

**Graph architecture.** The specification mentions Microsoft's GraphRAG framework or LightRAG. The traversal was implemented directly. This choice guarantees control over the parameters of the setup — hop weighting, anchoring method, depth — which are made explicit in this report and would have been concealed by a framework. It further removes a heavy dependency in a compute environment rebuilt at each session.

**Vector store.** The specification mentions ChromaDB or FAISS. Vectors are kept as normalised tensors and search is performed by dot product. On 475 documents, an approximate index brings no gain: exhaustive search runs in a few milliseconds and avoids the approximation introduced by neighbourhood structures.

**Compute hardware.** The specification provides for a departmental GPU workstation or a laptop with at least 8 GB of video memory. The available workstation having no dedicated GPU, inference was moved to Google Colab's free tier. This substitution respects the zero-budget constraint but introduces the ephemerality of sessions, whose practical consequences are documented above.

### Scope reductions provided for in the specification

The specification explicitly provides for several reductions to meet the four-week duration. All were respected: a single structured dataset (DrugMechDB, the choice being justified in section 3.1), a corpus of a few hundred abstracts (475), a test set of twenty to thirty questions (twenty), automated validation without expert evaluation, a deliberately standard vector baseline, and a functional rather than polished dashboard.
