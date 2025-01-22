from dflow import (
    InputParameter,
    OutputParameter,
    Inputs,
    InputArtifact,
    Outputs,
    OutputArtifact,
    Step,
    Steps,
    argo_len,
    argo_sequence,
    if_expression
)
from aesp.workflow.op.gen_structure import GenStruc
from dflow.python import PythonOPTemplate, Slices
from aesp.workflow.op.model_devi import CalcModelDevi
from dpgen2.utils.step_config import init_executor
from aesp.workflow.op.scheduler  import SchedulerStage
from typing import Any, Dict
from copy import deepcopy
from dpgen2.op import SelectConfs, CollectData
from aesp.workflow.superop.prep_run_calc_so import PrepRunCalc
from aesp.workflow.op.scheduler import SchedulerGen

# class STCalcBlock(Steps):
#     def __init__(
#             self,
#             prep_calc_step_config, 
#             run_calc_step_config,
#             scheduler_step_config
#     ):
#         self._input_parameters={
#             "scheduler": InputParameter(),
#             "generation": InputParameter(),
#             "stage": InputParameter(),
#             "calc_config": InputParameter() 
#         }
#         self._input_artifacts={
#             "db": InputArtifact()
#         }
#         self._output_parameters={
#             "scheduler": OutputParameter()
#         }
#         self._output_artifacts={
#             # "db": OutputArtifact(),
#             "db": OutputArtifact()
#         }
        
#         super().__init__(
#             inputs = Inputs(
#                 parameters=self._input_parameters,
#                 artifacts=self._input_artifacts
#             ),
#             outputs=Outputs(
#                 parameters=self._output_parameters,
#                 artifacts=self._output_artifacts
#             ),
#         )

#         _keys = ['relax', "scheduler-stage"]
#         self.step_keys = {}
#         for key in _keys:
#             self.step_keys[key] = "{}--g{}-s{}".format(
#                     key, self.inputs.parameters["generation"],
#                     self.inputs.parameters["stage"]
#             )
#         self.step_keys['block'] = "calc-block--g{}-s{}"

#         self = _stcalc_block(
#             self,
#             self.step_keys,
#             relax_so,
#             scheduler_step_config
#         )

# def _stcalc_block(
#         steps : Steps,
#         step_keys : Dict[str, Any],
#         relax_so,
#         scheduler_step_config
# ):
    
#     step_config = {
#         "scheduler":  deepcopy(scheduler_step_config)
#     }
    
#     template_config = {}
#     for key, value in step_config.items():
#         template_config[key] = value.pop("template_config")

#     executor_config = {}
#     for key, value in step_config.items():
#         executor_config[key] = init_executor(value.pop("executor"))

#     slice_config = {}
#     for key, value in step_config.items():
#         slice_config[key] = value.pop("template_slice_config", {})
        
#     relax_step = Step(
#         'prep-calc',
#         template=relax_so,
#         parameters={
#             "stage": steps.inputs.parameters['stage'], 
#             "generation": steps.inputs.parameters['generation'],
#             "calc_config": steps.inputs.parameters['calc_config']
#         },
#         artifacts={
#             "db": steps.inputs.artifacts['db']
#         },
#         key=step_keys['relax']
#     )
#     steps.add(relax_step)

#     scheduler = Step(
#         'scheduler',
#         template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
#         parameters={
#             "scheduler": steps.inputs.parameters['scheduler']
#         },
#         artifacts={
#             "labeled_data": relax_step.outputs.artifacts['labeled_data'],
#             "db": steps.inputs.artifacts['db']
#         },
#         key=step_keys["scheduler-stage"],
#         executor=executor_config['scheduler'],
#         **step_config['scheduler']
#     )
#     steps.add(scheduler)

