# Rapport — TP Ordonnancement de tâches

---

## Modélisation

### 1. Variables de décision, contraintes et objectifs

#### Variables de décision

Le problème demande de décider trois choses pour chaque solution :


- x[o, m] = 1 si l’opération o est choisie pour la machine m, sinon 0. Pour chaque opération, on choisit sur quelle machine compatible elle sera exécutée. 


- S[o] = heure de début de l’opération o. Une fois la machine choisie, on détermine à quel moment l'opération commence sur cette machine.

- S[m,t] = état marche/arrêt de la machine m à l’instant t. 
La machine peut être allumée et éteinte plusieurs fois à des nstants t.

#### Contraintes

- chaque opération est exécutée sur exactement une machine. On ne peut pas répartir une opération sur plusieurs machines.

- Toutes les tâches doivent être exécutées

- au sein d'un même job, les opérations doivent s'exécuter dans leur ordre défini. L'opération numéro i ne peut démarrer qu'une fois l'opération numéro i-1 entièrement terminée.

- une machine ne peut exécuter qu'une seule opération à la fois. Deux opérations planifiées sur la même machine ne peuvent donc pas se chevaucher dans le temps.

- une opération ne peut pas commencer sur une machine avant que le démarrage (set_up) de celle-ci soit terminé. 

- chaque machine doit avoir terminé toutes ses opérations avant son heure limite end_time. La machine doit pouvoir être arrêtée avant son end_time

#### Objectifs

Nous avons déduit trois objectifs d'optimisation :

- construire un planning qui minimise la consommation énergétique totale de l’usine. Cette consommation comprend l’énergie nécessaire à l’exécution des opérations, l’énergie liée aux phases de démarrage et d’arrêt des machines, ainsi que l’énergie consommée lorsque les machines restent allumées sans produire.
 
- Limiter la durée totale du planning, 

- Réduire la durée moyenne de complétion des jobs et les retards éventuels, car la rapidité d’exécution reste un critère important.

---

### 2. Fonction objectif agrégée

Pour obtenir un critère unique à minimiser, on combine les trois objectifs par une somme pondérée :

**Score = w_E × énergie totale + w_T × date de fin de la dernière opération planifiée (makespan) + w_M × somme des temps de complétion**

- **w_E** poids de l'économie d'énergie.
- **w_T** l'importance de finir les jobs rapidement (date à laquelle la dernière opération du planning est achevée).
- **w_M** l'importance de la réactivité job par job.

En jouant sur ces poids, l'entreprise peut exprimer ses priorités. Des poids égaux donnent une solution de compromis équilibrée. 


### 3. Évaluation d'une solution

#### Solution réalisable


Pour évaluer une solution réalisable, on calcule dans l'ordre :

1. L'heure de fin de chaque opération (heure de début + durée de traitement sur la machine choisie).
2. Le makespan : heure de fin maximale parmi tous les jobs.
3. La somme des temps de complétion : somme des heures de fin de la dernière opération de chaque job.
4. L'énergie totale : énergie des opérations + énergie des démarrages/arrêts + énergie à vide de chaque machine.
5. Le score final via la fonction objectif agrégée.

#### Solution non réalisable

Une solution **non réalisable** viole au moins une contrainte. Plutôt que de la rejeter, on peut lui attribuer une valeur pénalisée afin de pouvoir la comparer à d'autres solutions non réalisables et guider l'algorithme vers la faisabilité.

---

### 4. Instance sans solution réalisable

On propose une instance volontairement infaisable, composée d'un seul job, d'une seule opération et d'une seule machine m0. Cette opération dure 100 minutes et ne peut être exécutée que sur m0. La machine a besoin de 10 minutes pour s'allumer avant de pouvoir traiter l'opération, puis de 10 minutes supplémentaires pour s'éteindre une fois celle-ci terminée : il faut donc au minimum 10 + 100 + 10 = 120 minutes pour enchaîner allumage, traitement et extinction. Or le end_time de la machine est fixé à 90 minutes, c'est-à-dire que la machine doit être complètement éteinte avant cet instant. Même en démarrant l'allumage dès l'instant 0, il est impossible de terminer l'allumage, exécuter l'opération et éteindre la machine avant la minute 90. Cette instance ne possède donc aucune solution réalisable.

