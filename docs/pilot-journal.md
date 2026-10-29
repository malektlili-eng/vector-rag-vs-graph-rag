# Pilot journal — week 1

*[Version française](journal-pilote.md)*

## Coverage test, exact matching (scripts/12_test_couverture.py)

Corpus: 144 abstracts, 5 drugs. DrugMechDB chains concerned: 16.

Result: 0 chains fully covered, 3 partially, 13 with no step at all.
18 entities out of about 23 not found by exact string search.

Diagnosis: a nomenclature gap, not an absence of content. DrugMechDB uses the canonical
designations of the reference databases (UniProt, GO); the literature uses usage forms.
Verified example: the entity `serotonin uptake` is literally absent, whereas abstract
PMID 20048460 states "blocks the synaptic reuptake of serotonin" — reversed order, re-
prefix, intervening preposition.

Consequence: an entity normalisation step (entity linking) is necessary. It will also be
necessary downstream, to compare the relations extracted by the LLM with the ground
truth, since the model likewise produces usage forms.

## Coverage test, relaxed matching (scripts/13_couverture_souple.py)

Three matching levels tested: exact phrase, last two significant words, set of
significant tokens.

Entities detected: 12/30 (exact), 13/30 (phrase), 18/30 (tokens).
Chains fully covered: 0/16 at all three levels.

Three distinct failure modes identified:
1. Granularity mismatch — `serotonin uptake` appears in 26 abstracts,
   `Sodium-dependent serotonin transporter` in none. The pharmacological literature
   describes the action, not the protein that carries it.
2. Canonical qualifiers absent from usage — the UniProt nomenclature prefixes
   ("Sodium-dependent") never appear in the abstracts.
3. Absence of co-occurrence — Filgrastim chain: the four entities are each present
   individually but never two at a time in the same abstract, a necessary condition for
   extracting a relation.

Limitation of the test: relaxing the criterion introduces false positives. The entity
`Solute carrier family 12 member 3` matches at the "phrase" level through the fragment
"family member", used in an abstract in its familial sense. The token-level figures are
therefore slightly optimistic.

## Nomenclature survey (scripts/14_nomenclature_reelle.py)

Reverse inspection: instead of searching the corpus for DrugMechDB's canonical names,
direct observation of the designations the literature uses.

Correspondences established:
  Sodium-dependent serotonin transporter         → SERT, 5-HT transporter
  Sodium-dependent noradrenaline transporter     → NET, norepinephrine transporter
  Granulocyte colony-stimulating factor receptor → G-CSF receptor
  Solute carrier family 12 member 3              → sodium-chloride cotransporter
  serotonin uptake                               → serotonin reuptake

Three forms of mismatch: abbreviation, functional versus genetic nomenclature, lexical
variant. None amounts to an absence of content.

Exception: Thyroid peroxidase is genuinely absent from the propylthiouracil corpus. The
two occurrences of "peroxidase" designate lactoperoxidase and myeloperoxidase, distinct
enzymes. Risk of false friends under partial matching: three different proteins share
that fragment.

Methodological correction: the literal-matching coverage test (scripts 12 and 13)
measured a lower bound unrepresentative of the actual pipeline. The pipeline does not
require the LLM to produce the canonical form: it extracts the usage form, which a
normalisation step then links to a reference identifier. The relevant question is
therefore not "is the canonical form present?" but "can normalisation connect usage form
and canonical form?".

Pilot conclusion: the founding premise is validated — the DrugMechDB chains are indeed
described in PubMed abstracts. An entity normalisation step is necessary and its scope is
bounded: roughly 40 to 60 entities for 25 to 30 questions, with synonyms available in
UniProt and MeSH.

## Building the normalisation table

Preliminary step: the chain extraction script kept only entity names, not their
identifiers. These were restored (fields source_id and cible_id), identifiers being what
links DrugMechDB to the reference databases.

Source of synonyms: the UniProt API (rest.uniprot.org), fields recommendedName,
alternativeNames, shortNames, geneName and gene synonyms.
Output: data/processed/synonymes_proteines.json

Result: 7 proteins queried, 2 to 8 designations each. The forms observed in the corpus
during the nomenclature survey are all present in UniProt (SERT, NET, norepinephrine
transporter, G-CSF receptor, sodium-chloride cotransporter).

