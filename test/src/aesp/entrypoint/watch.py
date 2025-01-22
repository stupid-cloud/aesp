import logging
from typing import (List, Optional)
from aesp.utils.tool import expand_idx
import yaml
from dpgen2.utils.dflow_query import matched_step_key
from dpgen2.utils.download_dpgen2_artifacts import download_dpgen2_artifacts


default_watching_keys = [
    "prep-run-train",
    "prep-run-explore",
    "prep-run-fp",
    "collect-data",
]

default_watching_keys = [
    "prep-run-train",
    "prep-run-explore",
    "prep-run-fp",
    "collect-data",
]


def update_finished_steps(
    wf,
    finished_keys: Optional[List[str]] = None,
    download: Optional[bool] = False,
    watching_keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    chk_pnt: bool = False,
):
    wf_keys = wf.query_keys_of_steps()
    wf_keys = matched_step_key(wf_keys, watching_keys)
    if finished_keys is not None:
        diff_keys = []
        for kk in wf_keys:
            if not (kk in finished_keys):
                diff_keys.append(kk)
    else:
        diff_keys = wf_keys
    for kk in diff_keys:
        logging.info(f'steps {kk.ljust(50,"-")} finished')
        if download:
            download_dpgen2_artifacts(wf, kk, prefix=prefix, chk_pnt=chk_pnt)
            logging.info(f'steps {kk.ljust(50,"-")} downloaded')
    finished_keys = wf_keys
    return finished_keys

def watch(
    step_list,
    step_id
):  
    if step_id is None:
        return
    step_id = expand_idx(step_id)
    
    info_dict = {}
    # For reused steps whose startedAt are identical, sort them by key
    if step_id is not None:
        for id in step_id:
            info_dict['key'] = step_list[int(id)].data['key']
            info_dict['status'] = step_list[int(id)].data['phase']
            info_dict['inputs'] = {}
            info_dict['outputs'] = {}
            info_dict['inputs']['parameters'] = list(step_list[int(id)].data['inputs']['parameters'].keys())
            info_dict['inputs']['artifacts'] = list(step_list[int(id)].data['inputs']['artifacts'].keys())
            info_dict['outputs']['parameters'] = list(step_list[int(id)].data['outputs']['parameters'].keys())
            info_dict['outputs']['artifacts'] = list(step_list[int(id)].data['outputs']['artifacts'].keys())
            print(yaml.dump(info_dict, sort_keys=False))

        # pprint(steps[0].data)