#     next_step = Step(
#         name="calc-block",
#         template=steps,
#         parameters={
#             "stage": scheduler.outputs.parameters['stage'],  
#             "generation": steps.inputs.parameters['generation'],
#             "scheduler": scheduler.outputs.parameters['scheduler'],
#             "calc_config": steps.inputs.parameters['calc_config']
#         },
#         artifacts={
#             "db": scheduler.outputs.artifacts['db']
#         },
#         key=step_keys['block'].format(
#             steps.inputs.parameters['generation'], 
#             scheduler.outputs.parameters['stage']
#         ),
#         when="%s == false" % (scheduler.outputs.parameters['s_converged'])
#     )
#     steps.add(next_step)

#     steps.outputs.parameters['scheduler'].value_from_expression = \
#         if_expression(
#             _if = (scheduler.outputs.parameters['s_converged'] == True),
#             _then = scheduler.outputs.parameters['scheduler'],
#             _else = next_step.outputs.parameters['scheduler']
#         )

#     steps.outputs.artifacts['db'].from_expression = \
#         if_expression(
#             _if = (scheduler.outputs.parameters['s_converged'] == True),
#             _then = scheduler.outputs.artifacts['db'],
#             _else = next_step.outputs.artifacts['db']
#         )

class STCalcBlock(Steps):
    def __init__(
            self,
            prep_calc_step_config,
            run_calc_step_config,
            scheduler_step_config
    ):
        self._input_parameters={
            "scheduler": InputParameter(),
            "generation": InputParameter(),
            "stage": InputParameter(),
            "calc_config": InputParameter() 
        }
        self._input_artifacts={
            "db": InputArtifact()
        }
        self._output_parameters={
            "scheduler": OutputParameter()
        }
        self._output_artifacts={
            # "db": OutputArtifact(),
            "db": OutputArtifact()
        }
        
        super().__init__(
            inputs = Inputs(
                parameters=self._input_parameters,
                artifacts=self._input_artifacts
            ),
            outputs=Outputs(
                parameters=self._output_parameters,
                artifacts=self._output_artifacts
            ),
        )

        _keys = ['relax', "scheduler-stage"]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = key + "--g{}-s{}"
        self.step_keys['block'] = "calc-block--g{}-s{}"
        self = _stcalc_block(
            self,
            self.step_keys,
            prep_calc_step_config,
            run_calc_step_config,
            scheduler_step_config
        )

def _stcalc_block(
        steps : Steps,
        step_keys : Dict[str, Any],
        prep_calc_step_config,
        run_calc_step_config,
        scheduler_step_config
):
    
    step_config = {
        "scheduler":  deepcopy(scheduler_step_config)
    }
    
    template_config = {}
    for key, value in step_config.items():
        template_config[key] = value.pop("template_config")

    executor_config = {}
    for key, value in step_config.items():
        executor_config[key] = init_executor(value.pop("executor"))

    slice_config = {}
    for key, value in step_config.items():
        slice_config[key] = value.pop("template_slice_config", {})

    relax_so = PrepRunCalc(prep_calc_step_config, run_calc_step_config, 'relax')   
    relax_step = Step(
        'prep-run-calc',
        template=relax_so,
        parameters={
            "stage": steps.inputs.parameters['stage'], 
            "generation": steps.inputs.parameters['generation'],
            "calc_config": steps.inputs.parameters['calc_config']
        },
        artifacts={
            "db": steps.inputs.artifacts['db']
        },
        key=step_keys['relax'].format(steps.inputs.parameters['generation'], steps.inputs.parameters['stage'])
    )
    steps.add(relax_step)

    scheduler = Step(
        'scheduler',
        template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
        parameters={
            "scheduler": steps.inputs.parameters['scheduler']
        },
        artifacts={
            "labeled_data": relax_step.outputs.artifacts['labeled_data'],
            "db": steps.inputs.artifacts['db']
        },
        key=step_keys["scheduler-stage"].format(steps.inputs.parameters['generation'], steps.inputs.parameters['stage']),
        # executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler)

    next_step = Step(
        name="calc-block",
        template=steps,
        parameters={
            "stage": scheduler.outputs.parameters['stage'],  
            "generation": steps.inputs.parameters['generation'],
            "scheduler": scheduler.outputs.parameters['scheduler'],
            "calc_config": steps.inputs.parameters['calc_config']
        },
        artifacts={
            "db": scheduler.outputs.artifacts['db']
        },
        key=step_keys['block'].format(
            steps.inputs.parameters['generation'], 
            scheduler.outputs.parameters['stage']
        ),
        when="%s == false" % (scheduler.outputs.parameters['s_converged'])
    )
    steps.add(next_step)

    steps.outputs.parameters['scheduler'].value_from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = scheduler.outputs.parameters['scheduler'],
            _else = next_step.outputs.parameters['scheduler']
        )

    steps.outputs.artifacts['db'].from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = scheduler.outputs.artifacts['db'],
            _else = next_step.outputs.artifacts['db']
        )
   

