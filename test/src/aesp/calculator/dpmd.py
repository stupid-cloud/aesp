from pathlib import Path
from dargs import Argument
from dpgen2.fp.prep_fp import PrepFp
from dpgen2.fp.run_fp import RunFp
import dpdata
from typing import List, Tuple
from dpgen2.utils.run_command import run_command
import logging
from dflow.python import TransientError
import numpy as np
import random

class DpmdInputs:
    def __init__(
        self,
        pstress,
        relax_cell,
        step_max,
        f_max,
        model: str
    ):
        """
        Parameters
        ----------
        incar : str
            A template INCAR file.
      
        """
        self.pstress = pstress
        self._incar_template = self.incar_from_file(pstress, relax_cell, step_max, f_max, model)

    @property
    def incar_template(self):
        return self._incar_template

    def incar_from_file(
        self,
        pstress,
        relax_cell,
        step_max,
        f_max,
        model: str
    ):
        c_path = Path(__file__).resolve().parent
        incar_template = Path(c_path / "template/dpmd_relax.py").read_text()
        incar_template = incar_template.replace("{{pstress}}", str(pstress))
        incar_template = incar_template.replace("{{relax_cell}}", str(relax_cell))
        incar_template = incar_template.replace("{{step_max}}", str(step_max))
        incar_template = incar_template.replace("{{f_max}}", str(f_max))
        incar_template = incar_template.replace("{{model}}", model)
        return incar_template

    @staticmethod
    def args():
        doc_step_max = "The path to the template incar file"
        doc_relax_cell = "The path to the template incar file"
        doc_f_max = "The path to the template incar file"
        doc_model = "The path to the template incar file"
        return [
            Argument("relax_cell", bool, optional=True, default=True, doc=doc_relax_cell),
            Argument("step_max", int, optional=True, default=1000, doc=doc_step_max),
            Argument("f_max", float, optional=True, default=0.05, doc=doc_f_max),
            Argument("model", str, optional=True, default="frozen_model.pb", doc=doc_model)
        ]

    @staticmethod
    def normalize_config(data={}, strict=True):
        ta = DpmdInputs.args()
        base = Argument("base", dict, ta)
        data = base.normalize_value(data, trim_pattern="_*")
        base.check_value(data, strict=strict)
        return data
    
    

# global static variables
dpmd_conf_name = "POSCAR"
dpmd_input_name = "calc.py"
dpmd_model_name = "frozen_model.pb"

class PrepDpmd(PrepFp):
    def prep_task(
        self,
        conf_frame: dpdata.System,
        dpmd_inputs: DpmdInputs
    ):
        r"""Define how one Vasp task is prepared.

        Parameters
        ----------
        conf_frame : dpdata.System
            One frame of configuration in the dpdata format.
        vasp_inputs : VaspInputs
            The VaspInputs object handels all other input files of the task.
        """

        conf_frame.to("vasp/poscar", dpmd_conf_name)
        Path(dpmd_input_name).write_text(dpmd_inputs.incar_template)
        if dpmd_inputs.models is not None:
            model_list = []
            for model in dpmd_inputs.models.glob("task*/*"):
                model_list.append(model)
            model = random.choice(model_list)
        else:
            model = dpmd_inputs.model_path
        Path(dpmd_model_name).symlink_to(model)
    
        Path(dpmd_input_name).write_text(dpmd_inputs.incar_template)
        
        # fix the case when some element have 0 atom, e.g. H0O2


class RunDpmd(RunFp):
    def input_files(self) -> List[str]:
        r"""The mandatory input files to run a vasp task.

        Returns
        -------
        files: List[str]
            A list of madatory input files names.

        """
        return [dpmd_conf_name, dpmd_input_name, dpmd_model_name]

    def optional_input_files(self) -> List[str]:
        r"""The optional input files to run a vasp task.

        Returns
        -------
        files: List[str]
            A list of optional input files names.

        """
        return []

    def run_task(
        self,
        command: str,
        out: str,
        log: str,
    ) -> Tuple[str, str]:
        r"""Defines how one FP task runs

        Parameters
        ----------
        command : str
            The command of running vasp task
        out : str
            The name of the output data file.
        log : str
            The name of the log file

        Returns
        -------
        out_name: str
            The file name of the output data in the dpdata.LabeledSystem format.
        log_name: str
            The file name of the log.
        """

        log_name = log
        out_name = out
        # run vasp
        command = " ".join([command, dpmd_input_name, ">", log_name])
        ret, out, err = run_command(command, shell=True)
        if ret != 0:
            logging.error(
                "".join(
                    ("ase failed\n", "out msg: ", out, "\n", "err msg: ", err, "\n")
                )
            )
            raise TransientError("ase failed")
        
        # convert the output to deepmd/npy format
        from dpdata import LabeledSystem
        ls = LabeledSystem().from_dpmd_traj("relax.traj")
        ls.to("deepmd/npy", out_name)
        return out_name, log_name
        

    @staticmethod
    def args():
        r"""The argument definition of the `run_task` method.

        Returns
        -------
        arguments: List[dargs.Argument]
            List of dargs.Argument defines the arguments of `run_task` method.
        """

        doc_dpmd_cmd = "The command of Ase"
        doc_dpmd_log = "The log file name of Ase"
        doc_dpmd_out = "The output dir name of labeled data. In `deepmd/npy` format provided by `dpdata`."
        return [
            Argument("command", str, optional=True, default="python", doc=doc_dpmd_cmd),
            Argument("out", str, optional=True, default="data", doc= doc_dpmd_out),
            Argument("log", str, optional=True, default="calc.log", doc=doc_dpmd_log)
        ]
