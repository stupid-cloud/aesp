from pyxtal import pyxtal
import numpy as np
from aesp.operator.base import OperatorBase

class RandomGenerator(object):
    def __init__(self, composition, spgnum, factor, thickness, max_count, tol_matrix) -> None:
        self.species = list(composition.keys())
        self.natoms = list(composition.values())
        self.spgnum = spgnum
        self.factor = factor
        self.thickness = thickness
        self.max_count = max_count
        self.tol_matrix = tol_matrix

    def get_new_candidate(self, struc):
        generator = pyxtal()
        while True:
            spg = np.random.choice(self.spgnum, size=1)[0]
            # generator.from_random(self.dim, spg, self.species, self.natoms, 
            #                           conventional=True, tm=self.tol_matrix, factor=self.factor,
            #                           thickness=self.thickness, max_count=self.max_count
            #                     )
            try:
                generator.from_random(self.dim, spg, self.species, self.natoms, 
                                      conventional=True, tm=self.tol_matrix, factor=self.factor,
                                      thickness=self.thickness, max_count=self.max_count
                                )
            except Exception as e:
                # logger.warning(e.args[0])
                continue
            # logger.info(f's_{idx+1} was generated: Space group: {spg} ({g.symbol}))')

            atoms = generator.to_ase()
            atoms.info.update({"oper_name": 'random_gen', 'oper_type': 'generator'})
            atoms.info['data'] = {}
            struc = struc.from_atoms(atoms)
            if struc.is_within_bounds():
                return struc
# class RandomGenerator(OperatorBase):
#     def __init__(self, hc, tol_matrics, dim) -> None:
#         self.hc = hc
#         self.tol_matrics = tol_matrics 
#         self.dim = dim

#     def get_new_candidate(self, species, natoms, spgnum):
#         generator = pyxtal()
#         while True:
#             spg = np.random.choice(spgnum, size=1)[0]
#             try:
#                 generator.from_random(self.dim, spg, species,natoms, 
#                                       conventional=True, tm=self.tol_matrics
#                                 )
#             except Exception as e:
#                 # logger.warning(e.args[0])
#                 continue
#             # logger.info(f's_{idx+1} was generated: Space group: {spg} ({g.symbol}))')

#             struc = generator.to_ase()
#             struc.info.update({"oper_name": 'random_gen', 'oper_type': 'generator'})
#             struc.info['data'] = {}
#             if self.hc.is_within_bounds(struc.cell):
#                 return struc