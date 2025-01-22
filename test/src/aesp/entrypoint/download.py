from dflow import download_artifact
from pathlib import Path
import logging
from aesp.utils.tool import expand_idx



def download(
    step_list,
    step_id,
    path,
    input_flag,
    output_flag   
):
    step_id = expand_idx(step_id)
    for id in step_id:
        id = int(id)
        file_path = Path(path) / step_list[id].key
        file_path.mkdir(parents=True, exist_ok=True)
        
        if input_flag:
            f_path = file_path / 'inputs'
            f_path.mkdir(parents=True, exist_ok=True)
            for key in step_list[id].inputs.artifacts.keys():
                download_artifact(step_list[id].inputs.artifacts[key], path=f_path, skip_exists=True)

        if output_flag:
            f_path = file_path / 'outputs'
            f_path.mkdir(parents=True, exist_ok=True)
            for key in step_list[id].outputs.artifacts.keys():
                download_artifact(step_list[id].outputs.artifacts[key], path=f_path, skip_exists=True)
        logging.info(f"Step {step_list[id].key} has been downloaded")