"""Experimental exception hierarchy. This may be too complex and unhelpful for now"""

from typing import Optional

from qcio import ProgramOutput, Results


class QCOPBaseError(Exception):
    """
    Base class for all qcop exceptions.

    All QCOP exceptions must eventually have a non-None program_output attribute.
    Lower-level code may leave program_output as None; the top-level compute() method
    should attach the final ProgramOutput before propagating the error. If some results
    were computed before the error occurred, they should be attached to the exception
    as well.
    """

    def __init__(
        self,
        message: str,
        # Needed as positional arg for celery serialization
        program_output: Optional[ProgramOutput] = None,
        *,
        results: Optional[Results] = None,
    ):
        super().__init__(message)
        self.program_output = program_output
        self.results = results

    def __str__(self):
        # Only the message is shown in the string representation.
        return self.args[0]

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"program_output={self.program_output!r}, results={self.results!r})"
        )


# ===================== Adapter-Related Errors =====================


class AdapterError(QCOPBaseError):
    """Exceptions due to misconfiguration or invalid inputs for adapters."""

    pass


class AdapterNotFoundError(AdapterError):
    """Raised when no adapter can be found for the requested program."""

    def __init__(
        self,
        message: Optional[str] = None,
        program_output: Optional[ProgramOutput] = None,
        *,
        program: str,
    ):
        if message is None:
            message = f"No adapter found for program '{program}'."
        super().__init__(message, program_output)
        self.program = program

    def __repr__(self):
        return f"{super().__repr__()}, program={self.program!r}"


class AdapterInputError(AdapterError):
    """Raised when the inputs provided to an adapter are invalid."""

    def __init__(
        self,
        message: Optional[str] = None,
        program_output: Optional["ProgramOutput"] = None,
        *,
        program: str,
    ):
        if message is None:
            message = f"Invalid inputs for program '{program}'."
        super().__init__(message, program_output)
        self.program = program


# ===================== External Program Errors =====================


class ExternalProgramError(QCOPBaseError):
    """
    Raised when an external program or package fails to complete successfully.

    This covers failures from external subprocesses, Python packages (like qcparse or QCEngine),
    or any other external libraries.

    Attributes:
        results: Any results computed before the error was raised.
        program: The name of the external program that failed.
        original_exception: The original exception that was caught (if any).
        stdout: The standard output produced by the external call.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        program_output: Optional["ProgramOutput"] = None,
        *,
        program: str,
        results: Optional["Results"] = None,
        original_exception: Optional[Exception] = None,
        stdout: Optional[str] = None,
    ):
        if message is None:
            message = f"External program '{program}' failed."
        super().__init__(message, program_output, results=results)
        self.program = program
        self.original_exception = original_exception
        self.stdout = stdout


class ProgramNotFoundError(ExternalProgramError):
    """Raised when the external program is not found on the host system."""

    def __init__(
        self,
        message: Optional[str] = None,
        program_output: Optional["ProgramOutput"] = None,
        *,
        program: str,
        install_msg: Optional[str] = None,
    ):
        if message is None:
            message = install_msg or (
                f"Program not found: '{program}'. Please install it and ensure it is on your PATH."
            )
        super().__init__(message, program_output, program=program)
        self.program = program
        self.install_msg = install_msg
