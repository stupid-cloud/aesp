from dflow.python import OP, OPIO, OPIOSign, Artifact, BigParameter
from pathlib import Path
from aesp.func.database import DataConnection
from pymatgen.io.ase import AseAtomsAdaptor
from dpgen2.utils import set_directory 
import json
import dpdata
from typing import Tuple, List
from aesp.calculator import calc_styles
from aesp.constant import struc_info_name
import os
from dflow.python import FatalError

from aesp.structure import struc_type

class PrepCalc(OP):
    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "calc_config": BigParameter(dict),
                "db": Artifact(Path, optional=True),
                "stage": int,
                "generation": int,
                "models": Artifact(Path, optional=True),
                "confs": Artifact(List[Path], optional=True)
            }
        )

    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "task_names": List[str],
                "task_paths": Artifact(List[Path])
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        stage = op_in['stage']
        generation = op_in['generation']
        config = op_in["calc_config"][op_in['stage']-1]

        calc_inputs = config['inputs']
        pstress = config['pstress']  # 压力
        calc_style = config["type"]
        confs = op_in['confs']

        calc_prep = calc_styles[calc_style]['prep']()

        task_names = []
        task_paths = []
        # fp-static使用
        if confs is not None:
            for conf in confs:
                ms = dpdata.MultiSystems(type_map=config['type_map'])
                ms.from_deepmd_npy(conf, labeled=False)  # type: ignore
                # loop over Systems in MultiSystems
                for ii in range(len(ms)):
                    s = ms[ii]
                    for ff in range(s.get_nframes()):
                        task_name = f"g{generation}_s{stage}_confs{ff}"
                        work_path = Path(task_name)
                        task_names.append(task_name)
                        task_paths.append(work_path)
                        info = {
                            "stage": stage,
                            "calc_style": calc_style,
                            "pstress" : pstress,
                            "data" : {}
                        }
                        with set_directory(work_path):
                            # 写入信息文件
                            with open(struc_info_name, 'w') as f:
                                json.dump(info, f)
                            # dp-csp使用
                            if op_in["models"] is not None:
                                calc_inputs.models = op_in["models"]
                            try:
                                calc_prep.prep_task(s[ff], calc_inputs)
                            except:
                                task_names.pop()
                                task_paths.pop()

        # 正常弛豫使用
        elif op_in['db'] is not None:
            dc = DataConnection(db_file_name=op_in['db'])
            strucs = dc.get_candidates(generation=generation, stage=stage-1)
            
            for struc in strucs:
                work_name = f"g{generation}_s{stage}_sid{struc.info['key_value_pairs']['s_id']}"
                work_path = Path(work_name)
                task_names.append(work_name)
                task_paths.append(work_path)
                work_path.mkdir(exist_ok=True, parents=True)

                info=struc.info['key_value_pairs']
                info.update({
                    "stage": stage,
                    "calc_style": calc_style,
                    "pstress" : pstress,
                    "data": struc.info['data']
                })
                
                # 写入信息文件
                with open(work_path / struc_info_name, 'w') as f:
                    json.dump(info, f)

                s = dpdata.System().from_ase_structure(struc)
                with set_directory(work_path):
                    # dp-csp使用
                    if op_in["models"] is not None:
                        calc_inputs.models = op_in["models"]
                    # 处理dpdata的错误
                    try:
                        calc_prep.prep_task(s, calc_inputs)
                    except:
                        task_names.pop()
                        task_paths.pop()
        else:
            raise FatalError()

        return OPIO(
            {
                "task_names": task_names,
                "task_paths": task_paths
            }
        )



class RunCalc(OP):

    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "task_path": Artifact(Path),
                "task_name": str,
                "calc_config": BigParameter(dict),
                "stage": int
            }
        )

    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "log": Artifact(Path),
                "labeled_data": Artifact(Path)
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        config = op_in["calc_config"][op_in['stage']-1]
        run_config = config["run_config"]

        calc_style = config["type"]
        calc_run= calc_styles[calc_style]['run']()


        task_name = op_in["task_name"]
        task_path = op_in["task_path"]
        input_files = calc_run.input_files()
        input_files = [(Path(task_path) / ii).resolve() for ii in input_files]
        opt_input_files = calc_run.optional_input_files()
        opt_input_files = [(Path(task_path) / ii).resolve() for ii in opt_input_files]
        work_dir = Path(task_name)

        with set_directory(work_dir):
            try:
                # link input files
                for ii in input_files:
                    if os.path.isfile(ii) or os.path.isdir(ii):
                        iname = ii.name
                        Path(iname).symlink_to(ii)
                    else:
                        raise FatalError(f"cannot find file {ii}")

                for ii in opt_input_files:
                    if os.path.isfile(ii) or os.path.isdir(ii):
                        iname = ii.name
                        Path(iname).symlink_to(ii)
                out_name, log_name = calc_run.run_task(**run_config)
            except:
                return OPIO(
                    {
                        "log": None,
                        "labeled_data": None
                    }
                )
            
        ls = dpdata.LabeledSystem().from_deepmd_npy(work_dir / out_name)

        with open(task_path / struc_info_name, "r") as f:
            info = json.load(f)
        # TODO 不同程序的收敛性判断
        info["status"] = 'converged'
        # # 写入信息文件
        with open(work_dir / out_name / struc_info_name, 'w') as f:
            json.dump(info, f)

        return OPIO(
            {
                "log": work_dir / log_name,
                "labeled_data": work_dir / out_name
            }
        )