---

### 5. Implémentation des classes

#### Choix d'implémentation

**`Operation` et `OperationScheduleInfo`** : chaque opération stocke un dictionnaire de ses options de traitement par machine (durée et énergie). Quand elle est planifiée, un objet `OperationScheduleInfo` mémorise la machine choisie, l'heure de début, la durée et l'énergie. Les contraintes de précédence sont représentées par des listes de prédécesseurs et successeurs.

**`Machine`** : lors du premier appel à `add_operation`, la machine calcule automatiquement l'heure de démarrage optimale — le plus tard possible pour que le set_up soit terminé exactement quand l'opération en a besoin. Par défaut, la machine est arrêtée à end_time (un seul cycle allumé/éteint dans l'implémentation de base). Le calcul de l'énergie à vide prend en compte le temps total allumé moins le temps de set_up et les durées d'opérations.

**`Job`** : la méthode `add_operation` gère automatiquement l'ajout des contraintes de précédence entre opérations consécutives du même job.

**`Instance`** : `from_file` lit les deux fichiers CSV. Les identifiants d'opérations dans le fichier sont des identifiants globaux (uniques sur toute l'instance, pas par job), ce qui permet d'indexer directement la liste `operations`.

**`Solution`** : `available_operations` retourne les opérations dont tous les prédécesseurs sont déjà planifiés. `schedule(operation, machine)` délègue à `machine.add_operation` qui calcule l'heure de début effective. `is_feasible` vérifie les quatre contraintes principales. La valeur objectif est mise en cache et invalidée à chaque nouvelle planification.

---

## Premières heuristiques

### Heuristique gloutonne déterministe (`Greedy`)

L'algorithme `Greedy` construit une solution en planifiant les opérations une par une. À chaque étape, il évalue toutes les paires (opération disponible, machine compatible) et choisit **irrémédiablement** celle dont le score local est minimal.

Le score d'une paire est une somme pondérée :
- l'énergie de traitement de l'opération sur la machine,
- le temps de complétion estimé (temps de début estimé + durée de traitement).

Le temps de début estimé tient compte de l'état de la machine : si elle n'est pas encore démarrée, on ajoute son temps de mise en route ; si elle est déjà active, on attend sa disponibilité.

**Pourquoi cet algorithme est-il glouton ?**  
Il prend des décisions localement optimales sans aucun retour arrière : une fois une opération planifiée sur une machine, ce choix n'est plus remis en question même s'il s'avère sous-optimal à plus long terme. L'heuristique ignore tout effet de bord futur (propagation des précédences, charge globale des machines).

**Complexité** : O(O² × M) — à chacune des O étapes, on évalue les O × M paires disponibles.

Les poids `w_energy` et `w_time` sont paramétrables (valeur par défaut : 1,0 chacun).

---

### Heuristique non-déterministe (`NonDeterminist`)

L'algorithme `NonDeterminist` est inspiré de **GRASP** (*Greedy Randomized Adaptive Search Procedure*, Feo & Resende, 1995).

À la différence du glouton pur, il ne sélectionne pas systématiquement le meilleur candidat : il construit à chaque étape une **liste restreinte de candidats** (RCL) composée des k meilleures paires (opération, machine), puis en choisit une **au hasard**.

Ce mécanisme introduit de la diversité : deux appels successifs sur la même instance produisent généralement des solutions différentes. On peut fixer une graine aléatoire (`seed`) pour obtenir des résultats reproductibles.

**Intérêt** : en lançant plusieurs fois l'heuristique, on explore davantage l'espace des solutions et on peut conserver la meilleure solution obtenue. C'est la base de la méthode GRASP complète, qui ajoute une phase de recherche locale après chaque construction.

**Paramètres** : `w_energy` (défaut 1,0), `w_time` (défaut 1,0), `k` (taille de la RCL, défaut 3), `seed` (graine aléatoire, défaut `None`).

