from aesp.structure.base import StructBase
from ase.atoms import Atoms
from ase.spacegroup import get_spacegroup
import numpy as np 
from dscribe.descriptors import ValleOganov
from pyxtal import pyxtal
from pyxtal.tolerance import Tol_matrix
from pyxtal.symmetry import Group
from itertools import combinations_with_replacement
import os
import warnings
from pymatgen.core.structure import Molecule
from pymatgen.symmetry.analyzer import PointGroupAnalyzer
import pandas as pd
from pymatgen.io.ase import AseAtomsAdaptor
from ase.ga.standard_comparators import InteratomicDistanceComparator
import copy

from aesp.operator.crossover.plane import PlaneCrossoverCluster
from aesp.operator.crossover.sphere import SphereCrossoverCluster
from aesp.operator.crossover.cylinder import CylinderCrossoverCluster
from aesp.operator.generator.random import RandomGeneratorCluster
from aesp.operator.mutation.permutation import PermutationMutation
from aesp.operator.mutation.ripple import RippleMutationCluster

from ase.ga.ofp_comparator import OFPComparator

from aesp.structure.base import StructBase
from ase.atoms import Atoms
from dargs import Argument, Variant
from ase.spacegroup import get_spacegroup
import numpy as np 
from dscribe.descriptors import ValleOganov
from pyxtal import pyxtal
from pyxtal.tolerance import Tol_matrix
from pyxtal.symmetry import Group
from itertools import combinations_with_replacement
import os
import pandas as pd
from pymatgen.io.ase import AseAtomsAdaptor
from ase.ga.standard_comparators import InteratomicDistanceComparator
import copy
from dscribe.descriptors import CoulombMatrix

from aesp.operator.crossover.plane import PlaneCrossoverBulk
from aesp.operator.crossover.sphere import SphereCrossoverBulk
from aesp.operator.crossover.cylinder import CylinderCrossoverBulk
from aesp.operator.generator.random import RandomGeneratorBulk
from aesp.operator.mutation.strain import StrainMutationBulk
from aesp.operator.mutation.permutation import PermutationMutation
from aesp.operator.mutation.ripple import RippleMutationBulk



