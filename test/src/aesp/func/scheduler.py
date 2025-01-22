


class STScheduler(object):
    def __init__(self, max_generation, max_stage) -> None:
        self.stage = 1
        self.generation = 1
        self.max_stage = max_stage
        self.max_generation = max_generation

    def next_stage(self, **kwargs):
        self.stage += 1
        
    def next_generation(self, gen_complete, **kwargs):
        self.generation += 1
        self.stage = 1
        self.gen_complete = gen_complete

    @property
    def s_converged(self):
        return self.stage > self.max_stage

    @property
    def g_converged(self):
        is_max = self.generation > self.max_generation
        if not is_max:
            return self.gen_complete
        else:
            return True

class DPScheduler(STScheduler):
    def __init__(self, max_generation, max_stage, fatal_at_max) -> None:
        super().__init__(max_generation, max_stage)
        self.fatal_at_max = fatal_at_max
        self.stage_complete = False
        self.gen_complete = False

    def next_stage(self, stage_complete):
        super().next_stage()
        self.stage_complete = stage_complete  

    @property
    def s_converged(self):
        is_max = super().s_converged
        if not is_max:
            return self.stage_complete
        else:
            return True

if __name__ == "__main__":
    dp = DPScheduler(10, 1, False)
    print(dp.s_converged)