"""Top level compute functions for qcop."""

import traceback
from collections.abc import Callable
from typing import Any
from warnings import warn

from qcio import (
    CalcType,
    DataType,
    Files,
    InputType,
    Model,
    ProgramInput,
    Results,
    Structure,
)
from qcio.helper_types import StrOrPath

from .adapters import BaseAdapter
from .exceptions import AdapterNotFoundError, ProgramNotFoundError
from .utils import get_adapter, inherit_docstring_from


@inherit_docstring_from(BaseAdapter.compute)
def compute(
    program: str,
    input_data: InputType,
    *,
    scratch_dir: StrOrPath | None = None,
    rm_scratch_dir: bool = True,
    collect_logs: bool = True,
    collect_files: bool = False,
    collect_wfn: bool = False,
    update_func: Callable | None = None,
    update_interval: float | None = None,
    print_logs: bool = False,
    raise_exc: bool = True,
    propagate_wfn: bool = False,
    qcng_fallback: bool = True,
    **adapter_kwargs,
) -> Results[InputType, DataType]:
    """Use the given program to compute on the given input.

    See BaseAdapter.compute for more details.
    """
    try:
        adapter = get_adapter(program, input_data, qcng_fallback)
    except (AdapterNotFoundError, ProgramNotFoundError) as e:
        # Add results to the exception
        output_obj = Results[type(input_data), Files](  # type: ignore
            input_data=input_data,
            data=Files(),
            success=False,
            provenance={"program": program},
            traceback=traceback.format_exc(),
        )
        e.results = output_obj
        e.args = (*e.args, output_obj)
        raise e

    else:
        if "collect_stdout" in adapter_kwargs:
            warn(
                "`collect_stdout` is deprecated; use `collect_logs` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            collect_logs = adapter_kwargs.pop("collect_stdout")
        if "print_stdout" in adapter_kwargs:
            warn(
                "`print_stdout` is deprecated; use `print_logs` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            print_logs = adapter_kwargs.pop("print_stdout")

        return adapter.compute(
            input_data,
            scratch_dir=scratch_dir,
            rm_scratch_dir=rm_scratch_dir,
            collect_logs=collect_logs,
            collect_files=collect_files,
            collect_wfn=collect_wfn,
            update_func=update_func,
            update_interval=update_interval,
            print_logs=print_logs,
            raise_exc=raise_exc,
            propagate_wfn=propagate_wfn,
            **adapter_kwargs,
        )


def compute_args(
    program: str,
    structure: Structure,
    *,
    calctype: str | CalcType,
    model: dict[str, str] | Model,
    keywords: dict[str, Any] | None = None,
    files: dict[str, str | bytes] | Files | None = None,
    extras: dict[str, Any] | None = None,
    **kwargs,
) -> Results[InputType, DataType]:
    """Compute function that accepts independent argument for a ProgramInput.

    Args:
        program: The program to run.
        structure: The structure to use.
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

    program_input = ProgramInput(
        calctype=calctype,  # type: ignore
        structure=structure,
        model=model,  # type: ignore
        keywords=keywords or {},
        files=files or {},
        extras=extras or {},
    )

    return compute(program, program_input, **kwargs)
