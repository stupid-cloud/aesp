from matgl.ext.ase import Relaxer
import torch
import matgl
from pymatgen.io.vasp import Poscar

device = 'cuda' if torch.cuda.is_available() else 'cpu'
torch.set_default_device(device)
poscar = Poscar.from_file('POSCAR')

pot = matgl.load_model("{{model}}")
relaxer = Relaxer(potential=pot, relax_cell={{relax_cell}})
relax_results = relaxer.relax(
    poscar.structure, fmax={{f_max}}, verbose=True, steps={{step_max}}, traj_file='relax.traj',
    params_asecellfilter=dict(scalar_pressure={{pstress}})
)
# extract results
final_structure = relax_results["final_structure"]
# print out the final relaxed structure and energy
Poscar(final_structure).write_file('CONTCAR')
