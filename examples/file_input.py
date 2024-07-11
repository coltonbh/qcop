"""An example of how to create a FileInput object for a QC Program."""

from pathlib import Path

from qcio import FileInput, Structure

from qcop import compute

# Input files for QC Program
qc_inp = Path("path/to/tc.in").read_text()  # Or your own function to create tc.in

# Structure object to XYZ file
structure = Structure.open("path/to/my/mol.xyz")
mol_xyz = structure.to_xyz()

# Create a FileInput object for TeraChem
file_inp = FileInput(
    files={"tc.in": qc_inp, "coords.xyz": mol_xyz}, cmdline_args=["tc.in"]
)

output = compute("terachem", file_inp, print_stdout=True)

# Data
output.stdout
output.input_data
output.files  # Has all the files terachem creates
output.files.keys()  # Print out file names
# Saves all outputs with the exact structure produced by the QC program
output.save_files("where")
