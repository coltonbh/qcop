"""Must run script like this: python -m examples.xtb"""

from qcio import CalcType, Molecule, ProgramInput

from qcop import compute

# Create the molecule
# Can also open a molecule from a file
# molecule = Molecule.open("path/to/h2o.xyz")
molecule = Molecule(
    symbols=["O", "H", "H"],
    geometry=[
        [0.0, 0.0, 0.0],
        [0.52421003, 1.68733646, 0.48074633],
        [1.14668581, -0.45032174, -1.35474466],
    ],
)

# Define the program input
prog_input = ProgramInput(
    molecule=molecule,
    calctype=CalcType.energy,
    model={"method": "GFN2xTB"},
)


output = compute("xtb", prog_input)
print(output)
