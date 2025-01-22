from dpgen2.exploration.render import TrajRenderLammps
from typing import List, Optional
import dpdata
from pathlib import Path


class TrajRender(TrajRenderLammps):

    def get_confs(
        self,
        trajs: List[Path],
        id_selected: List[List[int]],
        type_map: Optional[List[str]] = None,
        conf_filters = None,
    ) -> dpdata.LabeledSystem:
        del conf_filters  # by far does not support conf filters
        ntraj = len(trajs)
        traj_fmt = "lammps/dump"
        ms = dpdata.LabeledSystem(type_map=type_map)
        for ii in range(ntraj):
            if len(id_selected[ii]) > 0:
                ss = dpdata.System(trajs[ii], fmt=traj_fmt, type_map=type_map)
                ss.nopbc = self.nopbc
                ss = ss.sub_system(id_selected[ii])
                ms.append(ss)
        return ms