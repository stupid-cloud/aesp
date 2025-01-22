from dpgen2.op.run_dp_train import RunDPTrain
from dpgen2.utils.run_command import run_command
from dargs import Argument
from dflow.python import (
    OP,
    OPIO,
    TransientError,
    FatalError
)
from dpgen2.utils.chdir import set_directory
import os
import logging
import shutil
from dpgen2.op.run_dp_train import _expand_all_multi_sys_to_sys, _make_train_command
from dpgen2.constants import train_script_name
from pathlib import Path
import json

class RunDPTrain1(RunDPTrain):
    @OP.exec_sign_check
    def execute(
        self,
        ip: OPIO,
    ) -> OPIO:
        r"""Execute the OP.

        Parameters
        ----------
        ip : dict
            Input dict with components:

            - `config`: (`dict`) The config of training task. Check `RunDPTrain.training_args` for definitions.
            - `task_name`: (`str`) The name of training task.
            - `task_path`: (`Artifact(Path)`) The path that contains all input files prepareed by `PrepDPTrain`.
            - `init_model`: (`Artifact(Path)`) A frozen model to initialize the training.
            - `init_data`: (`Artifact(NestedDict[Path])`) Initial training data.
            - `iter_data`: (`Artifact(List[Path])`) Training data generated in the DPGEN iterations.

        Returns
        -------
        Any
            Output dict with components:
            - `script`: (`Artifact(Path)`) The training script.
            - `model`: (`Artifact(Path)`) The trained frozen model.
            - `lcurve`: (`Artifact(Path)`) The learning curve file.
            - `log`: (`Artifact(Path)`) The log file of training.

        Raises
        ------
        FatalError
            On the failure of training or freezing. Human intervention needed.
        """
        prep_command = ip["config"].pop('command')
        mixed_type = ip["optional_parameter"]["mixed_type"]
        finetune_mode = ip["optional_parameter"]["finetune_mode"]
        config = ip["config"] if ip["config"] is not None else {}
        impl = ip["config"].get("impl", "tensorflow")
        assert impl in ["tensorflow", "pytorch"]
        if impl == "pytorch":
            dp_command = ["dp", "--pt"]
        else:
            dp_command = ["dp"]
        finetune_args = config.get("finetune_args", "")
        train_args = config.get("train_args", "")
        config = RunDPTrain.normalize_config(config)
        task_name = ip["task_name"]
        task_path = ip["task_path"]
        init_model = ip["init_model"]
        init_data = ip["init_data"]
        iter_data = ip["iter_data"]
        valid_data = ip["valid_data"]
        iter_data_old_exp = _expand_all_multi_sys_to_sys(iter_data[:-1])
        iter_data_new_exp = _expand_all_multi_sys_to_sys(iter_data[-1:])
        iter_data_exp = iter_data_old_exp + iter_data_new_exp
        work_dir = Path(task_name)
        init_model_with_finetune = config["init_model_with_finetune"]

        # update the input script
        input_script = Path(task_path) / train_script_name
        with open(input_script) as fp:
            train_dict = json.load(fp)
        if "systems" in train_dict["training"]:
            major_version = "1"
        else:
            major_version = "2"

        # auto prob style
        do_init_model = RunDPTrain.decide_init_model(
            config,
            init_model,
            init_data,
            iter_data,
            mixed_type=mixed_type,
        )
        auto_prob_str = "prob_sys_size"
        if do_init_model:
            old_ratio = config["init_model_old_ratio"]
            if config["multitask"]:
                head = config["head"]
                len_init = len(init_data[head])
            else:
                len_init = len(init_data)
            numb_old = len_init + len(iter_data_old_exp)
            numb_new = numb_old + len(iter_data_new_exp)
            auto_prob_str = f"prob_sys_size; 0:{numb_old}:{old_ratio}; {numb_old}:{numb_new}:{1.-old_ratio:g}"

        # update the input dict
        train_dict = RunDPTrain.write_data_to_input_script(
            train_dict,
            config,
            init_data,
            iter_data_exp,
            auto_prob_str,
            major_version,
            valid_data,
        )
        train_dict = RunDPTrain.write_other_to_input_script(
            train_dict, config, do_init_model, major_version
        )

        if RunDPTrain.skip_training(
            work_dir, train_dict, init_model, iter_data, finetune_mode
        ):
            return OPIO(
                {
                    "script": work_dir / train_script_name,
                    "model": init_model,
                    "lcurve": work_dir / "lcurve.out",
                    "log": work_dir / "train.log",
                }
            )

        with set_directory(work_dir):
            # open log
            fplog = open("train.log", "w")

            def clean_before_quit():
                fplog.close()

            # dump train script
            with open(train_script_name, "w") as fp:
                json.dump(train_dict, fp, indent=4)

            if ip["optional_files"] is not None:
                for f in ip["optional_files"]:
                    Path(f.name).symlink_to(f)

            # train model
            command = _make_train_command(
                dp_command,
                train_script_name,
                impl,
                do_init_model,
                init_model,
                finetune_mode,
                finetune_args,
                init_model_with_finetune,
                train_args,
            )

            command = " ".join(command)
            command = prep_command + command
            ret, out, err = run_command(command, shell=True)
            if ret != 0:
                clean_before_quit()
                logging.error(
                    "".join(
                        (
                            "dp train failed\n",
                            "out msg: ",
                            out,
                            "\n",
                            "err msg: ",
                            err,
                            "\n",
                        )
                    )
                )
                raise FatalError("dp train failed")
            fplog.write("#=================== train std out ===================\n")
            fplog.write(out)
            fplog.write("#=================== train std err ===================\n")
            fplog.write(err)

            if finetune_mode == "finetune" and os.path.exists("input_v2_compat.json"):
                shutil.copy2("input_v2_compat.json", train_script_name)

            # freeze model
            if impl == "pytorch":
                model_file = "model.ckpt.pt"
            else:
                command = " ".join(["dp", "freeze", "-o", "frozen_model.pb"])
                command = prep_command + command
                ret, out, err = run_command(command, shell=True)
                if ret != 0:
                    clean_before_quit()
                    logging.error(
                        "".join(
                            (
                                "dp freeze failed\n",
                                "out msg: ",
                                out,
                                "\n",
                                "err msg: ",
                                err,
                                "\n",
                            )
                        )
                    )
                    raise FatalError("dp freeze failed")
                model_file = "frozen_model.pb"
            fplog.write("#=================== freeze std out ===================\n")
            fplog.write(out)
            fplog.write("#=================== freeze std err ===================\n")
            fplog.write(err)

            clean_before_quit()

        return OPIO(
            {
                "script": work_dir / train_script_name,
                "model": work_dir / model_file,
                "lcurve": work_dir / "lcurve.out",
                "log": work_dir / "train.log",
            }
        )
    
    @staticmethod
    def training_args():
        doc_command = ""
        temp = RunDPTrain.training_args()
        return temp + [
             Argument(
                "command",
                str,
                optional=True,
                default=None,
                doc=doc_command
            )
        ]
    
if __name__ =="__main__":
    print(RunDPTrain1.training_args())