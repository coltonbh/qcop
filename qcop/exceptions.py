"""Experimental exception hierarchy. This may be too complex and unhelpful for now"""

from subprocess import CalledProcessError
from typing import Optional

from qcio import ResultsBase


class QCOPBaseError(Exception):
    """Base class for exceptions in qcop. All custom exceptions should inherit from
    this class."""

    pass


class AdapterError(QCOPBaseError):
    """Base class for exceptions thrown by adapters."""

    pass


class AdapterNotFoundError(AdapterError):
    """
    Exception raised when no adapter can be found for a given program.

    Args:
        program: Program for which no adapter was found
    """

    def __init__(self, program: str):
        self.program = program
        self.message = f"No adapter found for program '{program}'."
        super().__init__(self.message)


class AdapterInputError(AdapterError):
    """
    Exception raised when inputs to an adaptor are incorrect.

    Args:
        program: Program for which input files could not be generated
        message: explanation of the error
    """

    def __init__(self, program: str, message: str):
        self.program = program
        self.message = message
        super().__init__(self.message)


class QCEngineError(QCOPBaseError):
    """Exception raised when any part of qcengine execution fails."""

    pass


class ExternalProgramError(QCOPBaseError):
    """Base Exception raised for errors with an external program."""

    pass


class ProgramNotFoundError(ExternalProgramError):
    """
    Exception raised when a program cannot be found on the host system.

    Args:
        program: program which was not found
        message: explanation of the error
    """

    def __init__(self, program: str):
        self.program = program
        self.message = (
            f"Program not found: '{self.program}'. To use {self.program} please "
            f"install it on your system and ensure that it is on your PATH."
        )
        super().__init__(self.message)


class ExternalProgramExecutionError(ExternalProgramError, CalledProcessError):
    """
    Exception raised when an external program fails.

    Args:
        returncode: Return code of the subprocess
        cmd: Command which failed
        results: Any computed results from the subprocess or previous steps in the
            workflow. Used to pass trajectory results e.g., from a geometry optimization
        stdout: Standard output of the subprocess
        stderr: Standard error of the subprocess
    """

    def __init__(
        self,
        returncode: int,
        cmd: str,
        results: Optional[ResultsBase] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(returncode, cmd, stdout, stderr)
        self.results = results
