# Relecture des chemins candidats

Vérifier pour chaque chemin :
1. les deux relations sont énoncées dans les abstracts cités ;
2. la polarité est correcte (inhibe / active) ;
3. les trois entités relèvent du même domaine ;
4. une question naturelle peut être formulée.

---
---

## Bilan de la relecture

16 chemins examinés : 14 validés, 2 écartés (chemins 3 et 5).
Entités ponts distinctes parmi les validés : 10.

Motifs de rejet : relation énoncée sous réserve modale, relation établie indirectement.
Les deux chemins écartés étaient par ailleurs redondants avec un chemin validé
partageant la même entité pont.

Note sur le chemin 14 (nomifensine → transporteur de la noradrénaline ← paroxetine) :
ce chemin avait été mis en doute par raisonnement de classe, la paroxétine étant un
inhibiteur sélectif de la recapture de la sérotonine. La lecture du PMID 12359676
l'infirme : l'article démontre précisément que la paroxétine inhibe aussi le transporteur
noradrénergique in vivo. Le caractère contre-intuitif de la réponse en fait un bon
élément de jeu de test, un système répondant de mémoire proposant vraisemblablement
un tricyclique.

Les itérations antérieures de la relecture, portant sur des lots de 61 puis 17 chemins,
ont conduit à écarter 13 chemins pour inversion de polarité et 10 pour faux multi-hop.
Ces exclusions sont inscrites dans le code de sélection (scripts/42), les relations
factuellement fausses sous forme de liste portant sur la relation, les rejets propres
à un chemin sous forme de liste distincte.

---
## 1. [pont] Drug → Protein → PhenotypicFeature

**Chemin :** paroxetine --negatively regulates--> **CYP2D6** → nor-imatinib/imatinib metabolic ratio

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 24424469

*A comparative review of escitalopram, paroxetine, and sertraline: Are they all alike?*

> It is known that newer antidepressants, such as the selective serotonin reuptake inhibitors (SSRIs), provide advantages in tolerability over antidepressants such as the tricyclics. However, even within the SSRI class, differences in efficacy or tolerability exist between the individual drugs. Among the three most widely prescribed SSRIs are paroxetine, sertraline, and escitalopram. Escitalopram is commonly referred to as an SSRI, but also has well-documented allosteric properties, and thus can be further classed as an allosteric serotonin reuptake inhibitor. All three antidepressants are efficacious compared with placebo, but there is evidence that escitalopram is more effective than a range of other antidepressants. There are no direct data to regard either paroxetine or sertraline as a superior antidepressant. Escitalopram is superior compared with paroxetine, which has a less favorable tolerability profile. Paroxetine is associated with cholinergic muscarinic antagonism and potent inhibition of CYP2D6, and sertraline has moderate drug interaction issues in comparison with escitalopram. Overall, as an allosteric serotonin reuptake inhibitor that is somewhat different from classical SSRIs, escitalopram is the first choice judged by combined efficacy and tolerability, and nonclinical data have offered possible mechanisms through which escitalopram could be more efficacious, based on its interaction with orthosteric and allosteric binding sites at the serotonin transporter.

### Relation 2 — PMID 36178950

*CYP2D6 and CYP2C8 pharmacogenetics and pharmacological interactions to predict imatinib plasmatic exposure in GIST patients.*