Two reservations about the resulting table:
- An annotation error in the source: SLC6A5 (the glycine transporter) appears among the
  synonyms of the noradrenaline transporter. The table is imported without an exhaustive
  audit of the UniProt records.
- Six acronyms of 3 to 4 characters (TSC, NAT1, HTT, TPO, DAT1, NET1) are ambiguous in
  biomedicine. Matching is restricted to whole words, and case is respected for acronyms
  of four characters or fewer, so as to limit chance matches.

The lexical variants of biological processes (uptake / reuptake) are entered manually
from the observations of script 14: UniProt covers proteins only.

## Re-measurement after protein normalisation (scripts/16_couverture_normalisee.py)

Result: 5 chains fully covered out of 16, against 0 before normalisation.
The normalisation mechanism is validated: the DrugMechDB chains are reconstructible from
PubMed abstracts.

Reservation: the five covered chains all come from the same drug (venlafaxine). Four
drugs out of five yield no usable chain. The overall rate of 31 % masks a concentration
on a single case.

Diagnosis of the 11 failures, three distinct causes:
1. Matching too strict — the function requires the whole synonym phrase. UniProt provides
   "Thiazide-sensitive sodium-chloride cotransporter" where the corpus writes
   "sodium-chloride cotransporter". A defect of the measurement, not of the data; actual
   coverage is therefore higher than the measured value.
2. Biological processes not normalised — UniProt covers proteins only. The
   BiologicalProcess entities received only three manually entered variants.
3. Genuine absence of content — Thyroid peroxidase is absent from the propylthiouracil
   corpus; the epoprostenol indications retained by DrugMechDB (allergic rhinitis, common
   cold) do not match the subject of its literature. These chains are definitively
   unusable.

Causes 1 and 2 are repairable; cause 3 requires discarding the chains concerned.

## Normalisation of biological processes (scripts/17_synonymes_go.py)

Source: the QuickGO API (EBI), synonyms of type "exact" and "narrow" only. Types
"related" and "broad" are set aside: they designate neighbouring but non-equivalent terms
and would produce erroneous matches.

Result: 7 processes queried, from 1 to 7 designations. Significant gain for norepinephrine
uptake (7 forms) and Neutrophil differentiation (4 forms).

Inconsistency noted in the source: Gene Ontology provides "norepinephrine reuptake" but
not "serotonin reuptake", although both terms are equally current in the literature. As
with the annotation error observed in UniProt (SLC6A5), this confirms that no reference
database is complete: the three sources — UniProt, Gene Ontology and manually collected
variants — are complementary and jointly necessary.

## Correcting the matching function

The matching function required the whole synonym phrase. In biomedical nomenclature the
qualifiers are prefixed ("Sodium-dependent X", "Thiazide-sensitive X") and the head noun
phrase carries the identity. Suffixes of the synonyms are therefore also accepted,
provided they contain at least two words and twenty characters — a floor meant to exclude
generic fragments ("factor receptor") liable to produce chance matches.

This threshold is a heuristic and not an exact rule; the generated forms are printed for
manual inspection.

Check on the suffix-generated forms: two of them are discarded after inspection. "cell
differentiation", derived from "neutrophil cell differentiation", is a generic term of
cell biology. "colony-stimulating factor receptor", derived from the G-CSF receptor, also
matches the GM-CSF and M-CSF receptors, which are distinct proteins. The twenty-character
floor does not discriminate these cases: the length of a term does not measure its
specificity.

## Pilot verdict

Final result: 5 usable chains out of 16, all from the same drug (venlafaxine). The other
four drugs produce none.

The diagnosis of the metolazone chain (scripts/19_diagnostic_chaine.py) confirms a
genuine absence of content rather than a defect of measurement: the target protein
appears in only one abstract out of 29, and that abstract does not mention the drug; the
biological process of the following step appears in none.

Conclusions:
1. The founding premise is validated — the DrugMechDB chains are reconstructible from
   PubMed abstracts, subject to entity normalisation.
2. The selection of the pilot drugs rested on a qualitative estimate of the mechanistic
   richness of their literature, not on a measurement. Four estimates out of five proved
   wrong.
3. The discriminating factor is the nature of the drug's literature: venlafaxine has a
   molecular pharmacology literature, the other four a predominantly clinical one.

