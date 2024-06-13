"""Top level compute functions for qcop."""

import traceback
from typing import Any, Callable, Dict, Optional, Union

from qcio import (
    CalcType,
    Files,
    InputType,
    Model,
    Molecule,
    NoResults,
    ProgramInput,
    ProgramOutput,
)
from qcio.helper_types import StrOrPath

from .adapters import BaseAdapter
from .exceptions import AdapterNotFoundError, ProgramNotFoundError
from .utils import get_adapter, inherit_docstring_from


@inherit_docstring_from(BaseAdapter.compute)
def compute(
    program: str,
    inp_obj: InputType,
    *,
    scratch_dir: Optional[StrOrPath] = None,
    rm_scratch_dir: bool = True,
    collect_stdout: bool = True,
    collect_files: bool = False,
    collect_wfn: bool = False,
    update_func: Optional[Callable] = None,
    update_interval: Optional[float] = None,
    print_stdout: bool = False,
    raise_exc: bool = True,
    propagate_wfn: bool = False,
    qcng_fallback: bool = True,
    **kwargs,
) -> ProgramOutput:
    """Use the given program to compute on the given input.

    See BaseAdapter.compute for more details.
    """
    try:
        adapter = get_adapter(program, inp_obj, qcng_fallback)
    except (AdapterNotFoundError, ProgramNotFoundError) as e:
        # Add program_output to the exception
        output_obj = ProgramOutput[type(inp_obj), NoResults](  # type: ignore
            input_data=inp_obj,
            success=False,
            provenance={"program": program},
            traceback=traceback.format_exc(),
        )
        e.program_output = output_obj
        e.args = (*e.args, output_obj)
        raise e

    else:
        return adapter.compute(
            inp_obj,
            scratch_dir=scratch_dir,
            rm_scratch_dir=rm_scratch_dir,
            collect_stdout=collect_stdout,
            collect_files=collect_files,
            collect_wfn=collect_wfn,
            update_func=update_func,
            update_interval=update_interval,
            print_stdout=print_stdout,
            raise_exc=raise_exc,
            propagate_wfn=propagate_wfn,
            **kwargs,
        )


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
) -> ProgramOutput:
    """Compute function that accepts independent argument for a ProgramInput.

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
        See compute function for details.
    """
    if isinstance(files, Files):  # Check in case Files object is passed instead of dict
        files = files.files

    inp_obj = ProgramInput(
        calctype=calctype,  # type: ignore
        molecule=molecule,
        model=model,  # type: ignore
        keywords=keywords or {},
        files=files or {},
        extras=extras or {},
    )

    return compute(program, inp_obj, **kwargs)
