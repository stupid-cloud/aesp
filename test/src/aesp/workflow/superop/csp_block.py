from dflow import (
    InputParameter,
    Inputs,
    InputArtifact,
    Outputs,
    Step,
    Steps,
)
from dflow.python import PythonOPTemplate
from dpgen2.op import CollectData
from dpgen2.utils.step_config import init_executor
from aesp.workflow.op.scheduler import SchedulerGen
from aesp.workflow.op.gen_structure import GenStruc
from copy import deepcopy


class STCSPBlock(Steps):
    def __init__(
            self,
            calc_block_op : Steps,
            scheduler_step_config,
            gen_struc_step_config
    ):
        
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "calc_config": InputParameter(),
            "info": InputParameter()
        }        
        self._input_artifacts={
            "db": InputArtifact(optional=True)
        }
        
        self._output_parameters = {}
        self._output_artifacts = {}        
        
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
        
        _keys = ['gen-struc', "scheduler-gen"]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}--g{}".format(
                key, self.inputs.parameters["generation"]
            )
        self.step_keys['block'] = "csp-block--g{}"
        self.step_keys['calc-block'] = "calc-block--g{}-s{}".format(
            self.inputs.parameters['generation'], self.inputs.parameters['stage']
            )

        self = _stcsp(
            self,
            self.step_keys,
            calc_block_op,
            scheduler_step_config,
            gen_struc_step_config
        )

def _stcsp(
        steps, 
        step_keys,
        calc_block_op,
        scheduler_step_config,
        gen_struc_step_config     
):     
    
    step_config = {
        "gen_struc": deepcopy(gen_struc_step_config), "scheduler":  deepcopy(scheduler_step_config)
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
        # executor=executor_config['gen_struc'],
        **step_config['gen_struc']
    )
    steps.add(gen_struc)

    # 结构优化计算块
    calc_block = Step(
        'calc-block',
        template=calc_block_op,
        parameters={
            "scheduler": steps.inputs.parameters['scheduler'],
            "generation": steps.inputs.parameters['generation'],
            "stage": steps.inputs.parameters['stage'],
            "calc_config": steps.inputs.parameters['calc_config']
        },
        artifacts={
            "db": gen_struc.outputs.artifacts['db']
        },
        key=step_keys['calc-block']
    )
    steps.add(calc_block)

    # scheduler更新
    scheduler = Step(
        'scheduler',
        template=PythonOPTemplate(SchedulerGen, **template_config['scheduler']),
        parameters={
            "scheduler": calc_block.outputs.parameters['scheduler'],
            'generation': steps.inputs.parameters['generation'],
            "opt_params_config": steps.inputs.parameters['opt_params_config'],
            "info": steps.inputs.parameters['info']
        },
        artifacts={
            "db": calc_block.outputs.artifacts['db']
        },
        key=step_keys['scheduler-gen'],
        # executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler)
    
    # 重复csp模块
    next_step = Step(
        name="csp-block",
        template = steps,
        parameters={
            "generation": scheduler.outputs.parameters['generation'],
            'scheduler': scheduler.outputs.parameters['scheduler'],
            "stage": steps.inputs.parameters['stage'],
            "opt_params_config": scheduler.outputs.parameters['opt_params_config'],
            "calc_config": steps.inputs.parameters['calc_config'],
            "info": scheduler.outputs.parameters['info']
        },
        artifacts={
            "db": scheduler.outputs.artifacts['db']
        },
        key=step_keys['block'].format(scheduler.outputs.parameters['generation']),
        when = "%s == false" % (scheduler.outputs.parameters['g_converged'])
    )
    steps.add(next_step)   

    return steps


class DPCSPBlock(Steps):
    def __init__(
            self,
            calc_block,
            fp_shield_so,
            scheduler_step_config,
            gen_struc_step_config,
            collect_data_step_config
    ):
        
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "fp_static_config": InputParameter(),
            "dp_relax_config": InputParameter(),
            "fp_shield_config": InputParameter(),
            "conf_selector": InputParameter(),
            "type_map": InputParameter(),
            "dp_train_config": InputParameter(),
            "numb_models": InputParameter(),
            "template_script": InputParameter(),
            "info": InputParameter()
        }        
        self._input_artifacts={
            "db": InputArtifact(optional=True),
            "models": InputArtifact(),
            "iter_data": InputArtifact(),
            "init_data": InputArtifact()
        }
        
        self._output_parameters = {}
        self._output_artifacts={}        
        
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
        
        _keys = ['gen-struc', "calc-block", "scheduler-gen", "collect-data", "fp-shield"]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}--g{}".format(
                key, self.inputs.parameters["generation"]
            )

        _keys = ["calc-block"]
        for key in _keys:
            self.step_keys[key] = "{}-s{}".format(
                self.step_keys[key], self.inputs.parameters['stage']
                )
        self.step_keys["fp-shield"] = "fp-shield--g{}-s{}"
        self.step_keys['dp-relax-block'] = "csp-block--g{}"
        
        self = _dpcsp(
            self,
            self.step_keys,
            calc_block,
            fp_shield_so,
            scheduler_step_config,
            gen_struc_step_config,
            collect_data_step_config
        )

