import os
import platform
import shutil
import tempfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from time import time
from typing import Optional

from qcio import Provenance
from qcio.helper_types import StrOrPath
from qcio.models import FileInput, InputBase

from .adapters import BaseAdapter, FileAdapter, registry
from .exceptions import AdapterNotFoundError, ProgramNotFoundError


@contextmanager
def tmpdir(directory: Optional[StrOrPath] = None, rmdir: bool = True):
    """Context manager for a temporary directory.

    Args:
        directory: Where to create the temporary directory. If None, a new directory is
            created in the system default temporary directory.
        rmdir: Whether to remove the temporary directory when the context manager exits.
    """
    path = Path(directory or tempfile.mkdtemp())  # Set path to directory
    path.mkdir(parents=True, exist_ok=True)  # Create directory
    cwd = Path.cwd()  # Save current working directory
    os.chdir(path)  # Change to temporary directory
    yield path  # Execute code in context manager
    if rmdir:  # After exiting context manager
        shutil.rmtree(path)
    os.chdir(cwd)


@lru_cache  # Improves perf of tests when repeatedly called
def prog_available(program: str) -> bool:
    """Check if a program is available on the system.

    Args:
        program: The program to check.

    Returns:
        True if the program is available, False otherwise.
    """
    path = shutil.which(program)
    if not path:
        return False
    # Perform secondary checks
    if ".pyenv/shims" in path:
        # Executable is in non activated pyenv environment; often a conda env
        print(
            f"Program {program} is in a pyenv shim. It may become available if you "
            f"run 'conda activate {path.split('/')[-1]}'"
        )
        return False
    return True


def available_programs():
    """Return a list of available programs on the system."""
    return [
        adapter.program
        for adapter in registry.values()
        if prog_available(adapter.program)
    ]


def check_qcng_support(program: str) -> None:
    """Wrapper around qcng.get_program that raises correct qcop errors if the
    adapter (harness) or program are not found.

    Args:
        program: The program to check.

    Raises:
        AdapterNotFoundError: If QCEngine has no adapter for the program.
        ProgramNotFoundError: If the program is not installed on the host system.
    """
    try:  # Import QCEngine
        from qcengine import get_program
        from qcengine.exceptions import InputError, ResourceError
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "QCEngine not installed. To use qcengine as a fallback, "
            "install it by running 'python -m pip install "
            "'qcop[qcengine]'."
        ) from e

    try:
        get_program(program)
    except InputError as e:  # Raised by QCEngine if program not registered
        raise AdapterNotFoundError(program) from e
    # Raised by QCEngine if program not installed on system
    # IndexError insulates from .pyenv/shims not covered in qcng
    except (ResourceError, IndexError):
        raise ProgramNotFoundError(program)


def get_adapter(
    program: str, inp_obj: InputBase, qcng_fallback: bool = False
) -> BaseAdapter:
    """Get the adapter for a program.

    Args:
        program: The program to get the adapter for.
        inp_obj: The input object for the calculation.
        qcng_fallback: Fallback to use QCEngine if the adapter is not in qcop.

    Returns:
        The adapter for the program.

    Raises:
        AdapterNotFoundError: If the adapter is not found.
    """
    if isinstance(inp_obj, FileInput):
        return FileAdapter(program)
    try:
        return registry[program]()
    except KeyError:
        if qcng_fallback:
            # Raises AdapterNotFoundError or ProgramNotFoundError
            check_qcng_support(program)
            return registry["qcengine"](program)
        raise AdapterNotFoundError(program)


def construct_provenance(
    program: str,
    adapter: BaseAdapter,
    working_dir: Path,
    start: float,
    stdout: Optional[str],
) -> Provenance:
    """Construct a provenance object for a calculation.

    Args:
        program: The program used for the calculation.
        adapter: The adapter used for the calculation.
        working_dir: The working directory of the calculation.
        start: The start time of the calculation.
        stdout: The stdout of the calculation.

    Returns:
        The Provenance object.
    """
    wall_time = time() - start
    program_version = getattr(adapter, "program_version", lambda _: None)(stdout)

    return Provenance(
        program=program,
        program_version=program_version,
        working_dir=str(working_dir),
        wall_time=round(wall_time, 6),
        hostname=platform.node(),
        hostcpus=os.cpu_count(),
    )
