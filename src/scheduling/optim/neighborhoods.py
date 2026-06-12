'''
Voisinages de solutions pour la recherche locale.

Deux voisinages sont implémentés :
- SwapOnMachine  (N1) : échange de deux opérations sur la même machine.
- MachineReassign (N2) : réaffectation d'une opération vers une autre machine compatible.

Fonctions utilitaires exposées :
- _extract_orderings(instance)     : snapshot {machine_id: [op, ...]}
- _reconstruct(instance, orderings) : reconstruit une Solution depuis un snapshot

@author: Vassilissa Lehoux
'''
from typing import Dict, List, Tuple
from collections import deque

from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation
from src.scheduling.solution import Solution


# ---------------------------------------------------------------------------
# Fonctions utilitaires partagées
# ---------------------------------------------------------------------------

def _is_ancestor(op_a: Operation, op_b: Operation) -> bool:
    '''
    Retourne True si op_a est un prédécesseur transitif de op_b.
    Utilisé pour détecter les conflits de précédence avant un échange.
    Algorithme : parcours en profondeur (DFS) sur les successeurs de op_a.
    '''
    stack = list(op_a.successors)
    visited = {op_a.operation_id}
    while stack:
        current = stack.pop()
        if current.operation_id == op_b.operation_id:
            return True
        if current.operation_id not in visited:
            visited.add(current.operation_id)
            stack.extend(current.successors)
    return False


def _extract_orderings(instance: Instance) -> Dict[int, List[Operation]]:
    '''
    Extrait un snapshot de l'ordonnancement courant de l'instance :
    {machine_id: [op1, op2, ...]} trié par heure de début.
    L'instance doit être dans l'état de la solution à capturer.
    '''
    return {
        machine.machine_id: sorted(
            machine.scheduled_operations,
            key=lambda o: o.start_time
        )
        for machine in instance.machines
    }


def _reconstruct(instance: Instance,
                 orderings: Dict[int, List[Operation]]) -> Solution:
    '''
    Reconstruit une Solution à partir d'un snapshot d'ordonnancement.
    Réinitialise l'instance puis planifie les opérations sur leurs machines
    dans l'ordre donné, en respectant les contraintes de précédence.

    Algorithme : list-scheduling avec files par machine.
    À chaque tour, on planifie toute opération en tête de file dont tous
    les prédécesseurs sont déjà planifiés.

    @param instance: instance à planifier (réinitialisée en interne)
    @param orderings: {machine_id: [op, ...]} (ordre fixé par machine)
    @return: Solution reconstruite
    '''
    solution = Solution(instance)   # réinitialise toutes les opérations / machines

    # Files d'attente par machine (ordre issu du snapshot)
    queues = {m_id: deque(ops) for m_id, ops in orderings.items() if ops}

    # Planifier jusqu'à épuisement ou blocage (deadlock détecté si aucun progrès)
    while any(queues.values()):
        progress = False
        for m_id, queue in list(queues.items()):
            # Avancer dans la file tant que le premier élément est prêt
            while queue and all(pred.assigned for pred in queue[0].predecessors):
                machine = instance.get_machine(m_id)
                solution.schedule(queue[0], machine)
                queue.popleft()
                progress = True
        if not progress:
            break   # deadlock (ne devrait pas arriver sur des instances valides)

    return solution


# ---------------------------------------------------------------------------
# Classe de base (à ne pas modifier)
# ---------------------------------------------------------------------------

