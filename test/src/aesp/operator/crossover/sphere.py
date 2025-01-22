from aesp.operator.crossover.base import Crossover
import numpy as np
import copy
from ase.atom import Atom

class SphereCrossoverBulk(Crossover):
    """crossover"""
    def __init__(
            self, 
            stddev, 
            max_count
            ):
        super().__init__(stddev, max_count)
        self.operator = 'sphere_cross'

    def _add_border(self, child):
        # 生成角度范围
        theta_num = int(2 * np.pi / self.theta_interval)
        phi_num = int(np.pi / self.phi_interval)
        theta = np.linspace(0, 2 * np.pi, theta_num)
        phi = np.linspace(0, np.pi, phi_num)

        # 生成球体的坐标网格
        theta, phi = np.meshgrid(theta, phi)
        x = self.cut_radius * np.sin(phi) * np.cos(theta)
        y = self.cut_radius * np.sin(phi) * np.sin(theta)
        z = self.cut_radius * np.cos(phi)
   
        for key, value in  self._natoms_diff.items():
            if value < 0:
                # 遍历网格
                for i in range(x.shape[0]):
                    for j in range(x.shape[1]):
                        coords = self.origin + np.array([float(x[i, j]), float(y[i, j]), float(z[i, j])])
                        child.append(Atom(key))
                       
                        child[-1].position = coords

                        if not child.check_distance()[0]:
                            child.pop()
                            continue
                        value += 1
                        self._natoms_diff[key] += 1
        return child
 
    @staticmethod
    def _get_center_index(child):
        for idx, i in enumerate(child):
            if i.tag == 1:
                return idx
            
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 
        child = child.copy()
        center_idx = self._get_center_index(child)
        if center_idx is None:
            center_idx = len(child)
            child.append(Atom(position=self.origin))

        dis = child.get_distances([i for i in range(len(child)) if i!=center_idx], center_idx, mic=True)
        dis = np.abs(dis-self.cut_radius)[:-1]
        sorted_indices = np.argsort(dis)
        return sorted_indices

    def _atom_crossover(self, a1, a2):
        a1 = a1.copy()
        a2 = a2.copy()
        # 随机旋转
        # a1.random_rotation()
        # a1.random_rotation()
   
        # random choose replace center
        center_i, center_j = np.random.randint(len(a1)), np.random.randint(len(a2))
        a1[center_i].tag = 1
        a2[center_j].tag = 1
        # 平移使得父类结构所选中心重合
        a2.positions += a1.positions[center_i] - a2.positions[center_j]
        a1.wrap()
        a2.wrap()
        
        dis1 = a1.get_distances(range(len(a1)), center_i, mic=True)
        mean1 = np.sum(dis1)/(len(a1)-1)
        dis2 = a2.get_distances(range(len(a2)), center_j, mic=True)
        mean2 = np.sum(dis2)/(len(a2)-1)
        self.cut_radius = np.random.normal(loc=min(mean1, mean2), scale=self.stddev)
   
        atoms_A = a1[dis1 > self.cut_radius] + a2[dis2 < self.cut_radius]
        atoms_B = a2[dis2 > self.cut_radius] + a1[dis1 < self.cut_radius]

        # ---------- use a structure with more atoms
        if len(atoms_A) > len(atoms_B):
            atoms = atoms_A
        else:
            atoms = atoms_B 
        atoms.wrap()
        # 获取origin
        for i in atoms:
            if i.tag == 1:
                self.origin = i.position

        return atoms


class SphereCrossoverCluster(Crossover):
    """crossover"""
    def __init__(
            self, 
            stddev, 
            max_count
            ):
        super().__init__(stddev, max_count)
        self.operator = 'sphere_cross'
            
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 

        dis = np.linalg.norm(child.get_positions(), axis=1)
        dis = np.abs(dis-self.cut_radius)
        sorted_indices = np.argsort(-dis)
        return sorted_indices

    def _atom_crossover(self, a1, a2):
        a1 = a1.copy()
        a2 = a2.copy()
        # 随机旋转
        a1.random_rotation()
        a1.random_rotation()
   
        # 中心平移到0
        a1.reset_positions()
        a2.reset_positions()

        dis1 = np.linalg.norm(a1.get_positions(), axis=1)
        mean1 = np.sum(dis1)/len(a1)
        dis2 = np.linalg.norm(a2.get_positions(), axis=1)
        mean2 = np.sum(dis2)/len(a2)
        self.cut_radius = np.random.normal(loc=min(mean1, mean2), scale=self.stddev)
        atoms_A = a1[dis1 > self.cut_radius] + a2[dis2 < self.cut_radius]
        atoms_B = a2[dis2 > self.cut_radius] + a1[dis1 < self.cut_radius]
        # ---------- use a structure with more atoms
        if len(atoms_A) > len(atoms_B):
            atoms = atoms_A
        else:
            atoms = atoms_B 
        return atoms