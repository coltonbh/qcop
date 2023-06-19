"""Top level compute functions for qcop."""
from typing import Callable, Optional
import subprocess

from qcio import FileInput, FailedComputation
from qcio.abc_io import InputBase, OutputBase
from qcio.helper_types import StrOrPath

from .adaptors import BaseAdaptor, FileAdaptor
from .helpers import tmpdir, get_adaptor


def compute(
    inp_obj: InputBase,
    program: str,
    *,
    calc_dir: Optional[StrOrPath] = None,
    rm_calc_dir: bool = True,
    collect_files: bool = False,
    update_func: Optional[Callable] = None,
    update_interval: float = 0.5,
    raise_exc: bool = False,
) -> OutputBase:
    """Compute the given program on the given files.

    Args:
        inp_obj: The qcio input object for a computation. E.g. FileInput or
            SinglePointInput.
        program: The program to run.
        calc_dir: The directory to run the program in. If None, a new directory is
            created in the system default temporary directory.
        rm_calc_dir: Delete the calculation directory when the program exits.
        collect_files: Whether to collect all files from the calc_dir as output.
        update_func: A function to call as the program executes. The function must
            accept the in-process stdout/stderr output as a string for its first
            argument.
        update_interval: The minimum time in seconds between calls to the update_func.
        raise_exc: Whether to raise an exception if the program fails. If False, a
            FailedComputation object will be returned instead.

    Returns:
        The qcio output object for a computation. Will either be a FailedComputation
            object or the corresponding output object for the input object.

    Raises:
        subprocess.CalledProcessError: If the program fails and raise_exc is True.
    """
    # Get Adaptor to execute program
    if isinstance(inp_obj, FileInput):
        adaptor: BaseAdaptor = FileAdaptor(program)
    else:
        adaptor = get_adaptor(program)

    # Change to a temporary directory to run the program.
    with tmpdir(calc_dir, rm_calc_dir) as calc_dir:
        # Write the input files to the working directory.
        inp_obj.args.write_files(calc_dir)
        try:
            # Execute the program.
            output = adaptor.compute(inp_obj, update_func, update_interval)
        except subprocess.CalledProcessError as e:
            if raise_exc:
                raise e
            else:
                # Return a FailedComputation object.
                output = FailedComputation.from_exc(e)

        if collect_files:
            # Collect output files from the calc_dir
            output.add_files(
                calc_dir, recursive=True, exclude=inp_obj.args.files.keys()
            )
    return output


if __name__ == "__main__":
    from qcio import FileInput

    fi = FileInput(**{"args": {"cmdline_args": ["-l"]}})
    output = compute(fi, "ls")
    print(output)