# class STCalcBlock2(Steps):
#     def __init__(
#             self,
#             prep_calc_step_config,
#             run_calc_step_config,
#             scheduler_step_config
#     ):
#         self._input_parameters={
#             "scheduler": InputParameter(),
#             "generation": InputParameter(),
#             "stage": InputParameter(),
#             "calc_config": InputParameter() 
#         }
#         self._input_artifacts={
#             "db": InputArtifact()
#         }
#         self._output_parameters={
#             "scheduler": OutputParameter()
#         }
#         self._output_artifacts={
#             # "db": OutputArtifact(),
#             "db": OutputArtifact()
#         }
        
#         super().__init__(
#             inputs = Inputs(
#                 parameters=self._input_parameters,
#                 artifacts=self._input_artifacts
#             ),
#             outputs=Outputs(
#                 parameters=self._output_parameters,
#                 artifacts=self._output_artifacts
#             ),
#         )

#         _keys = ['relax', "scheduler-stage"]
#         self.step_keys = {}
#         for key in _keys:
#             self.step_keys[key] = key + "--g{}-s{}"

#         self = _stcalc_block2(
#             self,
#             self.step_keys,
#             prep_calc_step_config,
#             run_calc_step_config,
#             scheduler_step_config
#         )

# def _stcalc_block2(
#         steps : Steps,
#         step_keys : Dict[str, Any],
#         prep_calc_step_config,
#         run_calc_step_config,
#         scheduler_step_config
# ):
    
#     step_config = {
#         "scheduler":  deepcopy(scheduler_step_config)
#     }
    
#     template_config = {}
#     for key, value in step_config.items():
#         template_config[key] = value.pop("template_config")

#     executor_config = {}
#     for key, value in step_config.items():
#         executor_config[key] = init_executor(value.pop("executor"))

#     slice_config = {}
#     for key, value in step_config.items():
#         slice_config[key] = value.pop("template_slice_config", {})

#     run_calc_config = run_calc_step_config.pop(0)
    
#     run_calc_config.pop("type")
#     relax_so = PrepRunCalc(prep_calc_step_config, run_calc_config, 'relax')   
#     relax_step = Step(
#         'prep-calc0',
#         template=relax_so,
#         parameters={
#             "stage": steps.inputs.parameters['stage'], 
#             "generation": steps.inputs.parameters['generation'],
#             "calc_config": steps.inputs.parameters['calc_config']
#         },
#         artifacts={
#             "db": steps.inputs.artifacts['db']
#         },
#         key=step_keys['relax'].format(steps.inputs.parameters['generation'], steps.inputs.parameters['stage'])
#     )
#     steps.add(relax_step)

