# Points à formuler en soutenance

## Sur la révision du schéma
La mesure a révélé le problème, la révision l'a corrigé, une seconde mesure l'a confirmé.
→ montre que la méthode est auto-correctrice, pas hésitante.

## Sur le calibrage de la requête PubMed
Le filtre [Title/Abstract] retire 92 % des résultats bruts sur epoprostenol :
le médicament y est le plus souvent cité hors du corps de l'article.
→ montre qu'une requête naïve aurait pollué le corpus.

## Sur le filtrage du corpus
Un abstract de 24 mots a été détecté dans la collecte initiale. Le réflexe naïf
aurait été de fixer un seuil de longueur ; l'inspection a montré que le vrai critère
était le type de document (avis réglementaire, pas article de recherche).
→ montre la différence entre traiter un symptôme et traiter la cause.

## Sur le pilote
Le test initial concluait à 0 chaîne couverte sur 16. L'inspection inverse a montré
que les concepts étaient présents sous forme d'usage (SERT, NET, G-CSF receptor).
Le test mesurait la présence de la forme canonique, non la faisabilité de l'extraction.
→ montre l'importance de vérifier ce qu'un test mesure réellement avant de conclure.

## Sur la valeur d'un pilote négatif
Le pilote a produit 5 chaînes exploitables sur 16, concentrées sur un seul des cinq
médicaments. Il a validé le mécanisme de normalisation et invalidé le critère de
sélection des médicaments — critère qui reposait sur une estimation qualitative.
→ montre qu'un pilote sert autant à réfuter une hypothèse de travail qu'à confirmer
une faisabilité, et qu'il vaut mieux le découvrir sur 5 cas que sur 30.

## Sur la vérification d'intégrité du corpus
33 articles identifiés n'ont pu être récupérés. Les compteurs globaux restaient
normaux, mais certains sauts de chaîne ne reposaient que sur deux articles : la perte
de ces deux-là aurait rendu une chaîne inutilisable sans qu'aucun indicateur ne le
signale. La vérification a été menée saut par saut plutôt que sur le volume global.
→ montre qu'un agrégat sain peut masquer une défaillance locale.

## Sur la valeur diagnostique d'un échec inchangé
Entre les deux itérations, le score est resté nul mais la cause a changé : d'une
relation absente du texte à une relation extraite sous un vocabulaire non conforme.
Un score identique peut recouvrir deux situations qui n'appellent pas la même
correction.

## Sur la nécessité de la vérification manuelle
Un échantillon aléatoire de 40 relations du graphe fait apparaître environ 10 %
d'inversions de polarité — conformes au schéma, syntaxiquement valides, sémantiquement
fausses. Aucun contrôle automatique ne les détecte. Les erreurs se regroupent en outre
par article source, sept d'entre elles provenant d'un seul texte.

## Sur les filtres en cascade
Un second test plus restrictif placé après un test général qui l'englobe constitue du
code mort : le `continue` du premier empêche le second d'être atteint. Son compteur
reste à zéro et suggère à tort que le cas n'existe pas.

## Sur le diagnostic des échecs de la baseline
Le rappel de 0,67 sur les questions de contrôle a d'abord été attribué à une troncature
des abstracts longs. La comparaison des longueurs entre documents retrouvés et manqués
a réfuté cette hypothèse. La cause réelle est la dilution : les documents manqués sont
ceux où l'entité recherchée n'est pas le sujet principal.
→ montre qu'une hypothèse plausible doit être testée avant d'orienter une correction.

## Le chiffre à retenir
Le graphe atteint 0,83 de rappel avec 5 documents — un niveau que la recherche
vectorielle n'atteint pas avec 50. Les documents manqués ne sont pas mal classés :
ils sont absents du classement.

## Sur le coût
L'énoncé demande « à quel coût en latence et en calcul ». La réponse est double : le
graphe coûte environ deux ordres de grandeur de plus à la construction (35 min de GPU
contre moins d'une minute) et moins à l'exploitation, s'interrogeant sans GPU là où le
vectoriel en exige un pour chaque question. Les latences de génération sont
équivalentes. Le coût d'extraction relève du pipeline de données en amont et aurait pu
être omis de la comparaison ; l'y intégrer était nécessaire.

## Sur l'asymétrie du recours au LLM
Le graphe est construit par un LLM, l'index vectoriel non. Le résultat porte donc sur
un couple architecture-extracteur, non sur l'architecture seule. Le biais joue contre
l'hypothèse — une extraction imparfaite dégrade le graphe sans toucher au vectoriel —
et le graphe l'emporte malgré lui : la mesure est conservatrice.

## Sur la correction apportée après mesure
La fonction de canonisation ne translittérait pas les caractères grecs, ce qui
empêchait l'ancrage d'une question sur le graphe. La correction porte sur l'étape
d'ancrage, en aval du jeu de test : la vérité terrain n'a pas été modifiée. Les deux
mesures, avant et après correction, sont rapportées.
→ un défaut d'implémentation existe indépendamment des questions posées ; le corriger
n'est pas ajuster le système à son évaluation.

## Sur la généralisation d'une observation d'échantillon
L'effet du filtre mécanistique avait été décrit à partir de cinq abstracts de
l'échantillon de dry run. La mesure sur les 493 abstracts du corpus ne confirme pas
cette description : le filtre rebrasse 12 % du corpus sans trier selon le critère visé.
→ une observation vraie sur un échantillon de cinq ne se généralise pas d'office.

## Sur les écarts au cahier des charges
Trois outils prescrits n'ont pas été employés : GraphRAG/LightRAG, ChromaDB/FAISS, et
le poste GPU du département. Chaque substitution est justifiée dans l'annexe D du
rapport. Les énoncer explicitement vaut mieux que laisser un correcteur les découvrir.

## Sur la définition d'une mesure
Trois chiffres de conformité au schéma coexistaient dans les journaux : 829, 822 et
820. Aucun n'était faux — chacun relevait d'une définition différente de « conforme ».
Le contrôle a consisté à recalculer les trois sur le même fichier plutôt qu'à choisir.
→ un désaccord entre deux mesures n'est pas nécessairement une erreur ; c'est souvent
une définition restée implicite.

## Sur l'attribution du mécanisme
L'argument théorique en faveur du Graph RAG est la traversée. La mesure montre que
l'écart est maximal sur les questions à un saut (+0,33), qui n'en requièrent aucune,
et moindre sur le multi-hop (+0,27 et +0,17). La hiérarchie est identique en proportion
d'erreur comblée, ce qui écarte l'objection d'un effet de plafond. Le mécanisme
dominant est donc l'absence de dilution, non la traversée.
→ montre qu'un résultat conforme à l'hypothèse globale peut infirmer le mécanisme
qu'on lui prêtait, et qu'il faut vérifier les deux séparément.