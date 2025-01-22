from dflow.python import OP, OPIO, OPIOSign, Artifact, BigParameter
from pyxtal.tolerance import Tol_matrix
from pathlib import Path
import numpy as np
from itertools import combinations_with_replacement
from aesp.func.database import DataConnection
from pathlib import Path
import shutil
from aesp.func.population import Population
from pathlib import Path
from typing import List
from aesp.structure.bulk import Bulk
from ase.io import read
import multiprocessing
import random
from aesp.structure.cluster import Cluster
from aesp.operator import operator_dict
import logging


struc_dict = {"bulk": Bulk, "cluster": Cluster}

def add_candidate(struc, generation, dc):
    struc.info['generation'] = generation
    struc.info['stage'] = 0
    struc.info['status'] = 'unrelaxed'
    dc.add_unrelaxed_candidate(struc)

def tol_matrix_setup(tol_matrix, species):
    tuples = tol_matrix.pop("tuples")
    # 设置距离矩阵
    if tuples is not None:
        tol_matrix = Tol_matrix(*tuples, **tol_matrix)
    else:
        tol_matrix = Tol_matrix(**tol_matrix)

    combinations = list(combinations_with_replacement(species, 2))

    info = []
    for idx, species in enumerate(combinations):
        dist = tol_matrix.get_tol(*species)
        info.append([*species, dist])
    return info, tol_matrix

def create_generator(struc, candis):
    np.random.seed(random.randint(0, 100000))
    atoms = struc.gen_by_generator(generator_type="random_gen") 
    if atoms is None:
        return
    # 同一空间群进行相似筛选
    for candi in candis:
        if atoms.looks_like(candi, simi_thres=0.99):
            # print("已经有类似的结构了generator")
            return None
    return atoms
    
def create_ea(struc, candis, p_list, operator_prob, mutation_prob, generator_prob, crossover_prob, continuous_mut_factor):
    np.random.seed(random.randint(0, 10000))
    atoms = struc.gen_ea(p_list, operator_prob, mutation_prob, generator_prob, crossover_prob, continuous_mut_factor) 
    if atoms is None:
        return
    # 同一空间群进行相似筛选
    for candi in candis:
        if atoms.looks_like(candi, simi_thres=0.99):
            # print("已经有类似的结构了ea")
            return None
    return atoms

class GenStruc(OP):
    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "generation": int,
                "opt_params_config": List[dict],
                "db": Artifact(Path, optional=True)
            }
        )
    
    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "min_dist_info": list,
                "db": Artifact(Path)
                
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        
        generation = op_in["generation"]
        opt_params_config = op_in["opt_params_config"][-1]
        
        hard_constrains = opt_params_config["operator"]["hard_constrains"] 
        tol_matrix = hard_constrains.pop("tol_matrix")
        min_dist, tol_matrix = tol_matrix_setup(tol_matrix, list(opt_params_config['operator']['generator']['random_gen_params']['composition'].keys()))
        opt_params_config['operator']['generator']['random_gen_params']['tol_matrix'] = tol_matrix
        
        
        # 产生结构operator
        operator_type = opt_params_config['operator'].pop('type')
        struc = struc_dict[operator_type](min_dist=min_dist, bounds=hard_constrains)
        struc.set_ea_params(opt_algo=opt_params_config)
       
        if generation > 1:
            shutil.copyfile(op_in['db'], 'generation.json')
        
        db = Path("./generation.json")
        dc = DataConnection(db_file_name=db)
        candidate_size = opt_params_config["generation"]['gen_size']
        
        candis = dc.get_candidates()
        # 随机创建初始结构
        if generation == 1:
            # seed结构
            # seed结构
            seed = opt_params_config['seeds']
            if seed is not None:
                current_dir = Path(seed)
                for entry in current_dir.iterdir():
                    if entry.is_file():
                        atoms = read(entry)
                        atoms = struc.gen_by_seeds(atoms)
                        add_candidate(atoms, generation, dc)

            # 创建结构
            while dc.get_number_of_candidates(generation=generation, stage=0) < candidate_size:
                size = candidate_size - dc.get_number_of_candidates(generation=generation, stage=0)
                pool = multiprocessing.Pool()
                results_list = []
                for _ in range(size):
                    result = pool.apply_async(create_generator, args=(struc, candis))
                    results_list.append(result)
                pool.close()
                pool.join()
                for r in results_list:
                    atoms = r.get()
                    if atoms is not None:
                        add_candidate(atoms, generation, dc)
                              
        else:  
            pop_list = dc.get_candidates(population=generation-1)
            population = Population(pop_list=pop_list)
            
            operator_prob = {}
            for k in operator_dict.keys():
                v = opt_params_config['operator'].get(k, None)
                if v is not None:
                    operator_prob[k] = v['prob']

            mutation_prob = {}
            for k in operator_dict['mutation']:
                v = opt_params_config['operator']['mutation'].get(k+"_prob", None)
                if v is not None:
                    mutation_prob[k] = v
          
            crossover_prob = {}
            for k in operator_dict['crossover']:
                v = opt_params_config['operator']['crossover'].get(k+"_prob", None)
                if v is not None:
                    crossover_prob[k] = v
          
            generator_prob = {}
            for k in operator_dict['generator']:
                v = opt_params_config['operator']['generator'].get(k+"_prob", None)
                if v is not None:
                    generator_prob[k] = v
           
            continuous_mut_factor = opt_params_config['operator']['mutation']["continuous_mut_factor"]

            while dc.get_number_of_candidates(generation=generation, stage=0) < candidate_size:
                size = candidate_size - dc.get_number_of_candidates(generation=generation, stage=0)
                parents = population.get_candidates(size=2)
                p_list = [struc.copy().from_atoms(atoms) for atoms in parents]

                results_list = []
                pool = multiprocessing.Pool()
                for i in range(size):
                    result = pool.apply_async(create_ea, args=(struc, candis, p_list, operator_prob, mutation_prob, generator_prob, crossover_prob, continuous_mut_factor))
                    results_list.append(result)
                pool.close()
                pool.join()
                for r in results_list:
                    atoms = r.get()
                    if atoms is not None:
                        add_candidate(atoms, generation, dc)
                
                # struc = struc_generator.gen_by_crossover(parents, "spherecross")
                # struc = struc_generator.gen_by_mutation(parents[0], "permutmut")
                # struc = struc_generator.gen_ea(parents, operator_prob, mutation_prob, generator_prob, crossover_prob, continuous_mut_factor)      
               
        # 返回文件目录
        op_out = OPIO(
            {
                "db": db,
                "min_dist_info": min_dist
            }
        )
        return op_out
