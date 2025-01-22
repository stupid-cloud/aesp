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

from aesp.operator.crossover.plane import PlaneCrossoverBulk
from aesp.operator.crossover.sphere import SphereCrossoverBulk
from aesp.operator.crossover.cylinder import CylinderCrossoverBulk
from aesp.operator.generator.random import RandomGeneratorBulk
from aesp.operator.mutation.strain import StrainMutationBulk
from aesp.operator.mutation.permutation import PermutationMutation
from aesp.operator.mutation.ripple import RippleMutationBulk

from ase.ga.ofp_comparator import OFPComparator


class Bulk(StructBase):
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
        self.struc_type = 'bulk'

    def set_ea_params(self, opt_algo):
        random_gen_params = opt_algo['operator']['generator']["random_gen_params"]
        permutation_mut_params = opt_algo['operator']['mutation']["permutation_mut_params"]
        plane_cross_params = opt_algo['operator']['crossover']["plane_cross_params"]
        sphere_cross_params = opt_algo['operator']['crossover']["sphere_cross_params"]
        cylinder_cross_params = opt_algo['operator']['crossover']["cylinder_cross_params"]
        ripple_mut_params = opt_algo['operator']['mutation']["ripple_mut_params"]
        strain_mut_params = opt_algo['operator']['mutation']["strain_mut_params"]
        randomgen = RandomGeneratorBulk(**random_gen_params)
        ripplemut = RippleMutationBulk(**ripple_mut_params)
        strainmut = StrainMutationBulk(**strain_mut_params) 
        planecross = PlaneCrossoverBulk(**plane_cross_params)
        spherecross = SphereCrossoverBulk(**sphere_cross_params)
        cylindecross = CylinderCrossoverBulk(**cylinder_cross_params)
        
        super().set_ea_params(permutation_mut_params)
        self.generator_dict.update({"random_gen": randomgen}) 
        self.mutation_dict.update({'ripple_mut': ripplemut, 'strain_mut': strainmut}) 
        self.crossover_dict.update({"plane_cross": planecross, "sphere_cross": spherecross, "cylinder_cross": cylindecross}) 
    
    def calc_fp_describe(self, r_cut=6, n=50, sigma=10**(-0.5), function='distance'):
        vo = ValleOganov(
            species=list(set(self.get_chemical_symbols())),
            function=function,
            sigma=sigma,
            n=n,
            r_cut=r_cut,
        )
        vo_fp = vo.create(self)    # np.array
        return vo_fp.tolist()
    
    def random_rotation(self):
         # 生成随机的旋转轴 
        random_axis = np.random.rand(3)
        random_axis /= np.linalg.norm(random_axis)

        # 生成随机的旋转角度（以弧度为单位）
        random_angle = np.random.uniform(0, 2 * np.pi)

        # 对原子体系进行旋转
        self.rotate(v=random_axis, a=random_angle, center='COM')
        self.wrap()

    def random_move(self):
        self.set_scaled_positions(self.get_scaled_positions() + np.random.rand(3))
        self.wrap()

    @classmethod
    def args(cls):
        doc_generator = "随机生成的概率"
        doc_crossover = "交叉的概率"
        doc_mutation = "个体变异的概率"
        doc_adaptive_config = ""
        doc_hard_constrains = "hard_constrains"
        return [
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
        doc_composition = "Compositions of the structure to be predicted"
        doc_spgnum = "随机生成机结构的空间群"
        doc_factor = "随机生成机结构时对空间群的限定"
        doc_thickness = ""
        doc_max_count = ""
        spgnum = [i for i in range(1, 231)]
        return [
            Argument("composition", dict, optional=False, doc=doc_composition),
            Argument("spgnum", list, optional=True, default=spgnum, doc=doc_spgnum),
            Argument("factor", float, optional=True, default=1.1, doc=doc_factor),
            Argument("thickness", float, optional=True, default=None, doc=doc_thickness),
            Argument("max_count", float, optional=True, default=50, doc=doc_max_count)
        ]

    @classmethod
    def crossover_config(cls):
        doc_plane_cross_prob = "Probability of plane crossover"
        doc_sphere_cross_prob = "Probability of sphere crossover"
        doc_cylinder_cross_prob = "Probability of cylinder crossover"
        doc_plane_cross_params = "configuration of plane crossover"
        doc_sphere_cross_params = "configuration of sphere crossover"
        doc_cylinder_cross_params = "configuration of cylinder crossover"
        
        doc_prob = 'Probability of crossover'
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
        doc_strain_mut_prob = "Probability of Strain Mutation"
        doc_permutation_mut_prob = "Probability of permutation Mutation"
        doc_ripple_mut_prob = "Probability of ripple Mutation"
        doc_prob = 'Probability of mutation'
        doc_continuous_mut_factor = 'continuous mutation factor'
        doc_strain_mut_params = 'configuration of Strain Mutation'
        doc_permutation_mut_params = 'configuration of permutation Mutation'
        doc_ripple_mut_params = 'configuration of ripple Mutation'
        return [
            Argument("continuous_mut_factor", float, optional=True, default=1, doc=doc_continuous_mut_factor),
            Argument("prob", float, optional=True, default=0.4, doc=doc_prob),
            Argument("strain_mut_prob", float, optional=True, default=0.3, doc=doc_strain_mut_prob),
            Argument("permutation_mut_prob", float, optional=True, default=0.3, doc=doc_permutation_mut_prob),
            Argument("ripple_mut_prob", float, optional=True, default=0.3, doc=doc_ripple_mut_prob),
            Argument("strain_mut_params", dict, cls.strain_mut_params_config(), optional=True, doc=doc_strain_mut_params),
            Argument("permutation_mut_params", dict, cls.permutation_mut_params_config(), optional=True, doc=doc_permutation_mut_params),
            Argument("ripple_mut_params", dict, cls.ripple_mut_params_config(), optional=True, doc=doc_ripple_mut_params),  
        ]

    @classmethod
    def hard_constrains_config(cls):
        doc_alpha = "angle"
        doc_beta = "angle"
        doc_gamma = "angle"
        doc_chi = "dihedral angle"
        doc_psi = "dihedral angle"
        doc_phi = "dihedral angle"
        doc_a = "lattice constant"
        doc_b = "lattice constant"
        doc_c = "lattice constant"
        doc_tol_matrix = "Tolerance matrix of the structure"
        return [
            Argument("alpha", float, optional=True, default=[20 ,160], doc=doc_alpha),
            Argument("beta", float, optional=True, default=[20 ,160],doc=doc_beta),
            Argument("gamma", float, optional=True, default=[20 ,160],doc=doc_gamma),
            Argument("chi", float, optional=True, default=[20 ,160],doc=doc_chi),
            Argument("psi", float, optional=True, default=[20 ,160],doc=doc_psi),
            Argument("phi", float, optional=True, default=[20 ,160],doc=doc_phi),
            Argument("a", float, optional=True, default=[0 ,100], doc=doc_a),
            Argument("b", float, optional=True, default=[0 ,100], doc=doc_b),
            Argument("c", float, optional=True, default=[0 ,100], doc=doc_c),
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