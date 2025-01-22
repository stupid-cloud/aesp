from dargs import Argument, Variant
from aesp.calculator import calc_styles
from dpgen2.entrypoint.args import variant_conv, dp_train_args, dp_dist_train_args
from dpgen2.entrypoint.args import input_args
from aesp.workflow.op.run_dp_train import RunDPTrain1


def dpcsp_stages_config():
    doc_fp_relax = "Configuration for preparing inputs"
    doc_dp_relax = "Configuration for running tasks"
    doc_fp_static = "Maximum number of calc tasks for each iteration"
    doc_fp_shield = ""
    doc_dp_train_inputs = ""
    doc_dp_train = "Configuration for preparing inputs"
    doc_stage_stop_cond = "Maximum number of calc tasks for each iteration"
    return [
        Argument(
            "fp_relax",
            dict,
            sub_variants=[calc_stages_variant("fp_relax")],
            optional=True,
            default=None,
            doc=doc_fp_relax,
        ),
        Argument(
            "dp_relax",
            dict,
            sub_variants=[calc_stages_variant()],
            optional=False,
            doc=doc_dp_relax,
        ),
        Argument(
            "fp_static",
            dict,
            sub_variants=[calc_stages_variant()],
            optional=False,
            doc=doc_fp_static,
        ),
        Argument(
            "fp_shield",
            dict,
            sub_variants=[calc_stages_variant()],
            optional=True,
            default=None,
            doc=doc_fp_shield,
        ),
        Argument(
            "dp_train",
            dict,
            sub_variants=[variant_train1()],
            optional=False,
            doc=doc_dp_train,
        ),
        Argument("dp_train_inputs", dict, input_args(), optional=False, doc=doc_dp_train_inputs),
        Argument(
            "stage_stop_cond",
            dict,
            stage_stop_cond_config(),
            optional=False,
            doc=doc_stage_stop_cond,
        )
    ]

def stage_stop_cond_config():
    doc_max_stage_iter = "Maximum number of iterations per stage"
    doc_fatal_at_max = (
        "Fatal when the number of iteration per stage reaches the `max_numb_iter`"
    )
    doc_convergence = "The method of convergence check."

    return [
       Argument(
            "convergence",
            dict,
            [],
            [variant_conv()],
            optional=False,
            doc=doc_convergence,
        ),
        Argument(
            "max_stage_iter", int, optional=True, default=10, doc=doc_max_stage_iter
        ),
        Argument(
            "fatal_at_max", bool, optional=True, default=True, doc=doc_fatal_at_max
        )
    ]


def calc_stage_config(inputs, run):
    doc_inputs_config = "Configuration for preparing inputs"
    doc_run_config = "Configuration for running tasks"
    doc_task_max = "Maximum number of calc tasks for each iteration"
    doc_pstress = "" 
    return [
        Argument(
            "inputs_config",
            dict,
            inputs.args(),
            optional=False,
            doc=doc_inputs_config,
        ),
        Argument(
            "run_config",
            dict,
            run.args(),
            optional=False,
            doc=doc_run_config,
        ),
        Argument("task_max", int, optional=True, default=10, doc=doc_task_max),
        Argument("pstress", float, optional=True, default=0.0, doc=doc_pstress)
    ]

def calc_stages_variant(key=None):
    doc_input = "the type of the calc_stages"
    doc_gen_num = "the type of the calc_stages"
    inputs_list = []
    for k in calc_styles.keys():
        sub_filed = calc_stage_config(calc_styles[k]['inputs'], calc_styles[k]['run'])
        if k == key:
            sub_filed += [
                Argument("gen_num", int, optional=True, default=1, doc=doc_gen_num)
            ]
        inputs_list.append(Argument(k, dict, calc_stage_config(calc_styles[k]['inputs'], calc_styles[k]['run'])))
    return Variant("type", inputs_list, doc=doc_input)

# ---------------------------
def dp_train_args1():
    doc_config = "Configuration of training"
    temp = dp_train_args()
    temp.pop(0)
    return temp + [
        Argument(
            "config",
            dict,
            RunDPTrain1.training_args(),
            optional=True,
            default=RunDPTrain1.normalize_config({}),
            doc=doc_config,
        )
    ]

def dp_dist_train_args1():
    doc_config = "Configuration of training"
    temp = dp_dist_train_args()
    temp.pop(0)
    return temp + [
        Argument(
            "config",
            dict,
            RunDPTrain1.training_args(),
            optional=True,
            default=RunDPTrain1.normalize_config({}),
            doc=doc_config,
        )
    ]
def variant_train1():
    doc = "the type of the training"
    return Variant(
        "type",
        [
            Argument("dp", dict, dp_train_args1()),
            Argument("dp-dist", dict, dp_dist_train_args1()),
        ],
        doc=doc,
    )
# ---------------------------