import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Callable, List, Optional

from qcio.helper_types import StrOrPath

from .adapters import registry
from .exceptions import (
    AdapterNotFoundError,
    ExternalProgramExecutionError,
    ProgramNotFoundError,
)


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


def execute_subprocess(
    program: str,
    cmdline_args: Optional[List[str]] = None,
    update_func: Optional[Callable] = None,
    update_interval: Optional[float] = 0.5,
) -> str:
    """Execute a subprocess and monitor its stdout/stderr using a callback function.

    Args:
        program: The program to run.
        cmdline_args: The command line arguments to pass to the program.
        update_func: A function to call as the program executes to monitor stdout. The
            function must accept two string arguments, 1) The entire stdout/stderr
            output from the process, and 2) The output since the last call to
            update_func. The update_func is called at least once, and then every
            update_interval seconds. This is useful when executing code on remote
            servers and you want to pass a callback to monitor the output in real time.
            If you want to simply monitor stdout on your local machine in real time
            pass a simple update_func like this:
                execute_subprocess(
                    program,
                    update_func=lambda stdout, new_stdout: print(new_stdout
                    update_interval=0.5,
                )
        update_interval: The minimum time in seconds between calls to the update_func.
            Defaults to 0.5 seconds if update_func is not None. Default is set inside
            the function to avoid issues with mypy and default arguments.

    Returns:
        The stdout of the program as a string.

    Raises:
        ProgramNotFoundException: If the program is not found.
        ExternalProgramExecutionError: If the program fails during execution and
            returns a non-zero exit code.
    """
    cmd = [program] + (cmdline_args or [])
    # Execute subprocess asynchronously so we can monitor stdout and stderr.
    try:
        proc = subprocess.Popen(
            cmd,
            # redirects stdout to a pipe, ensures proc.stdout is not None
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # stderr is redirected to stdout
            universal_newlines=True,  # returns stdout as string
        )
    except FileNotFoundError:
        raise ProgramNotFoundError(program)

    # Setup variables for monitoring stdout
    stdout_lines: List[str] = []
    prev_update_time = time.time()
    prev_line_count = len(stdout_lines)

    # Read stdout line by line as it is available until proc terminates
    while proc.poll() is None:
        # This blocks until it receives a newline.
        # ignore mypy because stdout=subprocess.PIPE, not None
        line = proc.stdout.readline()  # type: ignore
        if line:  # readline may return '' at EOF and we don't want to append that
            stdout_lines.append(line)

        if (
            update_func
            and time.time() - prev_update_time > (update_interval or 0.5)
            and len(stdout_lines) > prev_line_count
        ):
            # Call update_func with the current stdout
            stdout = "".join(stdout_lines)
            stdout_since_last_update = "".join(stdout_lines[prev_line_count:])
            update_func(stdout, stdout_since_last_update)
            prev_update_time = time.time()
            prev_line_count = len(stdout_lines)

    # Unconsumed output may still need to be processed
    # ignore mypy because stdout=subprocess.PIPE, not None
    for line in proc.stdout.readlines():  # type: ignore
        stdout_lines.append(line)
    stdout = "".join(stdout_lines)

    # Check if program executed successfully
    if proc.returncode != 0:
        raise ExternalProgramExecutionError(
            returncode=proc.returncode, cmd=" ".join(cmd), stdout=stdout
        )

    return stdout


def qcng_get_program(program: str) -> None:
    """Wrapper around qcng.get_program that raises correct qcop errors if the
    adapter (harness) or program are not found
    """
    from qcengine import get_program
    from qcengine.exceptions import InputError, ResourceError

    try:
        get_program(program)
    except InputError as e:  # Program not registered with QCEngine
        raise AdapterNotFoundError(program) from e
    # IndexError insulates from .pyenv/shims not covered in qcng
    except (ResourceError, IndexError):  # Program not installed on system
        raise ProgramNotFoundError(program)


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