class Neighborhood(object):
    '''
    Classe de base pour les voisinages.
    Do not modify!!!
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        '''
        Constructeur.
        '''
        self._instance = instance

    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Retourne le meilleur voisin de sol (ou sol lui-même si aucun ne l'améliore).
        '''
        raise NotImplementedError

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Retourne le premier voisin de sol qui l'améliore,
        ou sol lui-même si aucun ne l'améliore.
        '''
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Voisinage N1 : SwapOnMachine
# ---------------------------------------------------------------------------

class SwapOnMachine(Neighborhood):
    '''
    Voisinage N1 — Échange de deux opérations sur la même machine.

    Un mouvement (i, j, machine_id) inverse les positions i et j
    dans la file d'ordonnancement de la machine machine_id.
    Les échanges créant un deadlock (relation de précédence transitive
    entre les deux opérations) sont exclus.

    Taille du voisinage :
        sum_{m} C(|ops_m|, 2)
      - Pire cas : O(O²) (toutes les opérations sur une seule machine).
      - Cas moyen équilibré : O(O²/M).
      → Polynomiale en la taille de l'instance.

    Connexité : ce voisinage ne modifie pas l'affectation des opérations
    aux machines, donc il ne permet pas d'atteindre toutes les solutions
    depuis une solution de départ arbitraire.
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        super().__init__(instance, params)

    def _moves(self, snap: Dict[int, List[Operation]]) -> List[Tuple]:
        '''
        Génère tous les échanges valides à partir du snapshot courant.
        Exclut les paires (op_i, op_j) reliées par une précédence transitive.
        '''
        moves = []
        for m_id, ops in snap.items():
            for i in range(len(ops)):
                for j in range(i + 1, len(ops)):
                    # Exclure les paires avec contrainte de précédence
                    if (not _is_ancestor(ops[i], ops[j])
                            and not _is_ancestor(ops[j], ops[i])):
                        moves.append((i, j, m_id))
        return moves

    def _apply(self, snap: Dict, i: int, j: int, m_id: int) -> Dict:
        '''Retourne un nouveau snapshot avec les positions i et j échangées.'''
        new_snap = {mid: list(ops) for mid, ops in snap.items()}
        new_snap[m_id][i], new_snap[m_id][j] = new_snap[m_id][j], new_snap[m_id][i]
        return new_snap

    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Explore tout le voisinage et retourne le meilleur voisin.
        Si aucun voisin n'améliore la solution, retourne la solution courante.
        '''
        current_obj = sol.objective     # Valeur mise en cache avant tout changement d'état
        snap = _extract_orderings(self._instance)
        best_snap = snap
        best_obj = current_obj
        n_ops = len(self._instance.operations)

        for move in self._moves(snap):
            new_snap = self._apply(snap, *move)
            neighbor = _reconstruct(self._instance, new_snap)
            # Ignorer les mouvements qui créent un deadlock (planning incomplet)
            if any(not op.assigned for op in self._instance.operations):
                continue
            objectif_voisin = neighbor.objective
            if objectif_voisin < best_obj:
                best_obj = objectif_voisin
                best_snap = {mid: list(ops) for mid, ops in new_snap.items()}

        # Reconstruction finale dans l'état optimal trouvé
        return _reconstruct(self._instance, best_snap)

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Retourne le premier voisin qui améliore la solution.
        Si aucun, retourne la solution courante (instance restaurée).
        '''
        current_obj = sol.objective
        snap = _extract_orderings(self._instance)

        for move in self._moves(snap):
            new_snap = self._apply(snap, *move)
            neighbor = _reconstruct(self._instance, new_snap)
            # Ignorer les mouvements qui créent un deadlock (planning incomplet)
            if any(not op.assigned for op in self._instance.operations):
                continue
            if neighbor.objective < current_obj:
                return neighbor     # Première amélioration trouvée

        # Aucune amélioration : restaurer l'état courant
        return _reconstruct(self._instance, snap)


# ---------------------------------------------------------------------------
# Voisinage N2 : MachineReassign
# ---------------------------------------------------------------------------