#     scheduler = Step(
#         'scheduler0',
#         template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
#         parameters={
#             "scheduler": steps.inputs.parameters['scheduler']
#         },
#         artifacts={
#             "labeled_data": relax_step.outputs.artifacts['labeled_data'],
#             "db": steps.inputs.artifacts['db']
#         },
#         key=step_keys["scheduler-stage"].format(steps.inputs.parameters['generation'], steps.inputs.parameters['stage']),
#         executor=executor_config['scheduler'],
#         **step_config['scheduler']
#     )
#     steps.add(scheduler)


#     if len(run_calc_step_config) >= 1:
#         for idx, run_calc_config in enumerate(run_calc_step_config):
#             run_calc_config.pop('type')
#             relax_so = PrepRunCalc(prep_calc_step_config, run_calc_config, 'relax')  

#             relax_step = Step(
#                 'prep-calc'+str(idx+1),
#                 template=relax_so,
#                 parameters={
#                     "stage": scheduler.outputs.parameters['stage'], 
#                     "generation": steps.inputs.parameters['generation'],
#                     "calc_config": steps.inputs.parameters['calc_config']
#                 },
#                 artifacts={
#                     "db": scheduler.outputs.artifacts['db']
#                 },
#                 key=step_keys['relax'].format(steps.inputs.parameters['generation'], scheduler.outputs.parameters['stage'])
#             )
#             steps.add(relax_step)        

#             # prev_scheduler = scheduler
#             scheduler = Step(
#                 'scheduler'+str(idx+1),
#                 template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
#                 parameters={
#                     "scheduler": scheduler.outputs.parameters['scheduler']
#                 },
#                 artifacts={
#                     "labeled_data":  relax_step.outputs.artifacts['labeled_data'],
#                     "db": scheduler.outputs.artifacts['db']
#                 },
#                 key=step_keys["scheduler-stage"].format(steps.inputs.parameters['generation'], scheduler.outputs.parameters['stage']),
#                 executor=executor_config['scheduler'],
#                 **step_config['scheduler']
#             )
#             steps.add(scheduler)
            
#     steps.outputs.parameters['scheduler'].value_from_parameter = scheduler.outputs.parameters['scheduler']
#     steps.outputs.artifacts['db']._from = scheduler.outputs.artifacts['db']


class DPCalcBlock(Steps):
    def __init__(
            self,
            dp_relax_so,  
            fp_static_so,
            dp_train_so,
            scheduler_step_config,
            select_confs_step_config,
            collect_data_step_config,
            calc_model_devi_step_config
    ):
        
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "fp_static_config": InputParameter(),
            "dp_relax_config": InputParameter(),
            "conf_selector": InputParameter(),
            "type_map": InputParameter(),
            "dp_train_config": InputParameter(),
            "numb_models": InputParameter(),
            "template_script": InputParameter()
        }        
        self._input_artifacts={
            "db": InputArtifact(optional=True),
            "models": InputArtifact(),
            "iter_data": InputArtifact(),
            'init_data': InputArtifact()
        }
        self._output_parameters = {
            "scheduler": OutputParameter(),
            "stage": OutputParameter()
        }
        self._output_artifacts={
            "db": OutputArtifact(),
            'models': OutputArtifact(),
            "iter_data": OutputArtifact()
        }        
        
        super().__init__(
            inputs=Inputs(
                parameters=self._input_parameters,
                artifacts=self._input_artifacts
            ),
            outputs=Outputs(
                parameters=self._output_parameters,
                artifacts=self._output_artifacts
            )
        )
        
        _keys = [
            'gen-struc', 'dp-relax', "scheduler-stage", 'fp-static',
            'dp-train', 'calc-model-devi', "select-confs", "collect-data"
        ]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}--g{}".format(
                key, self.inputs.parameters["generation"]
            )
        self.step_keys["calc-block"] = "calc-block--g{}-s{}"
        _keys = ['dp-relax', 'fp-static', 'dp-train', "scheduler-stage", "calc-model-devi", "select-confs", "collect-data"]
        for key in _keys:
            self.step_keys[key] = "{}-s{}".format(
                self.step_keys[key], self.inputs.parameters['stage']
                )
        self.step_keys['calc-model-devi'] += '-{{item}}'

        self = _dpcalc_block(
            self,
            self.step_keys,
            dp_relax_so,  
            fp_static_so,
            dp_train_so,
            scheduler_step_config,
            select_confs_step_config,
            collect_data_step_config,
            calc_model_devi_step_config
        )

