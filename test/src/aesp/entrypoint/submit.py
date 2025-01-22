from dflow import upload_artifact, Step, Workflow
from aesp.workflow.superop.csp_block import STCSPBlock, DPCSPBlock
from aesp.workflow.superop.calc_block import FPRelaxBlock, DPCalcBlock, STCalcBlock
from aesp.workflow.superop.csp_so import DPCSP, STCSP
from aesp.workflow.superop.prep_run_dp_so import PrepRunDP
from aesp.workflow.superop.prep_run_calc_so import PrepRunCalc
from dpgen2.exploration.render import TrajRenderLammps
from dpgen2.exploration.report import conv_styles
from dpgen2.exploration.selector import ConfSelectorFrames
from dpgen2.utils import get_artifact_from_uri, upload_artifact_and_print_uri
from pathlib import Path
from aesp.calculator import calc_styles
from aesp.func.scheduler import STScheduler, DPScheduler
from aesp.constant import stand_csp_mode, dp_csp_mode
from dpgen2.entrypoint.submit import (
    get_artifact_from_uri, upload_artifact_and_print_uri, get_systems_from_data,
    make_optional_parameter
)
import json
import logging


def submit_csp(
        wf_config,
        mode,
        reuse_step=None
    ):

    if mode == "std-sp":
        logging.info('Structure prediction (Standard)')
        dlcsp_step = workflow_stcsp(wf_config)
    elif mode == "al-sp":
        logging.info('Structure prediction (AL+MLP)')
        dlcsp_step = workflow_dpcsp(wf_config)
    else:
        return

    wf = Workflow(name=mode, parallelism=wf_config.pop("parallelism"))
    wf.add(dlcsp_step)
    wf.submit(reuse_step=reuse_step)

