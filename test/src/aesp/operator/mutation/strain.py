from aesp.operator.mutation.base import Mutation
import numpy as np
import copy

# strain
class StrainMutationBulk(Mutation):
    
    def __init__(self, max_count, stddev):
        super().__init__(max_count)
        self.stddev = stddev
        self.operator = 'strain_mut'

    def mutate(self, mutant):
        """ Does the actual mutation. """
        cell_ref = mutant.get_cell()

        e = np.random.normal(0, self.stddev, size=(6,))
            # 构造矩阵
        strain = np.array([
                            [1 + e[0], e[3] / 2, e[4] / 2],
                            [e[3] / 2, 1 + e[1], e[5] / 2],
                            [e[4] / 2, e[5] / 2, 1 + e[2]]
                            ])
        strain /= np.linalg.det(strain)**(1/3)
        cell_new = np.dot(strain, cell_ref)
        mutant.set_cell(cell_new, scale_atoms=True)

        return mutant


class StrainMutationLayer(Mutation):
    
    def __init__(self, max_count, stddev):
        super().__init__(max_count)
        self.stddev = stddev
        self.operator = 'strain_mut'

    def mutate(self, mutant):
        """ Does the actual mutation. """
        cell_ref = mutant.get_cell()
        pos_ref = mutant.get_scaled_positions()
        cell_new = mutant.get_cell()
        e = np.random.normal(0.5, self.stddev, size=(3,))
        # 构造矩阵
        strain = np.array([
                    [1 + e[0], e[2] / 2],
                    [e[2] / 2, 1 + e[1]]
                    ])

        strain /= np.linalg.det(strain)**(1/2)
        cell_new[:2, :2] = np.dot(strain, cell_ref[:2, :2])
        mutant.set_cell(cell_new, scale_atoms=True)
        mutant.set_scaled_positions(pos_ref)
        return mutant