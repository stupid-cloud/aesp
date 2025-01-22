from dargs import Argument, Variant
from dpgen2.utils import step_conf_args
from aesp.calculator import calc_styles


def base_step_config(default_config):
    doc_gen_struc_config = "Step configuration for structure generation"
    doc_scheduler_config = "Step configuration for scheduler"
    return [   
        Argument(
            "gen_struc_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_gen_struc_config,
        ),
        Argument(
            "scheduler_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_scheduler_config,
        )
    ]

def stcsp_step_config(default_config):
    doc_prep_calc_config = "Step configuration for prepare calcalation"
    doc_run_calc_config = "Step configuration for run calcalation"
    return base_step_config(default_config) + [
        Argument(
            "prep_calc_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_calc_config,
        ),
        Argument(
            "run_calc_step",
            dict, 
            step_conf_args(), 
            optional=True,
            default=default_config,
            doc=doc_run_calc_config
        )
    ]



def dpcsp_step_config(default_config):
    doc_prep_dp_config = ""
    doc_run_dp_config = ""
    doc_prep_dp_config = ""
    doc_run_dp_config = ""
    doc_prep_dp_config = ""
    doc_run_dp_config = ""
    doc_prep_dp_config = ""
    doc_run_dp_config = ""
    return base_step_config(default_config) + [
        Argument(
            "prep_dp_train_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_dp_config,
        ),
        Argument(
            "run_dp_train_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "prep_fp_relax_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_dp_config,
        ),
        Argument(
            "run_fp_relax_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "prep_fp_static_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_dp_config,
        ),
        Argument(
            "run_fp_static_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "prep_fp_shield_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_dp_config,
        ),
        Argument(
            "run_fp_shield_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "prep_dp_relax_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_prep_dp_config,
        ),
        Argument(
            "run_dp_relax_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "select_confs_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "collect_data_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
        Argument(
            "calc_model_devi_step",
            dict,
            step_conf_args(),
            optional=True,
            default=default_config,
            doc=doc_run_dp_config,
        ),
    ]

# def run_calc_step_variant(default_config):
#     doc_input = "the type of the calc_stages"
#     inputs_list = []
#     for k in calc_styles.keys():
#         inputs_list.append(Argument(k, dict, step_conf_args(), default=default_config))
#     return Variant("type", inputs_list, optional=True, default_tag='vasp', doc=doc_input)

# def dp_run_calc_step_variant(default_config):
#     doc_input = "the type of the calc_stages"
#     return [
#         Argument('fp_relax', dict, step_conf_args(), default=default_config)
#     ]

