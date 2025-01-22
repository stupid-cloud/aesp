from dflow.python import OP, OPIO, OPIOSign, Artifact
from pathlib import Path
import numpy as np 
from typing import List
from dpdata import LabeledSystem
from dpgen2.op.run_caly_model_devi import atoms2lmpdump



class CalcModelDevi(OP):
    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign(
            {
                "models": Artifact(List[Path]),
                "labeled_data": Artifact(Path),
                "task_name": str
            }
        )
    
    @classmethod
    def get_output_sign(cls):
        return OPIOSign(
            {
                "model_devis": Artifact(Path),
                "trajs": Artifact(Path), 
                "type_map": List[str]
            }
        )

    @OP.exec_sign_check
    def execute(
        self,
        op_in: OPIO,
    ) -> OPIO:
        from deepmd.infer.model_devi import calc_model_devi
        from deepmd.infer import DeepPot
        model_list = op_in['models']
        labeled_data = op_in['labeled_data']
        
        ls = LabeledSystem(labeled_data, fmt='deepmd/npy')

        work_dir = Path("./{}".format(op_in['task_name']))
        work_dir.mkdir(parents=True, exist_ok=True)
        graphs = [DeepPot(model) for model in model_list]
        ase_strucs = ls.to_ase_structure()

        # traj
        dump_str = ""
        for idx, atom in enumerate(ase_strucs):
            dump_str += atoms2lmpdump(atom, idx, list(set(atom.get_chemical_symbols())), ignore=True) % idx  
        work_dir.joinpath('traj.dump').write_text(dump_str)

        # dump
        devi = calc_model_devi(ls['coords'], ls['cells'], ls['atom_types'], graphs)
        header = "step\t"
        for item in "vf":
            header += "%s\t%s\t%s\t" % (
                f"max_devi_{item}",
                f"min_devi_{item}",
                f"avg_devi_{item}"
            )
        header += "%s" % "devi_e"
        np.savetxt(work_dir.joinpath("model_devi.out"), devi, delimiter='\t', header=header, fmt=["%6d"]+["%6e" for _ in range(devi.shape[1]-1)])


        # 返回文件目录
        op_out = OPIO(
            {
                "model_devis": work_dir.joinpath("model_devi.out"),
                "trajs": work_dir.joinpath('traj.dump'),
                "type_map": ls['atom_names']
            }
        )
        return op_out
