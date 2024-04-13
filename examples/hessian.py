from qcio import CalcType, Molecule, ProgramInput

from qcop import compute, exceptions

# Create the molecule
# Can also open a molecule from a file
# molecule = Molecule.open("path/to/h2o.xyz")
molecule = Molecule(
    symbols=["O", "H", "H"],
    geometry=[
        [0.0253397, 0.01939466, -0.00696322],
        [0.22889176, 1.84438441, 0.16251426],
        [1.41760224, -0.62610794, -1.02954938],
    ],
)

# Define the program input
prog_input = ProgramInput(
    molecule=molecule,
    calctype=CalcType.hessian,
    model={"method": "b3lyp", "basis": "6-31g"},
    keywords={"purify": "no"},
)

# Run the calculation
try:
    output = compute("terachem", prog_input)
except exceptions.QCOPBaseError as e:
    output = e.program_failure
    print(output.traceback)  # See why the program failed; output.ptraceback for short
    raise

else:
    print("Energy:", output.results.energy)
    print("Gradient:", output.results.gradient)
    print("Hessian:", output.results.hessian)
    # The CalcType results will always be available at .return_result
    print("Hessian:", output.return_result)

    # Input data used to generate the calculation
    print(output.input_data)
    # Provenance of generated calculation
    print(output.provenance)
    # Print stdout; will be present on successful and failed calculations
    print(output.stdout)  # or output.pstdout for short
