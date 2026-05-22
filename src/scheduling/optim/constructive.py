'''
Heuristiques constructives : glouton déterministe et non-déterministe.

@author: Vassilissa Lehoux
'''
from typing import Dict, List, Tuple
import random

from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine
from src.scheduling.solution import Solution
from src.scheduling.optim.heuristics import Heuristic


def _estimated_start(op: Operation, machine: Machine) -> int:
    '''
    Estime l'heure de début de l'opération sur la machine,
    en tenant compte de la disponibilité de la machine et des précédences.
    Si la machine n'est pas encore démarrée, on tient compte du set_up_time.
    '''
    if not machine.start_times:
        # Machine pas encore démarrée : elle devra faire son set_up avant de traiter l'op.
        # Elle démarre au plus tôt à max(0, min_start - set_up_time),
        # donc est prête à max(set_up_time, min_start_time).
        return max(op.min_start_time, machine.set_up_time)
    else:
        # Machine déjà démarrée : l'op commence dès qu'elle est libre
        return max(op.min_start_time, machine.available_time)


def _pair_score(op: Operation, machine: Machine,
                w_energy: float, w_time: float) -> float:
    '''
    Calcule le score immédiat d'une paire (opération, machine).
    Le score est une somme pondérée de l'énergie de traitement
    et du temps de complétion estimé.
    Plus le score est bas, meilleur est le choix.
    @param w_energy: poids de la composante énergie
    @param w_time: poids de la composante temps de complétion
    '''
    machine_id = machine.machine_id
    pt = op.get_processing_time_on(machine_id)
    energy = op.get_energy_on(machine_id)
    if pt < 0:
        return float('inf')  # machine incompatible

    start = _estimated_start(op, machine)
    completion = start + pt
    return w_energy * energy + w_time * completion


def _all_candidates(solution: Solution, instance: Instance,
                    w_energy: float, w_time: float
                    ) -> List[Tuple[float, Operation, Machine]]:
    '''
    Construit et trie la liste de tous les couples (score, op, machine)
    parmi les opérations disponibles et leurs machines compatibles.
    '''
    candidates = []
    for op in solution.available_operations:
        for machine_id in op.compatible_machines:
            machine = instance.get_machine(machine_id)
            score = _pair_score(op, machine, w_energy, w_time)
            candidates.append((score, op, machine))
    # Tri par score croissant (meilleur choix en premier)
    candidates.sort(key=lambda x: x[0])
    return candidates


class Greedy(Heuristic):
    '''
    Heuristique gloutonne déterministe.

    Principe glouton : à chaque étape, parmi toutes les paires (opération disponible,
    machine compatible), on choisit irrémédiablement celle qui minimise un score local
    combinant l'énergie de traitement et le temps de complétion estimé.
    Aucun retour arrière n'est effectué.

    Complexité : O(O² × M) où O = nombre d'opérations, M = nombre de machines.
    À chaque étape (O étapes au total), on évalue O × M paires et on prend le minimum.
    '''

    def __init__(self, params: Dict = dict()):
        '''
        @param params: dictionnaire optionnel avec les clés :
            - "w_energy" (float, défaut 1.0) : poids de l'énergie dans le score local
            - "w_time"   (float, défaut 1.0) : poids du temps de complétion dans le score local
        '''
        super().__init__(params)

    def run(self, instance: Instance, params: Dict = dict()) -> Solution:
        '''
        Construit une solution déterministe en choisissant à chaque étape
        la paire (opération, machine) de score minimal.
        @param instance: instance à résoudre
        @param params: peut contenir "w_energy" et "w_time"
        @return: Solution construite (réalisable si l'instance l'admet)
        '''
        # Fusion des paramètres (priorité à ceux passés dans run)
        merged = {**self._params, **params}
        w_energy = float(merged.get('w_energy', 1.0))
        w_time   = float(merged.get('w_time',   1.0))

        solution = Solution(instance)

        # Boucle principale : planifier une opération par itération
        while solution.available_operations:
            candidates = _all_candidates(solution, instance, w_energy, w_time)
            if not candidates:
                break  # aucune paire réalisable (ne devrait pas arriver sur instances valides)
            # Choix glouton : la paire avec le score le plus bas
            _, best_op, best_machine = candidates[0]
            solution.schedule(best_op, best_machine)

        return solution


class NonDeterminist(Heuristic):
    '''
    Heuristique constructive non-déterministe (inspirée de GRASP).

    Référence :
        Feo, T.A. & Resende, M.G.C. (1995). Greedy Randomized Adaptive Search
        Procedures. Journal of Global Optimization, 6(2), 109-133.

    Principe : à chaque étape, on construit une liste restreinte de candidats (RCL)
    composée des k meilleures paires (opération, machine), puis on en choisit une
    au hasard. Cela produit une solution différente à chaque appel pour la même
    instance.

    Complexité : O(O² × M × log(O × M)) — comme Greedy avec un tri supplémentaire
    pour construire la RCL.
    '''

    def __init__(self, params: Dict = dict()):
        '''
        @param params: dictionnaire optionnel avec les clés :
            - "w_energy" (float, défaut 1.0)  : poids énergie dans le score
            - "w_time"   (float, défaut 1.0)  : poids temps de complétion
            - "k"        (int,   défaut 3)    : taille de la liste restreinte (RCL)
            - "seed"     (int,   défaut None) : graine aléatoire (None = non fixée)
        '''
        super().__init__(params)

    def run(self, instance: Instance, params: Dict = dict()) -> Solution:
        '''
        Construit une solution en choisissant aléatoirement parmi les k meilleures
        paires (opération, machine) à chaque étape.
        @param instance: instance à résoudre
        @param params: peut contenir "w_energy", "w_time", "k", "seed"
        @return: Solution construite (différente à chaque appel sans seed fixée)
        '''
        merged = {**self._params, **params}
        w_energy = float(merged.get('w_energy', 1.0))
        w_time   = float(merged.get('w_time',   1.0))
        k        = int(merged.get('k', 3))
        seed     = merged.get('seed', None)

        rng = random.Random(seed)  # générateur isolé pour ne pas perturber l'état global

        solution = Solution(instance)

        while solution.available_operations:
            candidates = _all_candidates(solution, instance, w_energy, w_time)
            if not candidates:
                break
            # Liste restreinte : les k meilleures paires (ou moins s'il en reste peu)
            rcl = candidates[:min(k, len(candidates))]
            # Choix aléatoire dans la RCL
            _, chosen_op, chosen_machine = rng.choice(rcl)
            solution.schedule(chosen_op, chosen_machine)

        return solution


if __name__ == "__main__":
    # Exemple d'utilisation : générer et afficher un Gantt
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    inst = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp1")
    heur = NonDeterminist()
    sol = heur.run(inst)
    gantt = sol.gantt("tab20")
    gantt.savefig("gantt.png")
