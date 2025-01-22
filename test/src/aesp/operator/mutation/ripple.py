from aesp.operator.mutation.base import Mutation
import copy
import numpy as np

# bulk
class RippleMutationBulk(Mutation):
   
    def __init__(self, max_count, rho, miu, eta):
        super().__init__(max_count)
        self.operator = 'ripple_mut'
        self.rho = rho
        self.miu = miu
        self.eta = eta

    def mutate(self, mutant):
        """Does the actual mutation."""
        pos_ref = mutant.get_scaled_positions()
        pos_new = copy.deepcopy(pos_ref)
        indx_list= [0, 1, 2]
        np.random.shuffle(indx_list)
        pos_new[:, indx_list[2]] += self._displacement(pos_ref[:, indx_list[0]], pos_ref[:, indx_list[1]])
        mutant.set_scaled_positions(pos_new)
        return mutant

    def _displacement(self, x, y):
        theta_x, theta_y = np.random.uniform(0, 2, size=2)*np.pi
        delta_d = self.rho*np.cos(2*np.pi*self.miu*x+theta_x)*np.cos(2*np.pi*self.eta*y+theta_y)
        return delta_d

# cluster
class RippleMutationCluster(Mutation):
   
    def __init__(self, max_count, rho, miu, eta):
        super().__init__(max_count)
        self.operator = 'ripple_mut'
        self.rho = rho
        self.miu = miu
        self.eta = eta

    def mutate(self, mutant):
        """Does the actual mutation."""
        pos_ref = mutant.get_positions()
        pos_new = copy.deepcopy(pos_ref)
        indx_list= [0, 1, 2]
        np.random.shuffle(indx_list)
        pos_new[:, indx_list[2]] += self._displacement(pos_ref[:, indx_list[0]], pos_ref[:, indx_list[1]])
        mutant.set_scaled_positions(pos_new)
        return mutant

    def _displacement(self, x, y):
        theta_x, theta_y = np.random.uniform(0, 2, size=2)*np.pi
        delta_d = self.rho*np.cos(2*np.pi*self.miu*x+theta_x)*np.cos(2*np.pi*self.eta*y+theta_y)
        return delta_d

# layer
class RippleMutationLayer(Mutation):
   
    def __init__(self, max_count, rho, miu, eta):
        super().__init__(max_count)
        self.operator = 'ripple_mut'
        self.rho = rho
        self.miu = miu
        self.eta = eta

    def mutate(self, mutant):
        """Does the actual mutation."""
     
        pos_ref = mutant.get_scaled_positions()
        pos_new = copy.deepcopy(pos_ref)
        indx_list= [0, 1]
        np.random.shuffle(indx_list)
        pos_new[:, indx_list[1]] += self._displacement(pos_ref[:, indx_list[0]])
        mutant.set_scaled_positions(pos_new)
        mutant.wrap()
        return mutant

    def _displacement(self, x):
        theta_x = np.random.uniform(0, 2)*np.pi
        delta_d = self.rho*np.cos(2*np.pi*self.miu*x+theta_x)
        return delta_d