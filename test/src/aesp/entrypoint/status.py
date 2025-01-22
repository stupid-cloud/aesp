import json
from aesp.utils.tool import format_ranges
from aesp.constant import dflow_status

def status(
    wf,
    mode,
    step_dict,
    show_step_status,
    file_path,
    last_step
):
    
    print("Mode :", mode)
    status = wf.query_status()
    print("Workflow :", status)
    print("Current step :", last_step.key, last_step.phase)
    print()

    if show_step_status:
        for key, value in step_dict.items():
            print(f"Status ({key}):")  
            for k, v in value.items():
                t = []
                if isinstance(v, list):
                    str1 = v[0].key.rsplit('-', 1)[0]
                    for i in v:
                        t.append(int(i.key.rsplit('-', 1)[1]))             
                    res = f"{str1}-[{format_ranges(t)}]"        
                else:
                    res = v.key

                max_length_key =max(len(item) for item in value.keys())
                print(f"\t{k:{max_length_key}}:\t{res}")
            print()
    
    # 所有状态存入文件
    if file_path is not None:
        with open(file_path, "w") as f:
            json.dump(step_dict, f)

  