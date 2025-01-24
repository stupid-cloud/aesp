.. _input_script:

Guide on writing input scripts
==============================

如果你熟悉 `dpgen2 <https://docs.deepmodeling.com/projects/dpgen2>`_，就能很容易理解下面的内容。反之如果你理解了下面的内容就容易上手dpgen2了.
The reader of this doc is assumed to be familiar with the 自适应进化算法 that the aesp implements. 
If not, one may check this `paper <https://docs.deepmodeling.com/projects/dpgen2>`_.


AESP的输入文件是json格式的文件，主要为三个个大部分，分别为dflow的配置文件（dflow_config，dflow_s3_config，default_step_config），
以及aesp关于算法的一些配置（aesp_config）。

The input script for all aesp commands
--------------------------------------

For all the aesp commands, one need to provide `dflow <https://github.com/deepmodeling/dflow>`_ global configurations. 
一般情况下设置为以下模式：


.. code:: json

    "dflow_config" : {
		"mode" : "debug"
	},
    "dflow_s3_config" : {}

The aesp simply pass all keys of "dflow_config" to dflow.config and all keys of "dflow_s3_config" to dflow.s3_config.

The input script for submit or resubmit commands
------------------------------------------------

aesp_config主要有两种模式，一种是常规的遗传算法结构预测流程,利用经验势、量子力学计算以及已经训练好的机器学习势函数进行结构预测;
另一种是使用主动学习和机器学习势相结合的方式，可以在结构预测的同时训练相应的机器学习势函数，加快预测的效率。指定模式可以输入如下：

.. code:: json

    "aesp_config" : {
        "mode": "std-csp"
    }

首先是优化算法的一些参数设置。进化算法也设置了两种方式，包括传统方式，也就是结构随每一代的进化而更新，另一种是所有的结构都带进程池中，
没有代的概念。

常规模式
^^^^^^^

完整的输入文件可以在这里下载。

std
>>>

首先是种群以及代的参数

.. code:: json

    "aesp_config" : {
        "opt_params" : {
            "generation" : {
                "gen_size" : 50,
                "adaptive" : {
                    "type" : "rca",
                    "size_change_ratio" : 0.5
                }
            },
            "population" : {
                "pop_size" : 40,
                "adaptive" : {
                    "type" : "rca",
                    "size_change_ratio" : 0.5
                }	
            }
        }  
    }

其中 ``generation`` 和 ``population`` 的参数基本是一致的，但我们最好保持 ``population`` 的 ``size`` 要大于 ``generation`` 的；
其中 ``adptive`` 是自适应的参数，也有两种方式。两种方式的参数是一样的都只有 ``size_change_ratio``，代表了 ``size``的变化比例；
比如 ``size`` 为50, 则 ``size`` 的变化范围为[50*(1-0.5), 50*(1+0.5)]


其次是一些操作符的参数

.. code:: json

    "aesp_config" : {
        "opt_params" : {
            "type" : "std",
            "operator" : {
                "type" : "bulk",
                "generator" : {
                    "prob" : 0.4,
                    "random_gen_prob" : 1,
                    "random_gen_params" : {
                        "composition" : {"B": 1, "C": 3},
                        "_spgnum" : ["1-230"],
                        "factor" : 1.1,
                        "_thickness" : 2,
                        "max_count" : 50
                    }
                },
                "crossover" : {
                    "prob" : 0.3,
                    "plane_cross_prob" : 0.333,
                    "sphere_cross_prob" : 0.333,
                    "cylinder_cross_prob" : 0.334,
                    "plane_cross_params" : {
                        "stddev" : 0.1,
                        "max_count" : 5
                    },
                    "sphere_cross_params" : {
                        "max_count" : 5
                    },
                    "cylinder_cross_params" : {
                        "max_count" : 5
                    }
                },
                "mutation" : {
                    "prob" : 0.3,
                    "continuous_mut_factor" : 2, 
                    "strain_mut_prob" : 0.333,
                    "permutation_mut_prob" : 0.333,
                    "ripple_mut_prob" : 0.334,
                    "strain_mut_params" : {
                        "stddev" : 0.1,
                        "max_count" : 5
                    },
                    "permutation_mut_params" : {
                        "max_count" : 5
                    },
                    "ripple_mut_params" : {
                        "max_count" : 5,
                        "rho" : 0.3,
                        "miu" : 2,
                        "eta" : 1
                    }
                },
                "adaptive" : {
                    "type": "adjustment",
                    "use_recent_gen" : 2
                },
                "hard_constrains" : {
                    "alpha" : [30, 150],
                    "beta" : [30, 150],
                    "gamma" : [30, 150],
                    "chi" : [0, 180],
                    "psi" : [0, 180],
                    "phi" : [0, 180],
                    "a" : [0, 100],
                    "b" : [0, 100],
                    "c" : [0, 100],
                    "tol_matrix" : {
                        "_tuples" : [["Cl", "Na", 12], ["Cl", "Cl", 12], ["Na", "Na", 12]],
                        "prototype" : "atomic", 
                        "factor" : 1.0
                    }
                }
            }
        }
    }

