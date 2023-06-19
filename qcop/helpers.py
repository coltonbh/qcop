import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from typing import Callable, Optional, List

from qcio.helper_types import StrOrPath

from .adaptors import BaseAdaptor


@contextmanager
def tmpdir(directory: Optional[StrOrPath] = None, rmdir: bool = True):
    """Context manager for a temporary directory.

    Args:
        directory: Where to create the temporary directory. If None, a new directory is
            created in the system default temporary directory.
        rmdir: Whether to remove the temporary directory when the context manager exits.
    """
    path = directory or tempfile.mkdtemp()  # Set path to directory
    cwd = os.getcwd()  # Save current working directory
    os.chdir(path)  # Change to temporary directory
    yield path  # Execute code in context manager
    if rmdir:  # After exiting context manager
        shutil.rmtree(path)
    os.chdir(cwd)


def execute_subprocess(
    program: str,
    cmdline_args: Optional[list] = None,
    update_func: Optional[Callable] = None,
    update_interval: float = 0.5,
) -> str:
    """Execute a subprocess and monitor its stdout/stderr using a callback function.

    Args:
        program: The program to run.
        cmdline_args: The command line arguments to pass to the program.
        update_func: A function to call as the program executes. The function must
            accept the in process stdout/stderr output as a string for its first
            argument.
        update_interval: The minimum time in seconds between calls to the update_func.

    Returns:
        The stdout of the program as a string.

    Raises:
        CalledProcessError: If the program returns a non-zero exit code.
    """
    cmd = [program] + (cmdline_args or [])
    # Execute subprocess asynchronously so we can monitor stdout and stderr.
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,  # stdout is redirected to a pipe
        stderr=subprocess.STDOUT,  # stderr is redirected to stdout
        universal_newlines=True,  # returns stdout as string
    )

    # Setup variables for monitoring stdout
    stdout_lines: List[str] = []
    prev_update_time = time.time()
    prev_line_count = len(stdout_lines)

    # Read stdout line by line as it is available until proc terminates
    while proc.poll() is None:
        # TODO: Make sure this doesn't block indefinitely if no line is available.
        if proc.stdout is not None:
            line = proc.stdout.readline()  # This blocks until it receives a newline.
            stdout_lines.append(line)
            if (
                update_func
                and time.time() - prev_update_time > update_interval
                and len(stdout_lines) > prev_line_count
            ):
                # Call update_func with the current stdout
                stdout = "".join(stdout_lines)
                update_func(stdout)
                prev_update_time = time.time()
                prev_line_count = len(stdout_lines)

    # Unconsumed output may still need to be processed
    if proc.stdout is not None:
        for line in proc.stdout.readlines():
            stdout_lines.append(line)
    stdout = "".join(stdout_lines)

    # Check if program executed successfully
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=proc.returncode, cmd=cmd, output=stdout
        )

    return stdout


def get_adaptor(program: str) -> BaseAdaptor:
    raise NotImplementedError
