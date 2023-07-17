"""Top level compute functions for qcop."""
import traceback
from time import time
from typing import Any, Callable, Dict, Optional, Union

from qcio import (
    CalcType,
    FileInput,
    Files,
    Model,
    Molecule,
    ProgramFailure,
    ResultsBase,
)
from qcio.helper_types import StrOrPath
from qcio.models import InputBase, OutputBase
from qcio.utils import calctype_to_output

from .exceptions import QCOPBaseError
from .utils import construct_provenance, get_adapter, tmpdir


def compute(
    program: str,
    inp_obj: InputBase,
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
        print_stdout: Whether to print stdout/stderr to the terminal in real time as
            the program executes. Will be ignored if an update_func passed.
        raise_exc: If False, qcop will return a subclass of the FailedComputation object
            when the QC program fails rather than raise an exception. qcop exceptions
            not related external program failure will always be raised.
        qcng_fallback: Whether to fall back to qcengine if qcop doesn't have an
            adapter for the program.
        **kwargs: Additional keyword arguments to pass to the adapter or qcng.compute().

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
        UnsupportedCalcTypeError: If the program is supported but the calctype is not.
        ExecutionFailedException: If the program fails during execution and
            raise_exc=True.
        QCEngineException: If QCEngine performed the computation, fails and
            raise_exc=True.
    """
    # Set update_func if print_stdout is True and update_func is None
    if print_stdout and update_func is None:
        update_func, update_interval = (lambda _, stdout_new: print(stdout_new), 0.1)

    # Change cwd to a temporary directory to run the program.
    with tmpdir(working_dir, rm_working_dir) as calc_dir:
        # Get adapter to execute program
        adapter = get_adapter(program, inp_obj, qcng_fallback)

        if adapter.write_files:  # Write non structured input files to disk.
            inp_obj.write_files()

        output_dict: Dict[str, Optional[str]] = {}
        stdout: Optional[str]

        start = time()
        try:
            # Execute the program.
            results, stdout = adapter.compute(
                inp_obj, update_func, update_interval, **kwargs
            )
            # getattr covers FileInput
            output_cls = calctype_to_output(getattr(inp_obj, "calctype", None))
        except QCOPBaseError as e:
            if raise_exc:
                raise e
            else:
                # Return a ProgramFailure object.
                output_cls = ProgramFailure
                # Someday may may put half-completed results here
                results, stdout = None, getattr(e, "stdout", None)
                # For mypy because e.stdout is not of a a known type
                stdout = str(stdout) if stdout is not None else None
                output_dict["traceback"] = traceback.format_exc()

        # Construct Provenance object
        provenance = construct_provenance(program, adapter, calc_dir, start, stdout)

        # Construct output object
        stdout = stdout if collect_stdout and output_cls != ProgramFailure else None
        # Ensure results is not None to maintain interface
        results = results if results is not None else ResultsBase()
        output_dict.update(
            {
                "input_data": inp_obj,
                "stdout": stdout,
                "results": results,
                "provenance": provenance,
            }
        )

        output_obj = output_cls(**output_dict)

        # Optionally collect output files
        if collect_files or isinstance(inp_obj, FileInput):
            # Collect output files from the calc_dir
            output_obj.add_files(calc_dir, recursive=True, exclude=inp_obj.files.keys())

    return output_obj


def compute_args(
    program: str,
    molecule: Molecule,
    *,
    calctype: Union[str, CalcType],
    model: Union[Dict[str, str], Model],
    keywords: Optional[Dict[str, Any]] = None,
    files: Optional[Union[Dict[str, Union[str, bytes]], Files]] = None,
    extras: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> OutputBase:
    """An alternative to the compute function that accepts independent argument for
    SinglePointInput.

    Args:
        program: The program to run.
        molecule: The molecule to use.
        calctype: The type of calculation to run.
        model: The model to use for the calculation.
        keywords: The keywords to use for the calculation.
        files: The files to use for the calculation. Either a qcio.Files object or a
            dict mapping file names to file contents (bytes or str).
        extras: Extra arguments to pass to the adapter.
        **kwargs: Extra arguments to pass to the compute function.

    Returns:
        The output of the computation.

    Raises:
        AdapterNotFoundError: If no adapter is found for the given program.
        AdapterInputError: If the adapter raises an exception when generating input
            files.
        QCEngineError: If the adapter raises an exception when running the program.
    """
    if isinstance(files, Files):  # Check in case Files object is passed instead of dict
        files = files.files

    inp_obj = SinglePointInput(
        calctype=calctype,
        molecule=molecule,
        model=model,
        keywords=keywords or {},
        files=files or {},
        extras=extras or {},
    )

    return compute(program, inp_obj, **kwargs)


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
        model={"method": "HF", "basis": "6-31g"},
        calctype="gradient",
        keywords={"purify": "no"},
    )
    files = Files(files={"file1": "string data"})
    files = {"file1": "string data"}
    # output = compute("terachemd", sp_energy, collect_stdout=False, collect_files=True)
    output = compute_args(
        "terachemd",
        h2,
        calctype="energy",
        model={"method": "HF", "basis": "6-31g"},
        files=files,
        keywords={"purify": "no"},
        collect_files=True,
    )
