from aesp.operator.crossover.base import Crossover
import numpy as np
from ase.atom import Atom
from ase.geometry import cell_to_cellpar
import itertools


class PlaneCrossoverBulk(Crossover):
    """crossover"""
    def __init__(self, stddev, max_count):
        super().__init__(stddev, max_count)
        self.operator = 'plane_cross'
    
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 
        coords_axis = child.get_scaled_positions()[:, self._axis]
        coord_diiff_list = []
        for i in [self._slice_point, 0]:
            coord_diiff = abs(coords_axis - i)
            coord_diiff[coord_diiff>0.5] = 1 - coord_diiff[coord_diiff>0.5]
            coord_diiff_list.append(coord_diiff)

        coord_diiff = [min(item1, item2) for item1, item2 in zip(*coord_diiff_list)]
        sorted_indices = np.argsort(coord_diiff)
        return sorted_indices
    
    def _atom_crossover(self, a1, a2):
        a1 = a1.copy()
        a2 = a2.copy()

        # 随机旋转
        # a1.random_rotation()
        # a1.random_rotation()
        
        # 随机移动
        a1.random_move()
        a2.random_move()

        # ---------- crossover
        self._slice_point = np.random.normal(loc=0.5, scale=self.stddev)
        # self._slice_point = np.random.uniform(loc=0.5, scale=self.stddev)
        self._axis = np.random.choice([0, 1, 2]) 
      

        scaled_positions_A = np.vstack((a1.get_scaled_positions()[a1.get_scaled_positions()[:, self._axis]<=self._slice_point, :], a2.get_scaled_positions()[a2.get_scaled_positions()[:, self._axis]>self._slice_point, :]))
        scaled_positions_B = np.vstack((a2.get_scaled_positions()[a2.get_scaled_positions()[:, self._axis]<=self._slice_point, :], a1.get_scaled_positions()[a1.get_scaled_positions()[:, self._axis]>self._slice_point, :]))
        atoms_A = a1[a1.get_scaled_positions()[:, self._axis]<=self._slice_point] + a2[a2.get_scaled_positions()[:, self._axis]>self._slice_point]
        atoms_B = a2[a2.get_scaled_positions()[:, self._axis]<=self._slice_point] + a1[a1.get_scaled_positions()[:, self._axis]>self._slice_point]
        # ---------- use a structure with more atoms
        if len(atoms_A) > len(atoms_B):
            atoms = atoms_A
            scaled_positions = scaled_positions_A
        else:
            atoms = atoms_B  
            scaled_positions = scaled_positions_B

        cut_cell = 0.5 * (atoms_A.get_cell() + atoms_B.get_cell())
        cut_volume = 0.5 * (atoms_A.get_volume() + atoms_B.get_volume())
        cut_cellpar = cell_to_cellpar(cut_cell)
        ratio = cut_volume / abs(np.linalg.det(cut_cell))
        cut_cellpar[:3] = [length * ratio ** (1/3) for length in cut_cellpar[:3]]   
        atoms.set_cell(cut_cellpar)
        atoms.set_scaled_positions(scaled_positions)
        atoms.wrap()
        return atoms


class PlaneCrossoverCluster(Crossover):
    """crossover"""
    def __init__(self, stddev, max_count):
        super().__init__(stddev, max_count)
        self.operator = 'plane_cross'
    
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 
        child = child.copy()
        positions = child.get_positions() 
        dis = abs(positions[:, self._axis]-self._slice_point)
        sorted_indices = np.argsort(-dis)
        return sorted_indices
    
    def _atom_crossover(self, a1, a2):
        a1 = a1.copy()
        a2 = a2.copy()

        # 随机旋转
        a1.random_rotation()
        a2.random_rotation()
        
        # 中心平移到0
        a1.reset_positions()
        a2.reset_positions()
     
        # ---------- crossover
        self._slice_point = np.random.normal(loc=0, scale=self.stddev)
        # self._slice_point = np.random.uniform(loc=0.5, scale=self.stddev)
        self._axis = np.random.choice([0, 1, 2]) 
      
        atoms_A = a1[a1.get_positions()[:, self._axis]<=self._slice_point] + a2[a2.get_positions()[:, self._axis]>self._slice_point]
        atoms_B = a2[a2.get_positions()[:, self._axis]<=self._slice_point] + a1[a1.get_positions()[:, self._axis]>self._slice_point]
        # ---------- use a structure with more atoms
        if len(atoms_A) > len(atoms_B):
            atoms = atoms_A
        else:
            atoms = atoms_B  
        return atoms

class PlaneCrossoverLayer(Crossover):
    """crossover"""
    def __init__(self, stddev, max_count, interval):
        super().__init__(stddev, max_count)
        self.operator = 'plane_cross'
        self.interval = interval

    
    def _border_dist(self, child):
        """找出离边界的距离，两个边界以最近的为准""" 
        coords_axis = child.get_scaled_positions()[:, self._axis]
        coord_diiff_list = []
        for i in [self._slice_point, 0]:
            coord_diiff = abs(coords_axis - i)
            coord_diiff[coord_diiff>0.5] = 1 - coord_diiff[coord_diiff>0.5]
            coord_diiff_list.append(coord_diiff)

        coord_diiff = [min(item1, item2) for item1, item2 in zip(*coord_diiff_list)]
        sorted_indices = np.argsort(coord_diiff)
        return sorted_indices

    def _atom_crossover(self, a1, a2):
        
        a1 = a1.copy()
        a2 = a2.copy()       
        
        # 随机旋转
        a1 = self._random_rotation_layer(a1)
        a2 = self._random_rotation_layer(a2)

        # 随机移动
        for a in [a1, a2]:
            scaled_positions = a.get_scaled_positions()
            scaled_positions[:, :2] += np.random.rand(2)
            a.set_scaled_positions(scaled_positions)         

        # z方向中心对齐
        center_z_a1 = np.mean(a1.positions[:, 2])
        center_z_a2 = np.mean(a2.positions[:, 2])
        a2.positions[:, 2] += center_z_a1 - center_z_a2

        a1.wrap()
        a2.wrap()
        # ---------- crossover
        
        self._slice_point = np.random.normal(loc=0.5, scale=self.stddev)
        self._axis = np.random.choice([0, 1]) 

        atoms_A = a1[a1.get_scaled_positions()[:, self._axis]<=self._slice_point] + a2[a2.get_scaled_positions()[:, self._axis]>self._slice_point]
        atoms_B = a2[a2.get_scaled_positions()[:, self._axis]<=self._slice_point] + a1[a1.get_scaled_positions()[:, self._axis]>self._slice_point]
    
        # ---------- use a structure with more atoms
        if len(atoms_A) > len(atoms_B):
            atoms = atoms_A
            cell = a1.get_cell()
            # 变换cell
            cell[:2, :2] = self._slice_point*a1.get_cell()[:2, :2] + (1-self._slice_point)*a2.get_cell()[:2, :2]
        else:
            atoms = atoms_B  
            cell = a2.get_cell()
             # 变换cell
            cell[:2, :2] = (1-self._slice_point)*a1.get_cell()[:2, :2] + self._slice_point*a2.get_cell()[:2, :2]        
        atoms.set_cell(cell, scale_atoms=True)
        atoms.wrap()
        return atoms
