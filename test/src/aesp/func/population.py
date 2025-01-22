from math import tanh, sqrt, exp
from operator import itemgetter
import numpy as np
from aesp.func.database import DataConnection
from ase.db.core import now
import itertools
import math

def get_raw_score(atoms):
    """Gets the raw_score of the supplied atoms object.

    Parameters
    ----------
    atoms : Atoms object
        The atoms object from which the raw_score will be returned.

    Returns
    -------
    raw_score : float or int
        The raw_score set previously.
    """
    return atoms.info["key_value_pairs"]['fitness']

def count_looks_like(a, all_cand, comp):
    """Utility method for counting occurrences."""
    n = 0
    for b in all_cand:
        if a.info['s_id'] == b.info['s_id']:
            continue
        if comp.looks_like(a, b):
            n += 1
    return n


class Population:
    """Population class which maintains the current population
    and proposes which candidates to pair together.

    Parameters:

    data_connection: DataConnection object
        Bla bla bla.

    population_size: int
        The number of candidates in the population.

    comparator: Comparator object
        this will tell if two configurations are equal.
        Default compare atoms objects directly.

    logfile: str
        Text file that contains information about the population
        The format is::

            timestamp: generation(if available): id1,id2,id3...

        Using this file greatly speeds up convergence checks.
        Default None meaning that no file is written.

    use_extinct: boolean
        Set this to True if mass extinction and the extinct key
        are going to be used. Default is False.

    rng: Random number generator
        By default numpy.random.
    """
    def __init__(self, pop_list): 
        self.pop = pop_list

    def get_diversity(self, comp):
        """种群的多样性"""
        total_diff = 0
        num = 0
        for a, b in itertools.combinations(self.pop, 2):
            total_diff += comp.difference(a, b)
            num += 1
        total_diff /= num
        return total_diff
            

    def __calc_participation__(self):
        """ Determines, from the database, how many times each
            candidate has been used to generate new candidates. """
        (participation, pairs) = self.dc.get_participation_in_pairing()

        for a in self.pop:
            if a.info['key_value_pairs']['s_id'] in participation.keys():
                a.info['n_paired'] = participation[a.info['key_value_pairs']['s_id']]
            else:
                a.info['n_paired'] = 0
        self.pairs = pairs


    def __get_fitness__(self, min_best=True):
        """Calculates the fitness using the formula from
            L.B. Vilhelmsen et al., JACS, 2012, 134 (30), pp 12807-12816

        Sign change on the fitness compared to the formulation in the
        abovementioned paper due to maximizing raw_score instead of
        minimizing energy. (Set raw_score=-energy to optimize the energy)
        """

        scores = [get_raw_score(x) for x in self.pop]
        f_min = min(scores)
        f_max = max(scores)
        T = f_max - f_min
        #除0异常处理
        if math.isclose(T, 0, abs_tol = 1e-5):
            return [1 for _ in scores]
        if min_best:
            f = [(f_max-f_i)/T for f_i in scores] # 越小越好
        else:
            f = [(f_i-f_min)/T for f_i in scores]
        return f

    def get_candidates(self, size=1):
        """ Returns two candidates for pairing employing the
            fitness criteria from
            L.B. Vilhelmsen et al., JACS, 2012, 134 (30), pp 12807-12816
            and the roulete wheel selection scheme described in
            R.L. Johnston Dalton Transactions,
            Vol. 22, No. 22. (2003), pp. 4193-4207
        """

        if len(self.pop) < 2:
            raise ValueError('population太少')

        fit = self.__get_fitness__()
        p = [i/sum(fit) for i in fit]
        
        idx_list = np.random.choice(range(len(fit)), size=size, p=p) # 不放回抽样
        atom_list = [self.pop[i].copy() for i in idx_list]
   
        # c1, c2 = 
        return atom_list
