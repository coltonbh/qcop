from qcio import ProgramInput, Structure

from qcop import compute, exceptions

# Create the structure
# Can also open a structure from a file
# structure = Structure.open("path/to/h2o.xyz")
structure = Structure(
    symbols=["O", "H", "H"],
    geometry=[  # type: ignore
        [0.0, 0.0, 0.0],
        [0.52421003, 1.68733646, 0.48074633],
        [1.14668581, -0.45032174, -1.35474466],
    ],
)

# Define the program input
prog_input = ProgramInput(
    structure=structure,
    calctype="conformer_search",  # type: ignore
    model={"method": "gfnff"},  # type: ignore
    keywords={"calculation": {"level": [{"alpb": "acetonitrile"}]}},
)

# Run the calculation
try:
    # result is instance of Results
    result = compute(
        "crest", prog_input, collect_files=True, collect_rotamers=False
    )
except exceptions.QCOPBaseError as e:
    result = e.results
    print(result.logs)
    print(f"Success: {result.success}")  # False
    print(result.input_data)  # Input data used to generate the calculation
    print(result.provenance)  # Provenance of generated calculation
    print(result.traceback)  # or output.ptraceback for short
    raise

else:
    # Check results
    print(result.logs)
    print(f"Success: {result.success}")  # True
    print("output.data: ", result.data)
    print("output.data.conformer_energies:", result.data.conformer_energies)
    print(
        "output.data.conformer_energies_relative:",
        result.data.conformer_energies_relative,
    )
    print(result.input_data)  # Input data used to generate the calculation
    print(result.provenance)  # Provenance of generated calculation
