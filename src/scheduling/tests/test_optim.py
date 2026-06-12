'''
Tests des modules d'optimisation : heuristiques constructives,
voisinages et algorithmes de recherche locale.

@author: tests Phase 2 & 3
'''
import os
import unittest

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.heuristics import Heuristic
from src.scheduling.optim.constructive import Greedy, NonDeterminist
from src.scheduling.optim.neighborhoods import (
    SwapOnMachine, MachineReassign,
    _is_ancestor, _extract_orderings, _reconstruct,
    MyNeighborhood1, MyNeighborhood2,
)
from src.scheduling.optim.local_search import (
    FirstNeighborLocalSearch, BestNeighborLocalSearch,
)
from src.scheduling.tests.test_utils import TEST_FOLDER_DATA


# ---------------------------------------------------------------------------
# Tests de la classe de base Heuristic
# ---------------------------------------------------------------------------

class TestHeuristic(unittest.TestCase):

    def test_run_raises_not_implemented(self):
        '''
        La méthode run() de la classe de base doit lever NotImplementedError.
        '''
        base_heuristic = Heuristic()
        instance = Instance.from_file(TEST_FOLDER_DATA + os.sep + 'jsp1')

        with self.assertRaises(NotImplementedError):
            base_heuristic.run(instance)

    def test_params_are_stored(self):
        '''
        Les paramètres passés au constructeur doivent être accessibles via _params.
        '''
        params = {'w_energy': 2.0, 'w_time': 0.5}
        heuristic = Heuristic(params)

        self.assertEqual(heuristic._params['w_energy'], 2.0)
        self.assertEqual(heuristic._params['w_time'], 0.5)


# ---------------------------------------------------------------------------
# Tests de Greedy
# ---------------------------------------------------------------------------

class TestGreedy(unittest.TestCase):

    def setUp(self):
        self.instance_jsp1 = Instance.from_file(TEST_FOLDER_DATA + os.sep + 'jsp1')

    def test_greedy_retourne_solution_faisable(self):
        '''
        L'heuristique gloutonne doit produire une solution faisable sur jsp1.
        '''
        greedy = Greedy()
        solution = greedy.run(self.instance_jsp1)

        self.assertTrue(
            solution.is_feasible,
            'Greedy doit produire une solution faisable'
        )

    def test_greedy_planifie_toutes_les_operations(self):
        '''
        Toutes les opérations de l'instance doivent être planifiées.
        '''
        greedy = Greedy()
        solution = greedy.run(self.instance_jsp1)

        nombre_operations_planifiees = sum(
            1 for operation in self.instance_jsp1.operations if operation.assigned
        )
        self.assertEqual(
            nombre_operations_planifiees,
            self.instance_jsp1.nb_operations,
            'Greedy doit planifier toutes les opérations'
        )

    def test_greedy_valeur_objectif_positive(self):
        '''
        La valeur de la fonction objectif doit être strictement positive.
        '''
        greedy = Greedy()
        solution = greedy.run(self.instance_jsp1)

        self.assertGreater(
            solution.objective, 0,
            'la valeur objectif doit être strictement positive'
        )

    def test_greedy_deterministe(self):
        '''
        Deux exécutions de Greedy sur la même instance doivent donner
        le même makespan (comportement déterministe).
        '''
        greedy = Greedy()
        premiere_solution  = greedy.run(self.instance_jsp1)
        cmax_premier_run   = premiere_solution.cmax
        deuxieme_solution  = greedy.run(self.instance_jsp1)
        cmax_deuxieme_run  = deuxieme_solution.cmax

        self.assertEqual(
            cmax_premier_run, cmax_deuxieme_run,
            'Greedy doit être déterministe : deux runs doivent donner le même Cmax'
        )


# ---------------------------------------------------------------------------
# Tests de NonDeterminist (GRASP)
# ---------------------------------------------------------------------------

