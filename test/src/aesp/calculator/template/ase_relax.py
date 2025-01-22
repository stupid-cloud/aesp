
from ase.constraints import UnitCellFilter
from ase.io import read, write
from ase.optimize import LBFGS
from deepmd.calculator import DP


f_max = {{f_max}} 
step_max = {{step_max}}
relax_cell = {{relax_cell}}
model = "{{model}}"
pstress = {{pstress}}

model = DP(model=model)
# kBar to eV/A^3
aim_stress = 1.0 * pstress * 0.01 * 0.6242 / 10.0

ase_atom = read("POSCAR")
ase_atom.calc = model
if relax_cell:
    ucf = UnitCellFilter(ase_atom, scalar_pressure=aim_stress)
    # opt
    opt = LBFGS(ucf, trajectory='relax.traj')
    opt.run(fmax=f_max, steps=f_max)
else:
    opt = LBFGS(trajectory='relax.traj')
    opt.run(fmax=f_max, steps=f_max)
write('CONTCAR', ase_atom, format='vasp')