**Complexité** : O(O² × M × log(O × M)) — identique au glouton à un tri supplémentaire près pour construire la RCL.

**Référence** : Feo, T.A. & Resende, M.G.C. (1995). Greedy Randomized Adaptive Search Procedures. *Journal of Global Optimization*, 6(2), 109–133.

---

## Recherche locale

### 1. Voisinage N1 — SwapOnMachine

**Définition.** Un mouvement de SwapOnMachine consiste à inverser l'ordre de passage de deux opérations sur la même machine dans la file d'ordonnancement. Si une machine m traite les opérations [A, B, C, D], le mouvement (A, C) donne [C, B, A, D].

**Mouvements valides.** L'échange entre deux opérations i et j n'est autorisé que si aucune n'est l'ancêtre de l'autre, c'est-à-dire qu'il n'existe pas de relation de précédence directe ou transitive entre elles. Cette condition évite de créer des cycles évidents dans le graphe de précédences intra-machine ; les échanges qui créent un blocage inter-machines (deadlock entre plusieurs machines) sont détectés à la reconstruction et simplement ignorés.

**Taille du voisinage.** Pour une machine m comportant n_m opérations, le nombre de paires possibles est C(n_m, 2) = n_m × (n_m − 1) / 2. En sommant sur toutes les machines, la taille totale est de l'ordre de O(n²/M) par machine et O(n²) au total. Pour jsp2 (40 opérations, 4 machines), on obtient environ 167 mouvements valides après filtrage des paires ancêtres.

**Polynomialité.** L'énumération complète du voisinage est polynomiale en O(n²) ; l'application d'un mouvement et la reconstruction du planning associé sont en O(n log n).

**Connexité.** Ce voisinage n'est pas connexe en général : certaines solutions ne sont pas atteignables depuis une solution donnée par une séquence de swaps sur une même machine. Il permet néanmoins d'explorer efficacement l'espace des ordres locaux.

---

### 2. Voisinage N2 — MachineReassign

**Définition.** Un mouvement de MachineReassign consiste à réaffecter une opération d'une machine à une autre machine compatible, en l'insérant à une position qui respecte les précédences avec les opérations déjà planifiées sur la machine cible.

**Position d'insertion.** Pour chaque opération op à réaffecter vers la machine m', on calcule l'intervalle de positions valides : la position minimale est déterminée par les opérations de m' qui doivent précéder op (ancêtres) ; la position maximale est déterminée par les opérations de m' qui doivent suivre op (successeurs). Si aucune position valide n'existe, le mouvement est rejeté. Sinon, op est insérée à la première position valide (min_pos).

**Taille du voisinage.** Pour chaque opération, le nombre de machines cibles est au plus |machines_compatibles| − 1. La taille totale est O(n × M) où M est le nombre moyen de machines compatibles par opération. Ce voisinage complète N1 en permettant de changer les affectations machine, ce que N1 ne peut pas faire.

**Polynomialité.** L'énumération est polynomiale en O(n × M) ; le calcul de min_pos et max_pos est en O(n_m) par mouvement.

**Connexité.** N2 seul permet d'explorer les changements d'affectation. Combiné à N1, les deux voisinages couvrent conjointement les deux degrés de liberté du problème (ordre sur chaque machine, et affectation des opérations aux machines), ce qui améliore la connexité globale de l'exploration.

---

### 3. Algorithmes de recherche locale

#### Descente au premier améliorant — `FirstNeighborLocalSearch`

L'algorithme génère une solution initiale via NonDeterminist (GRASP), puis applique itérativement le voisinage N1 (SwapOnMachine) avec la stratégie **première amélioration** : dès qu'un voisin de meilleure valeur objectif est trouvé, il remplace la solution courante et l'itération repart de zéro. L'algorithme s'arrête lorsqu'aucun voisin n'améliore la solution courante (optimum local atteint).

**Avantage.** Chaque itération est rapide car on n'explore pas tout le voisinage.  
**Inconvénient.** Le premier voisin améliorant n'est pas nécessairement le meilleur ; la qualité de l'optimum local dépend fortement de l'ordre d'exploration.

