from pathlib import Path

from qcio import CalcType, Molecule, ProgramInput

from qcop import compute

current_dir = Path(__file__).resolve().parent

# Create the molecule
h2o_dict = Molecule.open(current_dir / "h2o.xyz").dict()
# Must have explicit connectivity for for fields
h2o_dict["connectivity"] = [[0, 1, 1], [0, 2, 1]]
h2o = Molecule(**h2o_dict)

# Define the program input
prog_input = ProgramInput(
    molecule=h2o,
    calctype=CalcType.energy,
    model={"method": "UFF"},
)

# Run the calculation
output = compute("rdkit", prog_input, collect_files=True)

# Stdout from the program
print(output.stdout)  # or output.pstdout for short
# Input data used to generate the calculation
print(output.input_data)
# Provenance of generated calculation
print(output.provenance)

# Check results
if output.success is True:
    print("output.results.energy:", output.results.energy)
    # The CalcType results will always be available at .return_result
    print("output.return_result:", output.return_result)

else:  # output.success is False
    print(output.traceback)  # See why the program failed; output.ptraceback for short
