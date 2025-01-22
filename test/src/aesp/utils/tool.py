from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Kpoints
import numpy as np
from ase.spacegroup import get_spacegroup
import textwrap

def print_in_box(text, width):
    """
    将给定文本打印在一个框内，能处理文本中的制表符和换行符，并自动进行合适的排版。
    """
    lines = []
    for line in text.splitlines():
        wrapped_lines = textwrap.wrap(line, width)  # 这里可根据实际需求调整width值来控制每行宽度
        lines.extend(wrapped_lines)
    max_length = max(len(line) for line in lines) + 4
    print("+" + "-" * max_length + "+")
    for line in lines:
        print("|  " + line.ljust(max_length - 4) + "  |")
    print("+" + "-" * max_length + "+")

def format_ranges(lst):
    """status格式化使用"""
    if not lst:
        return []
    lst.sort()
    # 初始化结果列表和当前区间的起始点
    result = []
    start = lst[0]
    end = lst[0]

    for i in range(1, len(lst)):
        # 检查当前元素是否是前一个元素的连续后续
        if lst[i] == lst[i - 1] + 1:
            end = lst[i]
        else:
            # 如果不是连续的，先保存之前的区间
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            # 更新起始点和终止点
            start = lst[i]
            end = lst[i]

    # 保存最后一个区间
    if start == end:
        result.append(str(start))
    else:
        result.append(f"{start}-{end}")
    rlt_str = " ".join(result)
    return rlt_str



def get_kpoints(structure: Structure, kppa: float, force_gamma: bool = False):
    """kpoints产生"""
    comment = f"K-Spacing Value to Generate K-Mesh: {kppa}"
    num_div = []
    num_div.append(structure.lattice.reciprocal_lattice.a/2/np.pi/kppa)
    num_div.append(structure.lattice.reciprocal_lattice.b/2/np.pi/kppa)
    num_div.append(structure.lattice.reciprocal_lattice.c/2/np.pi/kppa)
    num_div = [int(np.round(max(div, 1))) for div in num_div]
    lattice = structure.lattice

    is_hexagonal = lattice.is_hexagonal()
    is_face_centered = structure.get_space_group_info()[0][0] == "F"
    has_odd = any(idx % 2 == 1 for idx in num_div)
    if has_odd or is_hexagonal or is_face_centered or force_gamma:
        style = Kpoints.supported_modes.Gamma
    else:
        style = Kpoints.supported_modes.Monkhorst
    return Kpoints(comment, 0, style, [num_div], (0, 0, 0))


def expand_idx(in_list):
    ret = []
    for ii in in_list:
        if isinstance(ii, int):
            ret.append(ii)
        elif isinstance(ii, str):
            step_str = ii.split(":")
            if len(step_str) > 1:
                step = int(step_str[1])
            else:
                step = 1
            range_str = step_str[0].split("-")
            if len(range_str) == 2:
                ret += range(int(range_str[0]), int(range_str[1])+1, step)
            elif len(range_str) == 1:
                ret += [int(range_str[0])]
            else:
                raise RuntimeError("not expected range string", step_str[0])
    ret = sorted(list(set(ret)))
    return ret





def create_symlinks(source_dir, target_dir):
    # source_dir = Path(source_dir)
    # target_dir = Path(target_dir)
    
    # 确保目标目录存在
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # 遍历源目录中的所有文件
    for item in source_dir.iterdir():
        # 仅处理文件，跳过目录
        if item.is_file():
            target_path = target_dir / item.name        
            target_path.symlink_to(item)
            

