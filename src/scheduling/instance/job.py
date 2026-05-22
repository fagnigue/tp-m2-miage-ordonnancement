'''
Job composé de plusieurs opérations à effectuer dans l'ordre.

@author: Vassilissa Lehoux
'''
from typing import List, Optional

from src.scheduling.instance.operation import Operation


class Job(object):
    '''
    Représente un job (tâche) composé d'une suite d'opérations ordonnées.
    Les opérations doivent être exécutées dans l'ordre : l'opération i+1
    ne peut commencer qu'une fois l'opération i terminée.
    '''

    def __init__(self, job_id: int):
        '''
        Constructeur.
        @param job_id: identifiant unique du job
        '''
        self._job_id = job_id
        # Liste ordonnée des opérations du job
        self._operations: List[Operation] = []
        # Index de la prochaine opération à planifier
        self._next_op_index: int = 0

    @property
    def job_id(self) -> int:
        '''
        Retourne l'identifiant du job.
        '''
        return self._job_id

    def reset(self):
        '''
        Réinitialise l'index de planification (ne remet pas les opérations à zéro,
        cela est fait par Solution.reset via Operation.reset).
        '''
        self._next_op_index = 0

    @property
    def operations(self) -> List[Operation]:
        '''
        Retourne la liste ordonnée des opérations du job.
        '''
        return self._operations

    @property
    def next_operation(self) -> Optional[Operation]:
        '''
        Retourne la prochaine opération à planifier,
        ou None si toutes les opérations sont planifiées.
        '''
        if self._next_op_index < len(self._operations):
            return self._operations[self._next_op_index]
        return None

    def schedule_operation(self):
        '''
        Avance l'index de la prochaine opération à planifier.
        À appeler après avoir planifié next_operation.
        '''
        self._next_op_index += 1

    @property
    def planned(self) -> bool:
        '''
        Retourne True si toutes les opérations du job sont planifiées.
        '''
        return self._next_op_index >= len(self._operations)

    @property
    def operation_nb(self) -> int:
        '''
        Retourne le nombre d'opérations du job.
        '''
        return len(self._operations)

    def add_operation(self, operation: Operation):
        '''
        Ajoute une opération à la fin de la liste du job.
        Ajoute automatiquement la contrainte de précédence avec l'opération précédente.
        '''
        if self._operations:
            # L'opération précédente doit être terminée avant la nouvelle
            prev_op = self._operations[-1]
            prev_op.add_successor(operation)
            operation.add_predecessor(prev_op)
        self._operations.append(operation)

    @property
    def completion_time(self) -> int:
        '''
        Retourne l'heure de fin du job (heure de fin de la dernière opération).
        Retourne -1 si le job n'est pas entièrement planifié.
        '''
        if self._operations and self._operations[-1].assigned:
            return self._operations[-1].end_time
        return -1
