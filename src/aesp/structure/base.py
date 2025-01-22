from ase import Atoms
from aesp.operator.mutation.permutation import PermutationMutation
import numpy as np 
import copy
from dargs import Argument, Variant
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.ase import AseAtomsAdaptor
import spglib
from ase.ga.utilities import get_cell_angles_lengths

class StructBase(Atoms):
    def __init__(self, symbols=None,
                positions=None, numbers=None,
                tags=None, momenta=None, masses=None,
                magmoms=None, charges=None,
                scaled_positions=None,
                cell=None, pbc=None, celldisp=None,
                constraint=None,
                calculator=None,
                info=None,
                velocities=None, min_dist=None
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
                velocities)
        self.min_dist = min_dist

    @staticmethod
    def tol_matrix_config():
        doc_tuples = "Setting the minimum distance limit between atoms."
        doc_prototype = "Types of generated structures."
        doc_factor = "Scaling factor for minimum distance limit."
        return [
            Argument("tuples", list, optional=True, default=None, doc=doc_tuples),
            Argument("prototype", str, optional=True, default="atomic",doc=doc_prototype),
            Argument("factor", float, optional=True, default=1.0,doc=doc_factor)
        ]

    @classmethod
    def operator_adaptive_variant(cls):
        doc_adjustment = "Adjustment mode"
        doc_distribution = "Distribution model"
        doc_input = "Different kinds of adaptive"
        inputs_list = []
        inputs_list.append(Argument("adjustment", dict, cls.adjustment_config(), doc=doc_adjustment))
        inputs_list.append(Argument("distribution", dict, cls.distribution_config(), doc=doc_distribution))
        return Variant("type", inputs_list, doc=doc_input)
    
    @staticmethod
    def distribution_config():
        doc_use_recent_pop = "Use of information from recent generations"
        return [
            Argument("use_recent_pop", int, optional=True, default=2, doc=doc_use_recent_pop)
        ]

    @staticmethod
    def adjustment_config():
        doc_use_recent_pop = "Use of information from recent generations"
        doc_factor = ""
        return [
            Argument("factor", float, optional=True, default=0.5, doc=doc_factor),
            Argument("use_recent_pop", int, optional=True, default=2, doc=doc_use_recent_pop),
        ]

    @staticmethod
    def plane_cross_params_cofig():
        doc_stddev = "Standard deviation of the Gaussian distribution"
        doc_max_count = "Maximum number of attempts"
        # doc_interval = ""
        return [
            Argument("stddev", float, optional=True, default=0.1, doc=doc_stddev),
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count),
            # Argument("interval", float, optional=True, default=0.2, doc=doc_interval ),
        ]

    @staticmethod
    def cylinder_cross_params_config():
        doc_stddev = "Standard deviation of the Gaussian distribution"
        doc_max_count = "Maximum number of attempts"
        # doc_theta_interval= ""
        # doc_z_interval= ""
        return [
            Argument("stddev", float, optional=True, default=0.1, doc=doc_stddev),
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count)
            # Argument("theta_interval", float, optional=True, default=3.14/12, doc=doc_theta_interval),
            # Argument("z_interval", float, optional=True, default=0.2, doc=doc_z_interval),
        ]

    @staticmethod
    def sphere_cross_params_cofig():
        doc_stddev = "Standard deviation of the Gaussian distribution"
        doc_max_count = "Maximum number of attempts"
        # doc_theta_interval = ""
        # doc_phi_interval = ""
        return [
            Argument("stddev", float, optional=True, default=0.1, doc=doc_stddev),
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count),
            # Argument("theta_interval", float, optional=True, default=3.14/12, doc=doc_theta_interval),
            # Argument("phi_interval", float, optional=True, default=3.14/12, doc=doc_phi_interval),
        ]
    
    @staticmethod
    def strain_mut_params_config():
        doc_stddev = "Standard deviation of the Gaussian distribution"
        doc_max_count = "Maximum number of attempts"
        return [
            Argument("stddev", float, optional=True, default=0.1, doc=doc_stddev),
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count)
        ]

    @staticmethod
    def permutation_mut_params_config():
        doc_max_count = "Maximum number of attempts"
        return [
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count)
        ]

    @staticmethod
    def ripple_mut_params_config():
        doc_max_count = "Maximum number of attempts"
        doc_miu = "miu"
        doc_rho = "rho"
        doc_eta = "eta"
        return [
            Argument("max_count", int, optional=True, default=100, doc=doc_max_count),
            Argument("miu", int, optional=True, default=2, doc=doc_miu),
            Argument("rho", float, optional=True, default=0.3, doc=doc_rho),
            Argument("eta", int, optional=True, default=1, doc=doc_eta)
        ]

    def set_ea_params(self, permutation_mut_params):
        permutmut = PermutationMutation(**permutation_mut_params)
        self.mutation_dict = {'permutation_mut': permutmut}
        self.crossover_dict = {}
        self.generator_dict = {} 

    def from_atoms(self, atoms):
        self.__init__(symbols=atoms.symbols,
                positions=atoms.positions, pbc=atoms.pbc, cell=atoms.cell)
        self.info = atoms.info
        return self
    
    def get_fp_similarity(self, atoms):
        fp1 = np.array(atoms.info['data']['fp'])
        fp2 = np.array(self.info['data']['fp'])
        a = np.dot(fp1, fp2) / (np.linalg.norm(fp1) * np.linalg.norm(fp2))
        simi = 0.5 * (1+a)
        return float(simi)

    def looks_like(self, atoms, simi_thres):
        simi = self.get_fp_similarity(atoms)
        return simi > simi_thres

    def get_spg_info(self, symprec=0.1):
        try:
            # self.standardize_cell(symprec=symprec)
            analyzer = SpacegroupAnalyzer(AseAtomsAdaptor().get_structure(self), symprec=symprec)
            spg_sym = analyzer.get_space_group_symbol()  # 获取空间群符号
            spg_num = analyzer.get_space_group_number()  # 获取空间群编号
        except:
            spg_num, spg_sym = '-', '-'
        info = {'spg_num': spg_num, 'spg_sym': spg_sym}
        return info

    def standardize_cell(self, symprec=0.1, to_primitive=False):
        std_para = spglib.standardize_cell(
            (self.get_cell(), self.get_scaled_positions(), self.get_atomic_numbers()),
            symprec=symprec, to_primitive=to_primitive)
        if std_para is None:
            return False
        std_atoms = Atoms(cell=std_para[0], scaled_positions=std_para[1], numbers=std_para[2])
        self.set_cell(std_atoms.cell)
        self.set_scaled_positions(std_atoms.get_scaled_positions())
        self.set_atomic_numbers(self.numbers)


    def is_within_bounds(self):
        if self.bounds is None:
            return True
        values = get_cell_angles_lengths(self.cell)
        verdict = True
        for param, bound in self.bounds.items():
            if not (bound[0] <= values[param] <= bound[1]):
                verdict = False
        return verdict

    def update_species_order(self):
        # 获取原子的化学符号列表
        symbols = self.get_chemical_symbols()
        species = list(set(symbols))
        species.sort()
        # 构建排序后的索引列表
        sorted_indices = sorted(range(len(symbols)), key=lambda i: species.index(symbols[i]))
        # 根据排序后的索引列表重新排列原子
        self = self[sorted_indices]
        return self

    def check_distance(self):
        """检查两个元素之间的距离是否满足最小要求"""
        # 原子数小于2时
        if len(self) < 2 or self.min_dist is None:
            return True, []
        indices_list = []
        for species1, species2, dist in self.min_dist:
     
            distances = self.get_all_distances(mic=True)
            mask = np.zeros_like(distances)
            
            index = [i for i, symbol in enumerate(self.get_chemical_symbols()) if symbol == species1]
            column = [i for i, symbol in enumerate(self.get_chemical_symbols()) if symbol == species2]

            if len(index) == 0: 
                continue
            # 元素掩码矩阵
            for idx in index:
                mask[idx, column] = True
                np.fill_diagonal(mask, False)
                mask = np.tril(mask).astype('bool')

            matrics = (distances <= dist) & mask  # 原子距离小于特定值的矩阵

            indices_list.append(matrics)
        merged_matrix = np.any(indices_list, axis=0)
        indices = np.array(np.where(merged_matrix))  # 重复原子的索引列表
        flag = True 
        if len(indices[0]) > 0:
            flag = False
        return flag, indices

    def gen_continuous_mutation(self, parent, prob, mutation_list, continuous_mut_factor):
        mutation_list_copy = copy.deepcopy(mutation_list)
        index_list = list(range(len(mutation_list_copy)))
        struc = parent.copy()
        for mutation_index in range(len(mutation_list_copy)):
            index = np.random.choice(index_list, p=prob)

            if mutation_list_copy[index] is None:
                struc.info['data'].update({"parents": [parent.info["key_value_pairs"]['s_id']]})
                return struc
            p = prob[index]
            # mutation = self.mutation_dict[mutation_list_copy[index]] 
            if mutation_index == 0:
                clear_info = True
            else:
                clear_info = False
            struc = self.gen_by_mutation(struc, mutation_list_copy[index], clear_info, False)
            # struc = mutation.get_new_candidate(struc, mutation_index+1)
            if struc is None:
                return struc
            
            # 概率衰减
            total_prob = 0
            for i in index_list:
                if i== index:
                    continue
                prob[i] = prob[i] * p * continuous_mut_factor
                total_prob += prob[i] 
            prob[index] = 1 - total_prob
            mutation_list_copy[index] = None
 

    def gen_ea(self, parents, operator_prob, mutation_prob, generator_prob, crossover_prob, continuous_mut_factor):
        
        generator_list = list(generator_prob.keys())
        crossover_list = list(crossover_prob.keys())
        mutation_list = list(mutation_prob.keys())
        operator_list = list(operator_prob.keys())
    
        operator_type = operator_list[np.random.choice(list(range(len(operator_list))), p=list(operator_prob.values()))]
        
        if operator_type == "generator":
            generator_type = generator_list[np.random.choice(list(range(len(generator_list))), p=list(generator_prob.values()))]
            struc = self.gen_by_generator(generator_type)
            # struc = self.generator_dict[generator_type].get_new_candidate(self)
            # parents_id = []

        elif operator_type == "crossover": 
            crossover_type = crossover_list[np.random.choice(list(range(len(crossover_list))), p=list(crossover_prob.values()))]
            struc = self.gen_by_crossover(parents, crossover_type)
            # struc = self.crossover_dict[crossover_type].get_new_candidate(parents)
            # parents_id = [parents[0].info["key_value_pairs"]['s_id'], parents[1].info["key_value_pairs"]['s_id']]
        elif operator_type == "mutation":
            struc = self.gen_continuous_mutation(parents[0], list(mutation_prob.values()), mutation_list, continuous_mut_factor)
       
        # if struc is not None:
        #     struc.info['data'].update({'parents': parents_id})
        #     struc = self.get_spg_info(struc)
        return struc

    def calc_fp_describe(self, r_cut=6, n=100, sigma=10**(-0.5), function='distance'):
        raise NotImplementedError()  

    def gen_by_generator(self, generator_type):
        struc = self.generator_dict[generator_type].get_new_candidate(self)
        if struc is None:
            return None
        fp = self.calc_fp_describe()
        struc = struc.update_species_order()
        struc.info.update({"struc_type": self.struc_type})
        struc.info['data'].update({"parents": [], "fp": fp})
        struc.info.update(struc.get_spg_info())
        return struc

    def gen_by_seeds(self, atoms):
        struc = self.from_atoms(atoms)
        if struc is None:
            return None
        fp = self.calc_fp_describe()
        struc = struc.update_species_order()
        struc.info = {"oper_name": '-', "oper_type": 'seeds'}
        struc.info.update({"struc_type": self.struc_type})
        struc.info['data'] = {"parents": [], "fp": fp}
        struc.info.update(struc.get_spg_info())
        return struc

    def gen_by_mutation(self, parent, mutation_type, clear_info=True, update_parent=True):
        struc = self.mutation_dict[mutation_type].get_new_candidate(parent, clear_info)
        if struc is None:
            return None
        if update_parent:       
            struc.info['data'].update({"parents": [parent.info["key_value_pairs"]['s_id']]})
        struc = struc.update_species_order()
        fp = struc.calc_fp_describe()
        struc.info.update({"struc_type": self.struc_type})
        struc.info['data'].update({"fp": fp})
        struc.info.update(struc.get_spg_info())
        return struc

    def gen_by_crossover(self, parents, crossover_type, clear_info=True, update_parent=True):
        struc = self.crossover_dict[crossover_type].get_new_candidate(parents, clear_info)
        if struc is None:
            return None
        struc = struc.update_species_order()
        if update_parent:     
            struc.info['data'].update({'parents': [parents[0].info["key_value_pairs"]['s_id'], parents[1].info["key_value_pairs"]['s_id']]})
        fp = struc.calc_fp_describe()
        struc.info['data'].update({"fp": fp})
        struc.info.update({"struc_type": self.struc_type})
        struc.info.update(struc.get_spg_info())
        return struc

    # def


if __name__ == "__main__":
    d = 2.9
    L = 10.0
    atoms = Atoms('Au',
                positions=[[0, L / 2, L / 2]],
                cell=[d, L, L],
                pbc=[1, 0, 0])
    # print(atoms.__dict__)
    print(atoms)
    sb = StructBase(symbols=atoms.symbols,
                positions=atoms.positions, pbc=atoms.pbc)
    print(sb)
    # print(bs.get_spg_info())