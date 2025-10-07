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
# Define the program input
pi = CalcSpec(
    structure=structure,
    calctype=CalcType.gradient,
    model={"method": "hf", "basis": "sto-3g"},  # type: ignore
    keywords={"purify": "no"},
)

# Run the calculation
try:
    # po is instance of Results
    po = compute("terachem", pi, collect_files=True)
except exceptions.QCOPBaseError as e:
    po = e.results
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
    print("output.results.gradient:", po.results.gradient)
    print(po.input_data)  # Input data used to generate the calculation
    print(po.provenance)  # Provenance of generated calculation
