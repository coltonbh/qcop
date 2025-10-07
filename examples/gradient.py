from qcio import CalcSpec, CalcType, Structure

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
    calctype=CalcType.gradient,
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no"},
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
    print("output.data.gradient:", results.data.gradient)
    print(results.input_data)  # Input data used to generate the calculation
    print(results.provenance)  # Provenance of generated calculation
