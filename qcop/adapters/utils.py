"""
Utility functions for adapters. Avoids circular imports when these functions placed in
top-level utils.py module.
"""
import logging
import os
import platform
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from time import time
from typing import Callable, List, Optional

from qcio import Provenance
from qcio.helper_types import StrOrPath

from qcop.exceptions import ExternalProgramExecutionError, ProgramNotFoundError


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
    prev_update_time = time()
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
            and time() - prev_update_time > (update_interval or 0.5)
            and len(stdout_lines) > prev_line_count
        ):
            # Call update_func with the current stdout
            stdout = "".join(stdout_lines)
            stdout_since_last_update = "".join(stdout_lines[prev_line_count:])
            update_func(stdout, stdout_since_last_update)
            prev_update_time = time()
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


@contextmanager
def capture_logs(logger_name: str):
    """Capture logs from a program during execution."""

    # Create a logger
    logger = logging.getLogger(logger_name)

    # Set the level to capture all logs
    logger.setLevel(logging.DEBUG)

    # Create a string buffer and add a StreamHandler using the buffer
    log_capture_string = StringIO()
    handler = logging.StreamHandler(log_capture_string)

    # Optional: set a format for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    try:
        yield (logger, log_capture_string)
    finally:
        # Remove the handler when done
        logger.removeHandler(handler)


def construct_provenance(
    program: str,
    version: Optional[str],
    scratch_dir: Path,
    start: float,
) -> Provenance:
    """Construct a provenance object for a calculation.

    Args:
        program: The program used for the calculation.
        version: The program version.
        scratch_dir: The working directory of the calculation.
        start: The start time of the calculation.
        stdout: The stdout of the calculation.

    Returns:
        The Provenance object.
    """
    wall_time = time() - start

    return Provenance(
        program=program,
        program_version=version,
        scratch_dir=str(scratch_dir),
        wall_time=round(wall_time, 6),
        hostname=platform.node(),
        hostcpus=os.cpu_count(),
    )


@contextmanager
def tmpdir(directory: Optional[StrOrPath] = None, rmdir: bool = True):
    """Context manager for a temporary directory.

    Args:
        directory: Where to create the temporary directory. If None, a new directory is
            created in the system default temporary directory.
        rmdir: Whether to remove the temporary directory when the context manager exits.
    """
    temp_dir = Path(directory or tempfile.mkdtemp())  # Set path to directory
    temp_dir.mkdir(parents=True, exist_ok=True)  # Create directory
    cwd = Path.cwd()  # Save current working directory
    os.chdir(temp_dir)  # Change to temporary directory
    yield temp_dir  # Execute code in context manager
    if rmdir:  # After exiting context manager
        shutil.rmtree(temp_dir)
    os.chdir(cwd)
