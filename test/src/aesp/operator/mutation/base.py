import numpy as np
import copy
from aesp.operator.base import OperatorBase


class Mutation(OperatorBase):
    def __init__(self, max_count):
        super().__init__(max_count)
    
    def get_new_candidate(self, parent, clear_info):
        mutant = parent.copy()
        if clear_info:
            mutant.info = {}
        for _ in range(self.max_count):
            child = self.mutate(mutant) # 变异
            if child is None:
                continue
            if child.is_within_bounds() and child.check_distance()[0]:
                break   
        else:
            return None
   
        # 更新操作描述
        child.info.update({'oper_type': 'mutation'})
        child.info['data'] = {} # data初始化
        oper_name = child.info.get("oper_name", False)
        if child.info.get("oper_name", False):
            oper_name += f"->{self.operator}"
            child.info.update({"oper_name": oper_name})
        else:
            child.info.update({"oper_name": self.operator})
        return child
