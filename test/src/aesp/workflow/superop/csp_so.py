from dflow import (
    InputParameter,
    Inputs,
    InputArtifact,
    Outputs,
    Step,
    Steps  
)
from dflow.python import PythonOPTemplate
from dpgen2.op.collect_data import CollectData
from dpgen2.utils.step_config import init_executor
from aesp.workflow.op.scheduler import SchedulerGen
from aesp.workflow.op.gen_structure import GenStruc
from copy import deepcopy
from dpgen2.flow.dpgen_loop import cl_default_optional_parameter

class STCSP(Steps):
    def __init__(
        self,
        csp_block_op : Steps
    ):
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "calc_config": InputParameter()
        }      

        self._input_artifacts={}
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
        
        self._keys = ['csp-block']
        self.step_keys = {}
        for key in self._keys:
            self.step_keys[key] = "{}--g{}".format(key, self.inputs.parameters["generation"])

        self = _stcsp(
            self,
            self.step_keys,
            csp_block_op
        )

def _stcsp(
    steps,
    step_keys,
    csp_block_op
):
    stcsp_step = Step(
        name="csp-block",
        template=csp_block_op,
        parameters={ 
            "generation": steps.inputs.parameters['generation'],
            "stage": steps.inputs.parameters['stage'],
            'scheduler': steps.inputs.parameters["scheduler"],
            "opt_params_config": steps.inputs.parameters["opt_params_config"],
            "calc_config": steps.inputs.parameters["calc_config"],
            "info": {} # 统计信息
        },
        key=step_keys['csp-block']
    )
    steps.add(stcsp_step)
    return steps


class DPCSP(Steps):
    def __init__(
            self,
            fp_relax_block,
            dp_train_so,
            csp_block,
            scheduler_step_config,
            gen_struc_step_config,
            collect_data_step_config,     
    ):
        
        self._input_parameters = {
            "scheduler": InputParameter(),
            "generation": InputParameter(), 
            "stage": InputParameter(), 
            "opt_params_config": InputParameter(),
            "fp_relax_config": InputParameter(),
            "dp_relax_config": InputParameter(),
            "fp_static_config": InputParameter(),
            "dp_train_config": InputParameter(),
            "fp_shield_config": InputParameter(),
            "template_script": InputParameter(),
            "numb_models": InputParameter(),
            "conf_selector": InputParameter(),
            "type_map": InputParameter(),
            "optional_parameter": InputParameter(
                type=dict, value=cl_default_optional_parameter
            )
        }        
        self._input_artifacts={
            "db": InputArtifact(optional=True),
            "init_models": InputArtifact(optional=True),
            "iter_data": InputArtifact(),
            "init_data": InputArtifact(optional=True)
        }
        
        self._output_parameters = {}
        self._output_artifacts={
            # "db": OutputArtifact()
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
        
        _keys = ['fp-relax-block', "dp-train"]
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}--g{}".format(
                key, self.inputs.parameters["generation"]
            )
        self.step_keys['dp-relax-block'] = 'dp-relax-block--g{}'
        # _keys = ["fp-relax", 'dp-train']
        # for key in _keys:
        #     self.step_keys[key] += "-s{}".format(self.inputs.parameters["stage"])

        self = _dpcsp(
            self,
            self.step_keys,
            fp_relax_block,
            dp_train_so,
            csp_block 
        )



def _dpcsp(
        csp_steps, 
        step_keys,
        fp_relax_block,
        dp_train_so,
        csp_block
):     
    
    # csp_block
    if fp_relax_block is not None:
        fp_relax_block_step = Step(
            "fp-relax-block",
            template=fp_relax_block,
            parameters={
                "scheduler": csp_steps.inputs.parameters["scheduler"],
                "generation": csp_steps.inputs.parameters["generation"],
                "stage": csp_steps.inputs.parameters["stage"],
                "opt_params_config": csp_steps.inputs.parameters['opt_params_config'],
                "fp_relax_config": csp_steps.inputs.parameters['fp_relax_config'],
                "scheduler": csp_steps.inputs.parameters["scheduler"],
                "type_map": csp_steps.inputs.parameters['type_map'],
                "info": {}
            },
            artifacts={
                "iter_data":  csp_steps.inputs.artifacts['iter_data']
            },
            key=step_keys['fp-relax-block']
        )
        csp_steps.add(fp_relax_block_step)

    parameters={
            "generation": csp_steps.inputs.parameters["generation"],
            "stage": csp_steps.inputs.parameters['stage']-1,
            "dp_train_config": csp_steps.inputs.parameters["dp_train_config"],
            "numb_models": csp_steps.inputs.parameters["numb_models"],
            "template_script": csp_steps.inputs.parameters["template_script"]
        }
    artifacts={
            "init_models": csp_steps.inputs.artifacts["init_models"],
            "init_data": csp_steps.inputs.artifacts["init_data"], # Lableled
            "iter_data": csp_steps.inputs.artifacts["iter_data"],  # Muti
        } 
    if fp_relax_block is not None:
        parameters.update({"generation": fp_relax_block_step.outputs.parameters["generation"]}) 
        artifacts.update({"iter_data": fp_relax_block_step.outputs.artifacts["iter_data"]})
    # 训练dp势函数
    dp_train = Step(
        "dp-train",
        template=dp_train_so,
        parameters=parameters,
        artifacts=artifacts,
        key=step_keys['dp-train']
    )
    csp_steps.add(dp_train)
    
    parameters={
            "generation": csp_steps.inputs.parameters["generation"],
            "stage": csp_steps.inputs.parameters["stage"],
            "opt_params_config": csp_steps.inputs.parameters['opt_params_config'],
            "fp_static_config": csp_steps.inputs.parameters['fp_static_config'],
            "dp_relax_config": csp_steps.inputs.parameters['dp_relax_config'],
            "scheduler": csp_steps.inputs.parameters["scheduler"],
            "conf_selector": csp_steps.inputs.parameters['conf_selector'],
            "type_map": csp_steps.inputs.parameters['type_map'],
            "dp_train_config": csp_steps.inputs.parameters['dp_train_config'],
            "numb_models": csp_steps.inputs.parameters['numb_models'],
            "template_script": csp_steps.inputs.parameters['template_script'],
            "fp_shield_config": csp_steps.inputs.parameters['fp_shield_config'],
            "info": {}
        }
    artifacts={
            "db": csp_steps.inputs.artifacts['db'],
            "models": dp_train.outputs.artifacts['models'],
            "iter_data": csp_steps.inputs.artifacts["iter_data"],
            "init_data": csp_steps.inputs.artifacts["init_data"]
        }
    generation = csp_steps.inputs.parameters["generation"]

    if fp_relax_block is not None:
        generation = fp_relax_block_step.outputs.parameters["generation"]
        parameters.update({
            "generation": fp_relax_block_step.outputs.parameters["generation"],
            "opt_params_config": fp_relax_block_step.outputs.parameters['opt_params_config']
            }) 
        artifacts.update({
            "iter_data": fp_relax_block_step.outputs.artifacts["iter_data"],
            "db": fp_relax_block_step.outputs.artifacts['db']
            })
    # csp_block
    dp_relax_block_step = Step(
        "dp-relax-block",
        template=csp_block,
        parameters=parameters,
        artifacts=artifacts,
        key=step_keys['dp-relax-block'].format(generation)
    )
    csp_steps.add(dp_relax_block_step)
  

    return csp_steps