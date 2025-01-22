from .submit import submit_csp
from aesp.utils.tool import expand_idx

def split_list(lst):
    # 初始化结果列表和临时子列表
    result = []
    current_sublist = []

    # 遍历列表
    for item in lst:
        if item in [",", ":", '.']:  # 遇到逗号时，分割列表
            result.append(current_sublist)
            current_sublist = []
        else:
            current_sublist.append(item)

    # 将最后一个子列表添加到结果列表中
    if current_sublist:
        result.append(current_sublist)
    return result


def resubmit_csp(
    wf_config,
    mode,
    step_lists,
    step_id
):
  
    if step_id is None:
        return
    step_id_list = split_list(step_id)
 
    assert len(step_id_list) == len(step_lists)
    reuse_step = []
    for s_id, steps in zip(step_id_list, step_lists):
        new_id = expand_idx(s_id)
        reuse_step += [steps[ii] for ii in new_id]
    
    submit_csp(
        wf_config,
        mode,
        reuse_step=reuse_step
    )


