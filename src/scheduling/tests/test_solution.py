'''
Test of the Solution class.

@author: Vassilissa Lehoux
'''
import unittest
import os

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.tests.test_utils import TEST_FOLDER_DATA, TEST_FOLDER


class TestSolution(unittest.TestCase):

    def setUp(self):
        self.inst1 = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp1")

    def tearDown(self):
        pass

    def test_init_sol(self):
        sol = Solution(self.inst1)
        self.assertEqual(len(sol.all_operations), len(self.inst1.operations),
                         'Nb of operations should be the same between instance and solution')
        self.assertEqual(len(sol.available_operations), len(self.inst1.jobs),
                         'One operation per job should be available for scheduling')

    def test_schedule_op(self):
        sol = Solution(self.inst1)
        operation = self.inst1.operations[0]
        machine = self.inst1.machines[1]
        sol.schedule(operation, machine)
        self.assertEqual(operation.assigned, True, 'operation should be assigned')
        self.assertEqual(operation.assigned_to, 1, 'wrong machine machine')
        self.assertEqual(operation.processing_time, 12, 'wrong operation duration')
        self.assertEqual(operation.energy, 12, 'wrong operation energy cost')
        self.assertEqual(operation.start_time, 20, 'wrong set up time for machine')
        self.assertEqual(operation.end_time, 32, 'wrong operation end time')
        self.assertEqual(machine.available_time, 32, 'wrong available time')
        self.assertEqual(machine.working_time, 120, 'wrong working time for machine')
        operation = self.inst1.operations[2]
        sol.schedule(operation, machine)
        self.assertEqual(operation.assigned, True, 'operation should be assigned')
        self.assertEqual(operation.assigned_to, 1, 'wrong machine machine')
        self.assertEqual(operation.processing_time, 9, 'wrong operation duration')
        self.assertEqual(operation.energy, 10, 'wrong operation energy cost')
        self.assertEqual(operation.start_time, 32, 'wrong start time for operation')
        self.assertEqual(operation.end_time, 41, 'wrong operation end time')
        self.assertEqual(machine.available_time, 41, 'wrong available time')
        self.assertEqual(machine.working_time, 120, 'wrong working time for machine')
        operation = self.inst1.operations[1]
        machine = self.inst1.machines[0]
        sol.schedule(operation, machine)
        self.assertEqual(operation.assigned, True, 'operation should be assigned')
        self.assertEqual(operation.assigned_to, 0, 'wrong machine machine')
        self.assertEqual(operation.processing_time, 5, 'wrong operation duration')
        self.assertEqual(operation.energy, 6, 'wrong operation energy cost')
        self.assertEqual(operation.start_time, 32, 'wrong start time for operation')
        self.assertEqual(operation.end_time, 37, 'wrong operation end time')
        self.assertEqual(machine.available_time, 37, 'wrong available time')
        self.assertEqual(machine.working_time, 83, 'wrong working time for machine')
        self.assertEqual(machine.start_times[0], 17)
        self.assertEqual(machine.stop_times[0], 100)
        operation = self.inst1.operations[3]
        sol.schedule(operation, machine)
        self.assertEqual(operation.assigned, True, 'operation should be assigned')
        self.assertEqual(operation.assigned_to, 0, 'wrong machine machine')
        self.assertEqual(operation.processing_time, 10, 'wrong operation duration')
        self.assertEqual(operation.energy, 9, 'wrong operation energy cost')
        self.assertEqual(operation.start_time, 41, 'wrong start time for operation')
        self.assertEqual(operation.end_time, 51, 'wrong operation end time')
        self.assertEqual(machine.available_time, 51, 'wrong available time')
        self.assertEqual(machine.working_time, 83, 'wrong working time for machine')
        self.assertEqual(machine.start_times[0], 17)
        self.assertEqual(machine.stop_times[0], 100)
        self.assertTrue(sol.is_feasible, 'Solution should be feasible')
    def test_is_feasible_false_when_not_fully_scheduled(self):
        '''
        Vérifie que is_feasible retourne False quand toutes les opérations
        ne sont pas encore planifiées.
        '''
        solution = Solution(self.inst1)

        # Aucune opération planifiée
        self.assertFalse(
            solution.is_feasible,
            'is_feasible doit être False si aucune opération n\'est planifiée'
        )

        # Planifier seulement la première opération du premier job
        first_operation = self.inst1.operations[0]
        machine_one = self.inst1.machines[1]
        solution.schedule(first_operation, machine_one)

        self.assertFalse(
            solution.is_feasible,
            'is_feasible doit être False tant que toutes les opérations ne sont pas planifiées'
        )

    def test_objective_and_components(self):
        '''
        Vérifie les composantes de la fonction objectif sur un planning complet de jsp1.

        Planning :
          - op0 (job0) sur machine1 : début=20, fin=32 (set_up=20)
          - op2 (job1) sur machine1 : début=32, fin=41
          - op1 (job0) sur machine0 : début=32, fin=37 (set_up commence à t=17)
          - op3 (job1) sur machine0 : début=41, fin=51

        Valeurs attendues :
          - cmax        = max(37, 51) = 51
          - sum_ci      = 37 + 51 = 88
          - énergie m0  = (4+4) + (6+9) + 1*(83-30)/60  = 23 + 53/60
          - énergie m1  = (5+4) + (12+10) + 2*(120-41)/60 = 31 + 158/60
          - énergie totale = 54 + 211/60
          - objectif    = énergie_totale + cmax + sum_ci = 193 + 211/60
        '''
        solution = Solution(self.inst1)
        machine_zero = self.inst1.machines[0]
        machine_one  = self.inst1.machines[1]

        # Planifier les quatre opérations dans un ordre compatible avec les précédences
        solution.schedule(self.inst1.operations[0], machine_one)    # op0 job0
        solution.schedule(self.inst1.operations[2], machine_one)    # op2 job1
        solution.schedule(self.inst1.operations[1], machine_zero)   # op1 job0 (après op0)
        solution.schedule(self.inst1.operations[3], machine_zero)   # op3 job1 (après op2)

        self.assertTrue(solution.is_feasible, 'le planning doit être faisable')

        # Cmax : heure de fin du dernier job terminé
        self.assertEqual(solution.cmax, 51, 'cmax attendu = 51')

        # Somme des temps de complétion
        self.assertEqual(solution.sum_ci, 88, 'sum_ci attendu = 88')

        # Énergie totale
        energie_machine_zero = (4 + 4) + (6 + 9) + 1 * (83 - (15 + 5 + 10)) / 60
        energie_machine_one  = (5 + 4) + (12 + 10) + 2 * (120 - (20 + 12 + 9)) / 60
        energie_totale_attendue = energie_machine_zero + energie_machine_one
        self.assertAlmostEqual(
            solution.total_energy_consumption, energie_totale_attendue, places=5,
            msg='consommation totale d\'\u00e9nergie incorrecte'
        )

        # Valeur objectif = énergie + cmax + sum_ci
        valeur_objectif_attendue = energie_totale_attendue + 51 + 88
        self.assertAlmostEqual(
            solution.evaluate, valeur_objectif_attendue, places=5,
            msg='valeur objectif incorrecte'
        )

        # Vérifier que objective utilise bien la valeur mise en cache
        valeur_en_cache = solution.objective
        self.assertAlmostEqual(
            valeur_en_cache, valeur_objectif_attendue, places=5,
            msg='la valeur en cache de objective doit correspondre à evaluate'
        )

    def test_str_representation(self):
        '''
        Vérifie la représentation textuelle de la solution avant et après planification.
        '''
        solution = Solution(self.inst1)

        # Avant toute planification : seulement l'en-tête de l'instance
        representation_vide = str(solution)
        self.assertIn('jsp1', representation_vide,
                      'la représentation doit contenir le nom de l\'instance')

        # Après planification d'une opération
        first_operation = self.inst1.operations[0]
        machine_one = self.inst1.machines[1]
        solution.schedule(first_operation, machine_one)

        representation_avec_op = str(solution)
        self.assertIn('Op0', representation_avec_op,
                      'la représentation doit mentionner Op0 après sa planification')
        self.assertIn('M1', representation_avec_op,
                      'la représentation doit mentionner la machine M1')
        self.assertIn('[20, 32]', representation_avec_op,
                      'la représentation doit indiquer la fenêtre temporelle [20, 32]')

    def test_gantt(self):
        '''
        Vérifie que la méthode gantt génère un diagramme de Gantt sans erreur
        à partir d'un planning complet de jsp1.
        '''
        solution = Solution(self.inst1)
        machine_zero = self.inst1.machines[0]
        machine_one  = self.inst1.machines[1]

        # Planifier les quatre opérations dans un ordre compatible avec les précédences
        solution.schedule(self.inst1.operations[0], machine_one)   # op0 job0
        solution.schedule(self.inst1.operations[2], machine_one)   # op2 job1
        solution.schedule(self.inst1.operations[1], machine_zero)  # op1 job0 (après op0)
        solution.schedule(self.inst1.operations[3], machine_zero)  # op3 job1 (après op2)

        self.assertTrue(solution.is_feasible,
                        'le planning doit être faisable avant de générer le Gantt')

        # La méthode gantt doit retourner un objet figure matplotlib sans lever d'exception
        gantt_figure = solution.gantt('tab20')
        self.assertIsNotNone(gantt_figure,
                             'gantt() doit retourner un objet figure non nul')

        # Sauvegarder pour vérification visuelle
        gantt_figure.savefig(TEST_FOLDER + os.path.sep + 'temp.png')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