class MachineReassign(Neighborhood):
    '''
    Voisinage N2 — Réaffectation d'une opération vers une autre machine compatible.

    Un mouvement (op, old_machine_id, new_machine_id) retire l'opération
    de sa machine actuelle et l'ajoute en fin de file de la nouvelle machine.

    Taille du voisinage :
        sum_{o} (|machines_compatibles(o)| - 1)
      - Pire cas : O(O × M) (toutes les opérations compatibles avec toutes les machines).
      → Polynomiale en la taille de l'instance.

    Connexité : ce voisinage ne peut pas réordonner les opérations au sein
    d'une même machine, donc il ne permet pas d'atteindre toutes les solutions.
    Combiné à SwapOnMachine, l'espace des solutions est mieux couvert.
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        super().__init__(instance, params)

    def _moves(self, snap: Dict[int, List[Operation]]) -> List[Tuple]:
        '''
        Génère tous les mouvements de réaffectation valides.
        Chaque mouvement est (op, old_machine_id, new_machine_id, insert_pos) où
        insert_pos est la position d'insertion qui respecte les précédences
        entre op et les opérations déjà sur la nouvelle machine.
        '''
        moves = []
        for m_id, ops in snap.items():
            for op in ops:
                for new_m_id in op.compatible_machines:
                    if new_m_id == m_id:
                        continue
                    nouvelle_file = snap.get(new_m_id, [])
                    # Calculer la plage de positions valides pour l'insertion
                    min_pos, max_pos = 0, len(nouvelle_file)
                    for i, existing_op in enumerate(nouvelle_file):
                        if _is_ancestor(existing_op, op):   # existing_op précède op
                            min_pos = max(min_pos, i + 1)
                        elif _is_ancestor(op, existing_op): # op précède existing_op
                            max_pos = min(max_pos, i)
                    if min_pos <= max_pos:
                        # Insérer à la première position valide (respecte les précédences)
                        moves.append((op, m_id, new_m_id, min_pos))
        return moves

    def _apply(self, snap: Dict, op: Operation,
               old_m_id: int, new_m_id: int, insert_pos: int) -> Dict:
        '''Retourne un nouveau snapshot avec l'opération insérée à insert_pos.'''
        new_snap = {mid: list(ops) for mid, ops in snap.items()}
        # Retirer de l'ancienne machine
        new_snap[old_m_id] = [
            o for o in new_snap[old_m_id] if o.operation_id != op.operation_id
        ]
        # Insérer à la position calculée sur la nouvelle machine
        new_snap.setdefault(new_m_id, [])
        nouvelle_file = list(new_snap[new_m_id])
        nouvelle_file.insert(insert_pos, op)
        new_snap[new_m_id] = nouvelle_file
        return new_snap

    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Explore tout le voisinage et retourne le meilleur voisin.
        Si aucun voisin n'améliore la solution, retourne la solution courante.
        '''
        current_obj = sol.objective
        snap = _extract_orderings(self._instance)
        best_snap = snap
        best_obj = current_obj

        for move in self._moves(snap):
            new_snap = self._apply(snap, *move)
            neighbor = _reconstruct(self._instance, new_snap)
            # Ignorer les mouvements qui créent un deadlock (planning incomplet)
            if any(not op.assigned for op in self._instance.operations):
                continue
            objectif_voisin = neighbor.objective
            if objectif_voisin < best_obj:
                best_obj = objectif_voisin
                best_snap = {mid: list(ops) for mid, ops in new_snap.items()}

        return _reconstruct(self._instance, best_snap)

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Retourne le premier voisin qui améliore la solution.
        Si aucun, retourne la solution courante (instance restaurée).
        '''
        current_obj = sol.objective
        snap = _extract_orderings(self._instance)

        for move in self._moves(snap):
            new_snap = self._apply(snap, *move)
            neighbor = _reconstruct(self._instance, new_snap)
            # Ignorer les mouvements qui créent un deadlock (planning incomplet)
            if any(not op.assigned for op in self._instance.operations):
                continue
            if neighbor.objective < current_obj:
                return neighbor

        return _reconstruct(self._instance, snap)


# Alias pour la compatibilité avec le squelette d'origine
MyNeighborhood1 = SwapOnMachine
MyNeighborhood2 = MachineReassign
