'''
Objet contenant la solution au problème d'optimisation.

@author: Vassilissa Lehoux
'''
from typing import List, Optional
import os
import csv
from matplotlib import pyplot as plt
from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation

from matplotlib import colormaps
from src.scheduling.instance.machine import Machine


class Solution(object):
    '''
    Représente une solution du problème d'ordonnancement :
    pour chaque opération, la machine choisie et l'heure de début ;
    pour chaque machine, les heures de démarrage et d'arrêt.
    '''

    def __init__(self, instance: Instance):
        '''
        Constructeur.
        Initialise la solution à partir d'une instance (aucune opération planifiée).
        @param instance: instance du problème à résoudre
        '''
        self._instance = instance
        # Valeur de la fonction objectif (calculée par evaluate)
        self._objective_value: Optional[float] = None
        # Poids de la fonction objectif agrégée : (énergie, Cmax, sum_Ci)
        self._weights = (1.0, 1.0, 1.0)
        # Réinitialiser machines et opérations
        self.reset()

    @property
    def inst(self) -> Instance:
        '''
        Retourne l'instance associée à cette solution.
        '''
        return self._instance

    def reset(self):
        '''
        Réinitialise la solution : toutes les opérations et machines
        reviennent à leur état initial (rien de planifié).
        '''
        for op in self._instance.operations:
            op.reset()
        for machine in self._instance.machines:
            machine.reset()
        for job in self._instance.jobs:
            job.reset()
        self._objective_value = None

    @property
    def is_feasible(self) -> bool:
        '''
        Retourne True si la solution respecte toutes les contraintes :
          1. Toutes les opérations sont planifiées.
          2. Les contraintes de précédence intra-job sont respectées.
          3. Pas de chevauchement d'opérations sur une même machine.
          4. Chaque machine termine toutes ses opérations avant end_time.
        '''
        # 1. Toutes les opérations doivent être planifiées
        if not all(op.assigned for op in self._instance.operations):
            return False

        for op in self._instance.operations:
            # 2. Contraintes de précédence : chaque prédécesseur doit se terminer
            #    avant ou exactement au moment où cette opération commence
            for pred in op.predecessors:
                if pred.end_time > op.start_time:
                    return False

        for machine in self._instance.machines:
            ops_on_machine = sorted(
                machine.scheduled_operations, key=lambda o: o.start_time
            )
            # 3. Pas de chevauchement sur la machine
            for i in range(len(ops_on_machine) - 1):
                if ops_on_machine[i].end_time > ops_on_machine[i + 1].start_time:
                    return False
            # 4. Toutes les opérations doivent se terminer avant end_time
            for op in ops_on_machine:
                if op.end_time > machine.end_time:
                    return False

        return True

    @property
    def evaluate(self) -> float:
        '''
        Calcule et retourne la valeur de la fonction objectif agrégée.
        Fonction objectif = w_E * E_total + w_T * Cmax + w_M * sum_Ci
        (les poids sont normalisés par la magnitude des composantes)
        '''
        w_E, w_T, w_M = self._weights
        score = (
            w_E * self.total_energy_consumption
            + w_T * self.cmax
            + w_M * self.sum_ci
        )
        self._objective_value = score
        return score

    @property
    def objective(self) -> float:
        '''
        Retourne la valeur de la fonction objectif (calcule si nécessaire).
        '''
        if self._objective_value is None:
            return self.evaluate
        return self._objective_value

    @property
    def cmax(self) -> int:
        '''
        Retourne le makespan : heure de fin maximale parmi tous les jobs.
        '''
        completion_times = [
            job.completion_time for job in self._instance.jobs
            if job.completion_time >= 0
        ]
        return max(completion_times) if completion_times else 0

    @property
    def sum_ci(self) -> int:
        '''
        Retourne la somme des temps de complétion de tous les jobs.
        '''
        return sum(
            job.completion_time for job in self._instance.jobs
            if job.completion_time >= 0
        )

    @property
    def total_energy_consumption(self) -> float:
        '''
        Retourne la consommation énergétique totale de toutes les machines
        (opérations + démarrages/arrêts + consommation à vide).
        '''
        return sum(
            machine.total_energy_consumption
            for machine in self._instance.machines
        )

    def __str__(self) -> str:
        '''
        Représentation textuelle de la solution.
        '''
        lines = [f"Solution {self._instance.name}"]
        for op in self._instance.operations:
            if op.assigned:
                lines.append(
                    f"  Op{op.operation_id}(Job{op.job_id}) → "
                    f"M{op.assigned_to} : [{op.start_time}, {op.end_time}]"
                )
        return "\n".join(lines)

    def to_csv(self, output_folder: str):
        '''
        Sauvegarde la solution dans deux fichiers CSV.
        Fichier opérations : operation_id, machine_id, start_time
        Fichier machines   : machine_id, start_time, stop_time
        '''
        os.makedirs(output_folder, exist_ok=True)

        op_path = os.path.join(output_folder, 'solution_ops.csv')
        with open(op_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['operation_id', 'machine_id', 'start_time'])
            for op in self._instance.operations:
                if op.assigned:
                    writer.writerow([op.operation_id, op.assigned_to, op.start_time])

        mach_path = os.path.join(output_folder, 'solution_machines.csv')
        with open(mach_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['machine_id', 'start_time', 'stop_time'])
            for machine in self._instance.machines:
                for start, stop in zip(machine.start_times, machine.stop_times):
                    writer.writerow([machine.machine_id, start, stop])

    def from_csv(self, inst_folder: str, operation_file: str, machine_file: str):
        '''
        Lit une solution depuis des fichiers CSV.
        Reconstruit le planning à partir des fichiers de l'instance.
        '''
        # Lecture des affectations d'opérations
        with open(os.path.join(inst_folder, operation_file), 'r') as f:
            reader = csv.reader(f)
            next(reader)  # ignorer l'en-tête
            for row in reader:
                op_id      = int(row[0])
                machine_id = int(row[1])
                start_time = int(row[2])
                op = self._instance.get_operation(op_id)
                op.schedule(machine_id, start_time, check_success=False)

        # Lecture des cycles allumé/éteint des machines
        with open(os.path.join(inst_folder, machine_file), 'r') as f:
            reader = csv.reader(f)
            next(reader)  # ignorer l'en-tête
            for row in reader:
                machine_id = int(row[0])
                start_time = int(row[1])
                stop_time  = int(row[2])
                machine = self._instance.get_machine(machine_id)
                machine._start_times.append(start_time)
                machine._stop_times.append(stop_time)

        # Reconstruire les listes d'opérations par machine
        for op in self._instance.operations:
            if op.assigned:
                machine = self._instance.get_machine(op.assigned_to)
                if op not in machine.scheduled_operations:
                    machine._scheduled_operations.append(op)

        # Trier les opérations par heure de début sur chaque machine
        for machine in self._instance.machines:
            machine._scheduled_operations.sort(key=lambda o: o.start_time)
            if machine._scheduled_operations:
                machine._available_time = machine._scheduled_operations[-1].end_time

    @property
    def available_operations(self) -> List[Operation]:
        '''
        Retourne les opérations disponibles pour être planifiées :
        toutes leurs opérations précédentes (dans le même job) sont déjà planifiées.
        '''
        return [
            op for op in self._instance.operations
            if not op.assigned
            and all(pred.assigned for pred in op.predecessors)
        ]

    @property
    def all_operations(self) -> List[Operation]:
        '''
        Retourne toutes les opérations de l'instance.
        '''
        return self._instance.operations

    def schedule(self, operation: Operation, machine: Machine):
        '''
        Planifie l'opération sur la machine, au plus tôt après ses précédences.
        Démarre la machine si elle n'est pas encore allumée.
        @param operation: une opération disponible pour la planification
        '''
        assert operation in self.available_operations, (
            f"L'opération {operation} n'est pas disponible pour la planification"
        )
        # La machine calcule l'heure de début effective en tenant compte
        # de son propre planning et des précédences de l'opération
        machine.add_operation(operation, operation.min_start_time)
        # Invalider la valeur objectif mise en cache
        self._objective_value = None

    def gantt(self, colormapname):
        """
        Generate a plot of the planning.
        Standard colormaps can be found at https://matplotlib.org/stable/users/explain/colors/colormaps.html
        """
        fig, ax = plt.subplots()
        colormap = colormaps[colormapname]
        for machine in self.inst.machines:
            machine_operations = sorted(machine.scheduled_operations, key=lambda op: op.start_time)
            for operation in machine_operations:
                operation_start = operation.start_time
                operation_end = operation.end_time
                operation_duration = operation_end - operation_start
                operation_label = f"O{operation.operation_id}_J{operation.job_id}"
    
                # Set color based on job ID
                color_index = operation.job_id + 2
                if color_index >= colormap.N:
                    color_index = color_index % colormap.N
                color = colormap(color_index)
    
                ax.broken_barh(
                    [(operation_start, operation_duration)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=color,
                    edgecolor='black'
                )

                middle_of_operation = operation_start + operation_duration / 2
                ax.text(
                    middle_of_operation,
                    machine.machine_id,
                    operation_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
            set_up_time = machine.set_up_time
            tear_down_time = machine.tear_down_time
            for (start, stop) in zip(machine.start_times, machine.stop_times):
                start_label = "set up"
                stop_label = "tear down"
                ax.broken_barh(
                    [(start, set_up_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(0),
                    edgecolor='black'
                )
                ax.broken_barh(
                    [(stop, tear_down_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(1),
                    edgecolor='black'
                )
                ax.text(
                    start + set_up_time / 2.0,
                    machine.machine_id,
                    start_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
                ax.text(
                    stop + tear_down_time / 2.0,
                    machine.machine_id,
                    stop_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )          

        fig = ax.figure
        fig.set_size_inches(12, 6)
    
        ax.set_yticks(range(self._instance.nb_machines))
        ax.set_yticklabels([f'M{machine_id+1}' for machine_id in range(self.inst.nb_machines)])
        ax.set_xlabel('Time')
        ax.set_ylabel('Machine')
        ax.set_title('Gantt Chart')
        ax.grid(True)
    
        return plt
