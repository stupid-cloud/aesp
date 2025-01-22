from dpgen2.fp import fp_styles
from .matgl import MatglInputs, RunMatgl, PrepMatgl
from .dpmd import DpmdInputs, RunDpmd, PrepDpmd
from .gulp import GulpInputs, PrepGulp, RunGulp
calc_styles = {
    'matgl': {
        'inputs': MatglInputs,
        "prep": PrepMatgl,
        "run": RunMatgl
    },
    'dpmd': {
        'inputs': DpmdInputs,
        "prep": PrepDpmd,
        "run": RunDpmd
    },
    'gulp': {
        'inputs': GulpInputs,
        "prep": PrepGulp,
        "run": RunGulp
    }
}
calc_styles.update(fp_styles)