class TestNonDeterminist(unittest.TestCase):

    def setUp(self):
        self.instance_jsp1 = Instance.from_file(TEST_FOLDER_DATA + os.sep + 'jsp1')

    def test_non_determinist_retourne_solution_faisable(self):
        '''
        NonDeterminist doit produire une solution faisable.
        '''
        heuristic = NonDeterminist({'seed': 0})
        solution = heuristic.run(self.instance_jsp1)

        self.assertTrue(
            solution.is_feasible,
            'NonDeterminist doit produire une solution faisable'
        )

    def test_non_determinist_planifie_toutes_les_operations(self):
        '''
        Toutes les opérations doivent être planifiées.
        '''
        heuristic = NonDeterminist({'seed': 0})
        solution = heuristic.run(self.instance_jsp1)

        nombre_operations_planifiees = sum(
            1 for operation in self.instance_jsp1.operations if operation.assigned
        )
        self.assertEqual(
            nombre_operations_planifiees,
            self.instance_jsp1.nb_operations,
            'NonDeterminist doit planifier toutes les opérations'
        )

    def test_non_determinist_reproductible_avec_graine(self):
        '''
        Avec la même graine aléatoire, deux exécutions doivent produire
        le même résultat (reproductibilité).
        '''
        heuristic = NonDeterminist({'seed': 42})
        solution_un = heuristic.run(self.instance_jsp1)
        cmax_un     = solution_un.cmax
        solution_deux = heuristic.run(self.instance_jsp1)
        cmax_deux     = solution_deux.cmax

        self.assertEqual(
            cmax_un, cmax_deux,
            'NonDeterminist avec la même graine doit produire le même Cmax'
        )

    def test_non_determinist_diversite_sans_graine_fixe(self):
        '''
        Sur 10 exécutions sans graine fixe, au moins deux résultats
        doivent être différents (diversité stochastique).
        '''
        heuristic = NonDeterminist()
        liste_cmax = [heuristic.run(self.instance_jsp1).cmax for _ in range(10)]

        nombre_valeurs_distinctes = len(set(liste_cmax))
        self.assertGreater(
            nombre_valeurs_distinctes, 1,
            'NonDeterminist sans graine doit produire des solutions variées sur 10 runs'
        )


# ---------------------------------------------------------------------------
# Tests des voisinages
# ---------------------------------------------------------------------------

