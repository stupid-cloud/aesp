class OperatorBase(object):
    def __init__(self, max_count) -> None:
        self.max_count = max_count

    @staticmethod
    def update_species(species, atoms):
                # 获取原子的化学符号列表
                symbols = atoms.get_chemical_symbols()
                # 构建排序后的索引列表
                sorted_indices = sorted(range(len(symbols)), key=lambda i: species.index(symbols[i]))
                # 根据排序后的索引列表重新排列原子
                atoms = atoms[sorted_indices]

                atoms.wrap()
                return atoms

    # def check_and_update(self, child):
    #     species = list(set(child.symbols))  
    #     child = self.update_species(species, child)
    #     too_close, _ = self.hc.check_distance(child)
    #     within_bounds = self.hc.is_within_bounds(child.cell)
    #     if not too_close and within_bounds:
    #         return True, child
    #     return False, None