Methodological consequence: the selection of drugs for the full collection will rest on a
prior measurement of drug–target protein co-occurrence, obtained directly by PubMed query
without download or inference.

Revised conclusion: this verdict, established on five drugs and by lexical matching, was
overturned by the measurement on the full corpus. The entity coverage measured here does
not predict the extractability of relations, since the co-occurrence of two entities does
not imply that the text states a link between them. See docs/dry-run.md, section
"Caractérisation du décalage entre référence et corpus".

## Pre-screening of candidate drugs

Principle: rather than collecting and then testing, drug–target protein co-occurrence is
measured directly by PubMed query, without download or inference. One query returns the
number of articles mentioning both entities in their title or abstract.

Preliminary step: retrieval of the UniProt synonyms of every protein of the 193 candidate
chains (scripts/20_synonymes_masse.py).

Scope of the test: the screening evaluates the first hop of the chains (Drug → Protein).
It is a necessary and not a sufficient condition — the pilot showed that a chain can clear
this first hop and fail on the next one (Filgrastim). Its function is to eliminate drugs
whose literature does not descend to the molecular level, not to guarantee full
reconstructibility.

Revision of the screening: the screening was initially to bear on the first hop alone
(Drug → Protein). Confronted with the pilot results, that criterion proves imprecise:
three of the five drugs clear this first hop, only one yields a usable chain. The
screening therefore bears on every hop of each chain.

Normalisation sources by entity type:
  Protein            → UniProt (46 distinct entities, all with ≥ 2 designations)
  BiologicalProcess  → Gene Ontology, exact and narrow synonyms
  Disease, ChemicalSubstance, PhenotypicFeature → DrugMechDB name used as is

Acknowledged limitation: the DrugMechDB names of diseases and substances are common usage
forms, verified during the pilot (Hypertension detected in 8 abstracts, Major depressive
disorder in 4). No normalisation is applied to these three types for want of a unified
source available within the allotted time; the screening therefore underestimates them
wherever the literature uses an alternative designation.

Normalisation of biological processes at scale: 75 distinct processes queried through Gene
Ontology, of which 32 (42 %) have only one designation, against 0 out of 46 for proteins
through UniProt. The BiologicalProcess layer is therefore structurally the most fragile of
the normalisation chain, which the pilot already indicated: the Filgrastim and epoprostenol
chains cleared the Drug → Protein hop and failed on the Protein → BiologicalProcess link.

Calibration of the screening: the instrument is first applied to the five pilot drugs,
whose outcome is known, before being extended to the 130 candidates. A measuring instrument
that is not verified to reproduce an established result cannot ground any selection.

Limitation of the screening: PubMed search is case-insensitive, which exposes short
acronyms (NET, DAT, TSC) to chance matches. The screening therefore produces false
positives. Its function is elimination, not confirmation: a drug that fails despite
permissive matching is discarded with certainty, whereas a drug retained still has to be
verified after collection.

## Validation of the screening

The instrument was applied to the five pilot drugs, whose outcome was known. It returns the
same verdict: only venlafaxine yields usable chains (4 chains against 5 in the pilot). The
screening is slightly stricter, requiring the drug to be mentioned at every hop — a
constraint consistent with the actual pipeline, collection being carried out drug by drug.

Bottleneck confirmed: the first hop (Drug → Protein) is cleared by most chains, including
those that failed in the pilot (propylthiouracil: 89 articles associating the drug and
thyroid peroxidase in PubMed, against 0 in the 30 abstracts collected). The failure occurs
at the next link, towards the biological process.

Acknowledged bias of the selection criterion: the screening depends on the richness in
synonyms of the entities, which is itself uneven (0 % of proteins against 42 % of processes
have only one designation). It therefore partly measures the quality of the normalisation
rather than the availability of the literature alone. This bias is however identical to
that of the evaluation pipeline, which will use the same synonym table to confront the
extracted relations with the ground truth: a chain undetectable at screening would be no
more validatable at evaluation. The selection thus retains the chains the setup is capable
of measuring, which constitutes an explicit scope restriction and not a defect of method.

## Full screening

193 chains screened, roughly 524 PubMed queries. Raw result: 27 chains with non-zero
co-occurrence at each of their hops, across 23 drugs.