def workflow_dpcsp(wf_config):
    wf_config = wf_config['aesp_config']
    opt_params_config = wf_config['opt_params']
    fp_relax_config = wf_config['calc_stages']['fp_relax']
    if fp_relax_config is not None:
        fp_relax_gen_num = fp_relax_config.pop("gen_num")
    else:
        fp_relax_gen_num = 0
    fp_static_config = wf_config['calc_stages']['fp_static']
    dp_relax_config = wf_config['calc_stages']['dp_relax']
    fp_shield_config = wf_config['calc_stages']['fp_shield']  # config空则为None
    dp_style = wf_config['calc_stages']['dp_train']['type']
    dp_train_config = wf_config['calc_stages']['dp_train']["config"]

    # step config
    prep_fp_relax_step_config = wf_config["step_configs"]['prep_fp_relax_step']
    run_fp_relax_step_config = wf_config["step_configs"]["run_fp_relax_step"]
    prep_fp_static_step_config = wf_config["step_configs"]['prep_fp_static_step']
    run_fp_static_step_config = wf_config["step_configs"]["run_fp_static_step"]
    prep_dp_relax_step_config = wf_config["step_configs"]['prep_dp_relax_step']
    run_dp_relax_step_config = wf_config["step_configs"]["run_dp_relax_step"]
    prep_fp_shield_step_config = wf_config["step_configs"]['prep_fp_shield_step']
    run_fp_shield_step_config = wf_config["step_configs"]["run_fp_shield_step"]
    prep_dp_train_step_config = wf_config["step_configs"]["prep_dp_train_step"]
    run_dp_train_step_config = wf_config["step_configs"]["run_dp_train_step"]

    gen_struc_step_config = wf_config["step_configs"]['gen_struc_step']
    scheduler_step_config = wf_config["step_configs"]["scheduler_step"]
    select_confs_step_config = wf_config["step_configs"]["select_confs_step"]
    collect_data_step_config = wf_config["step_configs"]["collect_data_step"]
    calc_model_devi_step_config = wf_config["step_configs"]["calc_model_devi_step"]

    type_map = list(opt_params_config['operator']['generator']["random_gen_params"]["composition"].keys())
    
    # calc_config初始化
    temp_config_list = [fp_static_config, dp_relax_config]
    if fp_shield_config is not None:
        temp_config_list.append(fp_shield_config)
    if fp_relax_config is not None:
        temp_config_list.append(fp_relax_config)

    for config in temp_config_list:
        config.update({'type_map': type_map})
        calc_inputs_config = config.pop("inputs_config")
        calc_style = config["type"]
        if calc_style not in ["matgl", 'ase']:
            calc_inputs_config.pop('pstress')
        calc_inputs = calc_styles[calc_style]['inputs'](**calc_inputs_config)
        config['inputs'] = calc_inputs

    # dp-train初始化
    if dp_style == "dp":
        init_models_paths = wf_config['calc_stages']['dp_train'].get("init_models_paths", None)
        numb_models = wf_config['calc_stages']['dp_train']["numb_models"]
        if init_models_paths is not None and len(init_models_paths) != numb_models:
            raise RuntimeError(
                f"{len(init_models_paths)} init models provided, which does "
                "not match numb_models={numb_models}"
            )
    elif dp_style == "dp-dist":
        init_models_paths = (
            [wf_config['calc_stages']['dp_train']["student_model_path"]]
            if "student_model_path" in wf_config['train_stages']['dp_train']
            else None
        )
        wf_config['calc_stages']['dp_train']["numb_models"] = 1
    else:
        raise RuntimeError(f"unknown params, train_style: {dp_style}")
    
    valid_data = wf_config['calc_stages']['dp_train_inputs']["valid_data_sys"]
    if wf_config['calc_stages']['dp_train_inputs']["valid_data_uri"] is not None:
        valid_data = get_artifact_from_uri(config["inputs"]["valid_data_uri"])
    elif valid_data is not None:
        valid_data_prefix = wf_config['calc_stages']['dp_train_inputs']["valid_data_prefix"]
        valid_data = get_systems_from_data(valid_data, valid_data_prefix)
        valid_data = upload_artifact_and_print_uri(valid_data, "valid_data")

    numb_models = wf_config['calc_stages']['dp_train']["numb_models"]
    template_script_ = wf_config['calc_stages']['dp_train']["template_script"]
    if isinstance(template_script_, list):
        template_script = [json.loads(Path(ii).read_text()) for ii in template_script_]
    else:
        template_script = json.loads(Path(template_script_).read_text())
        

    multitask = wf_config['calc_stages']['dp_train_inputs']["multitask"]
    if multitask:
        head = wf_config['calc_stages']['dp_train_inputs']["head"]
        if wf_config['calc_stages']['dp_train_inputs']["multi_init_data_uri"] is not None:
            init_data = get_artifact_from_uri(wf_config['calc_stages']['dp_train_inputs']["multi_init_data_uri"])
        else:
            multi_init_data = wf_config['calc_stages']['dp_train_inputs']["multi_init_data"]
            init_data = {}
            for k, v in multi_init_data.items():
                sys = v["sys"]
                sys = get_systems_from_data(sys, v.get("prefix", None))
                init_data[k] = sys
            init_data = upload_artifact_and_print_uri(init_data, "multi_init_data")
        dp_train_config["multitask"] = True
        dp_train_config["head"] = head
    else:
        if wf_config['calc_stages']['dp_train_inputs']["init_data_uri"] is not None:
            init_data = get_artifact_from_uri(wf_config['calc_stages']['dp_train_inputs']["init_data_uri"])
        else:
            init_data_prefix = wf_config['calc_stages']['dp_train_inputs']["init_data_prefix"]
            init_data = wf_config['calc_stages']['dp_train_inputs']["init_data_sys"]
            init_data = get_systems_from_data(init_data, init_data_prefix)
            init_data = upload_artifact_and_print_uri(init_data, "init_data")
    iter_data = upload_artifact([])

    dp_optional_files = wf_config['calc_stages']['dp_train'].get("optional_files", None)

    if dp_style == "dp" and wf_config['calc_stages']['dp_train']["init_models_uri"] is not None:
        init_models = get_artifact_from_uri(wf_config['calc_stages']['dp_train']["init_models_uri"])
    elif dp_style == "dp-dist" and wf_config['calc_stages']['dp_train']["student_model_uri"] is not None:
        init_models = get_artifact_from_uri(wf_config['calc_stages']['dp_train']["student_model_uri"])
    elif init_models_paths is not None:
        init_models = upload_artifact_and_print_uri(init_models_paths, "init_models")
    else:
        init_models = None

    optional_parameter = make_optional_parameter(
        wf_config['calc_stages']['dp_train_inputs']["mixed_type"],
    )

    if wf_config['calc_stages']['dp_train_inputs'].get("do_finetune", False):
        if dp_train_config["init_model_policy"] != "yes":
            logging.warning("In finetune mode, init_model_policy is forced to be 'yes'")
            dp_train_config["init_model_policy"] = "yes"
        optional_parameter = make_optional_parameter(
            config["inputs"]["mixed_type"],
            finetune_mode="finetune",
        )

    # scheduer--------------
    max_stage_iter = wf_config['calc_stages']["stage_stop_cond"]["max_stage_iter"]
    fatal_at_max = wf_config['calc_stages']["stage_stop_cond"]["fatal_at_max"]
    fp_task_max = 1  # ================
    convergence = wf_config['calc_stages']["stage_stop_cond"]["convergence"]
    
    # report
    conv_style = convergence.pop("type")
    report = conv_styles[conv_style](**convergence)
    render = TrajRenderLammps(nopbc=False)
    # selector
    selector = ConfSelectorFrames(
        render,
        report,
        fp_task_max,
    )
    scheduler = DPScheduler(
        max_generation=opt_params_config['cvg_criterion']['max_gen_num'],
        max_stage=max_stage_iter,
        fatal_at_max=fatal_at_max
        )
    # scheduer--------------

    opt_params_config.update({'type_map': type_map})

    # 计算任务
    dp_relax = PrepRunCalc(prep_dp_relax_step_config, run_dp_relax_step_config, "dp-relax")
    fp_static = PrepRunCalc(prep_fp_static_step_config, run_fp_static_step_config, "fp-static")
    
    if fp_relax_config is not None and fp_relax_gen_num > 0:
        fp_relax = PrepRunCalc(prep_fp_relax_step_config, run_fp_relax_step_config, "fp-relax")
    else:
        fp_relax = None
    if fp_shield_config is not None:
        fp_shield = PrepRunCalc(prep_fp_shield_step_config, run_fp_shield_step_config, "fp-shield")
    else:
        fp_shield = None

    dp_train = PrepRunDP(
        "prep-run-dp",
        prep_config=prep_dp_train_step_config,
        run_config=run_dp_train_step_config,
        optional_files=dp_optional_files,
        valid_data=valid_data
    )
    if fp_relax is not None:
        fp_relax_block = FPRelaxBlock(
            fp_relax,
            fp_relax_gen_num,
            gen_struc_step_config,
            scheduler_step_config,
            collect_data_step_config
        )
    else:
        fp_relax_block = None
    calc_block = DPCalcBlock(
        dp_relax,  
        fp_static,
        dp_train,
        scheduler_step_config,
        select_confs_step_config,
        collect_data_step_config,
        calc_model_devi_step_config
        )
    csp_block = DPCSPBlock(
        calc_block,
        fp_shield,
        scheduler_step_config,
        gen_struc_step_config,
        collect_data_step_config
    )
    dpcsp_step = DPCSP(
        fp_relax_block,
        dp_train,
        csp_block,
        scheduler_step_config,
        gen_struc_step_config,
        collect_data_step_config
    )
   
    csp_step = Step(
            name=dp_csp_mode,
            template=dpcsp_step,
            parameters={ 
                "generation": scheduler.generation,
                "stage": scheduler.stage,
                'scheduler': scheduler,
                "opt_params_config": [opt_params_config],
                "fp_relax_config": [fp_relax_config],
                "dp_relax_config": [dp_relax_config]*max_stage_iter,
                "fp_static_config": [fp_static_config]*max_stage_iter,
                "fp_shield_config": [fp_shield_config]*(max_stage_iter+1),
                "dp_train_config": dp_train_config,
                "template_script": template_script,
                "numb_models": numb_models,
                "conf_selector": selector,
                "type_map": type_map,
                "optional_parameter": optional_parameter
            },
            artifacts={
                "init_models": init_models,
                "iter_data": iter_data,
                "init_data": init_data
            }
        )
    return csp_step


