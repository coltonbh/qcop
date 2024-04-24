from qcio import CalcType, Molecule, ProgramInput

from qcop import compute, exceptions

# Create the molecule
# Can also open a molecule from a file
# molecule = Molecule.open("path/to/h2o.xyz")
molecule = Molecule(
    symbols=["O", "H", "H"],
    geometry=[  # type: ignore
        [0.0, 0.0, 0.0],
        [0.52421003, 1.68733646, 0.48074633],
        [1.14668581, -0.45032174, -1.35474466],
    ],
)
# Define the program input
pi = ProgramInput(
    molecule=molecule,
    calctype=CalcType.gradient,
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no"},
)

# Run the calculation
try:
    # po is instance of ProgramOutput
    po = compute("terachem", pi, collect_files=True)
except exceptions.QCOPBaseError as e:
    po = e.program_output
    print(po.stdout)  # or output.pstdout for short
    print(f"Success: {po.success}")  # False
    print(po.input_data)  # Input data used to generate the calculation
    print(po.provenance)  # Provenance of generated calculation
    print(po.traceback)  # or output.ptraceback for short
    raise

else:
    # Check results
    print(po.stdout)  # or output.pstdout for short
    print(f"Success: {po.success}")  # True
    print("output.results: ", po.results)
    print("output.results.gradient:", po.results.gradient)
    print(po.input_data)  # Input data used to generate the calculation
    print(po.provenance)  # Provenance of generated calculation