其中 ``operator`` 根据不同的体系包含了多种模式，分别有bulk,cluster. ``operator`` 包含了三种方式，分别是 
``generator``, ``mutation`` 以及 ``crossover``.下面的 ``adaptive`` 指的是三种操作符的自适应参数。
其中 ``type`` 有两种方式。 ``hard_constrains`` 代表了对每种操作符生成结构的一些约束。包含了对晶格的一些角度（包括二面角）以及晶格常量
的一些限制； ``tol_matrix`` 是对原子间距离的一些限制。 ``generator``, ``mutation`` 以及 ``crossover`` 里面的 ``prob`` 代表了选择该方式的概率，并且三者的概率和为1.每个操作符又分别有不同的操作模式，
他们的概率分别为 ``xxx_gen_prob`` （和为1）, ``xxx_mut_prob`` （和为1） 以及 ``xxx_cross_prob`` （和为1）. 并且 ``xxx_xxx_params`` 
对应相应操作的一些参数。

同时我们需要定义算法的收敛条件，也就是 ``cvg_criterion`` .

.. code:: json
    
    "aesp_config" : {
        "opt_params" : {
            "cvg_criterion" : {
                "max_gen_num" : 10,
                "continuous_opt_num" : null
            }
        }
    }

我们还需要明确每个结构的计算方式

.. code:: json
    "aesp_config" : {
        "calc_stages" : [
            {
                "type" : "vasp",
                "task_max" : 1,
                "pstress" : 0.0,
                "inputs_config" : {
                    "incar" : "../1_INCAR",
                    "kspacing": 0.4,
                    "kgamma": false,
                    "pp_files": {"B": "../../POTCAR_B", "C": "../../POTCAR_C"}
                },
                "run_config" : {
                    "command" : "mpirun -np 2 vasp_std",
                    "_command" : "source /opt/intel/oneapi/setvars.sh;mpirun -np 8 vasp_std"
                }
            },
            {
                "type" : "vasp",
                "task_max" : 1,
                "pstress" : 0.0,
                "inputs_config" : {
                    "incar" : "../2_INCAR",
                    "kspacing": 0.25,
                    "kgamma": false,
                    "pp_files": {"B": "../../POTCAR_B", "C": "../../POTCAR_C"}
                },
                "run_config" : {
                    "command" : "mpirun -np 2 vasp_std",
                    "_command" : "source /opt/intel/oneapi/setvars.sh;mpirun -np 8 vasp_std"
                }
            }
        ]
    }
   




The execution units of the aesp are the dflow Steps. How each step is executed is defined by the "step_configs".

.. code:: json

    "aesp_config" : {
        "step_configs" : {}
    }

The configs for prepare training, run training, prepare exploration, run exploration, prepare fp, 
run fp, select configurations, collect data and concurrent learning steps are given correspondingly.

Any of the config in the "step_configs" can be ommitted. If so, the configs of the step is set to the 
default step configs, which is provided by the following section, for example,

.. code:: json

    "aesp_config" : {
        "default_step_config" : {
            "template_slice_config" : {
                "group_size": 8,
                "pool_size" : 1
            },
            "executor" : {
                "type" : "dispatcher",
                "host" : "127.0.0.1",
                "image_pull_policy" : "IfNotPresent",
                "username" : "clqin",
                "password" : "clqin",
                "machine_dict" : {
                    "batch_type" : "Shell",
                    "context_type" : "local",
                    "local_root" : "./",
                    "remote_root" : "/home/zhao/work"
                },
                "resources_dict" : {
                    "cpu_per_node" : 8,
                    "gpu_per_node" : 1,
                    "group_size" : 1
                }
            }
        }
    }

The way of writing the "default_step_config" is the same as any step config in the "step_configs".

pool
>>>>

.. note::

    还在开发中

主动学习
^^^^^^^

.. note::

    还在测试中

