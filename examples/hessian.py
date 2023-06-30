from pathlib import Path

from qcio import CalcType, Molecule, ProgramInput

from qcop import compute

current_dir = Path(__file__).resolve().parent
# Create the molecule
h2o = Molecule.open(current_dir / "h2o.xyz")

# Define the program input
prog_input = ProgramInput(
    molecule=h2o,
    calctype=CalcType.hessian,
    model={"method": "hf", "basis": "sto-3g"},
    keywords={"purify": "no"},
)

# Run the calculation
output = compute("terachem", prog_input)

# Input data used to generate the calculation
print(output.input_data)
# Provenance of generated calculation
print(output.provenance)
# Print stdout; will be present on successful and failed calculations
print(output.stdout)  # or output.pstdout for short

# Check results
if output.success is True:
    print("Energy:", output.results.energy)
    print("Gradient:", output.results.gradient)
    print("Hessian:", output.results.hessian)
    # The CalcType results will always be available at .return_result
    print("Hessian:", output.return_result)

else:  # output.success is False
    print(output.traceback)  # See why the program failed; output.ptraceback for short
