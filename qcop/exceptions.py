"""Experimental exception hierarchy. This may be too complex and unhelpful for now"""

import warnings
from typing import Optional

from qcio import ProgramOutput, Results


class QCOPBaseError(Exception):
    """Base class for exceptions in qcop. All custom exceptions should inherit from
    this class."""

    def __init__(
        self,
        message: str,
        program_output: Optional[ProgramOutput] = None,
        *,
        results: Optional[Results] = None,
        stdout: Optional[str] = None,
    ):
        self.program_output = program_output
        self.results = results
        self.stdout = stdout
        super().__init__(message)

    @property
    def program_failure(self):
        """Maintain backwards compatibility."""
        warnings.warn(
            "The 'program_failure' attribute is deprecated and will be removed in a "
            "future release. Use 'program_output' instead.",
            FutureWarning,
            stacklevel=2,
        )
        return self.program_output

    def __str__(self):
        """Omits the program_output attribute from the string representation."""
        return self.args[0]


class AdapterError(QCOPBaseError):
    """Base class for exceptions thrown by adapters."""

    pass


class AdapterNotFoundError(AdapterError):
    """
    Exception raised when no adapter can be found for a given program.

    Args:
        program: Program for which no adapter was found
    """

    def __init__(self, program: str, *args):
        super().__init__(f"No adapter found for program '{program}'.", *args)


class AdapterInputError(AdapterError):
    """
    Exception raised when inputs to an adaptor are incorrect.

    Args:
        program: Program for which input files could not be generated
        message: explanation of the error
    """

    def __init__(self, program: str, message: str, *args):
        self.program = program
        self.message = message
        super().__init__(self.message, *args)


class ExternalProgramError(QCOPBaseError):
    """Base Exception raised for errors with an external program."""

    pass


class ProgramNotFoundError(ExternalProgramError):
    """
    Exception raised when a program cannot be found on the host system.

    Args:
        program: program which was not found
    """

    def __init__(self, program: str, *args, install_msg: Optional[str] = None):
        self.program = program
        self.message = install_msg or (
            f"Program not found: '{self.program}'. To use {self.program} please "
            f"install it on your system and ensure that it is on your PATH."
        )
        super().__init__(self.message, *args)


class QCEngineError(ExternalProgramError):
    """Exception raised when any part of qcengine execution fails."""

    def __init__(self, external_program: str, *args):
        self.message = (
            f"Something went wrong with QCEngine trying to run {external_program}. See "
            "the traceback above for details."
        )
        super().__init__(self.message, *args)


class GeometricError(ExternalProgramError):
    """Exception raised when any part of geomeTRIC execution fails."""

    def __init__(self, *args):
        self.message = (
            "Something went wrong with geomeTRIC. See the traceback above for details."
        )
        super().__init__(self.message, *args)


class ExternalSubprocessError(ExternalProgramError):
    """
    Exception raised when an external subprocess fails.

    Args:
        returncode: Return code of the subprocess
        cmd: Command which failed
        stdout: Standard output of the subprocess
    """

    def __init__(
        self,
        returncode: int,
        cmd: str,
        stdout: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.message = (
            f"External program failed with return code {self.returncode}. "
            f"Command: '{self.cmd}'"
        )
        super().__init__(self.message, *args, **kwargs)
