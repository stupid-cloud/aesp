from pyxtal import pyxtal
import numpy as np
from aesp.operator.generator.base import RandomGenerator


class RandomGeneratorBulk(RandomGenerator):
    def __init__(self, composition, spgnum, factor, thickness, max_count, tol_matrix) -> None:
        super().__init__(composition, spgnum, factor, thickness, max_count, tol_matrix)
        self.dim = 3
        self.operator = 'random_gen'


class RandomGeneratorCluster(RandomGenerator):
    def __init__(self, composition, spgnum, factor, thickness, max_count, tol_matrix) -> None:
        super().__init__(composition, spgnum, factor, thickness, max_count, tol_matrix)
        self.dim = 0
        self.operator = 'random_gen'
