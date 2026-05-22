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


def _capture_metrics(sol, elapsed):
    '''Capture les métriques d'une solution IMMÉDIATEMENT (avant tout changement d'état).'''
    return {
        'obj':      sol.objective,
        'cmax':     sol.cmax,
        'energy':   sol.total_energy_consumption,
        'feasible': sol.is_feasible,
        'time':     elapsed,
    }


def _run_once(heuristic, instance, **run_kwargs):
    '''Exécute une heuristique et retourne les métriques capturées immédiatement.'''
    t0 = time.perf_counter()
    sol = heuristic.run(instance, **run_kwargs)
    elapsed = time.perf_counter() - t0
    return _capture_metrics(sol, elapsed)


def _best_of_n(heuristic_cls, instance, n, run_kwargs):
    '''
    Lance n exécutions d'une heuristique et retourne les métriques
    du meilleur run (objectif minimum), avec le temps total cumulé.
    '''
    best_metrics = None
    total_time = 0.0
    h = heuristic_cls()
    for _ in range(n):
        metrics = _run_once(h, instance, **run_kwargs)
        total_time += metrics['time']
        if best_metrics is None or metrics['obj'] < best_metrics['obj']:
            best_metrics = metrics
    best_metrics['time'] = total_time   # Remplacer par le temps total
    return best_metrics


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

    for inst_name in instances_names:
        inst_path = os.path.join(data_dir, inst_name)
        instance = Instance.from_file(inst_path)

        # ---- 1. Greedy déterministe (1 exécution) ----
        m_g = _run_once(Greedy(), instance)
        _print_row(inst_name, 'Greedy', m_g)

        # ---- 2. FirstNeighborLocalSearch (N_RUNS exécutions) ----
        m_fn = _best_of_n(
            FirstNeighborLocalSearch, instance, n_runs,
            {'NeighborClass': SwapOnMachine}
        )
        _print_row(inst_name, f'FirstNeighbor×{n_runs}', m_fn)

        # ---- 3. BestNeighborLocalSearch (N_RUNS exécutions) ----
        m_bn = _best_of_n(
            BestNeighborLocalSearch, instance, n_runs,
            {'NeighborClasses': [SwapOnMachine, MachineReassign]}
        )
        _print_row(inst_name, f'BestNeighbor×{n_runs}', m_bn)

        print()  # ligne vide entre instances


def _print_row(inst_name, method, m):
    feasible = 'oui' if m['feasible'] else 'non'
    print(f"{inst_name:<12} {method:<30} {m['obj']:>10.2f} "
          f"{m['cmax']:>7} {m['energy']:>10.2f} "
          f"{feasible:>9} {m['time']:>10.3f}")


if __name__ == '__main__':
    compare()
