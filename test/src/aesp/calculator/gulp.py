from pymatgen.command_line.gulp_caller import GulpIO
from pymatgen.io.vasp import Poscar
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


class GulpInputs:
    def __init__(
        self,
        kw_file: str,
        pp_file: str
    ):
        """
        Parameters
        ----------
        kspacing : Union[float, List[float]]
            The kspacing. If it is a number, then three directions use the same
            ksapcing, otherwise it is a list of three numbers, specifying the
            kspacing used in the x, y and z dimension.
        incar : str
            A template INCAR file.
        pp_files : Dict[str,str]
            The potcar files for the elements. For example
            {
               "H" : "/path/to/POTCAR_H",
               "O" : "/path/to/POTCAR_O",
            }
        kgamma : bool
            K-mesh includes the gamma point
        """

        self.kw = self.from_file(kw_file)
        self.pp = self.from_file(pp_file)

    def from_file(
        self,
        fname: str,
    ):
        return Path(fname).read_text()

    @staticmethod
    def args():
        doc_pp_files = 'The pseudopotential files set by a dict, e.g. {"Al" : "path/to/the/al/pp/file", "Mg" : "path/to/the/mg/pp/file"}'
        doc_kw_file = "The path to the template incar file"

        return [
            Argument("kw_file", str, optional=False, doc=doc_pp_files),
            Argument("pp_file", str, optional=False, doc=doc_pp_files),
        ]

    @staticmethod
    def normalize_config(data={}, strict=True):
        ta = VaspInputs.args()
        base = Argument("base", dict, ta)
        data = base.normalize_value(data, trim_pattern="_*")
        base.check_value(data, strict=strict)
        return data


  

# global static variables
gulp_conf_name = "POSCAR"
gulp_input_name = "input"

class PrepGulp(PrepFp):
    def prep_task(
        self,
        conf_frame: dpdata.System,
        gulp_inputs: GulpInputs
    ):
        r"""Define how one Vasp task is prepared.

        Parameters
        ----------
        conf_frame : dpdata.System
            One frame of configuration in the dpdata format.
        vasp_inputs : VaspInputs
            The VaspInputs object handels all other input files of the task.
        """

        conf_frame.to("vasp/poscar", gulp_conf_name)
        struc = Poscar.from_file(gulp_conf_name)
        gulpio = GulpIO()
        struc_gulp = gulpio.structure_lines(struc.structure, anion_shell_flg=False, symm_flg=False)
        ipt = gulp_inputs.kw + "\n" + struc_gulp + "\n" + gulp_inputs.pp
        with open("input", "w") as f:
            f.write(ipt)
        Path(gulp_input_name).write_text(ipt)
        # fix the case when some element have 0 atom, e.g. H0O2


class RunGulp(RunFp):
    def input_files(self) -> List[str]:
        r"""The mandatory input files to run a vasp task.

        Returns
        -------
        files: List[str]
            A list of madatory input files names.

        """
        return [gulp_input_name]

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
        command = " ".join([command, "<", gulp_input_name, ">", log_name])
        ret, out, err = run_command(command, shell=True)
        if ret != 0:
            logging.error(
                "".join(
                    ("gulp failed\n", "out msg: ", out, "\n", "err msg: ", err, "\n")
                )
            )
            raise TransientError("matgl failed")
        
        # convert the output to deepmd/npy format
        self.process_data(out_name, log_name)
        return out_name, log_name

    @staticmethod
    def process_data(out_name, log_name):
        Path(out_name).joinpath("set.000").mkdir(parents=True, exist_ok=True)
        out = Path(log_name).read_text()
        final_struc = GulpIO().get_relaxed_structure(out)
        type_map_r = []
        type_r = []
        for idx, (key,value) in enumerate(final_struc.composition.as_dict().items()):
            type_map_r.append(key)
            type_r += [str(idx)] * int(value)
        tm_str = "\n".join(type_map_r) +"\n"
        t_str = "\n".join(type_r) + "\n"
        with open(f"./{out_name}/type_map.raw", 'w') as f:
            f.write(tm_str)
        with open(f"./{out_name}/type.raw", 'w') as f:
            f.write(t_str)
        coords_list = []
        for site in GulpIO().get_relaxed_structure(out).sites:
            coords_list += site.coords.tolist()
    
        coords = np.array([coords_list])
        virial = np.zeros((1, 9))
        force = np.zeros((1, int(len(coords_list)/3)*3))
        energy = np.array([[GulpIO().get_energy(out)]])
        box = np.array([final_struc.lattice.matrix.flatten()])
        npy_dict = {
            "box.npy": box, "coord.npy": coords,
            "force.npy": force, "virial.npy": virial, 'energy.npy': energy
        }

        for key, value in npy_dict.items():
            np.save(f"./{out_name}/set.000/{key}", value)
        

    @staticmethod
    def args():
        r"""The argument definition of the `run_task` method.

        Returns
        -------
        arguments: List[dargs.Argument]
            List of dargs.Argument defines the arguments of `run_task` method.
        """

        doc_gulp_cmd = "The command of Gulp"
        doc_gulp_log = "The log file name of Gulp"
        doc_gulp_out = "The output dir name of labeled data. In `deepmd/npy` format provided by `dpdata`."
        return [
            Argument("command", str, optional=True, default="python", doc=doc_gulp_cmd),
            Argument("out", str, optional=True, default="data", doc= doc_gulp_out),
            Argument("log", str, optional=True, default="calc.log", doc=doc_gulp_log)
        ]
