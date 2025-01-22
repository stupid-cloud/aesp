from aesp.func.database import DataConnection
from dflow import download_artifact
from pathlib import Path
import pandas as pd
import logging
import multiprocessing
from aesp.utils.plotly_graph import draw_ea, draw_diversity, draw_prob, draw_size, draw_con_mut_factor
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.ase import AseAtomsAdaptor
from aesp.constant import operator
import copy
import shutil
from aesp.operator import operator_dict
from pymatgen.io.gaussian import GaussianInput

pd.set_option('display.colheader_justify', 'center')  # 对齐方式
def process_generation(generation, dc, path, csp_path, relaxed_flag=False):
    unrelaxed = list(dc.db.select(generation=generation, stage=0))
    u_rst_list = []
    rst_list = []
    pop_list = []
    u_string = ""
    r_string = ""

    for u in unrelaxed:
        u_rst_list.append(
            [generation, u.s_id, u.spg_num, u.spg_sym, u.oper_type, u.oper_name, u.data.parents]
        )
        u_s = dc.get_atoms(u.id)
        if u_s.get_cell_lengths_and_angles()[0] != 0:
            u_s = AseAtomsAdaptor.get_structure(u_s)
            u_string += Poscar(u_s, comment=f"s_id-{u.s_id}").get_string() 
        else:
            u_s = AseAtomsAdaptor.get_molecule(u_s)
            u_string += GaussianInput(u_s, title=f"s_id-{u.s_id}").to_str()
        
        if relaxed_flag:
            
            max_stage = dc.get_max_stage(generation)
            relaxed = list(dc.db.select(generation=generation, stage=max_stage, s_id=u.s_id))
            
            if len(relaxed) > 0:
                r = relaxed[0]
        
                pop = r.data.get('pop_list', [])

                rst_list.append(
                    [generation, u.s_id, pop, u.spg_num, u.spg_sym, r.spg_num,
                    r.spg_sym, r.fitness, u.oper_type, u.oper_name, u.data.parents, r.calc_style]
                )
                
                r_s = dc.get_atoms(r.id)   
                if r_s.get_cell_lengths_and_angles()[0] != 0:
                    r_s = AseAtomsAdaptor.get_structure(r_s)
                    r_string += Poscar(r_s, comment=f"s_id-{r.s_id}").get_string() 
                else:
                    r_s = AseAtomsAdaptor.get_molecule(r_s)
                    r_string += GaussianInput(r_s, title=f"s_id-{r.s_id}").to_str(cart_coords=True)
                
                if pop != []:
                    for i in pop:
                        pop_list.append([i, r.s_id,  r.spg_num,
                    r.spg_sym, r.fitness, r.oper_type, r.oper_name, r.data.parents, r.calc_style])       

    file_path = path / 'unrelaxed'
    file_path.mkdir(parents=True, exist_ok=True)
    with open(file_path / f'g-{generation}', 'w') as file:
        file.write(u_string)
    
    u_data = pd.DataFrame(u_rst_list, columns=[
        "gen.", 's_id', 'spg_num', 'spg_sym', 'oper_type','oper_name', "parents"
        ])
    u_data.to_csv(csp_path / "gen_init_{}.csv".format(generation), index=False)

    if relaxed_flag:
        data = pd.DataFrame(rst_list, columns=[
            "gen.", 's_id', 'pop.', 'spg_num_init', 'spg_sym_init', 
            'spg_num_opt', 'spg_sym_opt', 'fitness', 
            'oper_type', 'oper_name', "parents", "calc_style"
            ])
        data.to_csv(csp_path / "gen_{}.csv".format(generation), index=False)

        pop_data = pd.DataFrame(
            pop_list, columns=['gen.', 's_id', 'spg_num', 'spg_sym', 'fitness', 
            'oper_type', 'oper_name', "parents", "calc_style"]
        )
        pop_data.to_csv(csp_path / "pop_{}.csv".format(generation), index=False)
        
        file_path = path / 'relaxed'
        file_path.mkdir(parents=True, exist_ok=True)
        with open(file_path / f'g-{generation}', 'w') as file:
            file.write(r_string)
        logging.info(f"{generation}处理完成")