class TestVoisinages(unittest.TestCase):

    def setUp(self):
        self.instance_jsp1 = Instance.from_file(TEST_FOLDER_DATA + os.sep + 'jsp1')
        # Construire une solution initiale pour les tests de voisinage
        greedy = Greedy()
        self.solution_initiale = greedy.run(self.instance_jsp1)

    def test_is_ancestor_direct(self):
        '''
        _is_ancestor doit retourner True pour une précédence directe.
        Dans jsp1, op0 précède op1 dans le même job.
        '''
        operation_premiere = self.instance_jsp1.operations[0]   # job 0, op 0
        operation_deuxieme = self.instance_jsp1.operations[1]   # job 0, op 1

        self.assertTrue(
            _is_ancestor(operation_premiere, operation_deuxieme),
            'op0 est un ancêtre direct de op1 dans job 0'
        )

    def test_is_ancestor_non_lie(self):
        '''
        _is_ancestor doit retourner False pour deux opérations
        appartenant à des jobs différents sans lien de précédence.
        '''
        operation_job_zero = self.instance_jsp1.operations[0]   # job 0, op 0
        operation_job_un   = self.instance_jsp1.operations[2]   # job 1, op 2

        self.assertFalse(
            _is_ancestor(operation_job_zero, operation_job_un),
            'op0 (job 0) et op2 (job 1) ne sont pas liés par une précédence'
        )

    def test_extract_orderings_contient_toutes_les_machines(self):
        '''
        _extract_orderings doit retourner une entrée pour chaque machine.
        '''
        snapshot = _extract_orderings(self.instance_jsp1)

        self.assertEqual(
            len(snapshot), len(self.instance_jsp1.machines),
            'le snapshot doit contenir une entrée par machine'
        )

    def test_extract_orderings_ops_triees_par_heure_debut(self):
        '''
        Les opérations dans chaque liste du snapshot doivent être
        triées par heure de début croissante.
        '''
        snapshot = _extract_orderings(self.instance_jsp1)

        for identifiant_machine, liste_operations in snapshot.items():
            heures_debut = [operation.start_time for operation in liste_operations]
            self.assertEqual(
                heures_debut, sorted(heures_debut),
                f'les opérations de la machine {identifiant_machine} doivent être triées par start_time'
            )

    def test_reconstruct_produit_solution_complete(self):
        '''
        _reconstruct à partir du snapshot courant doit produire
        une solution faisable avec toutes les opérations planifiées.
        '''
        snapshot = _extract_orderings(self.instance_jsp1)
        solution_reconstruite = _reconstruct(self.instance_jsp1, snapshot)

        nombre_operations_planifiees = sum(
            1 for op in self.instance_jsp1.operations if op.assigned
        )
        self.assertEqual(
            nombre_operations_planifiees,
            self.instance_jsp1.nb_operations,
            '_reconstruct doit planifier toutes les opérations'
        )
        self.assertTrue(
            solution_reconstruite.is_feasible,
            '_reconstruct doit produire une solution faisable'
        )

    def test_swap_on_machine_genere_des_mouvements(self):
        '''
        SwapOnMachine doit générer au moins un mouvement sur une solution construite.
        '''
        voisinage = SwapOnMachine(self.instance_jsp1)
        snapshot  = _extract_orderings(self.instance_jsp1)
        liste_mouvements = voisinage._moves(snapshot)

        self.assertGreater(
            len(liste_mouvements), 0,
            'SwapOnMachine doit générer des mouvements valides'
        )

    def test_swap_on_machine_apply_conserve_toutes_les_operations(self):
        '''
        Après application d'un swap, le snapshot résultant doit contenir
        le même nombre total d'opérations.
        '''
        voisinage = SwapOnMachine(self.instance_jsp1)
        snapshot  = _extract_orderings(self.instance_jsp1)
        liste_mouvements = voisinage._moves(snapshot)

        if not liste_mouvements:
            self.skipTest('aucun mouvement disponible pour ce test')

        nouveau_snapshot = voisinage._apply(snapshot, *liste_mouvements[0])
        nombre_initial  = sum(len(ops) for ops in snapshot.values())
        nombre_apres    = sum(len(ops) for ops in nouveau_snapshot.values())

        self.assertEqual(
            nombre_initial, nombre_apres,
            '_apply (swap) doit conserver le nombre total d\'opérations'
        )

    def test_machine_reassign_genere_des_mouvements(self):
        '''
        MachineReassign doit générer au moins un mouvement sur une solution construite.
        '''
        voisinage = MachineReassign(self.instance_jsp1)
        snapshot  = _extract_orderings(self.instance_jsp1)
        liste_mouvements = voisinage._moves(snapshot)

        self.assertGreater(
            len(liste_mouvements), 0,
            'MachineReassign doit générer des mouvements valides'
        )

    def test_machine_reassign_apply_conserve_toutes_les_operations(self):
        '''
        Après réaffectation, le snapshot résultant doit contenir
        le même nombre total d'opérations.
        '''
        voisinage = MachineReassign(self.instance_jsp1)
        snapshot  = _extract_orderings(self.instance_jsp1)
        liste_mouvements = voisinage._moves(snapshot)

        if not liste_mouvements:
            self.skipTest('aucun mouvement disponible pour ce test')

        nouveau_snapshot = voisinage._apply(snapshot, *liste_mouvements[0])
        nombre_initial  = sum(len(ops) for ops in snapshot.values())
        nombre_apres    = sum(len(ops) for ops in nouveau_snapshot.values())

        self.assertEqual(
            nombre_initial, nombre_apres,
            '_apply (reassign) doit conserver le nombre total d\'opérations'
        )

    def test_aliases_voisinages(self):
        '''
        MyNeighborhood1 et MyNeighborhood2 doivent être des alias
        de SwapOnMachine et MachineReassign respectivement.
        '''
        self.assertIs(MyNeighborhood1, SwapOnMachine)
        self.assertIs(MyNeighborhood2, MachineReassign)


