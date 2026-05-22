# Rapport — TP Ordonnancement de tâches

---

## Modélisation

### 1. Variables de décision, contraintes et objectifs

#### Variables de décision

Le problème demande de décider trois choses pour chaque solution :

- **L'affectation de chaque opération à une machine** : pour chaque opération, on choisit sur quelle machine compatible elle sera exécutée. La durée de traitement et la consommation d'énergie de l'opération découlent de ce choix.

- **L'heure de début de chaque opération** : une fois la machine choisie, on détermine à quel moment l'opération commence sur cette machine.

- **Les heures de démarrage et d'arrêt de chaque machine** : une machine doit être démarrée (phase de set_up) avant d'accueillir des opérations et doit être arrêtée (phase de tear_down) en fin de planning. Elle peut être allumée et éteinte plusieurs fois si cela permet d'économiser de l'énergie.

#### Contraintes

**Contrainte d'affectation unique** : chaque opération est exécutée sur exactement une machine parmi celles qui lui sont compatibles. On ne peut pas répartir une opération sur plusieurs machines.

**Contrainte de précédence intra-job** : au sein d'un même job, les opérations doivent s'exécuter dans leur ordre défini. L'opération numéro i ne peut démarrer qu'une fois l'opération numéro i-1 entièrement terminée.

**Contrainte de non-chevauchement** : une machine ne peut exécuter qu'une seule opération à la fois. Deux opérations planifiées sur la même machine ne peuvent donc pas se chevaucher dans le temps.

**Contrainte de disponibilité après démarrage** : une opération ne peut pas commencer sur une machine avant que le démarrage (set_up) de celle-ci soit terminé. Si la machine commence son set_up à l'instant t, la première opération ne peut démarrer qu'à t + set_up_time.

**Contrainte de fin de planning** : chaque machine doit avoir terminé toutes ses opérations avant son heure limite end_time. La machine doit pouvoir être arrêtée dans cette fenêtre temporelle.

#### Objectifs

L'entreprise a plusieurs objectifs partiellement contradictoires :

- **Minimiser la consommation totale d'énergie** : énergie des opérations, énergie de démarrage et d'arrêt des machines, et énergie consommée à vide (machine allumée mais inactive).
- **Minimiser le makespan** : réduire la durée totale du planning, c'est-à-dire l'heure à laquelle le dernier job est terminé.
- **Minimiser le temps de complétion moyen** : réduire la durée moyenne nécessaire pour terminer chaque job, ce qui traduit une bonne réactivité de l'atelier.

Ces objectifs sont en tension : choisir la machine la plus rapide consomme souvent plus d'énergie, et maintenir plusieurs machines allumées réduit les temps d'attente mais augmente la consommation à vide.

---

### 2. Fonction objectif agrégée

Pour obtenir un critère unique à minimiser, on combine les trois objectifs par une somme pondérée :

**Score = w_E × énergie totale + w_T × makespan + w_M × somme des temps de complétion**

- **w_E** pilote l'importance de l'économie d'énergie.
- **w_T** pilote l'importance de finir le planning rapidement.
- **w_M** pilote l'importance de la réactivité job par job.

En jouant sur ces poids, l'entreprise peut exprimer ses priorités. Des poids égaux donnent une solution de compromis équilibrée. Il est recommandé de normaliser chaque composante (diviser par un ordre de grandeur typique) pour éviter qu'un terme domine les autres par son échelle.

**Décomposition de l'énergie totale** :

- *Énergie des opérations* : somme des consommations de chaque opération sur la machine choisie (données directement dans le fichier CSV).
- *Énergie de démarrage et d'arrêt* : pour chaque cycle allumé/éteint d'une machine, on ajoute set_up_energy et tear_down_energy.
- *Énergie à vide* : pendant les périodes où une machine est allumée mais n'exécute aucune opération (ni set_up ni traitement), elle consomme sa puissance minimale min_consumption (en kW) multipliée par la durée d'inactivité (convertie en heures).

---

### 3. Évaluation d'une solution

#### Solution réalisable

Une solution est **réalisable** si toutes les contraintes listées ci-dessus sont respectées : chaque opération est assignée à une machine compatible, les précédences sont respectées, aucune machine n'est surchargée à un instant donné, et toutes les opérations terminent avant la limite end_time de leur machine.

Pour évaluer une telle solution, on calcule dans l'ordre :

1. L'heure de fin de chaque opération (heure de début + durée de traitement sur la machine choisie).
2. Le makespan : heure de fin maximale parmi tous les jobs.
3. La somme des temps de complétion : somme des heures de fin de la dernière opération de chaque job.
4. L'énergie totale : énergie des opérations + énergie des démarrages/arrêts + énergie à vide de chaque machine.
5. Le score final via la fonction objectif agrégée.

#### Solution non réalisable

Une solution **non réalisable** viole au moins une contrainte. Plutôt que de la rejeter, on peut lui attribuer une valeur pénalisée afin de pouvoir la comparer à d'autres solutions non réalisables et guider l'algorithme vers la faisabilité.

La valeur pénalisée est : **Score_pénalisé = Score + κ × Pénalité**

où κ est un grand coefficient et la pénalité mesure l'ampleur des violations :

- **Violations de précédence** : durée totale pendant laquelle une opération commence avant que son prédécesseur soit terminé.
- **Chevauchements sur machine** : durée totale de chevauchement entre opérations sur la même machine.
- **Dépassement de end_time** : durée totale pendant laquelle des opérations dépassent la limite temporelle de leur machine.
- **Affectations invalides** : nombre d'opérations assignées à une machine incompatible.

En choisissant κ suffisamment grand, les solutions infaisables obtiennent toujours un score plus élevé que les solutions réalisables, ce qui garantit que l'algorithme préfère toujours une solution faisable à une infaisable.

---

### 4. Instance sans solution réalisable

**Description de l'instance :**

- Une seule machine m0 avec : set_up_time = 10 minutes, tear_down_time = 5 minutes, end_time = 30 minutes.
- Un seul job composé de deux opérations séquentielles, chacune ne pouvant s'exécuter que sur m0 avec une durée de 15 minutes.

**Pourquoi aucune solution n'est réalisable :**

La machine doit d'abord effectuer son démarrage (10 minutes), puis exécuter les deux opérations dans l'ordre (15 + 15 = 30 minutes), puis effectuer son arrêt (5 minutes). La durée minimale nécessaire est donc 10 + 15 + 15 + 5 = 45 minutes. Or end_time = 30 minutes : il est physiquement impossible de faire rentrer l'intégralité du planning dans la fenêtre autorisée. Aucun ordonnancement ne peut satisfaire simultanément les contraintes de précédence, de disponibilité après démarrage et de fin de planning.

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

*À compléter.*

---

## Recherche locale

*À compléter.*
