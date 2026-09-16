# Contraintes pour la construction du jeu de test

## 1. Exclure les chemins empruntant une arête `treats`
`treats` relie directement Drug → Disease dans DrugMechDB (91 médicaments).
Une chaîne contenant cette arête est répondable en un seul saut : elle constituerait
un faux multi-hop et ne discriminerait pas les deux architectures.
→ Écarter ces chemins lors de la sélection des questions.

## 2. Traiter les chemins ramifiés
La majorité des chemins comportent des branches convergentes (33 009 nœuds pour
32 641 liens sur 4 846 chemins). Plusieurs routes relient donc le même médicament
à la même maladie.
→ Décider quelle branche fait foi dans la vérité terrain, ou accepter toute branche
comme réponse correcte. Décision à prendre avant la construction du jeu de test.
→ RÉSOLUE. Le script scripts/06_extraire_chaines.py a établi que les 193 chaînes
candidates sont toutes linéaires : la contrainte de 2 à 3 sauts exclut mécaniquement
les ramifications, qui requièrent au minimum quatre arêtes. La question de la branche
faisant foi est donc sans objet sur le périmètre retenu.

## 3. Motif `Drug → ChemicalSubstance → Disease → Disease`
Cinq chemins comportent une arête Disease → Disease (relation `manifestation of`).
Vérifier au moment de la rédaction des questions que ces chaînes restent
sémantiquement interprétables ; les écarter sinon.

## 4. Éviter la sur-représentation d'un médicament
venlafaxine dispose de 8 chaînes candidates, la majorité des autres médicaments
n'en ayant qu'une ou deux. Plafonner le nombre de questions issues d'un même
médicament (2 à 3 maximum) pour ne pas reproduire le biais d'échantillon observé
lors du relevé manuel.

## 5. Écarter les médicaments à forte notoriété
dexamethasone et les antihistaminiques H1 courants (loratadine, doxylamine)
présentent un risque élevé de fuite par pré-entraînement : le modèle peut connaître
la réponse sans rien récupérer. Soumettre systématiquement les questions au test
à vide avant de les retenir.

## 6. Vérifier l'adéquation entre indication et littérature
Une chaîne n'est exploitable que si sa maladie correspond au sujet dominant de la
littérature du médicament. Les chaînes epoprostenol → Allergic rhinitis / Rhinitis /
Common cold sont inexploitables : le corpus PubMed d'epoprostenol traite quasi
exclusivement de l'hypertension pulmonaire, son indication principale.
→ Écarter les chaînes dont la maladie n'apparaît pas dans le corpus collecté.

## 7. Vérifier la présence réelle de l'entité, pas d'un fragment de son nom
Un appariement partiel produit des faux amis : « peroxidase » correspond
indifféremment à thyroperoxydase, lactoperoxidase et myéloperoxidase, trois enzymes
distinctes. Toute correspondance établie par normalisation doit être vérifiée sur
l'identifiant, non sur un fragment textuel.

## 8. Écarter les chaînes dont une entité est absente du corpus
Thyroid peroxidase n'apparaît pas dans le corpus propylthiouracil. Les chaînes qui
en dépendent sont inexploitables même après normalisation.

## 9. Écarter les chaînes à entité pont lexicalement triviale
Une chaîne dont l'entité pont est contenue dans le nom du médicament ou de la maladie
ne constitue pas un raisonnement multi-hop : l'entité pont doit être invisible depuis
la question et depuis la réponse. Exemples écartés :
  Potassium chloride → Potassium → Hypokalemia
  hydroxocobalamin → cobalamin → Cobalamin deficiency
Le motif Drug → ChemicalSubstance → Disease est structurellement exposé à ce défaut,
un médicament étant fréquemment nommé d'après la substance qu'il apporte.

## 10. Les deux sauts d'un chemin doivent provenir d'articles différents
Un chemin dont les deux relations sont extraites du même abstract est résoluble par
une unique récupération : la recherche vectorielle le trouve sans traversée, et le
chemin ne discrimine pas les deux architectures. Ce critère est appliqué à la
génération des chemins candidats.

## 11. Vérification manuelle obligatoire de chaque question
Les questions étant dérivées du graphe extrait, une erreur d'extraction produirait
une question à réponse fausse. Des inversions de polarité subsistent après correction
du prompt. Chaque question retenue est donc confrontée aux abstracts sources avant
d'être intégrée au jeu de test.

## 12. Décision de périmètre — effets indésirables
Plusieurs chemins d'intersection ont pour entité pont un effet indésirable partagé
(hyponatrémie, sécheresse buccale, trouble de l'éjaculation). Ils sont structurellement
valides et permettent des questions du type « quels autres médicaments provoquent
tel effet ? », mais relèvent de la pharmacovigilance et non du mécanisme d'action.
Leur inclusion ou leur exclusion constitue une décision de périmètre, à trancher lors
de la relecture et à documenter.
→ TRANCHÉE : inclusion. Ces chemins sont retenus et marqués comme catégorie distincte
dans le jeu de test (champ « categorie »). La question de recherche porte sur la
capacité à retrouver une information exigeant deux documents distincts, non sur la
nature mécanistique de cette information. Les exclure réduirait l'effectif pour un
motif étranger à ce qui est mesuré. Leur comportement propre sera examiné séparément
lors de l'analyse des résultats.

## 13. Faire varier K lors de l'évaluation finale
Le rappel est mesuré au rang 5, valeur correspondant au nombre de passages qu'un
système RAG fournit habituellement au modèle générateur, compte tenu de la fenêtre
de contexte. Ce choix reste un paramètre : l'évaluation finale mesurera le rappel
aux rangs 1, 3, 5, 10 et 20 afin de produire une courbe plutôt qu'une valeur unique.

Une question multi-hop exigeant deux documents distincts parmi les K récupérés,
elle est structurellement plus sensible à ce paramètre qu'une question à un saut.
La courbe permettra de vérifier si l'écart entre les deux architectures se creuse
ou se resserre lorsque K augmente.