def _dpcalc_block(
        steps,
        step_keys,
        dp_relax_so,  
        fp_static_so,
        dp_train_so,
        scheduler_step_config,
        select_confs_step_config,
        collect_data_step_config,
        calc_model_devi_step_config
):
    
    step_config = {
        "select_confs": deepcopy(select_confs_step_config), "scheduler":  deepcopy(scheduler_step_config), 
        "collect_data": deepcopy(collect_data_step_config), "calc_model_devi": deepcopy(calc_model_devi_step_config)
    }
    
    template_config = {}
    for key, value in step_config.items():
        template_config[key] = value.pop("template_config")

    executor_config = {}
    for key, value in step_config.items():
        executor_config[key] = init_executor(value.pop("executor"))

    slice_config = {}
    for key, value in step_config.items():
        slice_config[key] = value.pop("template_slice_config", {})

    # dp relax计算 
    dp_relax = Step(
        'PrepRunCalc',
        template=dp_relax_so,
        parameters={
            "generation": steps.inputs.parameters['generation'],
            "stage": steps.inputs.parameters['stage'],
            "calc_config": steps.inputs.parameters['dp_relax_config']
        },
        artifacts={
            "db": steps.inputs.artifacts['db'],
            "models": steps.inputs.artifacts["models"]
        },
        key=step_keys['dp-relax']
    )
    steps.add(dp_relax)

    # calc-model-devi
    run_model_devi = Step(
        'calc-model-devi',
        template=PythonOPTemplate(CalcModelDevi, **template_config['calc_model_devi']),
        slices=Slices(
            "int('{{item}}')",
            input_parameter=["task_name"],
            input_artifact=["labeled_data"],
            output_artifact=["model_devis", "trajs"],
            **slice_config['calc_model_devi']
        ),
        parameters={
            "task_name": dp_relax.outputs.parameters['task_names']
        },
        artifacts={
            "labeled_data": dp_relax.outputs.artifacts["labeled_data"],
            "models": steps.inputs.artifacts["models"]
        },
        key=step_keys['calc-model-devi'],
        with_sequence=argo_sequence(argo_len(dp_relax.outputs.parameters['task_names'])),
        # executor=executor_config['calc_model_devi'],
        **step_config['calc_model_devi']
    )
    steps.add(run_model_devi)

    # 选择结构
    select_confs = Step(
        name="select-confs",
        template=PythonOPTemplate(
            SelectConfs,
            output_artifact_archive={"confs": None},
            **template_config['select_confs']
        ),
        parameters={
            "conf_selector": steps.inputs.parameters["conf_selector"],
            "type_map": steps.inputs.parameters["type_map"],
        },
        artifacts={
            "trajs": run_model_devi.outputs.artifacts["trajs"],
            "model_devis": run_model_devi.outputs.artifacts["model_devis"],
        },
        key=step_keys["select-confs"],
        # executor=executor_config["select_confs"],
        **step_config["select_confs"],
    )
    steps.add(select_confs)

    # fp static计算
    fp_static = Step(
        name="fp-static",
        template=fp_static_so,
        parameters={
            "generation": steps.inputs.parameters['generation'],
            "stage": steps.inputs.parameters['stage'],
            "calc_config": steps.inputs.parameters['fp_static_config']
        },
        artifacts={
            "confs": select_confs.outputs.artifacts["confs"]
        },
        key=step_keys['fp-static']
    )
    steps.add(fp_static)

    # 收集数据
    collect_data = Step(
        name="collect-data",
        template=PythonOPTemplate(
            CollectData,
            output_artifact_archive={"iter_data": None},
            **template_config['collect_data'],
        ),
        parameters={
            "name": "g{}_s{}".format(
                steps.inputs.parameters['generation'],
                steps.inputs.parameters['stage']
                ),
            "type_map":steps.inputs.parameters["type_map"]
        },
        artifacts={
            "iter_data": steps.inputs.artifacts["iter_data"],
            "labeled_data": fp_static.outputs.artifacts["labeled_data"],
        },
        key=step_keys["collect-data"],
        executor=executor_config['collect_data'],
        **step_config['collect_data']
    )
    steps.add(collect_data)

    # dp 训练
    dp_train = Step(
        "dp-train",
        template=dp_train_so,
        parameters={
            "generation": steps.inputs.parameters["generation"],
            "stage": steps.inputs.parameters['stage'],
            "dp_train_config": steps.inputs.parameters["dp_train_config"],
            "numb_models": steps.inputs.parameters["numb_models"],
            "template_script": steps.inputs.parameters["template_script"]
        },
        artifacts={
            "init_models": steps.inputs.artifacts["models"],
            "init_data": steps.inputs.artifacts["init_data"],
            "iter_data": collect_data.outputs.artifacts["iter_data"]
            # "iter_data": []
        },
        key=step_keys['dp-train']
    )
    steps.add(dp_train)

    # scheduler next_stage
    scheduler = Step(
        'scheduler',
        template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
        parameters={
            "scheduler": steps.inputs.parameters['scheduler'],
            'report': select_confs.outputs.parameters['report']
        },
        artifacts={
            "labeled_data": dp_relax.outputs.artifacts['labeled_data'],
            "db": steps.inputs.artifacts['db']
        },
        key=step_keys["scheduler-stage"],
        # executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler)
    
    next_step = Step(
        name="calc-block",
        template=steps,
        parameters={
            "stage": scheduler.outputs.parameters['stage'],  
            "generation": steps.inputs.parameters['generation'],
            "scheduler": scheduler.outputs.parameters['scheduler'],
            "opt_params_config": steps.inputs.parameters['opt_params_config'],
            "fp_static_config": steps.inputs.parameters['fp_static_config'],
            "dp_relax_config": steps.inputs.parameters['dp_relax_config'],
            "conf_selector": steps.inputs.parameters['conf_selector'],
            "type_map": steps.inputs.parameters['type_map'],
            "dp_train_config": steps.inputs.parameters['dp_train_config'],
            "numb_models": steps.inputs.parameters['numb_models'],
            "template_script": steps.inputs.parameters['template_script']
        },
        artifacts={
            "db": scheduler.outputs.artifacts['db'],
            "models": dp_train.outputs.artifacts['models'],
            "iter_data": collect_data.outputs.artifacts['iter_data'],
            "init_data": steps.inputs.artifacts['init_data']
        },
        key=step_keys['calc-block'].format(
            steps.inputs.parameters['generation'], 
            scheduler.outputs.parameters['stage']
        ),
        when="%s == false" % (scheduler.outputs.parameters['s_converged'])
    )
    steps.add(next_step)

    steps.outputs.parameters['scheduler'].value_from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = scheduler.outputs.parameters['scheduler'],
            _else = next_step.outputs.parameters['scheduler']
        )
    
    steps.outputs.parameters['stage'].value_from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = scheduler.outputs.parameters['stage'],
            _else = next_step.outputs.parameters['stage']
        )
    
    steps.outputs.artifacts['db'].from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = scheduler.outputs.artifacts['db'],
            _else = next_step.outputs.artifacts['db']
        )

    steps.outputs.artifacts['models'].from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = dp_train.outputs.artifacts['models'],
            _else = next_step.outputs.artifacts['models']
        )
    
    steps.outputs.artifacts['iter_data'].from_expression = \
        if_expression(
            _if = (scheduler.outputs.parameters['s_converged'] == True),
            _then = collect_data.outputs.artifacts['iter_data'],
            _else = next_step.outputs.artifacts['iter_data']
        )

    return steps


