'''
Opération d'un job.
La durée et la consommation d'énergie dépendent de la machine sur laquelle
l'opération est exécutée. Quand l'opération est planifiée, ses informations
de planning sont mises à jour.

@author: Vassilissa Lehoux
'''
from typing import List, Dict, Tuple, Optional


class OperationScheduleInfo(object):
    '''
    Informations connues quand l'opération est planifiée :
    machine choisie, heure de début, durée et consommation d'énergie.
    '''

    def __init__(self, machine_id: int, schedule_time: int, duration: int, energy_consumption: int):
        # Identifiant de la machine sur laquelle l'opération est planifiée
        self._machine_id = machine_id
        # Heure de début de l'opération
        self._start_time = schedule_time
        # Durée de traitement sur cette machine (en minutes)
        self._duration = duration
        # Consommation énergétique de l'opération sur cette machine (en kWh)
        self._energy = energy_consumption


class Operation(object):
    '''
    Opération d'un job.
    Stocke les options de machines disponibles ainsi que les informations
    de précédence et de planning.
    '''

    def __init__(self, job_id: int, operation_id: int):
        '''
        Constructeur.
        @param job_id: identifiant du job auquel appartient cette opération
        @param operation_id: identifiant global unique de l'opération
        '''
        self._job_id = job_id
        self._operation_id = operation_id
        # Dictionnaire {machine_id: (processing_time, energy_consumption)}
        # contenant les options de traitement sur chaque machine compatible
        self._machine_options: Dict[int, Tuple[int, int]] = {}
        # Liste des opérations qui doivent être terminées avant celle-ci
        self._predecessors: List['Operation'] = []
        # Liste des opérations qui ne peuvent commencer qu'après celle-ci
        self._successors: List['Operation'] = []
        # Informations de planning (None si non planifiée)
        self._schedule_info: Optional[OperationScheduleInfo] = None

    def __str__(self):
        '''
        Représentation textuelle de l'opération.
        '''
        base_str = f"O{self.operation_id}_J{self.job_id}"
        if self._schedule_info:
            return base_str + f"_M{self.assigned_to}_ci{self.processing_time}_e{self.energy}"
        else:
            return base_str

    def __repr__(self):
        return str(self)

    def reset(self):
        '''
        Supprime les informations de planning (remet l'opération à l'état initial).
        '''
        self._schedule_info = None

    def add_machine_option(self, machine_id: int, processing_time: int, energy_consumption: int):
        '''
        Ajoute une option de machine pour cette opération.
        @param machine_id: identifiant de la machine
        @param processing_time: durée de traitement en minutes sur cette machine
        @param energy_consumption: énergie consommée en kWh sur cette machine
        '''
        self._machine_options[machine_id] = (processing_time, energy_consumption)

    def get_processing_time_on(self, machine_id: int) -> int:
        '''
        Retourne la durée de traitement sur une machine donnée.
        Retourne -1 si la machine n'est pas compatible.
        '''
        if machine_id in self._machine_options:
            return self._machine_options[machine_id][0]
        return -1

    def get_energy_on(self, machine_id: int) -> int:
        '''
        Retourne la consommation d'énergie sur une machine donnée.
        Retourne -1 si la machine n'est pas compatible.
        '''
        if machine_id in self._machine_options:
            return self._machine_options[machine_id][1]
        return -1

    @property
    def compatible_machines(self) -> List[int]:
        '''
        Retourne la liste des identifiants de machines compatibles avec cette opération.
        '''
        return list(self._machine_options.keys())

    def add_predecessor(self, operation: 'Operation'):
        '''
        Ajoute une opération précédente (contrainte de précédence).
        '''
        if operation not in self._predecessors:
            self._predecessors.append(operation)

    def add_successor(self, operation: 'Operation'):
        '''
        Ajoute une opération suivante (contrainte de précédence).
        '''
        if operation not in self._successors:
            self._successors.append(operation)

    @property
    def operation_id(self) -> int:
        return self._operation_id

    @property
    def job_id(self) -> int:
        return self._job_id

    @property
    def predecessors(self) -> List['Operation']:
        '''
        Retourne la liste des opérations précédentes.
        '''
        return self._predecessors

    @property
    def successors(self) -> List['Operation']:
        '''
        Retourne la liste des opérations suivantes.
        '''
        return self._successors

    @property
    def assigned(self) -> bool:
        '''
        Retourne True si l'opération est planifiée sur une machine.
        '''
        return self._schedule_info is not None

    @property
    def assigned_to(self) -> int:
        '''
        Retourne l'identifiant de la machine sur laquelle l'opération est planifiée.
        Retourne -1 si non planifiée.
        '''
        if self._schedule_info:
            return self._schedule_info._machine_id
        return -1

    @property
    def processing_time(self) -> int:
        '''
        Retourne la durée de traitement si planifiée, -1 sinon.
        '''
        if self._schedule_info:
            return self._schedule_info._duration
        return -1

    @property
    def start_time(self) -> int:
        '''
        Retourne l'heure de début si planifiée, -1 sinon.
        '''
        if self._schedule_info:
            return self._schedule_info._start_time
        return -1

    @property
    def end_time(self) -> int:
        '''
        Retourne l'heure de fin si planifiée, -1 sinon.
        '''
        if self._schedule_info:
            return self._schedule_info._start_time + self._schedule_info._duration
        return -1

    @property
    def energy(self) -> int:
        '''
        Retourne la consommation énergétique si planifiée, -1 sinon.
        '''
        if self._schedule_info:
            return self._schedule_info._energy
        return -1

    def is_ready(self, at_time: int) -> bool:
        '''
        Retourne True si tous les prédécesseurs sont planifiés et terminés avant at_time.
        '''
        for pred in self._predecessors:
            if not pred.assigned or pred.end_time > at_time:
                return False
        return True

    @property
    def min_start_time(self) -> int:
        '''
        Heure de début minimale imposée par les contraintes de précédence.
        Retourne 0 s'il n'y a pas de prédécesseur.
        '''
        if not self._predecessors:
            return 0
        # L'opération ne peut commencer qu'après la fin de tous ses prédécesseurs
        return max(pred.end_time for pred in self._predecessors)

    def schedule(self, machine_id: int, at_time: int, check_success: bool = True) -> bool:
        '''
        Planifie l'opération sur une machine à une heure donnée.
        Met à jour les informations de planning de l'opération.
        @param machine_id: identifiant de la machine choisie
        @param at_time: heure de début de l'opération
        @param check_success: si True, vérifie la compatibilité (précédences + machine)
        @return: True si la planification a réussi, False sinon
        '''
        if check_success:
            # Vérifier que la machine est compatible
            if machine_id not in self._machine_options:
                return False
            # Vérifier que les prédécesseurs sont terminés avant at_time
            if not self.is_ready(at_time):
                return False

        pt, energy = self._machine_options[machine_id]
        self._schedule_info = OperationScheduleInfo(machine_id, at_time, pt, energy)
        return True

    def schedule_at_min_time(self, machine_id: int, min_time: int) -> bool:
        '''
        Tente de planifier l'opération sur machine_id au plus tôt à partir de min_time.
        Retourne False si la machine n'est pas compatible.
        @param machine_id: identifiant de la machine
        @param min_time: heure minimale de début imposée par la machine
        '''
        if machine_id not in self._machine_options:
            return False
        # L'heure réelle est le max entre la contrainte machine et les précédences
        actual_time = max(min_time, self.min_start_time)
        return self.schedule(machine_id, actual_time, check_success=False)