def workflow_stcsp(wf_config):
    # config
    wf_config = wf_config['aesp_config']
    opt_params_config = wf_config['opt_params']
    calc_config = wf_config['calc_stages']
   
    prep_calc_step_config = wf_config["step_configs"]['prep_calc_step']
    gen_struc_step_config = wf_config["step_configs"]['gen_struc_step']
    
    run_calc_step_config = wf_config["step_configs"]["run_calc_step"]
    
    scheduler_step_config = wf_config["step_configs"]["scheduler_step"]
    # scheduler
    # type_map = list(opt_params_config['operator']['generator']["random_gen_params"]["composition"].keys())
    scheduler = STScheduler(opt_params_config['cvg_criterion']['max_gen_num'], len(calc_config))
    # opt_params_config.update({'type_map': type_map})
    
    #---
    if opt_params_config['seeds'] is not None:
        opt_params_config['seeds'] = Path(opt_params_config['seeds']).absolute()
    # calc_config初始化
    for config in calc_config:
        # config.update({'type_map': type_map})
        calc_inputs_config = config.pop("inputs_config")
        calc_style = config["type"]
        if calc_style in ["matgl", 'dpmd']:
            calc_inputs_config.update({'pstress': config['pstress']})
        calc_inputs = calc_styles[calc_style]['inputs'](**calc_inputs_config)
        config['inputs'] = calc_inputs

    # 计算任务

    calc_block = STCalcBlock(
        prep_calc_step_config, 
        run_calc_step_config,
        scheduler_step_config
    )
    csp_block = STCSPBlock(
        calc_block,  
        scheduler_step_config,
        gen_struc_step_config
    )
   
    stcsp_step = STCSP(csp_block)
   
    csp_step = Step(
            name=stand_csp_mode,
            template=stcsp_step,
            parameters={ 
                "generation": scheduler.generation,
                "stage": scheduler.stage,
                'scheduler': scheduler,
                "opt_params_config": [opt_params_config],
                "calc_config": calc_config  # 列表
            }
        )
    return csp_step

