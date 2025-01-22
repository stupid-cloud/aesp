# permutation
from aesp.operator.mutation.base import Mutation
import numpy as np
import copy

class PermutationMutation(Mutation):
    def __init__(self, max_count):
        super().__init__(max_count)
        self.operator  = 'permutation_mut'

    def mutate(self, mutant):
        """Does the actual mutation."""
        
        species = list(set(mutant.symbols))
        if len(species) == 1 or len(mutant) <=2:
            return None

        n = np.random.choice(range(1, int(len(mutant) / len(species))+1))  # 随机初始化交换次数

        for _ in range(n):
            # 交换两个原子的种类
            indx_each_type = []
            for specie in species:
                indx_each_type.append([i for i, atom in enumerate(mutant) if atom.symbol == specie])
            
            # ------ choose two atom type
            type_choice = np.random.choice(len(species), 2, replace=False)
            
            # ------ choose index
            indx_choice = []
            for tc in type_choice:
                indx_choice.append(np.random.choice(indx_each_type[tc]))
            
            # 交换坐标
            temp_position = copy.deepcopy(mutant.positions[indx_choice[0]])
            mutant.positions[indx_choice[0]] = mutant.positions[indx_choice[1]]
            mutant.positions[indx_choice[1]] = temp_position
        return mutant