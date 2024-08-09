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
    # prog_output is instance of ProgramOutput
    prog_output = compute(
        "crest", prog_input, collect_files=True, collect_rotamers=False
    )
except exceptions.QCOPBaseError as e:
    prog_output = e.program_output
    print(prog_output.stdout)  # or output.pstdout for short
    print(f"Success: {prog_output.success}")  # False
    print(prog_output.input_data)  # Input data used to generate the calculation
    print(prog_output.provenance)  # Provenance of generated calculation
    print(prog_output.traceback)  # or output.ptraceback for short
    raise

else:
    # Check results
    print(prog_output.stdout)  # or output.pstdout for short
    print(f"Success: {prog_output.success}")  # True
    print("output.results: ", prog_output.results)
    print("output.results.conformer_energies:", prog_output.results.conformer_energies)
    print(
        "output.results.conformer_energies_relative:",
        prog_output.results.conformer_energies_relative,
    )
    print(prog_output.input_data)  # Input data used to generate the calculation
    print(prog_output.provenance)  # Provenance of generated calculation
