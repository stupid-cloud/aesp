import json
import os
from copy import (
    deepcopy,
)
from pathlib import (
    Path,
)
from typing import (
    List,
    Optional,
    Set,
    Type,
)

from dflow import (
    InputArtifact,
    InputParameter,
    Inputs,
    OutputArtifact,
    OutputParameter,
    Outputs,
    S3Artifact,
    Step,
    Steps,
    Workflow,
    argo_len,
    argo_range,
    argo_sequence,
    download_artifact,
    upload_artifact,
)
from dflow.python import (
    OP,
    OPIO,
    Artifact,
    BigParameter,
    OPIOSign,
    PythonOPTemplate,
    Slices,
)

from dpgen2.constants import (
    train_index_pattern,
    train_script_name,
    train_task_pattern,
)

from dpgen2.utils.step_config import (
    init_executor,
)
from dpgen2.utils.step_config import normalize as normalize_step_dict
from dpgen2.op.prep_dp_train import PrepDPTrain
from dpgen2.op.run_dp_train import RunDPTrain
from aesp.workflow.op.run_dp_train import RunDPTrain1

class PrepRunDP(Steps):
    def __init__(
        self,
        name: str,
        prep_config: dict = normalize_step_dict({}),
        run_config: dict = normalize_step_dict({}),
        valid_data: Optional[S3Artifact] = None,
        optional_files: Optional[List[str]] = None,
    ):
        self._input_parameters = {
            "generation": InputParameter(),
            "stage": InputParameter(),
            "numb_models": InputParameter(type=int),
            "template_script": InputParameter(),
            "dp_train_config": InputParameter(),
            "run_optional_parameter": InputParameter(
                type=dict, value=RunDPTrain.default_optional_parameter
            ),
        }
        self._input_artifacts = {
            "init_models": InputArtifact(optional=True),
            "init_data": InputArtifact(),
            "iter_data": InputArtifact(),
        }
        self._output_parameters = {
            "template_script": OutputParameter(),
        }
        self._output_artifacts = {
            "scripts": OutputArtifact(),
            "models": OutputArtifact(),
            "logs": OutputArtifact(),
            "lcurves": OutputArtifact(),
        }

        super().__init__(
            name=name,
            inputs=Inputs(
                parameters=self._input_parameters,
                artifacts=self._input_artifacts,
            ),
            outputs=Outputs(
                parameters=self._output_parameters,
                artifacts=self._output_artifacts,
            ),
        )

        self._keys = ["dp-train-prep", "dp-train-run"]
        self.step_keys = {}
        for ii in self._keys:
            self.step_keys[ii] = "{}--g{}-s{}".format(
                ii, self.inputs.parameters["generation"], self.inputs.parameters["stage"]
                )
        self.step_keys["dp-train-run"] = self.step_keys["dp-train-run"] + "-{{item}}"

        self = _prep_run_dp_train(
            self,
            self.step_keys,
            prep_config=prep_config,
            run_config=run_config,
            valid_data=valid_data,
            optional_files=optional_files,
        )

def _prep_run_dp_train(
    train_steps,
    step_keys,
    prep_config: dict = normalize_step_dict({}),
    run_config: dict = normalize_step_dict({}),
    valid_data: Optional[S3Artifact] = None,
    optional_files: Optional[List[str]] = None,
):
    

    step_config = {
        "prep_train": deepcopy(prep_config), "run_train":  deepcopy(run_config)
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

    prep_train = Step(
        "dp-train-prep",
        template=PythonOPTemplate(
            PrepDPTrain,
            output_artifact_archive={"task_paths": None},
            **template_config['prep_train'],
        ),
        parameters={
            "numb_models": train_steps.inputs.parameters["numb_models"],
            "template_script": train_steps.inputs.parameters["template_script"],
        },
        artifacts={},
        key=step_keys["dp-train-prep"],
        # executor=executor_config["prep_train"],
        **step_config["prep_train"],
    )
    train_steps.add(prep_train)

    run_train = Step(
        "dp-train-run",
        template=PythonOPTemplate(
            RunDPTrain1,
            slices=Slices(
                "int('{{item}}')",
                input_parameter=["task_name"],
                input_artifact=["task_path", "init_model"],
                output_artifact=["model", "lcurve", "log", "script"],
                **slice_config['run_train'],
            ),
            **template_config['run_train']
        ),
        parameters={
            "config": train_steps.inputs.parameters["dp_train_config"],
            "task_name": prep_train.outputs.parameters["task_names"],
            "optional_parameter": train_steps.inputs.parameters[
                "run_optional_parameter"
            ],
        },
        artifacts={
            "task_path": prep_train.outputs.artifacts["task_paths"],
            "init_model": train_steps.inputs.artifacts["init_models"],
            "init_data": train_steps.inputs.artifacts["init_data"],
            "iter_data": train_steps.inputs.artifacts["iter_data"],
            "valid_data": valid_data,
            "optional_files": upload_artifact(optional_files)
            if optional_files is not None
            else None,
        },
        with_sequence=argo_sequence(
            argo_len(prep_train.outputs.parameters["task_names"])
        ),
        # with_param=argo_range(train_steps.inputs.parameters["numb_models"]),
        key=step_keys["dp-train-run"],
        executor=executor_config['run_train'],
        **step_config['run_train'],
    )
    train_steps.add(run_train)

    train_steps.outputs.parameters[
        "template_script"
    ].value_from_parameter = train_steps.inputs.parameters["template_script"]
    train_steps.outputs.artifacts["scripts"]._from = run_train.outputs.artifacts[
        "script"
    ]
    train_steps.outputs.artifacts["models"]._from = run_train.outputs.artifacts["model"]
    train_steps.outputs.artifacts["logs"]._from = run_train.outputs.artifacts["log"]
    train_steps.outputs.artifacts["lcurves"]._from = run_train.outputs.artifacts[
        "lcurve"
    ]

    return train_steps
