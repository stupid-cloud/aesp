
import numpy as np 
from pymatgen.io.ase import AseAtomsAdaptor
from ase import Atoms, Atom
import copy
from collections import Counter
from aesp.operator.base import OperatorBase


class Crossover(OperatorBase):
    def __init__(self, stddev, max_count):
        super().__init__(max_count)
        self.stddev = stddev


    def get_new_candidate(self, parents, clear_info):
        """The method called by the user that
        returns the paired structure."""
        f, m = copy.deepcopy(parents)
        if clear_info:
            f.info = {}
            m.info = {}
        for _ in range(self.max_count):
            child = self.crossover(f, m)
            if child is None:
                continue
            if child.is_within_bounds() and child.check_distance()[0] and self._check_ok():
                break   
        else:
            return None

        child.info.update({'oper_type': 'crossover', 'oper_name': self.operator})
        child.info['data'] = {}
        return child
      
    def _check_natoms(self, child, parent):
        """检查结果与输入的原子数量之差"""
        natoms_diff = {}
        species = list(set(parent.symbols))
        for i, spe in enumerate(species):
            count_child = sum(1 for atom in child if atom.symbol == spe)
            count_parent = sum(1 for atom in parent if atom.symbol == spe)
            natoms_diff[spe] = count_child - count_parent
        return natoms_diff
    
    def _check_ok(self):
        flag = True
        for key, value in self._natoms_diff.items():
            if value != 0:
                flag = False
        return flag
    
    def _check_more(self):
        flag = False
        for key, value in self._natoms_diff.items():
            if value > 0:
                flag = True
        return flag

    def _check_less(self):
        flag = False
        for key, value in self._natoms_diff.items():
            if value < 0:
                flag = True
        return flag

    def _remove_dist_atom(self, child):
        '''
        if success: self.child <-- child structure data
        if fail: self.child <-- None
        '''
        
        ok_flag, indices = child.check_distance()
        if ok_flag:
            return child
        
        del_index_list = []
        sorted_dict = copy.deepcopy(self._natoms_diff)

        # 优先删除有多余原子的元素
        while True:
            for key, value in list(sorted_dict.items()):
                if value <= 0:
                    sorted_dict.pop(key)
            
            if sorted_dict == {}:
                break
        
            sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: item[1], reverse=True))        
            index_list = Counter(indices.flatten()).most_common()

            index_dict = {}
            for index, value in index_list:
                index_dict[index] = child[index].symbol
      
            del_species = list(sorted_dict.keys())[0]

            try:
                tem_index = list(index_dict.values()).index(del_species)
            except:
                sorted_dict.pop(del_species)
                continue
            
            del_index = list(index_dict.keys())[tem_index]
    
            del_index_list.append(del_index)
            # 从距离判断列表中删除该原子
            mask = np.all(indices != del_index, axis=0)
            indices = indices[:, mask]  
            # diff数据减少
            sorted_dict[del_species] -= 1  
            self._natoms_diff[del_species] -= 1 
            
        # 按照重复的频率进行删除
        while True:
    
            if len(indices[0]) == 0:
                break
            index_list = Counter(indices.flatten()).most_common()
            
            index_dict = {}
            for index, value in index_list:
                index_dict[index] = child[index].symbol
            
            del_species = list(index_dict.values())[0]

            del_index = list(index_dict.keys())[0]
            del_index_list.append(del_index)
            # 从距离判断列表中删除该原子
            mask = np.all(indices != del_index, axis=0)
            indices = indices[:, mask]  
            # diff数据减少
            self._natoms_diff[del_species] -= 1 
       
        # 删除多余的原子
        indices_to_keep = np.ones(len(child), dtype=bool)
        indices_to_keep[del_index_list] = False
        child = child[indices_to_keep]
        return child
    
    def _remove_border(self, child):
        sorted_indices = self._border_dist(child)
        del_index_list = []
        # 按离边界距离依次移除多余原子
        for key, value in self._natoms_diff.items():
            for index in sorted_indices:
                if child[index].symbol == key and value>0:
                    del_index_list.append(index)
                    # diff数据减少
                    self._natoms_diff[key] -= 1   
                    value -= 1
         # 删除多余的原子
        indices_to_keep = np.ones(len(child), dtype=bool)
        indices_to_keep[del_index_list] = False
        child = child[indices_to_keep]

        return child

    def crossover(self, a1, a2):
        """Does the actual mutation."""
        # crossover
         # 保持parents的元素顺序并去重
        child = self._atom_crossover(a1, a2)
        if child is None:
            return None

        # 获取原子数差距
        self._natoms_diff = self._check_natoms(child, a1)

        # 移除距离小于阈值的原子
        child = self._remove_dist_atom(child)

        # TODO 修复原子
        
        # 在边界处删除原子
        if self._check_more():
            child = self._remove_border(child)

        # 在边界处添加原子
        # if self._check_less():
        #     child = self._add_border(child)
       
        return child
    
