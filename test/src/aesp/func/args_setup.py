from aesp.configs.inputs import input_config, normalize_step_dict
from dargs import Argument
from aesp import __version__
import argparse
import json
from aesp.utils.tool import expand_idx
import logging
from dpgen2.entrypoint.submit import global_config_workflow
from dpgen2.entrypoint.workflow import workflow_subcommands
from art import text2art
from aesp.constant import dflow_status
import copy


def args_setup():
    parser = argparse.ArgumentParser(
        'aesp', 
        description="aesp is a tool for crystal structure prediction", 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(title="Valid subcommands", dest="command")

    ##########################################
    # submit
    parser_submit = subparsers.add_parser(
        "submit",
        help="Submit aesp workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_submit.add_argument(
        "config", help="the config file in json format defining the workflow."
    )
    
    # -----------------------gui
    parser_gui = subparsers.add_parser(
        "gui",
        help="gui aesp workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # parser_gui.add_argument(
    #     "config", help="the config file in json format defining the workflow."
    # )
    parser_gui.add_argument(
        "-p",
        "--path",
        type=str,
        nargs=1,
        default=["./results"],
        help="specify which Steps to reuse.",
    )
    
    ##########################################
    # resubmit
    parser_resubmit = subparsers.add_parser(
        "resubmit",
        help="Submiting aesp workflow resuing steps from an existing workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_resubmit.add_argument(
        "config", help="the config file in json format defining the workflow."
    )
    parser_resubmit.add_argument("id", nargs="+", type=str, default=None, help="the ID of the existing workflow.")
    parser_resubmit.add_argument(
        "-s",
        "--stepid",
        type=str,
        nargs="+",
        default=None,
        help="specify which Steps (id) to reuse.",
    )


    ##########################################
    # download
    parser_download = subparsers.add_parser(
        "download",
        help="Dwnloading aesp workflow resuing steps from an existing workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_download.add_argument(
        "config", help="the config file in json format defining the workflow."
    )
    parser_download.add_argument("id", help="the ID of the existing workflow.")
    parser_download.add_argument(
        "-s",
        "--stepid",
        type=str,
        nargs="+",
        default=None,
        help="Determining which Steps will be downloaded.",
    )
    parser_download.add_argument(
        "-p",
        "--path",
        type=str,
        nargs=1,
        default=["./downloads"],
        help="specify which Steps to reuse.",
    )
    parser_download.add_argument('-i', '--input', help='当前状态', action='store_true')
    parser_download.add_argument('-o', '--output', help='当前状态', action='store_true')

    ##########################################
    # analysis
    parser_analysis = subparsers.add_parser(
        "analysis",
        help="Dwnload aesp workflow resuing steps from an existing workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_analysis.add_argument(
        "config", help="the config file in json format defining the workflow."
    )
    parser_analysis.add_argument("id", help="the ID of the existing workflow.")
    parser_analysis.add_argument('-i', '--init', help='当前状态', action='store_true')
    parser_analysis.add_argument('-t', '--train', help='当前状态', action='store_true')
    parser_analysis.add_argument(
        "-d",
        "--destination",
        type=str,
        nargs=1,
        default=["./results"],
        help="specify which Steps to reuse.",
    )

    ##########################################
    # status
    parser_status = subparsers.add_parser(
        "status",
        help="Print the status of the aesp workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_status.add_argument("config", help="the config file in json format.")
    parser_status.add_argument("id", help="the ID of the existing workflow.")
    parser_status.add_argument('-s', '--step', help='当前状态', action='store_true')

    parser_status.add_argument(
        "-d",
        "--destination",
        type=str,
        nargs=1,
        default=None,
        help="specify which Steps to reuse.",
    )
    # watch
    parser_watch = subparsers.add_parser(
        "watch",
        help="Watch a aesp workflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_watch.add_argument("config", help="the config file in json format.")
    parser_watch.add_argument("id", help="the ID of the existing workflow.")
    parser_watch.add_argument(
        "-s",
        "--stepid",
        type=str,
        nargs="+",
        default=None,
        help="specify which Steps to watch.",
    )

    ##########################################
    # workflow subcommands
    for cmd in workflow_subcommands:
        parser_cmd = subparsers.add_parser(
            cmd,
            help=f"{cmd.capitalize()} a aesp workflow.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser_cmd.add_argument("config", help="the config file in json format.")
        parser_cmd.add_argument("id", help="the ID of the workflow.")

    # --version
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="aesp v%s" % __version__,
    )
    return parser

