from aesp.operator.crossover.base import Crossover
import numpy as np
import copy
from ase.atom import Atom


class CylinderCrossoverBulk(Crossover):
    """crossover"""
    def __init__(
            self, 
            stddev, 
            max_count
            ):
        super().__init__(stddev, max_count)
        self.operator = 'cylinder_cross'
    
    def _add_border(self, child):

        # 生成角度范围
        z_length = child.cell[2, 2]
        z_num = int(z_length / self.z_interval)
        z_list = np.linspace(0, z_length, z_num)
        theta_num = int(2 * np.pi / self.theta_interval)
        theta_list = np.linspace(0, 2 * np.pi, theta_num)

        for key, value in  self._natoms_diff.items():
            if value < 0:
                for k in z_list:
                    for theta in theta_list:
                        i = self.cut_radius * np.cos(theta)
                        j = self.cut_radius * np.sin(theta)
                        coords = self.origin + [i, j, k]
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
        dis = self.calc_dis(child, center_idx)[:-1]
        dis = np.abs(dis-self.cut_radius)
        sorted_indices = np.argsort(dis)
        return sorted_indices
    
    @staticmethod
    def calc_dis(atoms, center_idx):
        a, b = atoms.cell.cellpar()[:2]
        # 计算原子在x,y平面的投影间距
        dis = np.abs(atoms.positions[:, :2] - atoms[center_idx].position[:2])
        dis[:, 0][dis[:, 0] > a/2] = a - dis[:, 0][dis[:, 0] > a/2]
        dis[:, 1][dis[:, 1] > b/2] = a - dis[:, 1][dis[:, 1] > b/2]
        dis = np.sqrt(np.power(dis, 2).sum(axis=1))
        return dis

    def _atom_crossover(self, a1, a2):
        
        a1 = a1.copy()
        a2 = a2.copy()
       # 随机旋转
        # a1.random_rotation()
        # a1.random_rotation()
        
        # 随机移动
        a1.random_move()
        a2.random_move() 

        # 随机选择替代中心
        center_i, center_j = np.random.randint(len(a1)), np.random.randint(len(a2))
        a1[center_i].tag = 1
        a2[center_j].tag = 1
        # x,y的中心重合
        a2.positions[:, :2] += a1.positions[center_i, :2] - a2.positions[center_j, :2]
        a1.wrap()
        a2.wrap()

        dis1 = self.calc_dis(a1, center_i)
        mean1 = np.sum(dis1)/(len(a1)-1)
        dis2 = self.calc_dis(a2, center_j)
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
                self.origin[2] = 0
        return atoms

class CylinderCrossoverCluster(Crossover):
    """crossover"""
    def __init__(
            self, 
            stddev, 
            max_count
            ):
        super().__init__(stddev, max_count)
        self.operator = 'cylinder_cross'
            
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 
        dis = np.linalg.norm(child.get_positions()[:, :2], axis=1)
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

        dis1 = np.linalg.norm(a1.get_positions()[:, :2], axis=1)
        mean1 = np.sum(dis1)/len(a1)
        dis2 = np.linalg.norm(a2.get_positions()[:, :2], axis=1)
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


class CylindeCrossoverLayer(Crossover):
    """crossover"""
    def __init__(
            self, 
            stddev, 
            max_count, 
            theta_interval,
            z_interval
            ):
        super().__init__(stddev, max_count)
        self.operator = 'cylinde_cross'
        self.theta_interval = theta_interval
        self.z_interval = z_interval

    def _add_border(self, child):

        # 生成角度范围
    
        z_coords = child.get_positions()[:, 2]
        z_length = max(z_coords)-min(z_coords)
        z_num = int(z_length / self.z_interval)
        z_list = np.linspace(0, z_length, z_num)
        theta_num = int(2 * np.pi / self.theta_interval)
        theta_list = np.linspace(0, 2 * np.pi, theta_num)

        for key, value in  self._natoms_diff.items():
            if value < 0:
                for k in z_list:
                    for theta in theta_list:
                        i = self.cut_radius * np.cos(theta)
                        j = self.cut_radius * np.sin(theta)
                        coords = self.origin + [i, j, k]
                        child.append(Atom(key))
                        
                        child[-1].position = coords
                        
                        too_close_flag, _ = self.hc.check_distance(child)
                        if too_close_flag:
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
        dis = self.calc_dis(child, center_idx)[:-1]
        dis = np.abs(dis-self.cut_radius)
        sorted_indices = np.argsort(dis)
        return sorted_indices
    
    @staticmethod
    def calc_dis(atoms, center_idx):
        a, b = atoms.cell.cellpar()[:2]
        # 计算原子在x,y平面的投影间距
        dis = np.abs(atoms.positions[:, :2] - atoms[center_idx].position[:2])
        dis[:, 0][dis[:, 0] > a/2] = a - dis[:, 0][dis[:, 0] > a/2]
        dis[:, 1][dis[:, 1] > b/2] = a - dis[:, 1][dis[:, 1] > b/2]
        dis = np.sqrt(np.power(dis, 2).sum(axis=1))
        return dis
    
    def _atom_crossover(self, a1, a2):
        
        a1 = a1.copy()
        a2 = a2.copy()
        # 随机旋转
        a1 = self._random_rotation_layer(a1)
        a2 = self._random_rotation_layer(a2)

        # 随机选择替代中心
        center_i, center_j = np.random.randint(len(a1)), np.random.randint(len(a2))
        a1[center_i].tag = 1
        a2[center_j].tag = 1
        # z方向中心对齐
        center_z_a1 = np.mean(a1.positions[:, 2])
        center_z_a2 = np.mean(a2.positions[:, 2])
        a2.positions[:, 2] += center_z_a1 - center_z_a2
        
        a1.wrap()
        a2.wrap()

        dis1 = self.calc_dis(a1, center_i)
        mean1 = np.sum(dis1)/(len(a1)-1)
        dis2 = self.calc_dis(a2, center_j)
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
                self.origin[2] = 0
        return atoms
    