# Points to make at the defence

*[Version française](points-soutenance.md)*

## On the schema revision
The measurement revealed the problem, the revision corrected it, a second measurement confirmed it.
→ shows the method is self-correcting rather than hesitant.

## On the calibration of the PubMed query
The [Title/Abstract] filter removes 92 % of the raw results for epoprostenol:
the drug is most often cited outside the body of the article.
→ shows that a naive query would have polluted the corpus.

## On corpus filtering
A 24-word abstract was detected in the initial collection. The naive reflex would have
been to set a length threshold; inspection showed that the real criterion was the
document type — a regulatory notice, not a research article.
→ shows the difference between treating a symptom and treating a cause.

## On the pilot
The initial test concluded that 0 chains out of 16 were covered. The reverse inspection
showed that the concepts were present in their usage forms (SERT, NET, G-CSF receptor).
The test measured the presence of the canonical form, not the feasibility of extraction.
→ shows how important it is to check what a test actually measures before concluding.

## On the value of a negative pilot
The pilot produced 5 usable chains out of 16, concentrated on a single one of the five
drugs. It validated the normalisation mechanism and invalidated the drug selection
criterion — a criterion that rested on a qualitative estimate.
→ shows that a pilot serves as much to refute a working hypothesis as to confirm
feasibility, and that it is better to discover this on 5 cases than on 30.

## On the corpus integrity check
33 identified articles could not be retrieved. The global counters remained normal, but
some chain hops rested on only two articles: losing those two would have made a chain
unusable without any indicator signalling it. The check was therefore carried out hop by
hop rather than on the global volume.
→ shows that a healthy aggregate can mask a local failure.

## On the diagnostic value of an unchanged failure
Between the two iterations the score remained nil but the cause changed: from a relation
absent from the text to a relation extracted under a non-compliant vocabulary. An
identical score can cover two situations that do not call for the same correction.

## On the necessity of manual verification
A random sample of 40 relations from the graph reveals about 10 % polarity inversions —
schema-compliant, syntactically valid, semantically false. No automated check detects
them. The errors moreover cluster by source article, seven of them coming from a single
text.

## On cascading filters
A second, more restrictive test placed after a general test that subsumes it is dead
code: the `continue` of the first prevents the second from being reached. Its counter
stays at zero and wrongly suggests that the case does not occur.

## On diagnosing the baseline's failures
The recall of 0.67 on the control questions was first attributed to truncation of long
abstracts. A comparison of lengths appeared to refute this, but it rested on a 512-token
window that was never checked: the encoder's actual window is 350
tokens, and 35 % of the abstracts exceed it. The refutation was therefore redone by
intervention — indexing only the portion the baseline actually read leaves recall
unchanged. The cause is indeed dilution, and it lies in the weight of the entity within
the representation, not in the length of the document.
→ shows that a plausible hypothesis must be tested, and that a test can itself be wrong
  without being absurd.

## The figure to remember
The graph reaches 0.83 recall with 5 documents — a level vector search does not reach
with 50. The documents missed are not poorly ranked: they are absent from the ranking.
This figure is set against a standard vector baseline; see below what a stronger
baseline takes away from it.

## On cost
The specification asks "at what cost in latency and compute". The answer is twofold: the
graph costs roughly two orders of magnitude more to build (35 min of GPU against under a
minute) and less to operate, being queried without a GPU where the vector pipeline needs
one for every question. Generation latencies are equivalent. The extraction cost belongs
to the upstream data pipeline and could have been left out of the comparison; including
it was necessary.

## On the asymmetric use of the LLM
The graph is built by an LLM, the vector index is not. The result therefore bears on an
architecture-extractor pair, not on the architecture alone. The bias works against the
hypothesis — imperfect extraction degrades the graph without touching the vector index —
and the graph prevails despite it: the measurement is conservative.

## On the correction made after measurement
The canonicalisation function did not transliterate Greek characters, which prevented a
question from being anchored on the graph. The correction bears on the anchoring stage,
downstream of the test set: the ground truth was not modified. Both measurements, before
and after correction, are reported.
→ an implementation defect exists independently of the questions asked; correcting it is
not tuning the system to its own evaluation.

## On generalising an observation from a sample
The effect of the mechanistic filter had been described from five abstracts of the dry
run sample. The measurement on the 493 abstracts of the corpus does not confirm that
description: the filter renews 12 % of the corpus without sorting on the intended
criterion.
→ an observation true of a sample of five does not generalise by default.

## On the departures from the specification
Three prescribed tools were not used: GraphRAG/LightRAG, ChromaDB/FAISS, and the
department's GPU workstation. Each substitution is justified in appendix D of the report.
Stating them explicitly is better than letting an examiner discover them.
LightRAG was eventually used, not as a pipeline but as a reference: its retrieval was run
on our own graph, which compares two retrieval methods on an identical graph. Running it
in full, with its own extraction, proved out of reach of the available hardware — 27.7
hours projected, half the documents failing in the pilot.

## On defining a measurement
Three schema-compliance figures coexisted in the journals: 829, 822 and 820. None was
wrong — each followed a different definition of "compliant". The check consisted in
recomputing all three on the same file rather than choosing between them.
→ a disagreement between two measurements is not necessarily an error; it is often a
definition left implicit.

## On attributing the mechanism
The theoretical argument in favour of Graph RAG is traversal. The measurement shows that
the gap is largest on single-hop questions (+0.33), which require none, and smaller on
multi-hop ones (+0.27 and +0.17). The hierarchy is identical in proportion of error
closed, which dispels the objection of a ceiling effect. An ablation confirms it by
measurement: at depth 1, with no traversal at all, 91 % of the gap remains. Two further
baselines then locate the mechanism: BM25, with no graph whatsoever, recovers three
quarters of the gap, and LightRAG, on our own graph, falls back to the vector level as
soon as it ranks documents by resemblance. The dominant mechanism is therefore the
absence of dilution, not traversal.
→ shows that a result consistent with the overall hypothesis can still refute the
mechanism ascribed to it, and that both must be checked separately.

## On what a stronger baseline takes away
The 0.28-point gap sets the graph against a standard vector baseline. Against BM25 it
falls to 0.07, and against LightRAG set to select its documents by entity it vanishes; in
both cases it ceases to be distinguishable from zero on twenty questions. The result is
therefore not "the graph wins" but "anchoring retrieval on entities wins" — which the
graph does, and which BM25 achieves by another route.
→ stating the limit of a result oneself is better than letting it be discovered.

## On the prediction written before the measurement
The last test — changing LightRAG's passage selection rule — was run after writing down
what it should produce if the explanation was right: the three single-hop questions that
had been missed should come back within the first five documents. They did. The
prediction appears in the text of the notebook, before the computing cells.
→ a prediction written before execution turns a confirmation into a test; written
  afterwards, it is worth nothing.