The binary criterion (co-occurrence > 0) proves insufficient: six retained chains rest on a
single article in the whole of PubMed. A general relevance-ranked collection has no
guarantee of including it. A minimum threshold is therefore applied to the lowest
co-occurrence of the chain.

Effect of the threshold: 27 chains / 23 drugs (> 0), 21 / 18 (≥ 2), 16 / 14 (≥ 4), 12 / 11
(≥ 10). The threshold of 4 is retained as the balance point between the volume required (15
to 20 multi-hop chains) and the probability that the collection reaches the carrier
articles.

Consequence for the collection strategy: since co-occurrences are sometimes limited to a
few articles out of several thousand, a general relevance-ranked collection does not
guarantee their presence in the corpus. The collection will therefore be mixed — articles
targeted by the co-occurrence queries, supplemented with general articles on the same drug
serving as distractors.

Scope of this choice: since both architectures are evaluated on an identical corpus, the
comparison remains fair. The restriction bears on external validity: the study measures
performance on a corpus where the chains are present, and not the ability to find them
across the literature at large. Without answer-bearing articles both pipelines would fail
uniformly and the setup would discriminate nothing; without distractors, retrieval would
become trivial and would discriminate no better.

## Analysis of the screened chains

Two defects identified at the threshold of 4:

Lexical triviality — four chains out of sixteen have a bridge entity contained in the name
of the drug or of the disease, which contravenes the definition of multi-hop reasoning. All
belong to the Drug → ChemicalSubstance → Disease pattern. These chains would not
discriminate between the two architectures and would artificially narrow the measured gap.

Mechanistic redundancy — five chains share the protein-process pair "noradrenaline
transporter → noradrenaline reuptake", two the equivalent serotonergic pair. These chains
do not constitute independent measurements: a system succeeding on one will most likely
succeed on the others. The effective sample size of the test set is therefore lower than its
nominal size, which must be taken into account when interpreting variance.

Diversity of patterns — no chain of the Drug → BiologicalProcess → Disease (32 candidates)
or Drug → Protein → PhenotypicFeature → Disease (13 candidates) patterns clears the
threshold. The test set will therefore bear mostly on the Drug → Protein →
BiologicalProcess → Disease pattern. This restriction follows from the weakness of the
normalisation of biological processes (42 % without a synonym).

## Set of chains retained

Co-occurrence threshold 3, after eliminating chains with a lexically trivial bridge entity:
14 chains retained out of 18, covering 9 distinct mechanisms.

Four chains discarded for triviality (Calcium Chloride → Calcium → Hypocalcemia; Potassium
chloride → Potassium → Hypokalemia; potassium citrate → Potassium → Hypokalemia;
hydroxocobalamin → cobalamin → Cobalamin deficiency), all of the Drug → ChemicalSubstance →
Disease pattern.

Nominal and effective sample size: the 14 chains rest on 9 mechanisms, five of them sharing
the noradrenaline transporter / noradrenaline reuptake pair and two the equivalent
serotonergic pair. These chains do not constitute independent observations. Results will be
reported mentioning both counts, the nominal count overstating the precision attainable.

Two risks identified, to be addressed by the closed-book test during the construction of the
test set:
- Pre-training leakage: the chain imatinib → BCR/ABL → chronic myeloid leukaemia is the
  canonical example of targeted therapy and appears in standard teaching literature;
  Clopidogrel → P2Y12 presents an analogous risk.
- Partial triviality: the extended designation of urokinase ("urokinase-type plasminogen
  activator") contains the bridge entity Plasminogen, without the DrugMechDB name revealing
  it.

Attainable volume: 12 three-hop chains each contain two bridge entities and therefore allow
two distinct questions, bearing on different traversals. The potential stands at about 26
questions, whose independence remains bounded by the 9 underlying mechanisms.

Final threshold: 2. The threshold is set on the gain in distinct mechanisms rather than in
number of chains. Moving from 3 to 2 adds two chains carrying two entirely new mechanisms
(terguride → 5-HT2B receptor; lafutidine → H2 receptor → gastric acid secretion), raising
the effective count from 9 to 11 mechanisms for 16 chains.

Since the collection is targeted at the articles carrying each co-occurrence, the
low-frequency chains remain reachable. The residual risk bears on extraction: a link
documented by only two articles offers the model only two opportunities to extract the
relation. Chains with low co-occurrence are therefore more fragile, which will be checked
after extraction.
