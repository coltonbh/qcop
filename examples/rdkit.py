from qcio import CalcType, Molecule, ProgramInput

from qcop import compute, exceptions

# Create the molecule
# Can also open a molecule from a file
# molecule = Molecule.open("path/to/h2o.xyz")
molecule = Molecule(
    symbols=["O", "H", "H"],
    connectivity=[[0, 1, 1], [0, 2, 1]],  # Required for MM models
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
    model={"method": "UFF"},
)

# Run the calculation
try:
    output = compute("terachem", prog_input, collect_files=True)
except exceptions.ExternalProgramError as e:
    output = e.program_failure
    print(output.stdout)  # or output.pstdout for short
    # Input data used to generate the calculation
    print(output.input_data)
    # Provenance of generated calculation
    print(output.provenance)
    print(output.traceback)
    raise

else:
    # Check results
    print("output.results.energy:", output.results.energy)
    # The CalcType results will always be available at .return_result
    print("output.return_result:", output.return_result)
    # Stdout from the program
    print(output.stdout)  # or output.pstdout for short
    # Input data used to generate the calculation
    print(output.input_data)
    # Provenance of generated calculation
    print(output.provenance)
