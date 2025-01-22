
from aesp import __version__
import logging
from dflow import Workflow
from aesp.entrypoint.resubmit import resubmit_csp
from aesp.entrypoint.submit import submit_csp
from .download import download
from .watch import watch
from .status import status
from .analysis import analysis
from dpgen2.entrypoint.workflow import workflow_subcommands
from aesp.func.args_setup import args_setup
from aesp.func.entrypoint_func import *
from pathlib import Path
import os


def parse_args(args=None):
    parser = args_setup()
    parsed_args = parser.parse_args(args=args)
    if parsed_args.command is None:
        parser.print_help()
    return parsed_args


def main():
    # 设置logger
    change_logger()

    args = parse_args()
    # 打印logo
    print_logo()
    # 打印引用信息
    print_citation()
    
    if args.command == "gui":
        python_path = os.path.dirname(__file__)
        pa = Path(python_path).joinpath("..", "gui", "gui.py")
        os.system('python {} {}'.format(pa, args.path[0]))
        return

    # config check
    logging.info(f"Input file being checked for correctness")
    config = config_check(args.config)

    # 写入输入文件
    logging.info(f"The complete input file will be written to input-{args.config}")
    write_input(config, args.config)

    mode = config['aesp_config']['type']

    # steps list
    if args.command not in ["submit", 'resubmit']:
        wf = Workflow(id=args.id)
        step_dict = get_step_dict(wf) 
        step_list = get_step_list(step_dict)

    # if args.command in ['status']:
    #     wf = Workflow(id=args.id)
    #     last_step = get_last_step(wf)

    step_lists = []
    if args.command in ["resubmit"]:
        for id in args.id:
            wf = Workflow(id=id)
            step_dict = get_step_dict(wf)
            step_list = get_step_list(step_dict)
            step_lists.append(step_list)
    # command 
    if args.command == "submit":
        logging.info(f"The structure prediction is about to start")
        submit_csp(config, mode)
    elif args.command == "resubmit":
        logging.info(f"The structure prediction is about to restart")
        resubmit_csp(config, mode, step_lists, args.stepid)
    elif args.command == "status":
        logging.info(f"The current running status is being queried{(args.id)}")
        status(wf, mode, step_dict, args.step, args.destination, step_list[-1])
    elif args.command == "watch":
        logging.info(f"查看输出文件")
        watch(step_list, step_id=args.stepid)  
    elif args.command == "download":
        logging.info(f"下载当前文件")
        download(step_list, args.stepid, args.path[0], args.input, args.output)
    elif args.command == "analysis":
        logging.info(f"The output results are being analyzed")
        analysis(step_list, args.init, args.train, args.destination[0])
    elif args.command in workflow_subcommands:
        getattr(wf, args.command)()
    elif args.command is None:
        pass
    else:
        raise RuntimeError(f"unknown command {args.command}")   


if __name__ == "__main__":
    
    main()
    