class FPRelaxBlock(Steps):
    def __init__(
            self,  
            fp_relax_so,  
            fp_relax_gen_num,
            gen_struc_step_config,
            scheduler_step_config,
            collect_data_step_config
    ):
        
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "fp_relax_config": InputParameter(), 
            "type_map": InputParameter(),
            "info": InputParameter()
        }        
        self._input_artifacts={
            "db": InputArtifact(optional=True),
            "iter_data": InputArtifact()
        }
        self._output_parameters = {
            "scheduler": OutputParameter(),
            "generation": OutputParameter(),
            "info": OutputParameter(),
            "opt_params_config": OutputParameter()
        }
        self._output_artifacts={
            "db": OutputArtifact(),
            "iter_data": OutputArtifact()
        }        
        
        super().__init__(
            inputs=Inputs(
                parameters=self._input_parameters,
                artifacts=self._input_artifacts
            ),
            outputs=Outputs(
                parameters=self._output_parameters,
                artifacts=self._output_artifacts
            )
        )
        
        _keys = [
            'gen-struc', 'fp-relax', "scheduler-gen", "scheduler-stage", "collect-data"
        ]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}--g{}".format(
                key, self.inputs.parameters["generation"]
            )
        _keys = ['fp-relax', "scheduler-stage"]
        for key in _keys:
            self.step_keys[key] = "{}-s{}".format(
                self.step_keys[key], self.inputs.parameters['stage']
                )
        self.step_keys['fp-relax-block'] = "fp-relax-block--g{}"
        self = _fp_relax_block(
            self,
            self.step_keys,
            fp_relax_so,  
            fp_relax_gen_num,
            gen_struc_step_config,
            scheduler_step_config,
            collect_data_step_config
        )