> AIMS: Patients on treatment with oral fixed dose imatinib are frequently under- or overexposed to the drug. We investigated the association between the gene activity score (GAS) of imatinib-metabolizing cytochromes (CYP3A4, CYP3A5, CYP2D6, CYP2C9, CYP2C19, CYP2C8) and imatinib and nor-imatinib exposure. We also investigated the impact of concurrent drug-drug-interactions (DDIs) on the association between GAS and imatinib exposure. METHODS: Serial plasma samples were collected from 33 GIST patients treated with imatinib 400 mg daily within a prospective clinical trial. Imatinib and nor-imatinib C trough were quantified by liquid chromatography with tandem mass spectrometry (LC-MS/MS). Genetic polymorphisms with a functional impact on imatinib-metabolizing cytochromes were identified and a GAS was calculated for each gene. A DDI-adjusted GAS was also generated. RESULTS: Imatinib and nor-imatinib C trough were measured in 161 plasma samples. CYP2D6 GAS and metabolizer status based on genotype were associated with imatinib and (imatinib + nor-imatinib) C trough . CYP2D6 poor and intermediate metabolizers were predicted to have a lower nor-imatinib/imatinib metabolic ratio than normal metabolizers (0.197 and 0.193 vs. 0.247, P = .0205), whereas CYP2C8*3 carriers had a higher ratio than CYP2C8*1/*1 patients (0.263 vs. 0.201, P = .0220). CYP2C9 metabolizer status was inversely related to the metabolic ratio with an effect probably driven by the linkage disequilibrium between CYP2C9*2 and CYP2C8*3. The CYP2D6 DDI-adjusted GAS was still predictive of imatinib exposure. CONCLUSIONS: These findings highlight that CYP2D6 plays a major role in imatinib pharmacokinetics, but other players (i.e., CYP2C8) may influence imatinib exposure. These findings could drive the selection of patients more susceptible to imatinib under- or overexposure who could be candidates for personalized treatment and intensified monitoring strategies.

---

## 2. [pont] Drug → Protein → BiologicalProcess

**Chemin :** cangrelor --decreases activity of--> **P2Y 12 receptor** → PI3 kinase (PI3K) pathway

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 33309519

*Molecular pharmacology of P2Y receptor subtypes.*

> Professor Geoffrey Burnstock proposed the concept of purinergic signaling via P1 and P2 receptors. P2Y receptors are G-protein-coupled receptors (GPCRs) for extracellular adenine and uracil nucleotides. Eight mammalian P2Y receptor subtypes have been identified. They are divided into two subgroups (P2Y 1 , P2Y 2 , P2Y 4 , P2Y 6 , and P2Y 11 ) and (P2Y 12 , P2Y 13 , and P2Y 14 ). P2Y receptors are found in almost all cells and mediate responses in physiology and pathophysiology including pain and inflammation. The antagonism of platelet P2Y 12 receptors by cangrelor, ticagrelor or active metabolites of the thienopyridine compounds ticlopidine, clopidogrel and prasugrel reduces the ADP-induced platelet aggregation in patients with thrombotic complications of vascular diseases. The nucleotide agonist diquafosol acting at P2Y 2 receptors is used for the treatment of the dry eye syndrome. Structural information obtained by crystallography of the human P2Y 1 and P2Y 12 receptor proteins, site-directed mutagenesis and molecular modeling will facilitate the rational design of novel selective drugs.

### Relation 2 — PMID 27628007

*Role of P2Y 12 Receptor in Thrombosis.*

> P2Y 12 receptor is a 342 amino acid Gi-coupled receptor predominantly expressed on platelets. P2Y 12 receptor is physiologically activated by ADP and inhibits adenyl cyclase (AC) to decrease cyclic AMP (cAMP) level, resulting in platelet aggregation. It also activates PI3 kinase (PI3K) pathway leading to fibrinogen receptor activation, and may protect platelets from apoptosis. Abnormalities of P2Y 12 receptor include congenital deficiencies or high activity in diseases like diabetes mellitus (DM) and chronic kidney disease (CKD), exposing such patients to a prothrombotic condition. A series of clinical antiplatelet drugs, such as clopidogrel and ticagrelor, are designed as indirect or direct antagonists of P2Y 12 receptor to reduce incidence of thrombosis mainly for patients of acute coronary syndrome (ACS) who are at high risk of thrombotic events. Studies on novel dual-/multi-target antiplatelet agents consider P2Y 12 receptor as a promising part in combined targets. However, the clinical practical phenomena, such as "clopidogrel resistance" due to gene variations of cytochrome P450 or P2Y 12 receptor constitutive activation, call for better antiplatelet agents. Researches also showed inverse agonist of P2Y 12 receptor could play a better role over neutral antagonists. Personalized antiplatelet therapy is the most ideal destination for antiplatelet therapy in ACS patients with or without other underlying diseases like DM or CKD, however, there is still a long way to go.

---

## 3. [pont] Drug → Protein → BiologicalProcess

**Chemin :** cangrelor --decreases activity of--> **P2Y 12 receptor** → apoptosis

**Décision :** [ ] VALIDE   [x] ÉCARTÉ   —  motif : relation énoncée sous réserve
(l'abstract écrit « may protect platelets from apoptosis ») ; redondant avec le chemin 2,
même départ et même entité pont.

### Relation 1 — PMID 33309519

*Molecular pharmacology of P2Y receptor subtypes.*

> Professor Geoffrey Burnstock proposed the concept of purinergic signaling via P1 and P2 receptors. P2Y receptors are G-protein-coupled receptors (GPCRs) for extracellular adenine and uracil nucleotides. Eight mammalian P2Y receptor subtypes have been identified. They are divided into two subgroups (P2Y 1 , P2Y 2 , P2Y 4 , P2Y 6 , and P2Y 11 ) and (P2Y 12 , P2Y 13 , and P2Y 14 ). P2Y receptors are found in almost all cells and mediate responses in physiology and pathophysiology including pain and inflammation. The antagonism of platelet P2Y 12 receptors by cangrelor, ticagrelor or active metabolites of the thienopyridine compounds ticlopidine, clopidogrel and prasugrel reduces the ADP-induced platelet aggregation in patients with thrombotic complications of vascular diseases. The nucleotide agonist diquafosol acting at P2Y 2 receptors is used for the treatment of the dry eye syndrome. Structural information obtained by crystallography of the human P2Y 1 and P2Y 12 receptor proteins, site-directed mutagenesis and molecular modeling will facilitate the rational design of novel selective drugs.

### Relation 2 — PMID 27628007

*Role of P2Y 12 Receptor in Thrombosis.*

> P2Y 12 receptor is a 342 amino acid Gi-coupled receptor predominantly expressed on platelets. P2Y 12 receptor is physiologically activated by ADP and inhibits adenyl cyclase (AC) to decrease cyclic AMP (cAMP) level, resulting in platelet aggregation. It also activates PI3 kinase (PI3K) pathway leading to fibrinogen receptor activation, and may protect platelets from apoptosis. Abnormalities of P2Y 12 receptor include congenital deficiencies or high activity in diseases like diabetes mellitus (DM) and chronic kidney disease (CKD), exposing such patients to a prothrombotic condition. A series of clinical antiplatelet drugs, such as clopidogrel and ticagrelor, are designed as indirect or direct antagonists of P2Y 12 receptor to reduce incidence of thrombosis mainly for patients of acute coronary syndrome (ACS) who are at high risk of thrombotic events. Studies on novel dual-/multi-target antiplatelet agents consider P2Y 12 receptor as a promising part in combined targets. However, the clinical practical phenomena, such as "clopidogrel resistance" due to gene variations of cytochrome P450 or P2Y 12 receptor constitutive activation, call for better antiplatelet agents. Researches also showed inverse agonist of P2Y 12 receptor could play a better role over neutral antagonists. Personalized antiplatelet therapy is the most ideal destination for antiplatelet therapy in ACS patients with or without other underlying diseases like DM or CKD, however, there is still a long way to go.

---

## 4. [pont] Drug → Protein → BiologicalProcess

**Chemin :** Amiloride --decreases activity of--> **plasmin** → myogenesis

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 28656379

*Physiology and pathophysiology of the plasminogen system in the kidney.*

> The plasminogen system is important for fibrinolysis in addition to tissue remodeling and inflammation with significance for kidney disease. The system consists of the circulating zymogen plasminogen (Plg) and the tissue- and urokinase-type plasminogen activators, tPA and uPA, expressed in the glomeruli, endothelium and tubular epithelium, respectively, and the inhibitors α 2 -antiplasmin and plasminogen activator inhibitor-type1, PAI-1. Plasminogen is activated by surface receptors, some with renal expression: urokinase-type plasminogen activator receptor (uPAR), plasminogen receptor KT (Plg-R KT ), and tPA, most evident in the endothelium. Plasmin may exert effects through protease-activated receptors, PARs, expressed in the kidney. Deletion of plasminogen system component genes confers no major developmental or renal phenotypes in normal mice. In glomerular injury and renal interstitial fibrosis, deletion of various components, notably Plg, uPA, PAI, and uPAR is associated with protection suggesting a disease promoting effect of plasmin, in some cases exerted through PAR1 receptor activation. Plasminogen and uPA are aberrantly filtrated across the glomerular barrier in proteinuria, and plasminogen is activated in the tubular fluid. In the tubular fluid, plasmin may activate proteolytically the epithelial sodium channel (ENaC) and inhibit the apical calcium transporter transient receptor potential cation channel subfamily V member 5 (TRPV5), which could explain impaired sodium excretion and enhanced calcium excretion in proteinuria. Amiloride, a potassium-sparing diuretic, inhibits urokinase and plasmin activation in the tubular fluid and uPAR expression in vitro, which highlights new indications for an old drug. Protease inhibitors lowered blood pressure and antagonized fibrosis in salt-sensitive Dahl rats. Current knowledge indicates that the plasminogen system aggravates renal disease by direct and indirect hypertensive effects and is a promising target to antagonize disease progression.

### Relation 2 — PMID 15574344

*Alpha-enolase plasminogen receptor in myogenesis.*

> Plasmin is a potent extracellular protease specialized in the degradation of fibrin (fibrinolysis). Active plasmin is generated by proteolytic activation of the zymogen plasminogen (Plg) by urokinase-type plasminogen activator (uPA) and tissue-type plasminogen activator (tPA). Alpha-enolase, although traditionally considered a glycolytic enzyme, constitutes a receptor for plasminogen on several cell types, serving to localize and promote plasminogen activation pericellularly. Localization of plasmin activity on the cell surface plays a critical role in fibrinolysis and in physiopathological processes involving extracellular matrix remodelling. Previous studies have unambiguously demonstrated that uPA-dependent plasmin generation is necessary for myogenesis in vitro and for muscle regeneration in vivo. However, the implication of alpha-enolase plasminogen receptor in myogenesis had never been investigated. This review focuses on the recently reported expression and function of alpha-enolase plasminogen receptor during myogenesis. Skeletal myoblasts express alpha-enolase plasminogen receptor, being its expression greatly induced during the differentiation process in vitro. MAb 11G1, a monoclonal antibody against anti-alpha-enolase plasminogen receptor, that inhibits plasmin generation, was able to fully abrogate myoblast fusion and differentiation. Moreover, both plasmin activity and alpha-enolase plasminogen receptor expression were significantly augmented in injury-induced regenerating muscle of wild type mice and in the dystrophic muscle of mdx mice, an animal model of Duchenne muscular dystrophy (DMD). Altogether, these results indicate that the plasminogen activation (PA) system is an important component of skeletal myogenesis in vitro and in vivo. In particular, the expression of alpha-enolase plasminogen receptor may serve to concentrate and enhance plasmin generation on the cell surface of migratory myoblasts contributing to efficient muscle repair.

---

## 5. [pont] Drug → Protein → BiologicalProcess

**Chemin :** Amiloride --decreases activity of--> **plasmin** → myoblast fusion

**Décision :** [ ] VALIDE   [x] ÉCARTÉ   —  motif : la relation plasmine → fusion
myoblastique n'est établie qu'indirectement, par l'effet d'un anticorps sur la génération
de plasmine ; redondant avec le chemin 4.

### Relation 1 — PMID 28656379

*Physiology and pathophysiology of the plasminogen system in the kidney.*

> The plasminogen system is important for fibrinolysis in addition to tissue remodeling and inflammation with significance for kidney disease. The system consists of the circulating zymogen plasminogen (Plg) and the tissue- and urokinase-type plasminogen activators, tPA and uPA, expressed in the glomeruli, endothelium and tubular epithelium, respectively, and the inhibitors α 2 -antiplasmin and plasminogen activator inhibitor-type1, PAI-1. Plasminogen is activated by surface receptors, some with renal expression: urokinase-type plasminogen activator receptor (uPAR), plasminogen receptor KT (Plg-R KT ), and tPA, most evident in the endothelium. Plasmin may exert effects through protease-activated receptors, PARs, expressed in the kidney. Deletion of plasminogen system component genes confers no major developmental or renal phenotypes in normal mice. In glomerular injury and renal interstitial fibrosis, deletion of various components, notably Plg, uPA, PAI, and uPAR is associated with protection suggesting a disease promoting effect of plasmin, in some cases exerted through PAR1 receptor activation. Plasminogen and uPA are aberrantly filtrated across the glomerular barrier in proteinuria, and plasminogen is activated in the tubular fluid. In the tubular fluid, plasmin may activate proteolytically the epithelial sodium channel (ENaC) and inhibit the apical calcium transporter transient receptor potential cation channel subfamily V member 5 (TRPV5), which could explain impaired sodium excretion and enhanced calcium excretion in proteinuria. Amiloride, a potassium-sparing diuretic, inhibits urokinase and plasmin activation in the tubular fluid and uPAR expression in vitro, which highlights new indications for an old drug. Protease inhibitors lowered blood pressure and antagonized fibrosis in salt-sensitive Dahl rats. Current knowledge indicates that the plasminogen system aggravates renal disease by direct and indirect hypertensive effects and is a promising target to antagonize disease progression.

### Relation 2 — PMID 15574344

*Alpha-enolase plasminogen receptor in myogenesis.*

> Plasmin is a potent extracellular protease specialized in the degradation of fibrin (fibrinolysis). Active plasmin is generated by proteolytic activation of the zymogen plasminogen (Plg) by urokinase-type plasminogen activator (uPA) and tissue-type plasminogen activator (tPA). Alpha-enolase, although traditionally considered a glycolytic enzyme, constitutes a receptor for plasminogen on several cell types, serving to localize and promote plasminogen activation pericellularly. Localization of plasmin activity on the cell surface plays a critical role in fibrinolysis and in physiopathological processes involving extracellular matrix remodelling. Previous studies have unambiguously demonstrated that uPA-dependent plasmin generation is necessary for myogenesis in vitro and for muscle regeneration in vivo. However, the implication of alpha-enolase plasminogen receptor in myogenesis had never been investigated. This review focuses on the recently reported expression and function of alpha-enolase plasminogen receptor during myogenesis. Skeletal myoblasts express alpha-enolase plasminogen receptor, being its expression greatly induced during the differentiation process in vitro. MAb 11G1, a monoclonal antibody against anti-alpha-enolase plasminogen receptor, that inhibits plasmin generation, was able to fully abrogate myoblast fusion and differentiation. Moreover, both plasmin activity and alpha-enolase plasminogen receptor expression were significantly augmented in injury-induced regenerating muscle of wild type mice and in the dystrophic muscle of mdx mice, an animal model of Duchenne muscular dystrophy (DMD). Altogether, these results indicate that the plasminogen activation (PA) system is an important component of skeletal myogenesis in vitro and in vivo. In particular, the expression of alpha-enolase plasminogen receptor may serve to concentrate and enhance plasmin generation on the cell surface of migratory myoblasts contributing to efficient muscle repair.

---

## 6. [intersection] Drug → Protein → Drug

**Chemin :** ergotamine --positively regulates--> **5-HT2B receptors** ← bromocriptine

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 25712664

*Ergotamine and nicergoline - facts and myths.*

> Ergotamine, being a representative of naturally occurring ergoline alkaloids, derived from d-lysergic acid, and nicergoline, a d-lumilysergic acid derivative belonging to semi-synthetic ergot-derived alkaloids, display diversified affinity for adrenergic, serotoninergic, and dopamine receptors. Although introduction of triptans marginalized use of ergotamine, nicergoline is used in cerebral metabolic-vascular disorders, and dementia. Additionally, nicergoline exhibits a safety profile comparable to that of placebo, and none of the reviewed studies reported any incidence of fibrosis or ergotism with nicergoline treatment. In line with the recent data, activation of 5-HT2B receptor by ergot derivatives i.e. ergotamine, methysergide, pergolide, and carbegoline is involved in pathogenesis of drug-induced valvulopathy. In contrary structurally related drugs - lisuride and terguride do not increase the risk of valvular heart disease. It seems, that more detailed mechanistic studies on nicergoline and ergotamine might be beneficial for determining structural requirements related to activation of G-protein as well as alternative signal transduction pathways e.g. β-arrestins or different kinases, and responsible for drug liabilities.

### Relation 2 — PMID 15862804

*Agonism at 5-HT2B receptors is not a class effect of the ergolines.*

> Restrictive cardiac valvulopathies observed in Parkinson patients treated with the ergoline dopamine agonist pergolide have recently been associated with the agonist efficacy of the drug at 5-hydroxytryptamine2B (5-HT2B) receptors. To evaluate whether agonism at 5-HT2B receptors is a phenomenon of the class of the ergolines, we studied 5-HT2B receptor-mediated relaxation in porcine pulmonary arteries to five ergolines which are used as antiparkinsonian drugs. Pergolide and cabergoline were potent full agonists in this tissue (pEC50 8.42 and 8.72). Bromocriptine acted as a partial agonist (pEC50 6.86). Lisuride and terguride, however, failed to relax the arteries but potently antagonized 5-HT-induced relaxation (pKB 10.32 and 8.49). Thus, agonism at 5-HT2B receptors seems not to be a class effect of the ergolines.

---

## 7. [intersection] Drug → BiologicalProcess → Drug

**Chemin :** ranibizumab --decreases activity of--> **angiogenesis** ← ramucirumab

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 35105268

*Monoclonal antibodies in diabetic retinopathy.*

> INTRODUCTION: Diabetic retinopathy (DR), as one of the main complications of diabetes, is among the leading causes of blindness and visual impairment worldwide. AREAS COVERED: Current clinical therapies include photocoagulation, vitrectomy, and anti-vascular endothelial growth factor (VEGF) therapies. Bevacizumab and ranibizumab are two monoclonal antibodies (mAbs) inhibiting angiogenesis. Intravitreal ranibizumab and bevacizumab can decrease the rate of blindness and retinal thickness, and improve visual acuity whether as monotherapy or combined with other treatments. They can increase the efficacy of other treatments and decrease their adverse events. Although administered intravitreally, they also might enter the circulation and cause systemic effects. This study is aimed to review our current knowledge about mAbs, bevacizumab and ranibizumab, in DR including superiorities, challenges, and limitations. Meanwhile, we tried to shed light on new ideas to overcome these limitations. Our latest search was done in April 2021 mainly through PubMed and Google Scholar. Relevant clinical studies were imported. EXPERT OPINION: Future direction includes detection of more therapeutic targets considering other components of DR pathophysiology and shared pathogenesis of DR and neurodegenerative diseases, such as Parkinson s disease and Alzheimer s disease, the treat-and-extend regimen, and new ways of drug delivery and other routes of ocular drug administration.

### Relation 2 — PMID 39453771

*Efficacy, Safety, and Influence on the Tumor Microenvironment of Neoadjuvant Pembrolizumab plus Ramucirumab for PD-L1-Positive NSCLC: A Phase II Trial (EAST ENERGY).*

> PURPOSE: Angiogenesis inhibitors are known to modify tumor immunity. Combination of angiogenesis inhibitors with immune checkpoint inhibitors has shown efficacy against many types of cancers, including non-small cell lung cancer (NSCLC). We investigated the feasibility of neoadjuvant therapy with pembrolizumab and ramucirumab, a VEGFR-2 antagonist for patients with PD-L1-positive NSCLC, and its influence on the tumor microenvironment. PATIENTS AND METHODS: Patients with pathologically proven, PD-L1-positive, clinical stage IB to IIIA NSCLC were eligible. Patients received two cycles of pembrolizumab (200 mg/body) and ramucirumab (10 mg/kg) every 3 weeks. Surgery was scheduled 4 to 8 weeks after the last dose. The primary endpoint was the major pathologic response rate by a blinded independent pathologic review. The sample size was 24 patients. Exploratory endpoints were evaluated to elucidate the effects of neoadjuvant therapy on the tumor microenvironment. RESULTS: The 24 eligible patients were enrolled between July 2019 and April 2022. The major pathologic response rate was 50.0% (90% confidence interval, 31.9%-68.1%). Six patients showed pathologic complete response. Grade 3 adverse events (AE) occurred in nine patients (37.5%), including three immune-related AEs (acute tubulointerstitial nephritis in two cases and polymyalgia rheumatica in one case). There were no grade 4 or 5 AEs. The transcriptome and multiplex IHC results suggested that tumors with greater CD8+ T-cell infiltration and higher expression of effector molecules at the baseline could show better sensitivity to treatment. CONCLUSIONS: This new neoadjuvant combination of pembrolizumab plus ramucirumab was feasible, and anti-VEGF agents may enhance the effects of immune checkpoint inhibitors.

---

## 8. [intersection] Drug → BiologicalProcess → Drug

**Chemin :** ranibizumab --decreases activity of--> **angiogenesis** ← nintedanib

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 35105268

*Monoclonal antibodies in diabetic retinopathy.*

> INTRODUCTION: Diabetic retinopathy (DR), as one of the main complications of diabetes, is among the leading causes of blindness and visual impairment worldwide. AREAS COVERED: Current clinical therapies include photocoagulation, vitrectomy, and anti-vascular endothelial growth factor (VEGF) therapies. Bevacizumab and ranibizumab are two monoclonal antibodies (mAbs) inhibiting angiogenesis. Intravitreal ranibizumab and bevacizumab can decrease the rate of blindness and retinal thickness, and improve visual acuity whether as monotherapy or combined with other treatments. They can increase the efficacy of other treatments and decrease their adverse events. Although administered intravitreally, they also might enter the circulation and cause systemic effects. This study is aimed to review our current knowledge about mAbs, bevacizumab and ranibizumab, in DR including superiorities, challenges, and limitations. Meanwhile, we tried to shed light on new ideas to overcome these limitations. Our latest search was done in April 2021 mainly through PubMed and Google Scholar. Relevant clinical studies were imported. EXPERT OPINION: Future direction includes detection of more therapeutic targets considering other components of DR pathophysiology and shared pathogenesis of DR and neurodegenerative diseases, such as Parkinson s disease and Alzheimer s disease, the treat-and-extend regimen, and new ways of drug delivery and other routes of ocular drug administration.

### Relation 2 — PMID 28934120

*Angiogenesis Inhibitors in NSCLC.*

> Angiogenesis is a complex biological process that plays a relevant role in sustaining the microenvironment, growth, and metastatic potential of several tumors, including non-small cell lung cancer (NSCLC). Bevacizumab was the first angiogenesis inhibitor approved for the treatment of patients with advanced NSCLC in combination with chemotherapy; however, it was limited to patients with non-squamous histology and first-line setting. Approval was based on the results of two phase III trials (ECOG4599 and AVAIL) that demonstrated an improvement of about two months in progression-free survival (PFS) in both trials, and in the ECOG4599 trial, an improvement in overall survival (OS) also. Afterwards, other antiangiogenic agents, including sunitinib, sorafenib, and vandetanib have been unsuccessfully tested in first and successive lines. Recently, two new antiangiogenic agents (ramucirumab and nintedanib) produced a significant survival benefit in second-line setting. In the REVEL study, ramucirumab plus docetaxel prolonged the median OS of patients with any histology NSCLC when compared with docetaxel alone (10.4 versus 9.1 months, hazard ratio (HR) 0.857, p = 0.0235). In the LUME-Lung 1 study, nintedanib plus docetaxel prolonged the median PFS of patients with any tumor histology ( p = 0.0019), and improved OS (12.6 versus 10.3 months) in patients with adenocarcinoma. As a result, it became a new option for the second-line treatment of patients with advanced NSCLC and adenocarcinoma histology. Identifying predictive biomarkers to optimize the benefit of antiangiogenic drugs remains an ongoing challenge.

---

## 9. [intersection] Drug → PhenotypicFeature → Drug

**Chemin :** finasteride --causes--> **ejaculation disorder** ← escitalopram

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 29447628

*Sexual side effects of 5-α-reductase inhibitors finasteride and dutasteride: A comprehensive review.*

> The 5-α-reductase inhibitors finasteride and dutasteride are frequently used in the treatment of androgenetic alopecia and benign prostatichyperplasia. These drugs are effective at reducing levels of dihydrotestosterone, the primary androgen responsible for the pathogenesis of both these conditions. However, finasteride and dutasteride have also been shown to produce an increase in the incidence of sexual dysfunction, namely, impotence, decreased libido, and ejaculation disorder. The purpose of this study is to review the existing medical literature with regard to the sexual side effects of 5-α-reductase inhibitor therapy. This review is an extensive look at the sexual effects of 5-α-reductase inhibitors and compares outcomes for finasteride versus dutasteride in addition to comparing sexualside effects for each of the different dosages prescribed of finasteride and dutasteride.

### Relation 2 — PMID 12387707

*Escitalopram.*

> Escitalopram oxalate (S-citalopram, Lexapro), a selective serotonin re-uptake inhibitor antidepressant which is the S-enantiomer of citalopram, is in clinical development worldwide for the treatment of depression and anxiety disorders. Preclinical studies demonstrate that the therapeutic activity of citalopram resides in the S-isomer and that escitalopram binds with high affinity to the human serotonin transporter. Conversely, R-citalopram is approximately 30-fold less potent than escitalopram at this transporter. Escitalopram has linear pharmacokinetics, so that plasma levels increase proportionately and predictably with increased doses and its half-life of 27 - 32 h is consistent with once-daily dosing. In addition, escitalopram has negligible effects on cytochrome P450 drug-metabolising enzymes in vitro, suggesting a low potential for drug-drug interactions. The efficacy of escitalopram in patients with major depressive disorder has been demonstrated in multiple short-term, placebo-controlled clinical trials, three of which included citalopram as an active control, as well as in a 36-week study evaluating efficacy in the prevention of depression relapse. In these studies, escitalopram was shown to have robust efficacy in the treatment of depression and associated symptoms of anxiety relative to placebo. Efficacy has also been shown in treating generalised anxiety disorder, panic disorder and social anxiety disorder. Results also suggest that, at comparable doses, escitalopram demonstrates clinically relevant and statistically significant superiority to placebo treatment earlier than citalopram. Analysis of the safety database shows a low rate of discontinuation due to adverse events, and there was no statistically significant difference between escitalopram 10 mg/day and placebo in the proportion of patients who discontinued treatment early because of adverse events. The most common adverse events associated with escitalopram which occurred at a rate greater than placebo include nausea, insomnia, ejaculation disorder, diarrhoea, dry mouth and somnolence. Only nausea occurred in > 10% of escitalopram-treated patients.

---

## 10. [intersection] Drug → PhenotypicFeature → Drug

**Chemin :** dutasteride --causes--> **ejaculation disorder** ← escitalopram

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 29447628

*Sexual side effects of 5-α-reductase inhibitors finasteride and dutasteride: A comprehensive review.*

> The 5-α-reductase inhibitors finasteride and dutasteride are frequently used in the treatment of androgenetic alopecia and benign prostatichyperplasia. These drugs are effective at reducing levels of dihydrotestosterone, the primary androgen responsible for the pathogenesis of both these conditions. However, finasteride and dutasteride have also been shown to produce an increase in the incidence of sexual dysfunction, namely, impotence, decreased libido, and ejaculation disorder. The purpose of this study is to review the existing medical literature with regard to the sexual side effects of 5-α-reductase inhibitor therapy. This review is an extensive look at the sexual effects of 5-α-reductase inhibitors and compares outcomes for finasteride versus dutasteride in addition to comparing sexualside effects for each of the different dosages prescribed of finasteride and dutasteride.

### Relation 2 — PMID 12387707

*Escitalopram.*

> Escitalopram oxalate (S-citalopram, Lexapro), a selective serotonin re-uptake inhibitor antidepressant which is the S-enantiomer of citalopram, is in clinical development worldwide for the treatment of depression and anxiety disorders. Preclinical studies demonstrate that the therapeutic activity of citalopram resides in the S-isomer and that escitalopram binds with high affinity to the human serotonin transporter. Conversely, R-citalopram is approximately 30-fold less potent than escitalopram at this transporter. Escitalopram has linear pharmacokinetics, so that plasma levels increase proportionately and predictably with increased doses and its half-life of 27 - 32 h is consistent with once-daily dosing. In addition, escitalopram has negligible effects on cytochrome P450 drug-metabolising enzymes in vitro, suggesting a low potential for drug-drug interactions. The efficacy of escitalopram in patients with major depressive disorder has been demonstrated in multiple short-term, placebo-controlled clinical trials, three of which included citalopram as an active control, as well as in a 36-week study evaluating efficacy in the prevention of depression relapse. In these studies, escitalopram was shown to have robust efficacy in the treatment of depression and associated symptoms of anxiety relative to placebo. Efficacy has also been shown in treating generalised anxiety disorder, panic disorder and social anxiety disorder. Results also suggest that, at comparable doses, escitalopram demonstrates clinically relevant and statistically significant superiority to placebo treatment earlier than citalopram. Analysis of the safety database shows a low rate of discontinuation due to adverse events, and there was no statistically significant difference between escitalopram 10 mg/day and placebo in the proportion of patients who discontinued treatment early because of adverse events. The most common adverse events associated with escitalopram which occurred at a rate greater than placebo include nausea, insomnia, ejaculation disorder, diarrhoea, dry mouth and somnolence. Only nausea occurred in > 10% of escitalopram-treated patients.

---

## 11. [intersection] Drug → BiologicalProcess → Drug

**Chemin :** insulin --decreases activity of--> **norepinephrine reuptake** ← maprotiline

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 8221132

*The effect of insulin on norepinephrine uptake by PC12 cells.*

> We have previously reported that insulin can enhance endogenous noradrenergic activity in vitro in the rat CNS. In the present study, we examined one potential mechanism underlying this effect: the ability of insulin to inhibit norepinephrine (NE) reuptake and secondarily increase its synaptic concentration. Acute (20 min) insulin treatment (0.1-10 nM) significantly inhibited specific 3H-norepinephrine uptake by rat hypothalamic slices. To ascertain whether this is a direct effect of insulin on cells that can synthesize and release norepinephrine, we studied NE uptake by the rat pheochromocytoma PC12 cell line. In PC12 cells, insulin (0.5-10 nM) inhibited NE uptake whereas the related peptide, insulin-like growth factor 1 (IGF-1), did not. Insulin did not compete with 3H-mazindol (a ligand for the NE reuptake transporter) binding to PC12 cell membranes. Thus, this effect of insulin is not due to interaction with either IGF-1 receptors or the norepinephrine transporter, but may be due to insulin interaction with its own receptor. Chronic (96-h) insulin treatment of PC12 cells also resulted in an inhibition of 3H-norepinephrine uptake, and membranes prepared from cells chronically treated with insulin bound less 3H-desipramine than control membranes. Thus, chronic insulin treatment may result in a decrease in the numbers of membrane-associated transporters. We conclude that insulin has a direct and physiological role in the modulation of synaptic norepinephrine levels by modulating reuptake by cells that synthesize and release norepinephrine.

### Relation 2 — PMID 27292786

*α2 Adrenoceptor: a Target for Neuropathic Pain Treatment.*

> Neuropathic pain is originated from different alterations of the nervous system. The difficulty of treatment strongly impairs quality of life of affected people. It is associated with severe, chronic sensory disturbances characterized by spontaneous pain, increased responsiveness to painful stimuli and pain perceived in response to normally non-noxious stimuli. The underlying mechanisms are complex and involve both peripheral and central nervous components. The noradrenergic system plays a pivotal role in the control of pain since its widespread distribution in the "pain matrix" representing a valuable therapeutic target. This review focused on the α2 adrenoceptor subtype modulation as strategy for neuropathic pain relief. Drugs acting as direct α2 adrenoceptor agonists (clonidine and dexmedetomidine) were analyzed as well as the indirect α2 adrenoceptor modulators. The overview included norepinephrine reuptake inhibitors (reboxetine, maprotiline), serotonin/norepinephrine reuptake inhibitors (venlafaxine, milnacipran, amitriptyline, duloxetine, bicifadine) and the compounds characterized by a double pharmacodynamic mechanism combining the norepinephrine reuptake inhibition and the μ opioid agonist profile (tramadol and tapentadol). A summary of recent compounds was illustrated.

---

## 12. [intersection] Drug → BiologicalProcess → Drug

**Chemin :** insulin --decreases activity of--> **norepinephrine reuptake** ← venlafaxine

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 8221132

*The effect of insulin on norepinephrine uptake by PC12 cells.*

> We have previously reported that insulin can enhance endogenous noradrenergic activity in vitro in the rat CNS. In the present study, we examined one potential mechanism underlying this effect: the ability of insulin to inhibit norepinephrine (NE) reuptake and secondarily increase its synaptic concentration. Acute (20 min) insulin treatment (0.1-10 nM) significantly inhibited specific 3H-norepinephrine uptake by rat hypothalamic slices. To ascertain whether this is a direct effect of insulin on cells that can synthesize and release norepinephrine, we studied NE uptake by the rat pheochromocytoma PC12 cell line. In PC12 cells, insulin (0.5-10 nM) inhibited NE uptake whereas the related peptide, insulin-like growth factor 1 (IGF-1), did not. Insulin did not compete with 3H-mazindol (a ligand for the NE reuptake transporter) binding to PC12 cell membranes. Thus, this effect of insulin is not due to interaction with either IGF-1 receptors or the norepinephrine transporter, but may be due to insulin interaction with its own receptor. Chronic (96-h) insulin treatment of PC12 cells also resulted in an inhibition of 3H-norepinephrine uptake, and membranes prepared from cells chronically treated with insulin bound less 3H-desipramine than control membranes. Thus, chronic insulin treatment may result in a decrease in the numbers of membrane-associated transporters. We conclude that insulin has a direct and physiological role in the modulation of synaptic norepinephrine levels by modulating reuptake by cells that synthesize and release norepinephrine.

### Relation 2 — PMID 27292786

*α2 Adrenoceptor: a Target for Neuropathic Pain Treatment.*

> Neuropathic pain is originated from different alterations of the nervous system. The difficulty of treatment strongly impairs quality of life of affected people. It is associated with severe, chronic sensory disturbances characterized by spontaneous pain, increased responsiveness to painful stimuli and pain perceived in response to normally non-noxious stimuli. The underlying mechanisms are complex and involve both peripheral and central nervous components. The noradrenergic system plays a pivotal role in the control of pain since its widespread distribution in the "pain matrix" representing a valuable therapeutic target. This review focused on the α2 adrenoceptor subtype modulation as strategy for neuropathic pain relief. Drugs acting as direct α2 adrenoceptor agonists (clonidine and dexmedetomidine) were analyzed as well as the indirect α2 adrenoceptor modulators. The overview included norepinephrine reuptake inhibitors (reboxetine, maprotiline), serotonin/norepinephrine reuptake inhibitors (venlafaxine, milnacipran, amitriptyline, duloxetine, bicifadine) and the compounds characterized by a double pharmacodynamic mechanism combining the norepinephrine reuptake inhibition and the μ opioid agonist profile (tramadol and tapentadol). A summary of recent compounds was illustrated.

---

## 13. [intersection] Drug → Protein → Drug

**Chemin :** venlafaxine --decreases activity of--> **norepinephrine transporter** ← nomifensine

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 37156838

*Venlafaxine antagonizes the noradrenaline-promoted colon cancer progression by inhibiting the norepinephrine transporter.*

> Epidemiological studies have demonstrated that the use of antidepressants is associated with a decreased risk of colorectal cancer (CRC); however, the mechanisms behind this association are yet unknown. Adrenergic system contributes to the stress-related tumor progression, with norepinephrine (NE) mainly secreted from adrenergic nerve fibers. Norepinephrine serotonin reuptake inhibitors are successfully used antidepressants. This study demonstrates that a widely used antidepressant venlafaxine (VEN) antagonizes NE-promoted colon cancer in vivo and in vitro. Bioinformatic analysis suggested that NE transporter (NET, SLC6A2), a target of VEN, was closely associated with the prognosis of clinical patients with CRC. In addition, the knockdown of NET antagonized the effect of NE. The NET-protein phosphatase 2 scaffold subunit alpha/phosphorylated Akt/vascular endothelial growth factor pathway partially mediates the antagonizing effect of VEN on NE's actions in colon cancer cells. These were also confirmed by in vivo experiments. Our findings revealed for the first time that, in addition to its primary function as a transporter, NET also promotes NE-enhanced colon cancer cell proliferation, tumor angiogenesis, and tumor growth. This provides direct experimental and mechanistic evidence for the use of antidepressant VEN in the treatment of CRC and a therapeutic potential for repurposing existing drugs as an anti-cancer approach to improve the prognosis of patients with CRC.

### Relation 2 — PMID 8448143

*Expression of a cocaine-sensitive norepinephrine transporter in the human placental syncytiotrophoblast.*

> Maternal-facing brush border membrane vesicles isolated from normal term human placentas were found to accumulate norepinephrine in a concentrative manner in the presence of an inwardly directed NaCl gradient. Both Na+ and Cl- were obligatory for maximal uptake. The NaCl-dependent norepinephrine uptake was further stimulated by the presence of K+ or an acidic pH in the intravesicular medium. The uptake process was electrogenic, being stimulated by an inside-negative membrane potential, and this characteristic was observed in the absence as well as in the presence of K+ inside the vesicles. Kinetic analyses revealed that one Na+ and one Cl- were involved per transport of one norepinephrine molecule. The apparent Michaelis-Menten constant for norepinephrine was 104 +/- 5nM. The uptake process exhibited higher affinity for dopamine than for norepinephrine but had low affinity for serotonin and histamine. The uptake of norepinephrine was inhibited very effectively by nomifensine, desipramine, imipramine, and cocaine, but much less effectively by bupropion and GBR 12909. Northern blot analysis with the cDNA of the human (SK-N-SH cell) norepinephrine transporter as the probe revealed that the human placenta contained two mRNAs, 5.8 and 3.6 kb in size, which hybridized to the probe. The JAR human placental choriocarcinoma cells were found unable to accumulate norepinephrine in a NaCl-dependent manner. These cells were also found not to contain mRNAs which hybridized to the norepinephrine cDNA probe in northern blot. It is concluded that the human placental syncytiotrophoblast expresses a cocaine-sensitive norepinephrine transporter and that these findings may be directly relevant and important to the clinical complications of maternal cocaine abuse during pregnancy.

---

## 14. [intersection] Drug → Protein → Drug

**Chemin :** nomifensine --decreases activity of--> **norepinephrine transporter** ← paroxetine

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 8448143

*Expression of a cocaine-sensitive norepinephrine transporter in the human placental syncytiotrophoblast.*

> Maternal-facing brush border membrane vesicles isolated from normal term human placentas were found to accumulate norepinephrine in a concentrative manner in the presence of an inwardly directed NaCl gradient. Both Na+ and Cl- were obligatory for maximal uptake. The NaCl-dependent norepinephrine uptake was further stimulated by the presence of K+ or an acidic pH in the intravesicular medium. The uptake process was electrogenic, being stimulated by an inside-negative membrane potential, and this characteristic was observed in the absence as well as in the presence of K+ inside the vesicles. Kinetic analyses revealed that one Na+ and one Cl- were involved per transport of one norepinephrine molecule. The apparent Michaelis-Menten constant for norepinephrine was 104 +/- 5nM. The uptake process exhibited higher affinity for dopamine than for norepinephrine but had low affinity for serotonin and histamine. The uptake of norepinephrine was inhibited very effectively by nomifensine, desipramine, imipramine, and cocaine, but much less effectively by bupropion and GBR 12909. Northern blot analysis with the cDNA of the human (SK-N-SH cell) norepinephrine transporter as the probe revealed that the human placenta contained two mRNAs, 5.8 and 3.6 kb in size, which hybridized to the probe. The JAR human placental choriocarcinoma cells were found unable to accumulate norepinephrine in a NaCl-dependent manner. These cells were also found not to contain mRNAs which hybridized to the norepinephrine cDNA probe in northern blot. It is concluded that the human placental syncytiotrophoblast expresses a cocaine-sensitive norepinephrine transporter and that these findings may be directly relevant and important to the clinical complications of maternal cocaine abuse during pregnancy.

### Relation 2 — PMID 12359676

*Inhibition of norepinephrine uptake in patients with major depression treated with paroxetine.*

> OBJECTIVE: The study examined whether paroxetine inhibits the human norepinephrine transporter in addition to the human serotonin (5-HT) transporter in patients with major depressive disorder. METHOD: In an open-label, parallel-group, forced-titration study, 52 outpatients with DSM-IV major depressive disorder and a baseline Montgomery Asberg Depression Rating Scale score > or =20 were randomly assigned to treatment with paroxetine (to 60 mg/day) or desipramine (to 30 mg/day) in a 3-to-1 ratio, respectively. Norepinephrine and 5-HT transporter function were assayed by using human transporter transfected cells in the presence of serum collected at baseline and the end of each treatment week. Data from 36 patients were analyzed. RESULTS: Paroxetine decreased norepinephrine uptake to 73% of control (27% inhibition) at an average serum concentration of 100 ng/ml and 57% of control (43% inhibition) at 200 ng/ml. Uptake of 5-HT was decreased to less than 15% (greater than 85% inhibition) of control at these paroxetine concentrations. Desipramine decreased norepinephrine uptake to near maximal 15% of control (85% inhibition) at 100 ng/ml. Uptake of 5-HT was decreased to 82% of control (18% inhibition) at 100 ng/ml and 49% of control (51% inhibition) at 500 ng/ml. CONCLUSIONS: Paroxetine, currently classified as a selective 5-HT reuptake inhibitor, can act as a 5-HT/norepinephrine uptake inhibitor in vivo. The clinical significance of this action on norepinephrine uptake is currently unknown, but this action may contribute to the broad therapeutic efficacy of paroxetine in the treatment of depression, panic disorder, social anxiety disorder, posttraumatic stress disorder, and generalized anxiety disorder.

---

## 15. [intersection] Protein → BiologicalProcess → Protein

**Chemin :** Plg-R KT --positively regulates--> **plasminogen activation** ← Starase

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 32662180

*Functions of the plasminogen receptor Plg-R KT .*

> Plg-R KT is a structurally unique transmembrane plasminogen receptor with both N- and C-terminal domains exposed on the extracellular face of the cell. Its C-terminal lysine functions to tether plasminogen to cell surfaces. Overexpression of Plg-R KT increases cell surface plasminogen binding capacity while genetic deletion of Plg-R KT decreases plasminogen binding. Plasminogen binding to Plg-R KT results in promotion of plasminogen activation to the broad spectrum serine protease plasmin. This function is promoted by the physical association of Plg-R KT with the urokinase receptor (uPAR). Plg-R KT is broadly expressed in cells and tissues throughout the organism and its sequence is remarkably conserved phylogenetically. Plg-R KT also is required for lactation and, thus, is necessary for survival of the species. This review provides an overview of established and emerging functions of Plg-R KT and highlights major roles for Plg-R KT in both the initiation and resolution of inflammation. While the roles for Plg-R KT in the inflammatory response are predominantly plasmin(ogen)-dependent, its role in lactation requires both plasminogen-dependent and plasminogen-independent mechanisms. Furthermore, the functions of Plg-R KT are dependent on sex. In view of the broad tissue distribution of Plg-R KT , its role in a broad array of physiological and pathological processes should provide a fruitful area for future investigation.

### Relation 2 — PMID 24977934

*Starase: A bi-functional fibrinolytic protease from hepatic caeca of Asterina pectinifera displays antithrombotic potential.*

> A bi-functional fibrinolytic serine protease, Starase exhibiting thrombolytic potency was purified from hepatic caeca of Asterina pectinifera. Starase showed a single band of approximately 48 kDa by SDS-PAGE and fibrin zymography. The N-terminal sequence of Starase was AIPTEFDARTKKHNN, which does not match with any known fibrinolytic enzyme. Starase had optimum amidolytic activity at 50 °C and pH 8.0 and the activity was inhibited by PMSF and APMSF. Starase showed the highest specificity toward the substrate H-D-Val-Leu-Lys-pNA for plasmin followed by pyroGlu-Gly-Arg-pNA for urokinase. The apparent Km and Vmax values of Starase toward a chromogenic substrate for plasmin H-D-Val-Leu-Lys-pNA were determined as 1.37 mM and 6.8 mM/min/mg respectively. The fibrinolytic activity of Starase by fibrin plate assay displayed that it could not only directly degrade fibrin clot but also activate plasminogen. Starase showed a strong fibrinogenolytic activity, cleaving all three major chains of fibrinogen rapidly. In addition, Starase with more than 1 μg could cleave extracellular matrix component type VII collagen, and plasma proteins such as bovine albumin and bovine gamma globulin. It could also inhibit factor Xa and thrombin activity. Starase at a dose of 0.8 mg/kg was devoid of hemorrhagic activity and it demonstrated antithrombotic effect in three animal models; FeCl2-induced carotid arterial thrombus model, carrageenan-induced tail thrombosis model and collagen and epinephrine induced pulmonary thromboembolism mice model. These results suggest that Starase has the potential to be a potent thrombolytic agent due to its bi-functional properties (containing both direct-acting and plasminogen-activating activities) and lack of hemorrhagic activity. Although Starase might interfere with the normal composition of the plasma proteins, it may be used not only for the treatment and prevention of thrombosis, but also in a number of biomedical applications.

---

## 16. [intersection] Drug → BiologicalProcess → Drug

**Chemin :** Levomilnacipran --decreases activity of--> **serotonin reuptake** ← clomipramine hydrochloride

**Décision :** [x] VALIDE   [ ] ÉCARTÉ   —  motif :

### Relation 1 — PMID 25657584

*Levomilnacipran for the treatment of major depressive disorder: a review.*

> Levomilnacipran (LVM, Fetzima(®)) was recently approved by the US Food and Drug Administration for the treatment of major depressive disorder. It is a unique dual neurotransmitter reuptake inhibitor. In contrast with other selective serotonin norepinephrine reuptake inhibitors, including duloxetine, venlafaxine, and desvenlafaxine, it has greater selectivity for inhibiting norepinephrine reuptake than serotonin reuptake. Our review focuses on the efficacy, safety, and tolerability data for five double-blind, placebo-controlled, short-term studies and two long-term studies. In the short-term studies, LVM was found to be more effective than placebo in reducing depression (Montgomery-Åsberg Depression Rating Scale) scores as well as improving functional impairment (Sheehan Disability Scale) scores. Long-term studies found LVM to be similarly effective but in the only placebo-controlled long-term study, LVM was not significantly superior to placebo. LVM is fairly well tolerated, with the most common adverse events being nausea, headache, dry mouth, hyperhidrosis, and constipation. Discontinuation rates were mildly increased in those being treated with LVM (9%) versus placebo (3%). Adverse events were not dose-related except for urinary hesitancy and erectile dysfunction. LVM was weight neutral, was not toxic to the liver, and did not cause clinically significant QTc prolongation. Consistent with being a predominant potentiator of norepinephrine, pulse and blood pressure were significantly elevated by LVM but rarely induced tachycardia or hypertension. LVM is a relatively safe alternative antidepressant treatment with minimal drug-drug interactions. It is the only antidepressant that has in its labeling that it is not only effective in improving depression but also effective in improving impaired functioning. Whether this important effect on functioning is unique to LVM must be researched. In addition, whether LVM might be effective in norepinephrine-deficit depression, refractory depression, atypical depression, or seasonal depression is yet to be evaluated. Ultimately, head-to-head studies comparing LVM with other antidepressants will determine the place of LM in antidepressant treatment.

### Relation 2 — PMID 2180623

*Clomipramine: an antiobsessional tricyclic antidepressant.*

> The chemistry, pharmacology, pharmacokinetics, adverse effects, and dosage of clomipramine hydrochloride are described, and clinical studies of the use of clomipramine in treating obsessive-compulsive disorder (OCD), other psychiatric conditions, and chronic pain are reviewed. Clomipramine hydrochloride, a tricyclic antidepressant, is a potent inhibitor of serotonin reuptake and may affect dopaminergic neurotransmission, suppress rapid eye movement sleep, produce changes in electrocardiograms, and elevate plasma prolactin. The drug is well absorbed from the gastrointestinal tract and undergoes extensive first-pass metabolism. Peak plasma concentrations occur three to four hours after a 150-mg oral dose. The mean elimination half-life is 39 hours. Some 66% of a dose is excreted in the urine, the remainder being eliminated in the feces. In clinical trials, clomipramine was significantly more effective than placebo, clorgiline, amitriptyline, imipramine, and doxepin in ameliorating the symptoms of OCD. Initial effects are seen at four weeks; improvement may continue for up to 18 weeks. Clomipramine may also be effective in treating panic attacks, phobias, depression, and chronic pain. The most common adverse effects of clomipramine are anticholinergic; others include nausea, seizures, and sexual difficulties. Interactions between clomipramine and barbiturates, haloperidol, monoamine oxidase inhibitors, and cigarette smoking have been documented. The usual initial adult dosage is 25-50 mg/day, titrated gradually to 250 mg/day if necessary. Clomipramine hydrochloride is a welcome new agent for the treatment of obsessive-compulsive disorder. Although its adverse-effect profile is like that of other tricyclic antidepressants, sexual dysfunction and seizures may be more frequent with this agent and limit its use.

---