def _dpcsp(
        steps, 
        step_keys,
        calc_block,
        fp_shield_so,
        scheduler_step_config,
        gen_struc_step_config,
        collect_data_step_config
        
):     
    step_config = {
        "gen_struc": deepcopy(gen_struc_step_config), "scheduler":  deepcopy(scheduler_step_config), 
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
        # executor=executor_config['gen_struc'],
        **step_config['gen_struc']
    )
    steps.add(gen_struc)

    # calc_block
    calc_block_step = Step(
        'calc-block',
        template=calc_block,
        parameters={
            "scheduler": steps.inputs.parameters['scheduler'],
            "generation": steps.inputs.parameters['generation'], 
            "stage": steps.inputs.parameters['stage'], 
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
            "db": gen_struc.outputs.artifacts['db'],
            "models": steps.inputs.artifacts['models'],
            "iter_data": steps.inputs.artifacts['iter_data'],
            "init_data": steps.inputs.artifacts['init_data']
        },
        key=step_keys['calc-block']
    )
    steps.add(calc_block_step)

    # fp-shield
    if fp_shield_so is not None:
         # fp relax计算
        fp_shield_step = Step(
            'fp-shield',
            template=fp_shield_so,
            parameters={
                "generation": steps.inputs.parameters['generation'],
                "stage": calc_block_step.outputs.parameters['stage'],
                "calc_config": steps.inputs.parameters['fp_shield_config']
            },
            artifacts={
                "db": calc_block_step.outputs.artifacts['db']
            },
            key=step_keys['fp-shield'].format(
                steps.inputs.parameters['generation'],
                calc_block_step.outputs.parameters['stage']
                )
        )
        steps.add(fp_shield_step)

        # 收集数据
        collect_data = Step(
            name="collect-data",
            template=PythonOPTemplate(
                CollectData,
                output_artifact_archive={"iter_data": None},
                **template_config['collect_data'],
            ),
            parameters={
                "name": "g{}".format(
                steps.inputs.parameters['generation'] 
                ),
                "type_map":steps.inputs.parameters["type_map"]
            },
            artifacts={
                "iter_data": calc_block_step.outputs.artifacts["iter_data"],
                "labeled_data": fp_shield_step.outputs.artifacts["labeled_data"],
            },
            key=step_keys["collect-data"],
            executor=executor_config['collect_data'],
            **step_config['collect_data']
        )
        steps.add(collect_data)
    
    scheduler = Step(
        'scheduler',
        template=PythonOPTemplate(SchedulerGen, **template_config['scheduler']),
        parameters={
            "scheduler": calc_block_step.outputs.parameters['scheduler'],
            'generation': steps.inputs.parameters['generation'],
            "opt_params_config": steps.inputs.parameters['opt_params_config'],
            "info": steps.inputs.parameters['info']
        },
        artifacts={
            "db": calc_block_step.outputs.artifacts['db']
        },
        key=step_keys['scheduler-gen'],
        # executor=executor_config['scheduler'],
        **step_config['scheduler']
    )
    steps.add(scheduler)

    artifacts_dict = {
            "db": scheduler.outputs.artifacts['db'],
            "models": calc_block_step.outputs.artifacts['models'],
            "iter_data": calc_block_step.outputs.artifacts['iter_data'],
            "init_data": steps.inputs.artifacts['init_data']
        }
    if fp_shield_so is not None:
        artifacts_dict['iter_data'] = collect_data.outputs.artifacts['iter_data']
    
    # 重复csp模块
    next_step = Step(
        name="dp-relax-block",
        template = steps,
        parameters = {
            "scheduler": scheduler.outputs.parameters['scheduler'],
            "generation": scheduler.outputs.parameters['generation'], 
            "stage": steps.inputs.parameters['stage'], 
            "opt_params_config": scheduler.outputs.parameters['opt_params_config'],
            "fp_static_config": steps.inputs.parameters['fp_static_config'],
            "dp_relax_config": steps.inputs.parameters['dp_relax_config'],
            "fp_shield_config": steps.inputs.parameters['fp_shield_config'],
            "conf_selector": steps.inputs.parameters['conf_selector'],
            "type_map": steps.inputs.parameters['type_map'],
            "dp_train_config": steps.inputs.parameters['dp_train_config'],
            "numb_models": steps.inputs.parameters['numb_models'],
            "template_script": steps.inputs.parameters['template_script'],
            "info": scheduler.outputs.parameters['info']
        },        
        artifacts=artifacts_dict,
        key=step_keys['dp-relax-block'].format(scheduler.outputs.parameters['generation']),
        when = "%s == false" % (scheduler.outputs.parameters['g_converged'])
    )
    steps.add(next_step)   

    
    return steps

