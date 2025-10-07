"""An example of how to create a FileSpec object for a QC Program."""

from pathlib import Path

from qcio import FileSpec, Structure

from qcop import compute

# Input files for QC Program
inp_file = Path("path/to/tc.in").read_text()  # Or your own function to create tc.in

# Structure object to XYZ file
structure = Structure.open("path/to/my/mol.xyz")
xyz_str = structure.to_xyz()  # type: ignore

# Create a FileSpec object for TeraChem
spec = FileSpec(
    files={"tc.in": inp_file, "coords.xyz": xyz_str}, cmdline_args=["tc.in"]
)

# This will write the files to disk in a temporary directory and then run
# "terachem tc.in" in that directory.
results = compute("terachem", spec, print_logs=True)

# Data
results.logs
results.input_data
results.data.files  # Has all the files terachem creates
results.data.files.keys()  # Print out file names
# Saves all outputs with the exact structure produced by the QC program
results.data.save_files("to/this/directory")
