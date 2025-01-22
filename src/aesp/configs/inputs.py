from dpgen2.utils import normalize_step_dict
from dargs import Argument, Variant
from dpgen2.entrypoint.args import dflow_conf_args, submit_args
from aesp.configs.step import stcsp_step_config, dpcsp_step_config
from aesp.configs.opt_params import opt_params_variant
from aesp.configs.stage import calc_stages_variant, dpcsp_stages_config
from dpgen2.entrypoint.args import step_conf_args



def input_config(default_step_config=normalize_step_dict({})):
    doc_aesp_config = "Configuration of AESP"
    doc_parallelism = "Maximum number of running pods for the workflow."
    doc_default_step_config = "The default step configuration."
    return dflow_conf_args() + [
            Argument("parallelism", int, optional=True, default=None, doc=doc_parallelism),
            Argument("default_step_config", dict, step_conf_args(), optional=True, default={}, doc=doc_default_step_config),
            Argument("aesp_config", dict, sub_variants=[input_varint(default_step_config)], optional=False, doc=doc_aesp_config)    
        ]

def input_varint(default_step_config):
    doc_type = "Different structure prediction workflow in AESP."
    doc_stdsp = "Standard workflow based on interatomic potentials or quantum chemistry methods."
    doc_alsp = "Workflow based on active learning and machine learning potentials."
    inputs_list = []
    inputs_list.append(Argument("std-sp", dict, stdcsp_config(default_step_config), doc=doc_stdsp))
    inputs_list.append(Argument("al-sp", dict, alcsp_config(default_step_config), doc=doc_alsp))
    # inputs_list.append(Argument("pool", dict, pool_config()))
    return Variant("type", inputs_list, optional=True, default_tag="std-sp", doc=doc_type)

def csp_base_config():
    doc_opt_algo = "Configuration of optimization algorithms."
    return [
            Argument("opt_params", dict, sub_variants=[opt_params_variant()], optional=False, doc=doc_opt_algo)
        ]
    
def stdcsp_config(default_step_config):
    doc_calc_stages = ""
    doc_step_configs = ""
    return csp_base_config() + [
        Argument(
                "calc_stages", 
                list, 
                sub_variants=[calc_stages_variant()], 
                optional=False, 
                repeat=True,
                doc=doc_calc_stages
            ),
        Argument(
                "step_configs",
                dict,
                stcsp_step_config(default_step_config),
                optional=False,
                default={},
                doc=doc_step_configs,
            ),
    ]         

def alcsp_config(default_step_config):
    doc_calc_stages = ''
    doc_step_configs = ''
    doc_train_stages = ''

    return csp_base_config() + [
            Argument(
                "step_configs",
                dict,
                dpcsp_step_config(default_step_config),
                optional=True,
                default={},
                doc=doc_step_configs,
            ),
            Argument(
                "calc_stages", 
                dict, 
                dpcsp_stages_config(), 
                optional=False, 
                doc=doc_calc_stages
            )  
    ]

# def gen_doc(*, make_anchor=True, make_link=False, **kwargs):
#     if make_link:
#         make_anchor = True
#     # sca = input_config()
#     # base = Argument("submit", dict, sub_variants=[sca])
#     sca = csp_base_config()
#     base = Argument("submit", dict, sca)
#     ptr = []
#     ptr.append(base.gen_doc(make_anchor=make_anchor, make_link=make_link, **kwargs))
#     key_words = []
#     for ii in "\n\n".join(ptr).split("\n"):
#         if "argument path" in ii:
#             key_words.append(ii.split(":")[1].replace("`", "").strip())
#     return "\n\n".join(ptr)

if __name__ == "__main__":
    print(gen_doc())
    # from dpgen2.entrypoint.args import gen_doc
    # print(gen_doc())