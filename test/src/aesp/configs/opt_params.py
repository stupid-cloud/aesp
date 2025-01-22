from dargs import Argument, Variant
from aesp.structure.bulk import Bulk
# from aesp.structure.layer import layer
from aesp.structure.cluster import Cluster


def opt_params_variant():
    doc_input = "Evolutionary algorithms based on different principles."
    doc_std = "Evolutionary algorithms based on each generation."
    inputs_list = []
    inputs_list.append(Argument("std", dict, std_config(), doc=doc_std))
    # inputs_list.append(Argument("pool", dict, pool_config()))
    return Variant("type", inputs_list, optional=True, default_tag='std', doc=doc_input)

def std_config():
    doc_generation = "Evolutionary algorithms are an iterative process, and each iteration is called a generation."
    doc_population = "In a evolutionary algorithm, a population is a collection of individuals."
    doc_operator = "The operator of structure generation."
    doc_cvg_criterion = "Convergence criteria for evolutionary algorithms"
    doc_seeds = "Random seed file path"
    return[
        Argument("generation", dict, generation_config(), optional=False, doc=doc_generation),
        Argument("population", dict, population_config(), optional=False, doc=doc_population),
        Argument("operator", dict, sub_variants=[operator_variant()], optional=False, doc=doc_operator),
        Argument("cvg_criterion", dict, cvg_criterion_confg(), optional=False, doc=doc_cvg_criterion),
        Argument("seeds", str, optional=True, default=None, doc=doc_seeds)
    ]


# generation ---------------------------------
def generation_config():
    doc_gen_size = "The size of the generated structures in each generation."
    doc_adaptive_config = 'Adaptive adjustment configuration'
    return [
        Argument("gen_size", int, optional=True, default=35, doc=doc_gen_size),
        Argument("adaptive", dict, sub_variants=[generation_adaptive_variant()], optional=True, default=None, doc=doc_adaptive_config)
    ]

def generation_adaptive_variant():
    doc_rca = ""
    doc_input = ""
    inputs_list = []
    inputs_list.append(Argument("rca", dict, generation_rca_config(), doc=doc_rca))
    return Variant("type", inputs_list, doc=doc_input)

def generation_rca_config():
    doc_size_change_ratio = 'The variable proportion of structure generation in each generation.'
    return [
        Argument("size_change_ratio", float, optional=True, default=0.5, doc=doc_size_change_ratio)
    ]

# population ---------------------------------
def population_config():
    doc_pop_size = "Population size per generation"
    doc_adaptive_config = 'Adaptive adjustment configuration'
    return [
        Argument("pop_size", int, optional=True, default=30, doc=doc_pop_size),
        Argument("adaptive", dict, sub_variants=[population_adaptive_variant()], optional=True, default=None, doc=doc_adaptive_config)
    ]

def population_adaptive_variant():
    doc_rca = "RCA mode"
    doc_input = "population change mode"
    inputs_list = []
    inputs_list.append(Argument("rca", dict, population_rca_config(), doc=doc_rca))
    return Variant("type", inputs_list, doc=doc_input)

def population_rca_config():
    doc_size_change_ratio = ''
    return [
        Argument("size_change_ratio", float, optional=True, default=0.2, doc=doc_size_change_ratio)
    ]

def operator_adaptive_variant():
    doc_adjustment = "Adjustment mode"
    doc_distribution = "Distribution model"
    doc_input = "Adaptive adjustment configuration"
    inputs_list = []
    inputs_list.append(Argument("adjustment", dict, adjustment_config(), doc=doc_adjustment))
    inputs_list.append(Argument("distribution", dict, distribution_config(), doc=doc_distribution))
    return Variant("type", inputs_list, doc=doc_input)


# ----------------------operator ----------------------
def operator_variant():
    doc_input = "The type of the operator"
    inputs_list = []
    inputs_list.append(Argument("bulk", dict, Bulk.args()))
    # inputs_list.append(Argument("layer", dict, operator_layer_config()))
    inputs_list.append(Argument("cluster", dict, Cluster.args()))
    return Variant("type", inputs_list, doc=doc_input)

  
# -----------------adaptive-------------------
# def operator_adaptive_variant():
#     doc_adjustment = "Adjustment mode"
#     doc_distribution = "Distribution model"
#     doc_input = ""
#     inputs_list = []
#     inputs_list.append(Argument("adjustment", dict, adjustment_config(), doc=doc_adjustment))
#     inputs_list.append(Argument("distribution", dict, distribution_config(), doc=doc_distribution))
#     return Variant("type", inputs_list, doc=doc_input)

# def adjustment_config():
#     doc_use_recent_pop = "Use of information from recent generations"
#     return [
#         Argument("use_recent_pop", int, optional=True, default=2, doc=doc_use_recent_pop),
#     ]

# def distribution_config():
#     doc_use_recent_pop = "Use of information from recent generations"
#     return [
#         Argument("use_recent_pop", int, optional=True, default=2, doc=doc_use_recent_pop)
#     ]

#  --------------cvg_criterion------------------------------------
def cvg_criterion_confg():
    doc_max_gen_num = "Maximum number of generations of evolutionary algorithms"
    doc_continuous_opt_num = "Number of consecutive optimizations of a single structure"
    return [
        Argument("max_gen_num", int, optional=True, default=10, doc=doc_max_gen_num),
        Argument("continuous_opt_num", int, optional=True, default=None, doc=doc_continuous_opt_num)
    ]