def _get_init_info(dc, path, relaxed_flag=False):
  # 常规数据
    max_generation = dc.get_max_generation() 
    
    csp_path = path / 'summary'
    csp_path.mkdir(parents=True, exist_ok=True)

    pool = multiprocessing.Pool()
    
    for generation in range(1, max_generation+1):
        # process_generation(generation, dc, path, csp_path, relaxed_flag)
        pool.apply_async(process_generation, args=(generation, dc, path, csp_path, relaxed_flag))
    pool.close()
    pool.join()

    data_list = []
    
    for generation in range(1, max_generation+1):
        path = csp_path.joinpath('gen_{}.csv'.format(generation))
        data = pd.read_csv(path)
        data_list.append(data)
        path.unlink()
    gen_data = pd.concat(data_list, axis=0, ignore_index=True)
    gen_data.to_csv(csp_path / "gen.csv".format(generation), index=False)
    new_data = gen_data.sort_values(by='fitness')
    new_data.to_csv(csp_path / "gen_sorted.csv".format(generation), index=False)

    data_list = []
    for generation in range(1, max_generation+1):
        path = csp_path.joinpath('gen_init_{}.csv'.format(generation))
        data = pd.read_csv(path)
        data_list.append(data)
        path.unlink()
    merged_df = pd.concat(data_list, axis=0, ignore_index=True)
    merged_df.to_csv(csp_path / "gen_init.csv".format(generation), index=False)

    data_list = []
    for generation in range(1, max_generation+1):
        path = csp_path.joinpath('pop_{}.csv'.format(generation))
        data = pd.read_csv(path)
        data_list.append(data)
        path.unlink()
    pop_data = pd.concat(data_list, axis=0, ignore_index=True)
    pop_data.to_csv(csp_path / "pop.csv".format(generation), index=False)
    new_data = pop_data.sort_values(by='fitness')
    new_data.to_csv(csp_path / "pop_sorted.csv".format(generation), index=False)
    return gen_data, pop_data

