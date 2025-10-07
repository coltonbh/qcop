from qcio import CalcSpec, Structure

from qcop import compute, exceptions

# Create the structure
# Can also open a structure from a file
# structure = Structure.open("path/to/h2o.xyz")
structure = Structure(
    symbols=["O", "H", "H"],
    connectivity=[(0, 1, 1), (0, 2, 1)],  # Required for MM models
    geometry=[  # type: ignore
        [0.0, 0.0, 0.0],
        [0.52421003, 1.68733646, 0.48074633],
        [1.14668581, -0.45032174, -1.35474466],
    ],
)

# Define the program input
pi = CalcSpec(
    structure=structure,
    calctype="energy",  # type: ignore
    model={"method": "UFF"},  # type: ignore
)

# Run the calculation
try:
    # po is instance of ProgramOutput
    po = compute("rdkit", pi, collect_files=True)
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
    print("output.results.energy:", po.results.energy)
    print(po.input_data)  # Input data used to generate the calculation
    print(po.provenance)  # Provenance of generated calculation
