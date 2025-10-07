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

# Define the calcspec
spec = CalcSpec(
    structure=structure,
    # Can be "energy", "gradient", "hessian", "optimization", "transition_state"
    calctype="optimization",  # type: ignore
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no", "new_minimizer": "yes"},  # new_minimizer yes is required
)

# Run the calculation
try:
    # results is instance of Results
    results = compute("terachem", spec, collect_files=True)
except exceptions.QCOPBaseError as e:
    results = e.results
    print(results.logs)
    print(f"Success: {results.success}")  # False
    print(results.input_data)  # Input data used to generate the calculation
    print(results.provenance)  # Provenance of generated calculation
    print(results.traceback)  # or output.ptraceback for short
    raise

else:
    # Check results
    print(results.logs)
    print(f"Success: {results.success}")  # True
    print("output.data: ", results.data)
    print("output.data.energies:", results.data.energies)
    print("output.data.structures:", results.data.structures)
    print("output.data.final_structure:", results.data.final_structure)
    print(results.input_data)  # Input data used to generate the calculation
    print(results.provenance)  # Provenance of generated calculation