def _fp_relax_block(
        steps,
        step_keys,
        fp_relax_so,  
        fp_relax_gen_num,
        gen_struc_step_config,
        scheduler_step_config,
        collect_data_step_config
):
    
    step_config = {
        "gen_struc": deepcopy(gen_struc_step_config), "scheduler": deepcopy(scheduler_step_config),
        "collect_data": deepcopy(collect_data_step_config)
    }
    
    template_config = {}
    for key, value in step_config.items():
        template_config[key] = value.pop("template_config")

    executor_config = {}
    for key, value in step_config.items():
        executor_config[key] = init_executor(value.pop("executor"))

    slice_config = {}
    for key, value in step_config.items():
        slice_config[key] = value.pop("template_slice_config", {})

     # 生成结构
    gen_struc = Step(
        'gen-struc',
        template=PythonOPTemplate(GenStruc, **template_config['gen_struc']),
        parameters={
            "generation": steps.inputs.parameters['generation'],
            "opt_params_config": steps.inputs.parameters['opt_params_config']
        },
        artifacts={
            "db": steps.inputs.artifacts['db']
        },
        key=step_keys['gen-struc'],
        executor=executor_config['gen_struc'],
        **step_config['gen_struc']
    )
    steps.add(gen_struc)
    
    # fp relax计算
    fp_relax = Step(
        'fp-relax',
        template=fp_relax_so,
        parameters={
            "generation": steps.inputs.parameters['generation'],
            "stage": steps.inputs.parameters['stage'],
            "calc_config": steps.inputs.parameters['fp_relax_config']
        },
        artifacts={
            "db": gen_struc.outputs.artifacts['db']
        },
        key=step_keys['fp-relax']
    )
    steps.add(fp_relax)

    
    # 收集数据
    collect_data = Step(
        name="collect-data",
        template=PythonOPTemplate(
            CollectData,
            output_artifact_archive={"iter_data": None},
            **template_config['collect_data'],
        ),
        parameters={
            "name": "g{}".format(steps.inputs.parameters['generation']),
            "type_map": steps.inputs.parameters["type_map"]
        },
        artifacts={
            "iter_data": steps.inputs.artifacts["iter_data"],
            "labeled_data": fp_relax.outputs.artifacts["labeled_data"],
        },
        key=step_keys["collect-data"],
        executor=executor_config['collect_data'],
        **step_config['collect_data']
    )
    steps.add(collect_data)

    # scheduler-stage更新
    scheduler_stage = Step(
        'scheduler-stage',
        template=PythonOPTemplate(SchedulerStage, **template_config['scheduler']),
        parameters={
            "scheduler": steps.inputs.parameters['scheduler']
        },
        artifacts={
            "labeled_data": fp_relax.outputs.artifacts['labeled_data'],
            "db": gen_struc.outputs.artifacts['db']
        },
        key=step_keys["scheduler-stage"],
        executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler_stage)

    # scheduler-gen更新
    scheduler_gen = Step(
        'scheduler',
        template=PythonOPTemplate(SchedulerGen, **template_config['scheduler']),
        parameters={
            "scheduler": scheduler_stage.outputs.parameters['scheduler'],
            'generation': steps.inputs.parameters['generation'],
            "opt_params_config": steps.inputs.parameters['opt_params_config'],
            "info": steps.inputs.parameters['info']
        },
        artifacts={
            "db": scheduler_stage.outputs.artifacts['db']
        },
        key=step_keys['scheduler-gen'],
        executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler_gen)
    
    next_step = Step(
        name="fp-relax-block",
        template=steps,
        parameters={
            "stage": steps.inputs.parameters['stage'],  
            "generation": scheduler_gen.outputs.parameters['generation'],
            "scheduler": scheduler_gen.outputs.parameters['scheduler'],
            "opt_params_config": scheduler_gen.outputs.parameters['opt_params_config'],
            "fp_relax_config": steps.inputs.parameters['fp_relax_config'],
            "type_map": steps.inputs.parameters['type_map'],
            "info": scheduler_gen.outputs.parameters['info']
        },
        artifacts={
            "db": scheduler_gen.outputs.artifacts['db'],
            "iter_data": collect_data.outputs.artifacts['iter_data']
        },
        key=step_keys['fp-relax-block'].format(
            scheduler_gen.outputs.parameters['generation']
        ),
        when="%s <= %s" % (scheduler_gen.outputs.parameters['generation'], str(fp_relax_gen_num))
    )
    steps.add(next_step)

    steps.outputs.parameters['opt_params_config'].value_from_expression = \
        if_expression(
             _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = scheduler_gen.outputs.parameters['opt_params_config'],
            _else = next_step.outputs.parameters['opt_params_config']
        )
    steps.outputs.parameters['scheduler'].value_from_expression = \
        if_expression(
             _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = scheduler_gen.outputs.parameters['scheduler'],
            _else = next_step.outputs.parameters['scheduler']
        )
    steps.outputs.parameters['generation'].value_from_expression = \
        if_expression(
             _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = scheduler_gen.outputs.parameters['generation'],
            _else = next_step.outputs.parameters['generation']
        )
    
    steps.outputs.parameters['info'].value_from_expression = \
        if_expression(
             _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = scheduler_gen.outputs.parameters['info'],
            _else = next_step.outputs.parameters['info']
        )
    
    steps.outputs.artifacts['db'].from_expression = \
        if_expression(
             _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = scheduler_gen.outputs.artifacts['db'],
            _else = next_step.outputs.artifacts['db']
        )
    
    steps.outputs.artifacts['iter_data'].from_expression = \
        if_expression(
            _if = (scheduler_gen.outputs.parameters['generation'] > fp_relax_gen_num),
            _then = collect_data.outputs.artifacts['iter_data'],
            _else = next_step.outputs.artifacts['iter_data']
        )

    return steps