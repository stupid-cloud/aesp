from dflow.python import OP, OPIO, OPIOSign, Artifact, BigParameter
from pathlib import Path
from aesp.func.database import DataConnection
from pathlib import Path
import shutil
from aesp.func.population import Population
import copy
from typing import List
import dpdata
import json
import multiprocessing
import numpy as np
from aesp.structure import struc_type

operator = {
    'generator': ['random_gen'],
    "mutation": ["strain_mut", "permutation_mut", "ripple_mut"],
	"crossover": ["plane_cross", 'cylinder_cross', 'sphere_cross']
}

lock = multiprocessing.Lock()
def add_struc(file_path, dc):
    ls = dpdata.LabeledSystem().from_deepmd_npy(file_path / "data")
    struc = ls[-1].to_ase_structure()[0]
    with open(file_path / "data/info.json", "r") as f:
        info = json.load(f)   
    struc = struc_type[info['struc_type']]().from_atoms(struc)        
    info.update(struc.get_spg_info())
    if info['struc_type'] != "bluk":
        info['data']['U'] = float(ls['energies'][-1])
        info['data']['H'] = info['data']['U']
        info['data']['H/atom'] = info['data']['H'] / len(struc)
        info['fitness'] = info['data']['H/atom']
        info['data']["fp"] = struc.calc_fp_describe()
    else:
        volume = struc.get_volume()
        pstress = info['pstress']
        info['data']['U'] = float(ls['energies'][-1])
        info['data']['PV'] = volume * pstress / 1602.1766208
        info['data']['H'] = info['data']['U'] + info['data']['PV']
        info['data']['H/atom'] = info['data']['H'] / len(struc)
        info['fitness'] = info['data']['H/atom']
        info['data']["fp"] = struc.calc_fp_describe()

    struc.info = info
    # 去除重复的结构
    try:
        lock.acquire()
        candis = dc.get_candidates(selection="{}<fitness<{}".format(info['fitness']-0.01, info['fitness']+0.01))
    finally:
        lock.release()
    for candi in candis:
        if struc.looks_like(candi, simi_thres=0.99):
            return 
    try:
        lock.acquire()
        dc.add_relaxed_stage(struc) 
    finally:
        lock.release()


class SchedulerStage(OP):
    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "scheduler": BigParameter(object),
                "report": BigParameter(object, default=None),
                "labeled_data": Artifact(Path),
                "db": Artifact(Path) 
            }
        )

    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "stage": int,
                "scheduler": BigParameter(object),
                "s_converged": bool,
                "db": Artifact(Path)
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        # 根据创建的结构准备提交计算的文件
        folders = [item for item in op_in["labeled_data"].iterdir() if item.is_dir() and not item.name.startswith('.')]
        
        shutil.copyfile(op_in['db'], "generation.json")
        db = Path("generation.json")
        dc = DataConnection(db_file_name=db)
        
        pool = multiprocessing.Pool()

        for file_path in folders:
            pool.apply_async(func=add_struc, args=(file_path, dc))
        pool.close()
        pool.join()

        scheduler = op_in["scheduler"]     
        stage_complete=True
        if op_in['report'] is not None:
            stage_complete = op_in['report'].converged(op_in['report'])
        scheduler.next_stage(stage_complete=stage_complete)

        # 返回文件目录
        op_out = OPIO(
            {
                "stage": scheduler.stage,
                "scheduler": scheduler,
                "s_converged": scheduler.s_converged,
                "db": db
            }
        )
        return op_out
    

