from qcio import CalcType, ProgramInput, Structure

from qcop import compute, exceptions

# Create the structure
# Can also open a structure from a file
# structure = Structure.open("path/to/h2o.xyz")
structure = Structure(
    symbols=["O", "H", "H"],
    geometry=[  # type: ignore
        [0.0253397, 0.01939466, -0.00696322],
        [0.22889176, 1.84438441, 0.16251426],
        [1.41760224, -0.62610794, -1.02954938],
    ],
)

# Define the program input
prog_input = ProgramInput(
    structure=structure,
    calctype=CalcType.hessian,
    model={"method": "b3lyp", "basis": "6-31g"},  # type: ignore
    keywords={"purify": "no"},
)

# Run the calculation
try:
    # results is instance of Results
    result = compute("terachem", prog_input, collect_files=True)
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
    print("output.data.hessian:", result.data.hessian)
    print(result.input_data)  # Input data used to generate the calculation
    print(result.provenance)  # Provenance of generated calculation