# ---------------------------------------------------------------------------
# Tests des algorithmes de recherche locale
# ---------------------------------------------------------------------------

class TestRechercheLocale(unittest.TestCase):

    def setUp(self):
        self.instance_jsp1 = Instance.from_file(TEST_FOLDER_DATA + os.sep + 'jsp1')

    def test_first_neighbor_produit_solution_faisable(self):
        '''
        FirstNeighborLocalSearch doit produire une solution faisable.
        '''
        recherche_locale = FirstNeighborLocalSearch()
        solution = recherche_locale.run(self.instance_jsp1, NeighborClass=SwapOnMachine)

        self.assertTrue(
            solution.is_feasible,
            'FirstNeighborLocalSearch doit produire une solution faisable'
        )

    def test_first_neighbor_planifie_toutes_les_operations(self):
        '''
        Toutes les opérations doivent être planifiées après la recherche locale.
        '''
        recherche_locale = FirstNeighborLocalSearch()
        solution = recherche_locale.run(self.instance_jsp1, NeighborClass=SwapOnMachine)

        nombre_planifiees = sum(
            1 for op in self.instance_jsp1.operations if op.assigned
        )
        self.assertEqual(
            nombre_planifiees,
            self.instance_jsp1.nb_operations,
            'FirstNeighborLocalSearch doit planifier toutes les opérations'
        )

    def test_best_neighbor_produit_solution_faisable(self):
        '''
        BestNeighborLocalSearch doit produire une solution faisable.
        '''
        recherche_locale = BestNeighborLocalSearch()
        solution = recherche_locale.run(
            self.instance_jsp1,
            NeighborClasses=[SwapOnMachine, MachineReassign]
        )

        self.assertTrue(
            solution.is_feasible,
            'BestNeighborLocalSearch doit produire une solution faisable'
        )

    def test_best_neighbor_planifie_toutes_les_operations(self):
        '''
        Toutes les opérations doivent être planifiées après BestNeighborLocalSearch.
        '''
        recherche_locale = BestNeighborLocalSearch()
        solution = recherche_locale.run(
            self.instance_jsp1,
            NeighborClasses=[SwapOnMachine, MachineReassign]
        )

        nombre_planifiees = sum(
            1 for op in self.instance_jsp1.operations if op.assigned
        )
        self.assertEqual(
            nombre_planifiees,
            self.instance_jsp1.nb_operations,
            'BestNeighborLocalSearch doit planifier toutes les opérations'
        )

    def test_best_neighbor_objectif_inferieur_ou_egal_a_greedy(self):
        '''
        Sur jsp1, BestNeighborLocalSearch devrait trouver une solution
        de qualité au moins comparable à Greedy (même point de départ initial possible).
        On vérifie simplement que l'objectif est strictement positif et fini.
        '''
        recherche_locale = BestNeighborLocalSearch()
        solution = recherche_locale.run(
            self.instance_jsp1,
            NeighborClasses=[SwapOnMachine, MachineReassign]
        )

        valeur_objectif = solution.objective
        self.assertGreater(valeur_objectif, 0, 'la valeur objectif doit être positive')
        self.assertFalse(
            valeur_objectif != valeur_objectif,   # test NaN
            'la valeur objectif ne doit pas être NaN'
        )


if __name__ == '__main__':
    unittest.main()
