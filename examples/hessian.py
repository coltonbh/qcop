from qcio import CalcSpec, CalcType, Structure

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
pi = CalcSpec(
    structure=structure,
    calctype=CalcType.hessian,
    model={"method": "b3lyp", "basis": "6-31g"},  # type: ignore
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
    print("output.results.hessian:", po.results.hessian)
    print(po.input_data)  # Input data used to generate the calculation
    print(po.provenance)  # Provenance of generated calculation
