'''
Heuristiques de recherche locale.

Deux algorithmes sont implémentés :
- FirstNeighborLocalSearch : un seul voisinage, s'arrête sur la première solution améliorante.
- BestNeighborLocalSearch  : deux voisinages, retient la meilleure solution à chaque étape.

La solution initiale est construite par NonDeterminist (GRASP).

@author: Vassilissa Lehoux
'''
from typing import Dict, List, Type

from src.scheduling.optim.heuristics import Heuristic
from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.constructive import NonDeterminist
from src.scheduling.optim.neighborhoods import (
    Neighborhood, SwapOnMachine, MachineReassign,
    _reconstruct, _extract_orderings
)


class FirstNeighborLocalSearch(Heuristic):
    '''
    Recherche locale "première amélioration" avec un seul voisinage.

    Algorithme :
      1. Construire une solution initiale avec NonDeterminist.
      2. Explorer le voisinage ; prendre la première solution améliorante.
      3. Répéter jusqu'à obtenir un optimum local (aucun voisin ne l'améliore).

    Le voisinage par défaut est SwapOnMachine (N1).
    '''

    def __init__(self, params: Dict = dict()):
        '''
        @param params: dictionnaire optionnel avec les clés :
            - "w_energy", "w_time" : transmis à la construction initiale
        '''
        super().__init__(params)

    def run(self, instance: Instance,
            InitClass: Type = None,
            NeighborClass: Type = None,
            params: Dict = dict()) -> Solution:
        '''
        Calcule une solution par recherche locale avec première amélioration.
        @param instance: instance à résoudre
        @param InitClass: classe de l'heuristique de construction initiale
                          (défaut : NonDeterminist)
        @param NeighborClass: classe du voisinage à utiliser
                              (défaut : SwapOnMachine)
        @param params: paramètres supplémentaires
        @return: Solution (optimum local)
        '''
        merged = {**self._params, **params}

        if InitClass is None:
            InitClass = NonDeterminist
        if NeighborClass is None:
            NeighborClass = SwapOnMachine

        # Construction de la solution initiale
        current_sol = InitClass().run(instance, merged)
        neighborhood = NeighborClass(instance, merged)

        # Amélioration itérative : première solution améliorante
        while True:
            current_obj = current_sol.objective     # Valeur avant exploration
            next_sol = neighborhood.first_better_neighbor(current_sol)
            if next_sol.objective < current_obj:
                current_sol = next_sol
            else:
                break   # optimum local atteint

        return current_sol


class BestNeighborLocalSearch(Heuristic):
    '''
    Recherche locale "meilleure amélioration" avec deux voisinages.

    Algorithme :
      1. Construire une solution initiale avec NonDeterminist.
      2. Explorer les deux voisinages ; retenir la meilleure solution trouvée.
      3. Si une amélioration est trouvée, recommencer depuis cette solution.
      4. S'arrêter si aucun voisinage n'améliore OU si max_iterations est atteint.

    Les voisinages par défaut sont SwapOnMachine (N1) et MachineReassign (N2).
    '''

    def __init__(self, params: Dict = dict()):
        '''
        @param params: dictionnaire optionnel avec les clés :
            - "max_iterations" (int, défaut 100) : nombre maximal d'itérations
            - "w_energy", "w_time" : transmis à la construction initiale
        '''
        super().__init__(params)

    def run(self, instance: Instance,
            InitClass: Type = None,
            NeighborClasses=None,
            params: Dict = dict()) -> Solution:
        '''
        Calcule une solution par recherche locale avec meilleure amélioration.
        @param instance: instance à résoudre
        @param InitClass: classe de l'heuristique de construction initiale
                          (défaut : NonDeterminist)
        @param NeighborClasses: liste/tuple de classes de voisinage
                                (défaut : [SwapOnMachine, MachineReassign])
        @param params: paramètres supplémentaires (max_iterations, ...)
        @return: Solution (optimum local ou limite d'itérations atteinte)
        '''
        merged = {**self._params, **params}
        nb_iterations_max = int(merged.get('max_iterations', 100))

        if InitClass is None:
            InitClass = NonDeterminist
        if NeighborClasses is None:
            NeighborClasses = [SwapOnMachine, MachineReassign]
        # Accepter une seule classe passée directement (pas dans une liste)
        if not isinstance(NeighborClasses, (list, tuple)):
            NeighborClasses = [NeighborClasses]

        # Construction de la solution initiale
        current_sol = InitClass().run(instance, merged)
        neighborhoods: List[Neighborhood] = [classe_voisinage(instance, merged) for classe_voisinage in NeighborClasses]

        for _ in range(nb_iterations_max):
            # Valeur objectif courante (mise en cache avant tout changement)
            current_obj = current_sol.objective

            # Snapshot de l'état courant pour pouvoir restaurer entre voisinages
            current_snap = _extract_orderings(instance)

            best_snap = None
            best_obj = current_obj

            for neighborhood in neighborhoods:
                # Restaurer l'état courant avant d'explorer ce voisinage
                # (chaque neighborhood.best_neighbor change l'état de l'instance)
                _reconstruct(instance, {identifiant_machine: list(ops)
                                        for identifiant_machine, ops in current_snap.items()})

                candidate = neighborhood.best_neighbor(current_sol)
                objectif_candidat = candidate.objective
                if objectif_candidat < best_obj:
                    best_obj = objectif_candidat
                    # Capturer le snapshot du meilleur candidat
                    best_snap = _extract_orderings(instance)

            if best_snap is None:
                # Aucun voisinage n'a amélioré : optimum local
                _reconstruct(instance, current_snap)   # Restaurer l'état courant
                break

            # Reconstruire depuis le meilleur snapshot
            current_sol = _reconstruct(instance, best_snap)

        return current_sol


if __name__ == "__main__":
    # To play with the heuristics
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    inst = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp10")
    heur = FirstNeighborLocalSearch()
    sol = heur.run(inst, NonDeterminist, MyNeighborhood1)
    plt = sol.gantt("tab20")
    plt.savefig("gantt.png")
