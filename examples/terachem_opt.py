"""Example of how to run an optimization calculation with TeraChem using qcop."""

from qcio import CalcSpec, Structure

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
prog_input = CalcSpec(
    structure=structure,
    # Can be "energy", "gradient", "hessian", "optimization", "transition_state"
    calctype="optimization",  # type: ignore
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no", "new_minimizer": "yes"},  # new_minimizer yes is required
)

# Run the calculation
try:
    # prog_output is instance of ProgramOutput
    prog_output = compute("terachem", prog_input, collect_files=True)
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
    print("output.results.energies:", prog_output.results.energies)
    print("output.results.structures:", prog_output.results.structures)
    print("output.results.final_structure:", prog_output.results.final_structure)
    print(prog_output.input_data)  # Input data used to generate the calculation
    print(prog_output.provenance)  # Provenance of generated calculation
