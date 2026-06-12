'''
Tests for the Job class

@author: Vassilissa Lehoux
'''
import os
import unittest

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.tests.test_utils import TEST_FOLDER_DATA


class TestJob(unittest.TestCase):

    def setUp(self):
        self.instance = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + 'jsp1')

    def tearDown(self):
        pass

    def testCompletionTime(self):
        '''
        Vérifie que completion_time retourne -1 tant que la dernière opération
        du job n'est pas planifiée, puis retourne l'heure de fin de la dernière
        opération une fois celle-ci planifiée.
        '''
        solution = Solution(self.instance)
        first_job = self.instance.jobs[0]

        # Avant toute planification, aucune opération n'est assignée
        self.assertEqual(
            first_job.completion_time, -1,
            'completion_time doit être -1 quand aucune opération du job n\'est planifiée'
        )

        # Planifier uniquement la première opération du job (op0 sur machine 1)
        first_operation = self.instance.operations[0]
        machine_one = self.instance.machines[1]
        solution.schedule(first_operation, machine_one)

        # La dernière opération du job n'est pas encore assignée
        self.assertEqual(
            first_job.completion_time, -1,
            'completion_time doit être -1 tant que la dernière opération n\'est pas planifiée'
        )

        # Planifier la deuxième (et dernière) opération du job (op1 sur machine 0)
        second_operation = self.instance.operations[1]
        machine_zero = self.instance.machines[0]
        solution.schedule(second_operation, machine_zero)

        # Le job est entièrement planifié : completion_time == end_time de la dernière op
        self.assertEqual(
            first_job.completion_time, second_operation.end_time,
            'completion_time doit correspondre à l\'heure de fin de la dernière opération'
        )
        self.assertEqual(
            first_job.completion_time, 37,
            'pour jsp1 job 0, completion_time attendu = 37'
        )

    def testJobId(self):
        '''
        Vérifie que job_id retourne l'identifiant correct du job.
        '''
        first_job = self.instance.jobs[0]
        second_job = self.instance.jobs[1]

        self.assertEqual(first_job.job_id, 0, 'job_id du premier job doit être 0')
        self.assertEqual(second_job.job_id, 1, 'job_id du second job doit être 1')

    def testNextOperationAndPlanned(self):
        '''
        Vérifie que next_operation retourne les opérations dans l\'ordre,
        None quand le job est terminé, et que planned est cohérent.
        '''
        first_job = self.instance.jobs[0]
        first_operation  = self.instance.operations[0]
        second_operation = self.instance.operations[1]

        # État initial : next_operation est la première opération du job
        self.assertEqual(
            first_job.next_operation, first_operation,
            'next_operation doit retourner la première opération avant toute planification'
        )
        self.assertEqual(
            first_job.operation_nb, 2,
            'operation_nb doit être égal au nombre d\'opérations du job'
        )
        self.assertFalse(
            first_job.planned,
            'planned doit être False quand l\'index n\'a pas atteint la fin'
        )

        # Avancer l'index d'une position
        first_job.schedule_operation()
        self.assertEqual(
            first_job.next_operation, second_operation,
            'next_operation doit pointer sur la deuxième opération après un schedule_operation'
        )
        self.assertFalse(first_job.planned, 'planned doit rester False après une seule avance')

        # Avancer jusqu'à la fin du job
        first_job.schedule_operation()
        self.assertIsNone(
            first_job.next_operation,
            'next_operation doit retourner None quand toutes les opérations sont traitées'
        )
        self.assertTrue(
            first_job.planned,
            'planned doit être True quand l\'index a atteint la fin du job'
        )


if __name__ == '__main__':
    unittest.main()