class Cluster(StructBase):
    def __init__(self, symbols=None,
                positions=None, numbers=None,
                tags=None, momenta=None, masses=None,
                magmoms=None, charges=None,
                scaled_positions=None,
                cell=None, pbc=None, celldisp=None,
                constraint=None,
                calculator=None,
                info=None,
                velocities=None, min_dist=None,
                bounds=None
                ):

        super().__init__(symbols,
                positions, numbers,
                tags, momenta, masses,
                magmoms, charges,
                scaled_positions,
                cell, pbc, celldisp,
                constraint,
                calculator,
                info,
                velocities, min_dist)
        self.bounds = bounds
        self.struc_type = 'cluster'

    def set_ea_params(self, opt_algo):
        random_gen_params = opt_algo['operator']['generator']["random_gen_params"]
        permutation_mut_params = opt_algo['operator']['mutation']["permutation_mut_params"]
        plane_cross_params = opt_algo['operator']['crossover']["plane_cross_params"]
        sphere_cross_params = opt_algo['operator']['crossover']["sphere_cross_params"]
        cylinder_cross_params = opt_algo['operator']['crossover']["cylinder_cross_params"]
        ripple_mut_params = opt_algo['operator']['mutation']["ripple_mut_params"]
        randomgen = RandomGeneratorCluster(**random_gen_params)
        ripplemut = RippleMutationCluster(**ripple_mut_params)
        planecross = PlaneCrossoverCluster(**plane_cross_params)
        spherecross = SphereCrossoverCluster(**sphere_cross_params)
        cylindecross = CylinderCrossoverCluster(**cylinder_cross_params)
        
        super().set_ea_params(permutation_mut_params)

        self.add_cell_flag = opt_algo['operator']['add_cell']
        self.vacuum = opt_algo['operator']['vacuum']

        self.generator_dict.update({"random_gen": randomgen}) 
        self.mutation_dict.update({'ripple_mut': ripplemut}) 
        self.crossover_dict.update({"plane_cross": planecross, "sphere_cross": spherecross, "cylinder_cross": cylindecross}) 
    
    def calc_fp_describe(self):
        atoms = self.copy()
        # atoms.add_cell(2)
        cm = CoulombMatrix(n_atoms_max=len(atoms))  
        cm_fp = cm.create(atoms)
        return cm_fp.tolist()
    
    def random_rotation(self):
         # 生成随机的旋转轴 
        random_axis = np.random.rand(3)
        random_axis /= np.linalg.norm(random_axis)

        # 生成随机的旋转角度（以弧度为单位）
        random_angle = np.random.uniform(0, 2 * np.pi)

        # 对原子体系进行旋转
        self.rotate(v=random_axis, a=random_angle, center='COM')


    def reset_positions(self):
        self.positions -= self.positions.mean(axis=0)

    def add_cell(self, vacuum=15):
       
        self.positions -= self.positions.min(axis=0)
        self.positions += vacuum / 2
        length = abs(self.positions.max(axis=0)-self.positions.min(axis=0)+vacuum)
        self.set_cell([length[0], length[1], length[2], 90, 90, 90], scale_atoms=False)

        # self.get_center_of_coords()

    def get_spg_info(self):
        atoms = self.copy()
        atoms.cell = None
        try:
        # 创建 pymatgen 分子对象
            molecule = Molecule(atoms.get_chemical_symbols(), atoms.get_positions())
            # 使用 PointGroupAnalyzer 分析点群
            # warnings.filterwarnings('error')
            pga = PointGroupAnalyzer(molecule, tolerance=0.01)
            warnings.filterwarnings("ignore", message="1 matrices have been generated. The tol may be too small. Please terminate and rerun with a different tolerance.")
            point_group = pga.get_pointgroup()
            
            # with warnings.catch_warnings(record=True) as w:
            #     point_group = pga.get_pointgroup()
            #     if len(w) > 0:
            #         print(w[0].message)
            #         raise ValueError
            spg_sym = point_group.sch_symbol
        except:
            spg_sym = '-'
        info = {'spg_num': '-', 'spg_sym': spg_sym}
        return info

    def gen_by_generator(self, generator_type):
        struc = super().gen_by_generator(generator_type)
        if struc is None:
            return None
        # print(struc.get_volume())
        if self.add_cell_flag:
            struc.add_cell(self.vacuum)
        return struc

    def gen_by_seeds(self, atoms):
        struc = super().gen_by_seeds(atoms)
        
        if self.add_cell_flag:
            struc.add_cell(self.vacuum)
        return struc

    def gen_by_mutation(self, parent, mutation_type, clear_info=True, update_parent=True):
        struc = super().gen_by_mutation(parent, mutation_type, clear_info, update_parent)
        if struc is None:
            return None
        if self.add_cell_flag:
            struc.add_cell(self.vacuum)
        return struc

    def gen_by_crossover(self, parents, crossover_type, clear_info=True, update_parent=True):
        struc = super().gen_by_crossover(parents, crossover_type, clear_info, update_parent)
        if struc is None:
            return None
        if self.add_cell_flag:
            struc.add_cell(self.vacuum)
        return struc

    @classmethod
    def args(cls):
        doc_generator = "随机生成的概率"
        doc_crossover = "交叉的概率"
        doc_mutation = "个体变异的概率"
        doc_adaptive_config = ""
        doc_hard_constrains = "hard_constrains"
        doc_add_cell = ''
        doc_vacuum = ''
        return [
            Argument("add_cell", bool, optional=True, default=False, doc=doc_add_cell),
            Argument("vacuum", float, optional=True, default=15, doc=doc_vacuum),
            Argument("generator", dict, cls.generator_config(), optional=False, doc=doc_generator),
            Argument("crossover", dict, cls.crossover_config(), optional=False, doc=doc_crossover),
            Argument("mutation", dict, cls.mutation_config(), optional=False, doc=doc_mutation),
            Argument("adaptive", dict, sub_variants=[cls.operator_adaptive_variant()], optional=True, default=None, doc=doc_adaptive_config),
            Argument("hard_constrains", dict, cls.hard_constrains_config(), optional=False, doc=doc_hard_constrains)
        ]

    @classmethod
    def generator_config(cls):
        doc_random_gen_prob = ""
        doc_prob = ''
        doc_random_gen_params = ''
        return [
            Argument("prob", float, optional=True, default=0.3, doc=doc_prob),
            Argument("random_gen_prob", float, optional=True, default=1, doc=doc_random_gen_prob),
            Argument("random_gen_params", dict, cls.random_gen_params_config(), optional=True, doc=doc_random_gen_params)
        ]

    @staticmethod
    def random_gen_params_config():
        doc_composition = "需要预测的晶体组分信息"
        doc_spgnum = "随机生成机结构时对空间群的限定"
        doc_factor = "随机生成机结构时对空间群的限定"
        doc_thickness = ""
        doc_max_count = ""
        spgnum = [i for i in range(1, 57)]
        return [
            Argument("composition", dict, optional=False, doc=doc_composition),
            Argument("spgnum", list, optional=True, default=spgnum, doc=doc_spgnum),
            Argument("factor", float, optional=True, default=1.1, doc=doc_factor),
            Argument("thickness", float, optional=True, default=None, doc=doc_thickness),
            Argument("max_count", float, optional=True, default=50, doc=doc_max_count)
        ]

    @classmethod
    def crossover_config(cls):
        doc_plane_cross_prob = ""
        doc_sphere_cross_prob = ""
        doc_plane_cross_params = ""
        doc_sphere_cross_params = ""
        doc_cylinder_cross_params = ""
        doc_cylinder_cross_prob = ""
        doc_prob = ''
        return [
            Argument("prob", float, optional=True, default=0.3, doc=doc_prob),
            Argument("plane_cross_prob", float, optional=True, default=0.33, doc=doc_plane_cross_prob),
            Argument("sphere_cross_prob", float, optional=True, default=0.33, doc=doc_sphere_cross_prob),
            Argument("cylinder_cross_prob", float, optional=True, default=0.34, doc=doc_cylinder_cross_prob),
            Argument("plane_cross_params", dict, cls.plane_cross_params_cofig(), optional=True, doc=doc_plane_cross_params),
            Argument("sphere_cross_params", dict, cls.sphere_cross_params_cofig(), optional=True, doc=doc_sphere_cross_params),
            Argument("cylinder_cross_params", dict, cls.cylinder_cross_params_config(), optional=True, doc=doc_cylinder_cross_params)
        ]
    
    @classmethod
    def mutation_config(cls):
        doc_permutation_mut_prob = "Permutation变异的概率"
        doc_ripple_mut_prob = "ripple变异的概率"
        doc_prob = ''
        doc_continuous_mut_factor = ''
        doc_permutation_mut_params = ''
        doc_ripple_mut_params = ''
        return [
            Argument("continuous_mut_factor", float, optional=True, default=1, doc=doc_continuous_mut_factor),
            Argument("prob", float, optional=True, default=0.4, doc=doc_prob),
            Argument("permutation_mut_prob", float, optional=True, default=0.3, doc=doc_permutation_mut_prob),
            Argument("ripple_mut_prob", float, optional=True, default=0.3, doc=doc_ripple_mut_prob),
            Argument("permutation_mut_params", dict, cls.permutation_mut_params_config(), optional=True, doc=doc_permutation_mut_params),
            Argument("ripple_mut_params", dict, cls.ripple_mut_params_config(), optional=True, doc=doc_ripple_mut_params),  
        ]

    @classmethod
    def hard_constrains_config(cls):
        doc_tol_matrix = "随机生成机结构时对空间群的限定"
        return [
            Argument("tol_matrix", dict, cls.tol_matrix_config(), optional=True, default=None, doc=doc_tol_matrix)
        ]

if __name__ == "__main__":
    d = 2.9
    L = 10.0
    atoms = Atoms('Au2',
                positions=[[0, L / 2, L / 2], [L, L, L]],
                cell=[d, L, L],
                pbc=[1, 1, 1])
    # print(atoms.__dict__)
    print(atoms)
    sb = Bulk(symbols=atoms.symbols,
                positions=atoms.positions, pbc=atoms.pbc,
            cell=atoms.cell)
    print(sb.positions)
    # print(sb.random_rotation())
    sb.random_move()
    print(sb.get_spg_info())
    print(sb.positions)