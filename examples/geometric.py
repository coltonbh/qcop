"""Example of using geometric subprogram to optimize H2 bond length.

Constraints docs: https://geometric.readthedocs.io/en/latest/constraints.html
"""
from qcio import CalcType, DualProgramInput, Molecule

from qcop import compute

h2 = Molecule(
    symbols=["H", "H"],
    geometry=[[0, 0, 0], [0, 0, 1.4]],
)
prog_inp = DualProgramInput(
    calctype=CalcType.optimization,
    molecule=h2,
    subprogram="terachem",
    subprogram_args={
        "model": {"method": "HF", "basis": "6-31g"},
        "keywords": {"purify": "no"},
    },
    keywords={
        "check": 3,
        # This is obviously a stupid constraint, but it's just an example to show how
        # to use them
        "constraints": {
            "freeze": [
                {"type": "distance", "indices": [0, 1], "value": 1.4},
            ],
        },
    },
)
output = compute("geometric", prog_inp, propagate_wfn=True, rm_scratch_dir=False)
print(output.stdout)
print(output)