#### Descente au meilleur voisin — `BestNeighborLocalSearch`

L'algorithme génère une solution initiale via NonDeterminist, puis applique itérativement les deux voisinages N1 et N2 avec la stratégie **meilleure amélioration** : on explore la totalité du voisinage combiné (N1 ∪ N2) et on retient le voisin de moindre objectif. L'algorithme s'arrête lorsqu'aucun voisin dans N1 ∪ N2 n'améliore la solution. Un paramètre `max_iterations` (défaut 100) évite les boucles infinies sur les grandes instances.

**Avantage.** Garantit le meilleur mouvement disponible à chaque itération.  
**Inconvénient.** Plus coûteux par itération ; peut être lent sur les grandes instances.

**Gestion des deadlocks.** Lors de la reconstruction d'un planning à partir d'un snapshot de files machine, certains swaps peuvent créer des dépendances circulaires inter-machines (deadlock JSP). Ces mouvements produiraient des plannings incomplets (seule une partie des opérations est planifiée) avec une valeur objectif artificiellement basse (Cmax = 0, sum_Ci = 0). Pour éviter d'accepter ces solutions infaisables, tout mouvement dont la reconstruction laisse au moins une opération non planifiée est systématiquement ignoré.

---

### 4. Résultats de comparaison

Les trois méthodes ont été comparées sur trois instances de tailles croissantes. Pour les méthodes stochastiques, 10 exécutions sont lancées et la meilleure solution (objectif minimal) est retenue.

| Instance | Méthode                | Obj      | Cmax | Énergie | Faisable | Temps (s) |
|----------|------------------------|----------|------|---------|----------|-----------|
| jsp2     | Greedy                 | 1 224,73 |  145 |  244,73 | oui      |     0,002 |
| jsp2     | FirstNeighbor × 10     | 1 267,07 |  133 |  256,07 | oui      |     1,782 |
| jsp2     | BestNeighbor × 10      | 1 221,48 |  130 |  256,48 | oui      |     9,310 |
| jsp10    | Greedy                 | 1 560,58 |  168 |  280,58 | oui      |     0,002 |
| jsp10    | FirstNeighbor × 10     | 1 530,78 |  156 |  285,78 | oui      |     2,182 |
| jsp10    | BestNeighbor × 10      | 1 478,52 |  162 |  286,52 | oui      |    10,783 |
| jsp25    | Greedy                 | 2 110,25 |  177 |  444,25 | oui      |     0,010 |
| jsp25    | FirstNeighbor × 10     | 2 133,03 |  188 |  478,03 | oui      |    17,471 |
| jsp25    | BestNeighbor × 10      | 2 037,80 |  169 |  444,80 | oui      |    89,594 |

**Analyse.**

- **Greedy** est de loin le plus rapide (quelques millisecondes). Il produit des solutions de bonne qualité, mais non optimisées.
- **FirstNeighborLocalSearch** améliore le Cmax par rapport à Greedy sur jsp2 (133 vs 145) et jsp10 (156 vs 168), mais la valeur objectif globale peut être légèrement supérieure à Greedy en raison du point de départ aléatoire de NonDeterminist. Il reste nettement plus rapide que BestNeighbor.
- **BestNeighborLocalSearch** obtient la meilleure valeur objectif sur jsp10 (−5,3 % vs Greedy) et jsp25 (−3,4 % vs Greedy), et s'approche du Greedy sur jsp2. Le coût est un temps de calcul 5 à 10 fois supérieur à FirstNeighbor pour une même instance.

**Conclusion.** La recherche locale par meilleur voisin (N1 + N2) apporte une amélioration mesurable de la qualité des solutions au prix d'un temps de calcul plus élevé. Sur les petites instances, Greedy peut suffire ; sur les instances moyennes et grandes, BestNeighborLocalSearch offre un meilleur compromis qualité/temps. L'utilisation conjointe des deux voisinages (affectation et ordre) est bénéfique car ils explorent des axes différents de l'espace des solutions.
