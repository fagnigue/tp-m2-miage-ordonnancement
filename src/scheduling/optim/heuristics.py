'''
Classe mère pour toutes les heuristiques du TP.

@author: Vassilissa Lehoux
'''
from typing import Dict

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution


class Heuristic(object):
    '''
    Classe abstraite dont héritent toutes les heuristiques.
    Chaque sous-classe doit implémenter la méthode run().
    '''

    def __init__(self, params: Dict = dict()):
        '''
        Constructeur.
        @param params: paramètres de l'heuristique sous forme de dictionnaire.
                       Les sous-classes définissent leurs propres valeurs par défaut.
        '''
        self._params = dict(params)

    def run(self, instance: Instance, params: Dict = dict()) -> Solution:
        '''
        Calcule une solution pour l'instance donnée.
        @param instance: instance du problème à résoudre
        @param params: paramètres de l'exécution (optionnels)
        @return: une Solution (réalisable ou non)
        '''
        raise NotImplementedError("La méthode run() doit être implémentée dans la sous-classe.")
        
