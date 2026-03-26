"""Example of how to run an optimization calculation with TeraChem using qccompute."""

from qcdata import ProgramInput, Structure

from qccompute import compute, exceptions

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
    # Can be "energy", "gradient", "hessian", "optimization", "transition_state"
    calctype="optimization",  # type: ignore
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no", "new_minimizer": "yes"},  # new_minimizer yes is required
)

# Run the calculation
try:
    # prog_output is a ProgramOutput instance
    prog_output = compute("terachem", prog_input, collect_files=True)
except exceptions.QCComputeBaseError as e:
    prog_output = e.prog_output
    print(prog_output.logs)
    print(f"Success: {prog_output.success}")  # False
    print(prog_output.input_data)  # Input data used to generate the calculation
    print(prog_output.provenance)  # Provenance of generated calculation
    print(prog_output.traceback)  # or output.ptraceback for short
    raise

else:
    # Check results
    print(prog_output.logs)
    print(f"Success: {prog_output.success}")  # True
    print("output.data: ", prog_output.data)
    print("output.data.energies:", prog_output.data.energies)
    print("output.data.structures:", prog_output.data.structures)
    print("output.data.final_structure:", prog_output.data.final_structure)
    print(prog_output.input_data)  # Input data used to generate the calculation
    print(prog_output.provenance)  # Provenance of generated calculation