# -----------------------------------------------
def analysis(step_list, init_flag, dp_train, path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    csp_analysis(step_list, path, init_flag)
    if dp_train:
        dp_train_csp(step_list, path)


def csp_analysis(step_list, path, init_flag):
    temp_step_list = []
    for step in step_list:
        if ("gen-struc" in step.key or "scheduler-gen" in step.key) and step.phase == 'Succeeded':
            temp_step_list.append(step)
    if len(temp_step_list) <= 0:
        return
    temp_step_list.sort(key=lambda k: k.startedAt)

    if init_flag:
        step = temp_step_list[-1]
        db = step.outputs.artifacts['db']
        db = download_artifact(db, path=path)[0]
        dc = DataConnection(db_file_name=db)
        _get_init_info(dc, path)
        return
 
    c_step_list = []
    for step in temp_step_list:
        if "scheduler-gen" in step.key:
            c_step_list.append(step)
    if len(c_step_list) <= 0:
        return

    scheduler = c_step_list[-1]
    db = scheduler.outputs.artifacts['db']
    db = download_artifact(db, path=path)[0]
    dc = DataConnection(db_file_name=db)

    data, pop_data = _get_init_info(dc, path, relaxed_flag=True)

    # 进化信息
    gen_info_dict = {'operator': [[], []], 'single_mut': [[], []], 'continuous_mut': [[], []]}
    for k, v in operator.items():
        gen_info_dict[k] = [[], []]
        for i in v:
            gen_info_dict[i] = [[], []]
            if k =='mutation':
                gen_info_dict[i+"_r"] = [[], []]
    pop_info_dict = copy.deepcopy(gen_info_dict)
    print(gen_info_dict)
    # print(scheduler.outputs.parameters['info'].value)
    for t, d in zip(['gen_energy', 'pop_energy'], [gen_info_dict, pop_info_dict]):
        for idx, i in enumerate(scheduler.outputs.parameters['info'].value[t]):
            for k, v in i.items():
                if k in d.keys(): 
                    d[k][0].append(idx+1)
                    d[k][1].append(v)
    html_path = path / "html"
    html_path.mkdir(parents=True, exist_ok=True)
    print(gen_info_dict)
    draw_ea(data, gen_info_dict, html_path, 'generation') # generation
    draw_ea(pop_data, pop_info_dict, html_path, 'population') # population

    # 多样性
    diversity_info = [
        [ 
        i + 1,
        scheduler.outputs.parameters['info'].value['gen_diversity'][i],
        scheduler.outputs.parameters['info'].value['pop_diversity'][i]
        ]
        for i in range(len(scheduler.outputs.parameters['info'].value['gen_diversity']))
    ]

    diversity_info = pd.DataFrame(diversity_info, columns=["gen. or pop.", "gen_diversity", "pop_diversity"])
    diversity_info.to_csv(html_path / "diversity.csv", index=False)
    draw_diversity(diversity_info, html_path)

    # 参数变化趋势
    size_info = []
    operator_info = {}
    generator_info = {}
    mutation_info = {}
    crossover_info = {}
    continuos_mut_factor = []
    # print(scheduler.outputs.parameters['opt_params_config'].value)
    x_index = []
    for idx, d in enumerate(scheduler.outputs.parameters['opt_params_config'].value[:-1]):
        size_info.append([idx+1, d['generation']['gen_size'], d['population']['pop_size']])        
        continuos_mut_factor.append(d['operator']['mutation']['continuous_mut_factor'])
        for k in operator_dict.keys():
            v = d['operator'].get(k, None)
            if v is not None:
                if idx == 0:
                    operator_info[k] = [v['prob']]
                else:
                    operator_info[k].append(v['prob'])
        for k in operator_dict['mutation']:
            v = d['operator']['mutation'].get(k+"_prob", None)
            if v is not None:
                if idx == 0:
                    mutation_info[k] = [v]
                else:
                    mutation_info[k].append(v)
        for k in operator_dict['crossover']:
            v = d['operator']['crossover'].get(k+"_prob", None)
            if v is not None:
                if idx == 0:
                    crossover_info[k] = [v]
                else:
                    crossover_info[k].append(v)

        for k in operator_dict['generator']:
            v = d['operator']['generator'].get(k+"_prob", None)
            if v is not None:
                if idx == 0:
                    generator_info[k] = [v]
                else:
                    generator_info[k].append(v)
       
        x_index.append(idx+1)
    parm_path = html_path / 'params'
    parm_path.mkdir(parents=True, exist_ok=True)

    size_info = pd.DataFrame(size_info, columns=["gen. or pop.", "generation", "population"])
    size_info.to_csv(parm_path / "size.csv", index=False)

    draw_size(size_info, parm_path)
    draw_con_mut_factor(x_index, continuos_mut_factor, parm_path)
    draw_prob(x_index, operator_info, parm_path, key="operator")
    draw_prob(x_index, generator_info, parm_path, key="generator")
    draw_prob(x_index, mutation_info, parm_path, key="mutation")
    draw_prob(x_index, crossover_info, parm_path, key="crossover")



def dp_train_csp(step_list, path):
    temp_step_list = []
    for step in step_list:
        if "select-confs" in step.key:
            temp_step_list.append(step)
    temp_step_list.sort(key=lambda k: k.startedAt)
    rst_list = []
    for step in temp_step_list:
        report = step.outputs.parameters['report'].value

        failed_ratio = report.failed_ratio()
        accurate_ratio = report.accurate_ratio()
        candidate_ratio = report.candidate_ratio()
        converged = report.converged()
        g_s = step.key.split('--')[1].split('-')
        g = g_s[0][-1]
        s = g_s[1][-1]
        rst_list.append([g, s, accurate_ratio, failed_ratio, candidate_ratio, converged])

    data = pd.DataFrame(rst_list, columns=["gene.", 'stage', 'accu.', 'cand.', 'fail.', 'conv.'])
    data.to_csv(path / "dp-train.csv", index=False) 