'''
Machine sur laquelle les opérations sont exécutées.

@author: Vassilissa Lehoux
'''
from typing import List
from src.scheduling.instance.operation import Operation


class Machine(object):
    '''
    Représente une machine de l'atelier.
    Une machine doit être démarrée (set_up) avant de traiter des opérations,
    et arrêtée (tear_down) en fin de planning.
    Elle peut être allumée et éteinte plusieurs fois.
    '''

    def __init__(self, machine_id: int, set_up_time: int, set_up_energy: int,
                 tear_down_time: int, tear_down_energy: int,
                 min_consumption: int, end_time: int):
        '''
        Constructeur.
        La machine est éteinte au début du planning et doit être démarrée
        avant d'exécuter toute opération.
        @param machine_id: identifiant unique de la machine
        @param set_up_time: durée du démarrage en minutes
        @param set_up_energy: énergie consommée au démarrage en kWh
        @param tear_down_time: durée de l'arrêt en minutes
        @param tear_down_energy: énergie consommée à l'arrêt en kWh
        @param min_consumption: puissance consommée à vide en kW (machine allumée mais inactive)
        @param end_time: heure maximale à laquelle la machine doit avoir arrêté de fonctionner
        '''
        self._machine_id = machine_id
        self._set_up_time = set_up_time
        self._set_up_energy = set_up_energy
        self._tear_down_time = tear_down_time
        self._tear_down_energy = tear_down_energy
        self._min_consumption = min_consumption
        self._end_time = end_time

        # Opérations planifiées sur cette machine (dans l'ordre d'exécution)
        self._scheduled_operations: List[Operation] = []
        # Heures de démarrage (début du set_up) pour chaque cycle allumé/éteint
        self._start_times: List[int] = []
        # Heures d'arrêt (début du tear_down) pour chaque cycle allumé/éteint
        self._stop_times: List[int] = []
        # Prochain instant auquel la machine est disponible pour une nouvelle opération
        self._available_time: int = 0

    def reset(self):
        '''
        Remet la machine à son état initial (aucune opération planifiée).
        '''
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []
        self._available_time = 0

    @property
    def set_up_time(self) -> int:
        return self._set_up_time

    @property
    def tear_down_time(self) -> int:
        return self._tear_down_time

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def end_time(self) -> int:
        '''
        Heure maximale à laquelle la machine doit avoir arrêté de fonctionner.
        '''
        return self._end_time

    @property
    def scheduled_operations(self) -> List[Operation]:
        '''
        Retourne la liste des opérations planifiées sur cette machine.
        '''
        return self._scheduled_operations

    @property
    def available_time(self) -> int:
        '''
        Prochain instant auquel la machine est disponible (après sa dernière opération
        ou après son dernier démarrage).
        '''
        return self._available_time

    def add_operation(self, operation: Operation, start_time: int) -> int:
        '''
        Ajoute une opération sur la machine, à la suite du planning existant,
        au plus tôt à partir de start_time.
        Si la machine n'est pas encore démarrée, elle est démarrée automatiquement.
        Par défaut, la machine fonctionne jusqu'à end_time (un seul cycle on/off
        dans l'implémentation de base).
        @param operation: l'opération à planifier
        @param start_time: heure de début minimale imposée par les précédences
        @return: heure de début effective de l'opération
        '''
        if not self._start_times:
            # Première utilisation : démarrer la machine le plus tôt possible
            # pour que le set_up soit terminé au moment voulu.
            # Le set_up commence à max(0, start_time - set_up_time).
            machine_start = max(0, start_time - self._set_up_time)
            ready_time = machine_start + self._set_up_time
            actual_start = max(start_time, ready_time)

            self._start_times.append(machine_start)
            # Par défaut, la machine s'arrête à end_time
            self._stop_times.append(self._end_time)
            self._available_time = ready_time
        else:
            # La machine est déjà démarrée : l'opération commence dès qu'elle est libre
            actual_start = max(start_time, self._available_time)

        # Planifier l'opération sur cette machine à l'heure calculée
        operation.schedule(self._machine_id, actual_start)
        self._scheduled_operations.append(operation)
        # Mettre à jour la disponibilité de la machine
        self._available_time = actual_start + operation.processing_time
        return actual_start

    def stop(self, at_time: int):
        '''
        Arrête la machine à at_time (début du tear_down).
        La machine doit avoir terminé toutes ses opérations avant d'être arrêtée.
        @param at_time: heure de début de l'arrêt (tear_down)
        '''
        assert at_time >= self._available_time, (
            f"Impossible d'arrêter la machine {self._machine_id} à t={at_time} : "
            f"dernière opération se termine à t={self._available_time}"
        )
        if self._stop_times:
            self._stop_times[-1] = at_time

    @property
    def working_time(self) -> int:
        '''
        Durée totale pendant laquelle la machine est allumée (somme sur tous les cycles).
        Correspond à la somme des (stop_time - start_time) sur chaque cycle.
        '''
        return sum(
            stop - start
            for start, stop in zip(self._start_times, self._stop_times)
        )

    @property
    def start_times(self) -> List[int]:
        '''
        Liste des heures de démarrage (début du set_up) par ordre croissant.
        '''
        return self._start_times

    @property
    def stop_times(self) -> List[int]:
        '''
        Liste des heures d'arrêt (début du tear_down) par ordre croissant.
        '''
        return self._stop_times

    @property
    def total_energy_consumption(self) -> float:
        '''
        Consommation énergétique totale de la machine sur toute la durée du planning.
        Inclut : énergie de démarrage/arrêt, énergie des opérations,
        énergie à vide (min_consumption × temps_idle / 60).
        '''
        if not self._start_times:
            return 0.0

        n_cycles = len(self._start_times)

        # Énergie de démarrage et d'arrêt (une fois par cycle)
        e_switch = n_cycles * (self._set_up_energy + self._tear_down_energy)

        # Énergie consommée par les opérations planifiées
        e_proc = sum(op.energy for op in self._scheduled_operations)

        # Temps total pendant lequel la machine est allumée (working_time)
        total_working = self.working_time

        # Temps actif = set_up + somme des durées de traitement (sur tous les cycles)
        total_active = (
            n_cycles * self._set_up_time
            + sum(op.processing_time for op in self._scheduled_operations)
        )

        # Temps à vide = working_time - temps actif
        idle_time = max(0, total_working - total_active)

        # Énergie à vide : puissance (kW) × temps (min) / 60 → kWh
        e_idle = self._min_consumption * idle_time / 60.0

        return e_switch + e_proc + e_idle

    def __str__(self):
        return f"M{self.machine_id}"

    def __repr__(self):
        return str(self)
