'''
Script de comparaison des heuristiques de recherche locale.

Compare sur plusieurs instances :
  1. Greedy       (déterministe, 1 exécution)
  2. FirstNeighborLocalSearch (non-déterministe, N_RUNS exécutions, meilleure retenue)
  3. BestNeighborLocalSearch  (non-déterministe, N_RUNS exécutions, meilleure retenue)

Métriques : temps de calcul (s), valeur objectif, Cmax, énergie totale, faisabilité.

Usage :
    python -m src.scheduling.optim.compare
'''
import os
import time

from src.scheduling.instance.instance import Instance
from src.scheduling.optim.constructive import Greedy, NonDeterminist
from src.scheduling.optim.local_search import FirstNeighborLocalSearch, BestNeighborLocalSearch
from src.scheduling.optim.neighborhoods import SwapOnMachine, MachineReassign

# -------------------------------------------------------------------------
# Paramètres de la comparaison
# -------------------------------------------------------------------------
DATA_DIR  = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
# Instances utilisées pour la comparaison (choisies pour leur variété de taille)
INSTANCES = ['jsp2', 'jsp10', 'jsp25']
N_RUNS    = 10      # Nombre d'exécutions pour les méthodes stochastiques


def _capturer_metriques(solution, duree_execution):
    return {
        'objectif':  solution.objective,
        'cmax':      solution.cmax,
        'energie':   solution.total_energy_consumption,
        'faisable':  solution.is_feasible,
        'duree':     duree_execution,
    }


def _executer_une_fois(heuristique, instance, **kwargs_execution):
    instant_debut = time.perf_counter()
    solution = heuristique.run(instance, **kwargs_execution)
    duree_execution = time.perf_counter() - instant_debut
    return _capturer_metriques(solution, duree_execution)


def _meilleur_sur_n_executions(classe_heuristique, instance, nombre_executions, kwargs_execution):
    metriques_meilleur = None
    duree_totale = 0.0
    heuristique = classe_heuristique()
    for _ in range(nombre_executions):
        metriques = _executer_une_fois(heuristique, instance, **kwargs_execution)
        duree_totale += metriques['duree']
        if metriques_meilleur is None or metriques['objectif'] < metriques_meilleur['objectif']:
            metriques_meilleur = metriques
    metriques_meilleur['duree'] = duree_totale
    return metriques_meilleur


def compare(instances_names=None, n_runs=N_RUNS, data_dir=DATA_DIR):
    '''
    Exécute la comparaison et affiche un tableau de résultats.
    @param instances_names: liste de noms d'instances (sous-répertoires de data/)
    @param n_runs: nombre d'exécutions pour les méthodes stochastiques
    @param data_dir: chemin vers le répertoire de données
    '''
    if instances_names is None:
        instances_names = INSTANCES

    header = (f"{'Instance':<12} {'Méthode':<30} {'Obj':>10} "
              f"{'Cmax':>7} {'Energie':>10} {'Faisable':>9} {'Temps(s)':>10}")
    print(header)
    print('-' * len(header))

    for nom_instance in instances_names:
        chemin_instance = os.path.join(data_dir, nom_instance)
        instance = Instance.from_file(chemin_instance)

        # ---- 1. Greedy déterministe (1 exécution) ----
        metriques_greedy = _executer_une_fois(Greedy(), instance)
        _afficher_ligne(nom_instance, 'Greedy', metriques_greedy)

        # ---- 2. FirstNeighborLocalSearch (N_RUNS exécutions) ----
        metriques_premier_voisin = _meilleur_sur_n_executions(
            FirstNeighborLocalSearch, instance, n_runs,
            {'NeighborClass': SwapOnMachine}
        )
        _afficher_ligne(nom_instance, f'FirstNeighbor×{n_runs}', metriques_premier_voisin)

        # ---- 3. BestNeighborLocalSearch (N_RUNS exécutions) ----
        metriques_meilleur_voisin = _meilleur_sur_n_executions(
            BestNeighborLocalSearch, instance, n_runs,
            {'NeighborClasses': [SwapOnMachine, MachineReassign]}
        )
        _afficher_ligne(nom_instance, f'BestNeighbor×{n_runs}', metriques_meilleur_voisin)

        print()  # ligne vide entre instances


def _afficher_ligne(nom_instance, methode, metriques):
    faisable = 'oui' if metriques['faisable'] else 'non'
    print(f"{nom_instance:<12} {methode:<30} {metriques['objectif']:>10.2f} "
          f"{metriques['cmax']:>7} {metriques['energie']:>10.2f} "
          f"{faisable:>9} {metriques['duree']:>10.3f}")


if __name__ == '__main__':
    compare()
