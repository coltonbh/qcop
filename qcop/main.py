"""Top level compute functions for qcop."""
import os
import platform
from time import time
from typing import Callable, Optional

from qcio import FileInput
from qcio.helper_types import StrOrPath
from qcio.models.base_io import InputBase, OutputBase, Provenance

from .adapters import FileAdapter, registry
from .exceptions import AdapterNotFoundError, QCEngineError, QCOPBaseError
from .utils import tmpdir


def compute(
    inp_obj: InputBase,
    program: str,
    *,
    working_dir: Optional[StrOrPath] = None,
    rm_working_dir: bool = True,
    collect_stdout: bool = True,
    collect_files: bool = False,
    update_func: Optional[Callable] = None,
    update_interval: Optional[float] = None,
    print_stdout: bool = False,
    raise_exc: bool = False,
    qcng_fallback: bool = True,
    **kwargs,
) -> OutputBase:
    """Compute the given program on the given files.

    Args:
        inp_obj: A qcio input object for a computation. A subclass of InputBase. E.g.
            FileInput or SinglePointInput.
        program: The program to run.
        working_dir: The directory to run the program in. If None, a new directory is
            created in the system default temporary directory. If rm_working_dir is
            True this directory will be deleted after the program finishes.
        rm_working_dir: Delete the calculation directory when the program exits.
        collect_stdout: Whether to collect stdout/stderr from the program as output.
            Failed computations will always collect stdout/stderr.
        collect_files: Whether to collect all files from the calc_dir as output.
        update_func: A function to call as the program executes. The function must
            accept the in-process stdout/stderr output as a string for its first
            argument.
        update_interval: The minimum time in seconds between calls to the update_func.
        print_stdout: Whether to print stdout/stderr to the terminal as the program
            executes. Will be ignored if update_func passed
        raise_exc: If False, qcop will return a subclass of the FailedComputation object
            when the QC program fails rather than raise an exception. qcop exceptions
            not related external program failure will always be raised.
        qcng_fallback: Whether to fall back to qcengine if qcop doesn't have an
            adapter for the program.
        **kwargs: Additional keyword arguments to pass to the adapter.

    Returns:
        The qcio output object for a computation. A subclass of OutputBase. Will either
        be a FailedComputation object or the corresponding output object for the input
        type. E.g., SinglePointInput -> SinglePointOutput.

    Raises:
        AdapterNotFoundException: If the program is not supported (i.e., no Adapter is
            implemented for it in qcop or qcengine).
        ProgramNotFoundException: If the program executable is not found on the system
            at execution time. This likely means the program is not installed on the
            system.
        UnsupportedCalcTypeError: If the program is supported but the calc_type is not.
        ExecutionFailedException: If the program fails during execution and
            raise_exc=True.
        QCEngineException: If QCEngine performed the computation, fails and
            raise_exc=True.
    """
    # Get adapter to execute program
    if isinstance(inp_obj, FileInput):
        adapter = FileAdapter(program)
    else:
        try:
            adapter = registry[program]()
        except KeyError:
            # Use QCEngine as a fallback, if requested.
            if qcng_fallback:
                try:  # Import QCEngine
                    from qcengine import compute as qcng_compute
                    from qcengine.exceptions import QCEngineException

                    from .utils import qcng_get_program
                except ModuleNotFoundError as e:
                    raise ModuleNotFoundError(
                        "QCEngine not installed. To use qcengine as a fallback, "
                        "install it by running 'python -m pip install "
                        "qcop[qcengine]'."
                    ) from e

                # Check for QCEngine harness and that program is installed
                qcng_get_program(program)

                try:
                    return inp_obj.to_output_from_qcel(
                        qcng_compute(
                            inp_obj.to_qcel(),
                            program,
                            raise_error=raise_exc,
                            return_dict=True,  # qcio works with dicts for qcel i/o
                            **kwargs,
                        ),
                    )

                except QCEngineException as e:  # Base exception for all QCEngine
                    raise QCEngineError(
                        "Something went wrong with QCEngine. See the traceback above "
                        "for details."
                    ) from e
            else:
                raise AdapterNotFoundError(program)

    # Set update_func if print_stdout is True and update_func is None
    if print_stdout and update_func is None:
        update_func, update_interval = (lambda _, stdout_new: print(stdout_new), 0.1)

    # Change cwd to a temporary directory to run the program.
    with tmpdir(working_dir, rm_working_dir) as calc_dir:
        if adapter.write_files:  # Write non structured input files to disk.
            inp_obj.program_args.write_files()

        start = time()
        try:
            # Execute the program.
            computed_properties, stdout = adapter.compute(
                inp_obj, update_func, update_interval, **kwargs
            )
            output_constructor = inp_obj.to_success
        except QCOPBaseError as e:
            if raise_exc:
                raise e
            else:
                # Return a FailedOutput object.
                output_constructor = inp_obj.to_failure
                stdout = getattr(e, "stdout", None)
                exception = e

        # Construct Provenance object
        wall_time = time() - start
        if hasattr(adapter, "program_version"):
            version = adapter.program_version(stdout)
        else:
            version = None

        provenance = Provenance(
            program=program,
            program_version=version,
            working_dir=str(calc_dir),
            wall_time=round(wall_time, 6),
            hostname=platform.node(),
            hostcpus=os.cpu_count(),
        )

        # Construct output object
        if output_constructor == inp_obj.to_failure:  # Failure
            output: OutputBase = output_constructor(provenance, exception)
        else:  # Success
            # Remove stdout if not requested
            stdout = stdout if collect_stdout else None
            output = output_constructor(provenance, computed_properties, stdout)

        # Optionally collect output files
        if collect_files or isinstance(inp_obj, FileInput):
            # Collect output files from the calc_dir
            output.add_files(
                calc_dir, recursive=True, exclude=inp_obj.program_args.files.keys()
            )

    return output


if __name__ == "__main__":  # pragma: no cover
    from qcio import Molecule, SinglePointInput

    h2 = Molecule(
        symbols=["H", "H"],
        geometry=[[0, 0, 0], [0, 0, 0.7414]],
        charge=0,
        multiplicity=1,
    )
    sp_energy = SinglePointInput(
        molecule=h2,
        program_args={
            "model": {"method": "HF", "basis": "6-31g"},
            "calc_type": "gradient",
            "keywords": {"purify": "no"},
        },
    )
    output = compute(sp_energy, "terachemd", collect_stdout=False, collect_files=True)
    print(output.__repr__())
