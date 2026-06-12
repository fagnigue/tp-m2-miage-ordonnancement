'''
Informations sur une instance du problème d'optimisation.

@author: Vassilissa Lehoux
'''
from typing import List
import os
import csv

from src.scheduling.instance.job import Job
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class Instance(object):
    '''
    Représente une instance du problème d'ordonnancement :
    un ensemble de jobs (chacun composé d'opérations ordonnées)
    et un ensemble de machines (avec leurs paramètres énergétiques).
    '''

    def __init__(self, instance_name: str):
        '''
        Constructeur.
        @param instance_name: nom de l'instance (ex. "jsp1")
        '''
        self._instance_name = instance_name
        # Liste des machines indexée par machine_id
        self._machines: List[Machine] = []
        # Liste des jobs indexée par job_id
        self._jobs: List[Job] = []
        # Liste de toutes les opérations indexée par operation_id (global)
        self._operations: List[Operation] = []

    @classmethod
    def from_file(cls, folderpath: str) -> 'Instance':
        '''
        Crée une instance à partir des fichiers CSV du dossier folderpath.
        Lit d'abord le fichier des opérations, puis celui des machines.
        '''
        inst = cls(os.path.basename(folderpath))

        # Format : job, operation, machine, processing_time, energy_consumption
        op_file = folderpath + os.path.sep + inst._instance_name + '_op.csv'
        with open(op_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # ignorer l'en-tête
            for row in csv_reader:
                job_id       = int(row[0])
                operation_id = int(row[1])  # identifiant global de l'opération
                machine_id   = int(row[2])
                proc_time    = int(row[3])
                energy       = int(row[4])

                # Créer le job si nécessaire
                while len(inst._jobs) <= job_id:
                    inst._jobs.append(Job(len(inst._jobs)))

                # Créer l'opération si nécessaire (identifiant global unique)
                while len(inst._operations) <= operation_id:
                    inst._operations.append(None)  # type: ignore

                if inst._operations[operation_id] is None:
                    op = Operation(job_id, operation_id)
                    inst._operations[operation_id] = op
                    # Ajouter l'opération au job (gère les précédences intra-job)
                    inst._jobs[job_id].add_operation(op)

                # Ajouter l'option de traitement sur cette machine
                inst._operations[operation_id].add_machine_option(
                    machine_id, proc_time, energy
                )

        # --- Lecture du fichier des machines ---
        # Format : machine_id, set_up_time, set_up_energy, tear_down_time,
        #          tear_down_energy, min_consumption, end_time
        mach_file = folderpath + os.path.sep + inst._instance_name + '_mach.csv'
        with open(mach_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # ignorer l'en-tête
            for row in csv_reader:
                machine_id       = int(row[0])
                set_up_time      = int(row[1])
                set_up_energy    = int(row[2])
                tear_down_time   = int(row[3])
                tear_down_energy = int(row[4])
                min_consumption  = int(row[5])
                end_time         = int(row[6])

                # S'assurer que la liste des machines est assez grande
                while len(inst._machines) <= machine_id:
                    inst._machines.append(None)  # type: ignore

                inst._machines[machine_id] = Machine(
                    machine_id, set_up_time, set_up_energy,
                    tear_down_time, tear_down_energy,
                    min_consumption, end_time
                )

        return inst

    @property
    def name(self) -> str:
        return self._instance_name

    @property
    def machines(self) -> List[Machine]:
        return self._machines

    @property
    def jobs(self) -> List[Job]:
        return self._jobs

    @property
    def operations(self) -> List[Operation]:
        return self._operations

    @property
    def nb_jobs(self) -> int:
        return len(self._jobs)

    @property
    def nb_machines(self) -> int:
        return len(self._machines)

    @property
    def nb_operations(self) -> int:
        return len(self._operations)

    def __str__(self) -> str:
        return f"{self.name}_M{self.nb_machines}_J{self.nb_jobs}_O{self.nb_operations}"

    def get_machine(self, machine_id: int) -> Machine:
        '''
        Retourne la machine correspondant à machine_id.
        '''
        return self._machines[machine_id]

    def get_job(self, job_id: int) -> Job:
        '''
        Retourne le job correspondant à job_id.
        '''
        return self._jobs[job_id]

    def get_operation(self, operation_id: int) -> Operation:
        '''
        Retourne l'opération correspondant à operation_id (identifiant global).
        '''
        return self._operations[operation_id]
