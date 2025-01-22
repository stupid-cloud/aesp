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
    argo_sequence
)
from dflow.python import PythonOPTemplate, Slices
from dpgen2.utils.step_config import init_executor
from typing import Any, Dict
from copy import deepcopy
from aesp.workflow.op.prep_run_calc import PrepCalc, RunCalc


class PrepRunCalc(Steps):
    def __init__(
            self,
            prep_calc_step_config,
            run_calc_step_config,
            calc_key="calc"
    ):
        self._input_parameters={
            "generation": InputParameter(),
            "stage": InputParameter(),
            "calc_config": InputParameter()
        }
        self._input_artifacts={
            "db": InputArtifact(),
            "confs": InputArtifact(optional=True),
            "models": InputArtifact(optional=True)
        }
        self._output_parameters={
            "task_names": OutputParameter()
        }
        self._output_artifacts={
            "labeled_data": OutputArtifact()
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

        _keys = ['prep', 'run']
        self.step_keys = {}
        for key in _keys:
            self.step_keys[key] = "{}-{}--g{}-s{}".format(
                    calc_key, key, self.inputs.parameters["generation"],
                    self.inputs.parameters["stage"]
            )
        self.step_keys['run'] += "-{{item}}"

        self = _calc(
            self,
            self.step_keys,
            prep_calc_step_config,
            run_calc_step_config
        )

def _calc(
        calc_steps : Steps,
        step_keys : Dict[str, Any],
        prep_calc_step_config,
        run_calc_step_config
):
    
    step_config = {
        "prep_calc": deepcopy(prep_calc_step_config), "run_calc":  deepcopy(run_calc_step_config)
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

    prep_calc = Step(
        'prep-calc',
        template=PythonOPTemplate(PrepCalc, **template_config['prep_calc']),
        parameters={
            "stage": calc_steps.inputs.parameters['stage'], 
            "generation": calc_steps.inputs.parameters['generation'],
            "calc_config": calc_steps.inputs.parameters['calc_config']
        },
        artifacts={
            "db": calc_steps.inputs.artifacts['db'],
            "models": calc_steps.inputs.artifacts['models'],
            "confs": calc_steps.inputs.artifacts['confs']
        },
        key=step_keys['prep'],
        # executor=executor_config['prep_calc'],
        **step_config['prep_calc']
    )
    calc_steps.add(prep_calc)
  
    run_calc = Step(
        name = "run-calc",
        template = PythonOPTemplate(
            RunCalc,
            slices=Slices(
                # "int('{{item}}')",
                input_parameter=["task_name"],
                input_artifact=["task_path"],
                output_artifact=['log', 'labeled_data'],
                # create_dir=True,
                # sub_path=True,
                **slice_config['run_calc']
            ),
            **template_config['run_calc']
        ),
        parameters={
            "task_name": prep_calc.outputs.parameters['task_names'],
            "calc_config": calc_steps.inputs.parameters['calc_config'],
            "stage": calc_steps.inputs.parameters['stage']
        },
        artifacts={
            "task_path": prep_calc.outputs.artifacts['task_paths']
        },
        with_sequence=argo_sequence(argo_len(prep_calc.outputs.parameters["task_names"])),
        # with_param=argo_range(5),
        key=step_keys['run'],
        # executor=executor_config['run_calc'],
        **step_config['run_calc']
    )
  
    calc_steps.add(run_calc)

    calc_steps.outputs.artifacts['labeled_data']._from = run_calc.outputs.artifacts['labeled_data']
    calc_steps.outputs.parameters["task_names"].value_from_parameter = prep_calc.outputs.parameters['task_names']
    return calc_steps