class SchedulerGen(OP):
    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "scheduler": BigParameter(object),
                "db": Artifact(Path),
                "opt_params_config": List[dict],
                'generation': int,
                "info": dict
            }
        )

    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "generation": int,
                "scheduler": BigParameter(object),
                "g_converged": bool,
                "opt_params_config": List[dict],
                "info": dict,
                "db": Artifact(Path)
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        
        # 根据创建的结构准备提交计算的文件
        scheduler = op_in["scheduler"]
        opt_params_config_list = copy.deepcopy(op_in['opt_params_config'])
        opt_params_config = op_in['opt_params_config'][-1]
        shutil.copyfile(op_in['db'], "generation.json")
        db = Path("generation.json")
        # db = op_in['db']
        dc = DataConnection(db_file_name=db)  

        max_stage = dc.get_max_stage(op_in['generation'])
         # 数量检测
        num = dc.get_number_of_candidates(generation=op_in['generation'], stage=max_stage)
        if num < 2:
            raise ValueError("每代个数小于2")

        # 1.更新population
        dc.update_population(
            op_in['generation'], 
            opt_params_config['population']["pop_size"]
        )
        info = op_in['info']

        if len(info) == 0:
            pop_diversity_info, gen_diversity_info, pop_e_info, gen_e_info = [], [], [], []
        else:
            gen_e_info, pop_e_info, pop_diversity_info, gen_diversity_info = info["gen_energy"], info["pop_energy"], info["pop_diversity"], info["gen_diversity"]

        # 2.多样性
        # 计算generation多样性
        diversity = dc.get_diversity(generation=op_in['generation'], stage=max_stage)
        gen_diversity_info.append(diversity)
        # 计算种群多样性
        diversity = dc.get_diversity(population=op_in['generation'])
        pop_diversity_info.append(diversity)
        
        # 3.获得平均能量
        def update_mut(e_dict):
            """连续变异更新"""
            mut_dict = {}
            temp_e_dict = copy.deepcopy(e_dict)
            for k, v in temp_e_dict.items():
                if '_mut' in k: 
                    new_k = k.split('->')
                    if len(new_k) > 1:
                        if e_dict.get('continuous_mut'):
                            e_dict['continuous_mut'] = (e_dict['continuous_mut']+v) / 2
                        else:
                            e_dict['continuous_mut'] = v
                    else:
                        if e_dict.get('single_mut'):
                            e_dict['single_mut'] = (e_dict['single_mut']+v) / 2
                        else:
                            e_dict['single_mut'] = v
                      
                    for k in new_k:
                        if mut_dict.get(k+'_r'):
                            mut_dict[k+'_r'].append(v)
                        else:
                            mut_dict[k+'_r'] = [v]
            for k, v in mut_dict.items():
                e_dict[k] = sum(v) / len(v)
            return e_dict
            
        # generation
        e_dict = dc.get_energy_base_operator(oper_type_list=list(operator.keys()), generation=op_in['generation'], stage=max_stage)      
        e_dict = update_mut(e_dict)

        gen_e_info.append(e_dict)
        # print(e_dict)
        # population
        e_dict = dc.get_energy_base_operator(oper_type_list=list(operator.keys()), population=op_in['generation'])
        e_dict = update_mut(e_dict)
        pop_e_info.append(e_dict)

        info = {
            "gen_energy": gen_e_info, "gen_diversity": gen_diversity_info, 
            "pop_energy": pop_e_info, "pop_diversity": pop_diversity_info
        }

        # 4.自适应
        if op_in['generation'] >= 2:
            # 不同操作下的平均能量
  
            # 使用的generation
            use_recent_gen = opt_params_config['operator']['adaptive']['use_recent_gen']
            generation_list = [i for i in range(max(op_in['generation']-use_recent_gen, 0), op_in['generation'])]
            adaptive_type = opt_params_config['operator']['adaptive']['type']
            
            def get_mean(keys):
                "获取多代的平均值"
                tem_e_dict = {key: [] for key in keys}
                for i in generation_list:
                    for key in keys:
                        if gen_e_info[i].get(key):
                            tem_e_dict[key].append(gen_e_info[i][key])

                # 求平均值
                for k, v in tem_e_dict.items():
                    tem_e_dict[k] = sum(v) / len(v)
                return tem_e_dict
            
            def get_chg_ratio(tem_e_dict, factor):
                change_ratio_dict = {}
                for k, v in tem_e_dict.items():
                    mean_value = v-np.mean(list(tem_e_dict.values()))
                    sum_value = np.sum(np.abs(list(tem_e_dict.values())))
                    chg_prob = float(mean_value/sum_value)
                    change_ratio_dict[k] = chg_prob
                
                if np.abs(list(change_ratio_dict.values())).sum() == 0:
                    return change_ratio_dict
                # 绝对值总和归一化
                chg_ratio_dict = {}
                for k, v in change_ratio_dict.items():
                    chg_ratio_dict[k] = float(factor*v/np.sum(np.abs(list(change_ratio_dict.values()))))
                return chg_ratio_dict
            
            def get_chgnum(tem_e_dict, prob):
                chg_num_list = []
                for k, v in tem_e_dict.items():
                    chg_flag = v - np.mean(list(tem_e_dict.values()))
                    if chg_flag > 0:
                        chg_num_list.append(abs(prob[k]-0))
                    else:
                        chg_num_list.append(abs(prob[k]-1))
                chg_num = min(chg_num_list)
                return chg_num
    
            # operator
            # 获取key
            keys = set()
            for i in generation_list:
                o_keys = list(operator.keys())
                o_keys.remove('generator') # generator不变
                
                tem_keys = set(gen_e_info[i].keys()).intersection(set(o_keys))
                keys = keys.union(tem_keys)

            if len(keys) != 0:
                # 获得平均值
                tem_e_dict = get_mean(keys)

                if adaptive_type == "distribution":
                    total_prob = sum([opt_params_config['operator'][k]["prob"] for k in tem_e_dict.keys()])
                    for k, v in tem_e_dict.items():
                        opt_params_config['operator'][k]["prob"] = total_prob*v/sum(tem_e_dict.values())  
                    # 按照能量增减
                elif adaptive_type == "adjustment": 
                    factor = opt_params_config['operator']['adaptive']['factor']
                    chg_ratio_dict = get_chg_ratio(tem_e_dict, factor) 
                    prob_dict = {k: opt_params_config['operator'][k]["prob"] for k in tem_e_dict.keys()} 
                    chg_num = get_chgnum(tem_e_dict, prob_dict)
                    for k, v in tem_e_dict.items():    
                        opt_params_config['operator'][k]["prob"] -= chg_ratio_dict[k] * chg_num
            
            # generator和crossover, mutation
            # 获取key
            for t in ['generator', 'crossover', 'mutation']:
                keys = set()
                for i in generation_list:
                    if gen_e_info[i].get(t, False):
                        if t == 'mutation':
                            o_set = {i+'_r' for i in operator[t]} # mutation 为修正后的
                            tem_keys = set(gen_e_info[i].keys()).intersection(o_set)
                        else:  
                            tem_keys = set(gen_e_info[i].keys()).intersection(set(operator[t]))
                        keys = keys.union(tem_keys)
                if len(keys) == 0:
                    continue

                # 获得平均值
                tem_e_dict = get_mean(keys) 
                if adaptive_type == "distribution":
                    if t == 'mutation':
                        total_prob = sum([opt_params_config['operator'][t][k.rsplit('_r', 1)[0]+"_prob"] for k in tem_e_dict.keys()])
                        for k, v in tem_e_dict.items():
                            opt_params_config['operator'][t][k.rsplit('_r', 1)[0]+"_prob"] = total_prob*v/sum(tem_e_dict.values())
                    else:
                        total_prob = sum([opt_params_config['operator'][t][k+"_prob"] for k in tem_e_dict.keys()])
                        for k, v in tem_e_dict.items():
                            opt_params_config['operator'][t][k+"_prob"] =  total_prob *v / sum(tem_e_dict.values())     
                # 按照能量增减
                elif adaptive_type == "adjustment": 
                    factor = opt_params_config['operator']['adaptive']['factor']
                    chg_ratio_dict = get_chg_ratio(tem_e_dict, factor) 

                    if t == 'mutation':
                        prob_dict = {k: opt_params_config['operator'][t][k.rsplit('_r', 1)[0]+"_prob"] for k in tem_e_dict.keys()} 
                        chg_num = get_chgnum(tem_e_dict, prob_dict)
                        for k, v in tem_e_dict.items():
                            opt_params_config['operator'][t][k.rsplit('_r', 1)[0]+"_prob"] -= chg_ratio_dict[k] * chg_num
                    else:     
                        prob_dict = {k: opt_params_config['operator'][t][k+"_prob"] for k in tem_e_dict.keys()} 
                        chg_num = get_chgnum(tem_e_dict, prob_dict)   
    
                        for k, v in tem_e_dict.items():
                            opt_params_config['operator'][t][k+"_prob"] -= chg_ratio_dict[k] * chg_num
            # 连续变异    
            keys = set()
            for i in generation_list:
                tem_keys = set(gen_e_info[i].keys()).intersection({'single_mut', 'continuous_mut'})
                keys = keys.union(tem_keys)
            
            if len(keys) == 2:
                # 获得平均值
                tem_e_dict = get_mean(keys)

                # 修改概率
                # 按照能量分配
                if adaptive_type == "distribution":
                    total_prob = 4
                    for k, v in tem_e_dict.items(): 
                        if k == 'continuous_mut':
                            opt_params_config['operator']['mutation']["continuous_mut_factor"] = total_prob*v/sum(tem_e_dict.values())  
                # 按照能量增减
                elif adaptive_type == "adjustment":  
                    factor = opt_params_config['operator']['adaptive']['factor']
                    chg_ratio_dict = get_chg_ratio(tem_e_dict, factor) 
                    if tem_e_dict['continuous_mut'] - np.mean(list(tem_e_dict.values())) < 0:
                        chg_num = abs(opt_params_config['operator']['mutation']["continuous_mut_factor"]-4)
                    else:
                        chg_num = abs(opt_params_config['operator']['mutation']["continuous_mut_factor"]-0)                
                    opt_params_config['operator']['mutation']["continuous_mut_factor"] -= chg_ratio_dict['continuous_mut'] * chg_num

        # generation和population修改
        if op_in['generation'] >= 3:
            def get_chg_num(init_size, chg_ratio, current_size, e_info):
                c_chg_num = int(init_size * chg_ratio)
                min_size = init_size - c_chg_num
                max_size = init_size + c_chg_num
                # gen
                e_list = []
                for e in e_info:
                    e_list.append(e['operator'])
                diff = [abs(e_list[i]-e_list[i - 1]) for i in range(1, len(e_list))]
                mean_diff = np.mean(diff)
                if diff[-1] < mean_diff:
                    num = min_size
                else:
                    num = max_size
                chg_num = abs(current_size - num)
                chg_num = int(chg_num * (diff[-1] - mean_diff) / max(diff))
                return chg_num
        
            init_size = opt_params_config_list[0]['generation']['gen_size']
            chg_ratio = opt_params_config['generation']['adaptive']['size_change_ratio']
            current_size = opt_params_config['generation']['gen_size']
            chg_num = get_chg_num(init_size, chg_ratio, current_size, gen_e_info)
            opt_params_config['generation']['gen_size'] += chg_num

            init_size = opt_params_config_list[0]['population']['pop_size']
            chg_ratio = opt_params_config['population']['adaptive']['size_change_ratio']
            current_size = opt_params_config['population']['pop_size']
            chg_num = get_chg_num(init_size, chg_ratio, current_size, pop_e_info)
            opt_params_config['population']['pop_size'] += chg_num

        
        # 5.generation收敛判断
        gen_complete = False
        cvg_criterion = opt_params_config['cvg_criterion']
        if cvg_criterion['continuous_opt_num'] is not None:
            continuous_opt_num = dc.get_max_continuous_opt_num(op_in['generation']) # 连续最优次数
            if continuous_opt_num >= cvg_criterion['continuous_opt_num']:
                gen_complete = True
        scheduler.next_generation(gen_complete)
        opt_params_config_list.append(opt_params_config)
        # 返回文件目录
        op_out = OPIO(
            {
                "generation": scheduler.generation,   
                "scheduler": scheduler,
                "g_converged": scheduler.g_converged,
                "opt_params_config": opt_params_config_list,
                "info": info,
                "db": db
            }
        )
        return op_out

def min_distance_to_boundaries(value, lower_bound, upper_bound):
    distance_to_lower = abs(value - lower_bound)
    distance_to_upper = abs(value - upper_bound)
    return min(distance_to_lower, distance_to_upper)

def get_max_change_prob(value, bound):
    return abs(value - bound)
