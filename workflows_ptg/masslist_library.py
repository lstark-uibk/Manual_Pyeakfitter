import numpy as np

masses_elements = np.array([12,
                            13.00335,
                            1.00783,
                            1.007276,
                            14.00307,
                            15.99492,
                            17.99916,
                            31.97207,
                            33.967867,  # https://en.wikipedia.org/wiki/Isotopes_of_sulfur
                            126.90448,
                            27.9763
                            ])

def createCompound(C=0, C13=0,H=0,Hp=1,N=0,O=0,O18=0,S=0,S34=0,I=0,Si=0):
    coumpound_array = np.array([C,C13,H,Hp,N,O,O18,S,S34,I,Si])
    mass = (masses_elements*coumpound_array).sum()
    return [mass,coumpound_array]

masslibrary = {
    "PYRIDINE": createCompound(N=1, H=5, C=5),
    "ACETONE": createCompound(C=3, H=6, O=1),
    "APINENE": createCompound(C=10, H=16),
    "BCARY": createCompound(C=15, H=24),
    "ISOPRENE": createCompound(C=5, H=8),
    "HEXANONE": createCompound(C=6, H=12, O=1),
    "PINONALDEHYDE": createCompound(C=10, H=16, O=2),
    "PINONALDEHYDEPAN": createCompound(C=10, H=15, O=6, N=1),
    "PINONICACID": createCompound(C=10, H=16, O=3),
    "PINICACID": createCompound(C=9, H=14, O=4),
    "ACETIC": createCompound(C=2, H=4, O=2),
    "ACETICFRAG": createCompound(C=2, H=2, O=1),
    "DMA": createCompound(C=2, H=7, N=1),
    "TMA": createCompound(C=3, H=9, N=1),
    "TMB": createCompound(C=9, H=12),
    "ACETONITRILE": createCompound(C=2, H=3, N=1),
    "OrgNitratNO": createCompound(C=10, H=15, O=5, N=1),
    "NORPINONALDEHYDE": createCompound(C=9, H=14, O=2),
    "NORPINONALDEHYDEPAN": createCompound(C=9, H=13, O=6, N=1),
    "DMS": createCompound(C=2, H=6, S=1),
    "DMSO": createCompound(C=2, H=6, S=1, O=1),
    "DMSO2": createCompound(C=2, H=6, S=1, O=2),
    "MSIA": createCompound(C=1, H=4, S=1, O=2),
    "MSA": createCompound(C=1, H=4, S=1, O=3),
}

masslibrary_nh4 = {}

for compound in masslibrary:
    mass, compound_array = masslibrary[compound]
    compound_nh4 = compound + "NH4+"
    mass_nh4 = mass + 18.033836
    coumpound_array_nh4 = compound_array + np.array([0, 0, 3, 1, 1, 0, 0, 0, 0, 0, 0])
    masslibrary_nh4[compound_nh4] = [mass_nh4, coumpound_array_nh4]

masslibrary.update(masslibrary_nh4)