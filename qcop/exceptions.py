"""Experimental exception hierarchy. This may be too complex and unhelpful for now"""

from subprocess import CalledProcessError
from typing import List, Optional

from qcio import SPCalcType


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


class UnsupportedCalcTypeError(AdapterError):
    """
    Exception raised when the required driver is not supported by an adapter.

    Args:
        driver: driver which is not supported
        message: explanation of the error
    """

    def __init__(
        self,
        program: str,
        calc_type: SPCalcType,
        supported_calc_types: List[SPCalcType],
    ):
        self.program = program
        self.calc_type = calc_type
        self.supported_calc_types = supported_calc_types
        self.message = (
            f"The {self.program} adapter does not yet support "
            f"'{self.calc_type.value}' calculations. This adaptor can compute: "
            f"{[i.value for i in self.supported_calc_types]}"
        )
        super().__init__(self.message)


class QCEngineError(QCOPBaseError):
    """Exception raised when any part of qcengine execution fails."""

    pass


class ExternalProgramError(QCOPBaseError):
    """Base Exception raised when an external program fails."""

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
        cmd: Command which failed
        returncode: Return code of the subprocess
        stdout: Standard output of the subprocess
        stderr: Standard error of the subprocess
    """

    def __init__(
        self,
        returncode: int,
        cmd: str,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(returncode, cmd, stdout, stderr)
