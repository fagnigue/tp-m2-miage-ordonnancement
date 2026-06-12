'''
Tests for the Machine class

@author: Vassilissa Lehoux
'''
import os
import unittest

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.tests.test_utils import TEST_FOLDER_DATA


class TestMachine(unittest.TestCase):

    def setUp(self):
        self.instance = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + 'jsp1')

    def tearDown(self):
        pass

    def testWorkingTime(self):
        '''
        Vérifie que working_time est nul avant toute opération, puis égal à
        (stop_time - start_time) après planification de la première opération.
        Pour machine 1 (set_up_time=20, end_time=120) avec op0 débutant à t=0 :
          - démarrage machine à t=0, opération disponible à t=20
          - arrêt par défaut à end_time=120
          - working_time = 120 - 0 = 120
        '''
        machine_one = self.instance.machines[1]

        # Avant toute planification, la machine n'est pas encore allumée
        self.assertEqual(
            machine_one.working_time, 0,
            'working_time doit être 0 avant la première opération'
        )

        # Planifier op0 (première opération de job 0) sur machine 1
        solution = Solution(self.instance)
        first_operation = self.instance.operations[0]
        solution.schedule(first_operation, machine_one)

        self.assertEqual(
            machine_one.working_time, 120,
            'après la première opération, working_time doit couvrir tout le cycle (0 → 120)'
        )

    def testTotalEnergyConsumption(self):
        '''
        Vérifie le calcul de la consommation totale d\'énergie de machine 1.
        Formule : e_demarrage_arret + e_operations + e_inactivite
          - e_demarrage_arret = 1 cycle × (set_up_energy + tear_down_energy) = 1 × (5 + 4) = 9
          - e_inactivite = min_consumption × temps_inactif / 60  (kW × min / 60 → kWh)

        Après planification de op0 (processing_time=12, energy=12) :
          - temps_actif  = set_up_time + processing_time = 20 + 12 = 32
          - temps_inactif = working_time - temps_actif = 120 - 32 = 88
          - e_inactivite = 2 × 88 / 60 = 176/60
          - total = 9 + 12 + 176/60

        Après ajout de op2 (processing_time=9, energy=10) :
          - temps_actif  = 20 + 12 + 9 = 41
          - temps_inactif = 120 - 41 = 79
          - e_inactivite = 2 × 79 / 60 = 158/60
          - total = 9 + 22 + 158/60
        '''
        solution = Solution(self.instance)
        machine_one = self.instance.machines[1]

        # --- Étape 1 : une seule opération sur machine 1 ---
        first_operation = self.instance.operations[0]   # job 0, op 0 : pt=12, energy=12
        solution.schedule(first_operation, machine_one)

        energie_attendue_apres_premiere_op = 9 + 12 + 2 * 88 / 60
        self.assertAlmostEqual(
            machine_one.total_energy_consumption,
            energie_attendue_apres_premiere_op,
            places=5,
            msg='consommation incorrecte après planification de la première opération'
        )

        # --- Étape 2 : deuxième opération sur machine 1 ---
        second_operation_sur_machine_one = self.instance.operations[2]  # job 1, op 2 : pt=9, energy=10
        solution.schedule(second_operation_sur_machine_one, machine_one)

        energie_attendue_apres_deux_operations = 9 + 22 + 2 * 79 / 60
        self.assertAlmostEqual(
            machine_one.total_energy_consumption,
            energie_attendue_apres_deux_operations,
            places=5,
            msg='consommation incorrecte après planification de deux opérations'
        )

    def testStop(self):
        '''
        Vérifie que stop() modifie l\'heure d\'arrêt de la machine correctement
        et que la représentation textuelle est conforme.
        '''
        solution = Solution(self.instance)
        machine_one = self.instance.machines[1]
        first_operation = self.instance.operations[0]   # fin à t=32
        solution.schedule(first_operation, machine_one)

        # Avant stop explicite, la machine s'arrête à end_time=120
        self.assertEqual(
            machine_one.stop_times[0], 120,
            'par défaut, la machine s\'arrête à end_time=120'
        )
        self.assertEqual(
            machine_one.working_time, 120,
            'working_time initial = 120 - 0 = 120'
        )

        # Arrêter la machine à t=50 (après la fin de l\'opération à t=32)
        machine_one.stop(50)
        self.assertEqual(
            machine_one.stop_times[0], 50,
            'stop_times doit être mis à jour à 50 après l\'appel à stop()'
        )
        self.assertEqual(
            machine_one.working_time, 50,
            'working_time doit être 50 - 0 = 50 après arrêt à t=50'
        )

        # Vérifier la représentation textuelle
        self.assertEqual(
            str(machine_one), 'M1',
            'la représentation textuelle d\'une machine doit être "M<id>"'
        )


if __name__ == '__main__':
    unittest.main()