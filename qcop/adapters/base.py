import traceback
from abc import ABC, abstractmethod
from time import time
from typing import Any, Callable, Generic, Optional, Union

from qcio import (
    CalcType,
    FileInput,
    Files,
    InputType,
    ProgramOutput,
    Results,
    ResultsType,
    StructuredInputs,
)
from qcio.helper_types import StrOrPath

from qcop.exceptions import AdapterInputError, ProgramNotFoundError, QCOPBaseError

from .utils import construct_provenance, tmpdir

__all__ = ["BaseAdapter", "registry"]

# Registry for all Adaptors.
# NOTE: Registry stores class objects, not instances.
# Use registry[program]() to instantiate an adaptor
# Or use the higher level qcop.utils.get_adapter() function.
registry = {}


class BaseAdapter(ABC, Generic[InputType, ResultsType]):
    """Base class for all adapters."""

    # Whether to this program reads or writes files to disk.
    # If True, the adapter will write all files from inp_obj to a disk before executing
    # the program. If False, the adapter must handle input files itself in some other
    # way. Generally this should be True for most adapters unless the program can
    # handle input files directly from memory, stdin, or some other mechanism that is
    # more efficient than writing to disk.
    uses_files = True
    program: str  # All subclasses must define this attribute.

    def program_version(self, stdout: Optional[str]) -> Optional[str]:
        """Return program version. Adapters should override this method.

        Args:
            stdout: The stdout from the program. Because running "program --version"
                can be extremely slow for some programs, the stdout from the program
                is passed in here so that the version can be extracted from it if
                possible. If the version cannot be extracted from the stdout, then
                this function should return the program version in some other way.
        """
        return None

    @abstractmethod
    def validate_input(self, inp_obj: InputType) -> None:
        """Validate input object to ensure compatibility with adapter.
        Adapters should override this method.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_results(
        self,
        inp_obj: InputType,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        **kwargs,
    ) -> tuple[ResultsType, str]:
        """Subclasses should implement this method with custom compute logic."""
        raise NotImplementedError

    def compute(
        self,
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
        **adapter_kwargs,
    ) -> ProgramOutput[InputType, ResultsType]:
        """Compute the given input using the adapter's program.

        Args:
            inp_obj: A qcio input object for a computation. E.g. A FileInput,
                ProgramInput or DualProgramInput.
            scratch_dir: The scratch directory for the program. If None, a new directory
                is created in the system default temporary directory. If rm_scratch_dir
                is True this directory will be deleted after the program finishes.
            rm_scratch_dir: Delete the scratch directory after the program exits.
            collect_stdout: Whether to collect stdout/stderr from the program as output.
                Failed computations will always collect stdout/stderr.
            collect_files: Collect all files generated by the QC program as output.
            collect_wfn: Collect the wavefunction file(s) from the calculation.
                Not every program will support this. Use collect_files to collect
                all files including the wavefunction.
            update_func: A function to call as the program executes. The function must
                accept the in-process stdout/stderr output as a string for its first
                argument.
            update_interval: The minimum time in seconds between calls to the
                update_func.
            print_stdout: Whether to print stdout/stderr to the terminal in real time as
                the program executes. Will be ignored if an update_func passed.
            raise_exc: If False, qcop will return a ProgramOutput object when the QC
                program fails rather than raise an exception.
            propagate_wfn: For any adapter performing a sequential task, such
                as a geometry optimization, propagate the wavefunction from the previous
                step to the next step. This is useful for accelerating convergence by
                using a previously computed wavefunction as a starting guess. If an
                adapter does not support wavefunction propagation, an AdapterInputError
                will be raised.
            **adapter_kwargs: Additional keyword arguments to pass to the adapter or
                qcng.compute().

        Returns:
            A ProgramOutput object containing the results of the computation.

        Raises:
            AdapterNotFoundError: If the program is not supported (i.e., no Adapter
                is implemented for the program in qcop or qcengine).
            ProgramNotFoundError: If the program executable is not found on the
                system at execution time. This likely means the program is not installed
                or not available on the $PATH.
            AdapterInputError: If the input is invalid for the adapter.
            ExternalProgramExecutionError: If the QC program fails during execution.
            QCEngineError: If QCEngine performs the computation raises an error.
        """
        # Print stdout to terminal in real time as program executes
        if print_stdout and update_func is None:
            update_func, update_interval = (
                lambda _, stdout_new: print(stdout_new),
                0.1,
            )

        # cd to a temporary directory to run the program.
        with tmpdir(self.uses_files, scratch_dir, rm_scratch_dir) as final_scratch_dir:
            if self.uses_files:  # Write non structured input files to disk.
                inp_obj.save_files()

            # Define outputs
            output_dict: dict[str, Any] = {}
            stdout: Optional[str] = None
            results: Results
            exc: Optional[QCOPBaseError] = None
            program_version: Optional[str] = None

            start = time()
            try:
                # Validate input object
                self.validate_input(inp_obj)

                # Execute the program. results will be None if FileInput
                results, stdout = self.compute_results(
                    inp_obj,
                    update_func,
                    update_interval,
                    propagate_wfn=propagate_wfn,
                    **adapter_kwargs,
                )
                # None value covers FileInput case
                # TODO: Is there a type safe way to handle this??
                output_dict["success"] = True

                # Optionally collect wavefunction file
                if collect_wfn and not collect_files:
                    output_dict["files"] = self.collect_wfn()

            except QCOPBaseError as e:
                # TODO: Is there a type safe way to handle this??
                exc = e
                output_dict["success"] = False
                # Any half-completed results
                results = getattr(e, "results") or Files()
                stdout = getattr(e, "stdout", stdout)
                # For mypy because e.stdout is not of a known type
                stdout = str(stdout) if stdout is not None else None
                output_dict["traceback"] = traceback.format_exc()

            wall_time = time() - start

            try:
                program_version = self.program_version(stdout)
            except ProgramNotFoundError:
                pass  # program_version = None set above

            # Construct Provenance object
            provenance = construct_provenance(
                self.program,
                program_version,
                final_scratch_dir,
                wall_time,
            )

            # Always collect for failures; otherwise obey collect_stdout
            stdout = stdout if not output_dict["success"] or collect_stdout else None

            # Construct output object
            output_dict.update(
                {
                    "input_data": inp_obj,
                    "stdout": stdout,
                    "results": results,
                    "provenance": provenance,
                }
            )
            output_obj = ProgramOutput[InputType, ResultsType](**output_dict)

            # Collect files generated by the program
            if self.uses_files and (collect_files or type(inp_obj) is FileInput):
                output_obj.results.add_files(
                    final_scratch_dir,
                    recursive=True,
                    exclude=list(inp_obj.files.keys()),
                )

        # Append ProgramOutput to exception and raise if raise_exc=True
        # Helpful for BigChem and ChemCloud exception handling
        if raise_exc and exc:
            exc.program_output = output_obj
            raise exc

        return output_obj

    def collect_wfn(self) -> dict[str, Union[str, bytes]]:
        """Collect the wavefunction file(s) from the scratch_dir.

        Returns:
            Dictionary of filenames and file data. E.g. {"c0": b"filedata"}

        """
        # Collect wavefunction file from the calc_dir
        raise AdapterInputError(
            program=self.program,
            message=f"Adapter for {self.program} does not support wavefunction collection.",
        )


class ProgramAdapter(BaseAdapter, Generic[InputType, ResultsType]):
    """Base adapter for all program adapters (all but FileAdaptor)."""

    supported_calctypes: list[
        CalcType
    ]  # All subclasses must specify supported calctypes

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Ensure that subclasses define the required class attributes
        if not getattr(cls, "program", None):
            raise NotImplementedError(
                f"Subclasses of {ProgramAdapter.__name__} must define a program "
                f"string. {cls.__name__} does not meet this requirement."
            )

        # Automatically register all subclasses
        registry[cls.program] = cls

        if not getattr(cls, "supported_calctypes", None):
            raise NotImplementedError(
                f"Subclasses of {ProgramAdapter.__name__} must define a nonempty "
                f"supported_calctypes list. {cls.__name__} does not meet this "
                "requirement."
            )

    @abstractmethod
    def program_version(self, stdout: Optional[str]) -> str:
        """Get the version of the program.

        Args:
            stdout: The stdout from the program. Because running "program --version"
                can be extremely slow for some programs, the stdout from the program
                is passed in here so that the version can be extracted from it if
                possible. If the version cannot be extracted from the stdout, then
                this function should return the program version in some other way.
        """

    @abstractmethod
    def compute_results(
        self,
        inp_obj: InputType,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        **kwargs,
    ) -> tuple[ResultsType, str]:
        """All ProgramAdapters must return a ResultsType."""
        raise NotImplementedError

    def validate_input(self, inp_obj: StructuredInputs) -> None:
        """Validate the input object for compatibility with the adapter.

        Args:
            inp_obj: The input object to validate.

        Raises:
            AdapterInputError: If the input object's calctype is not supported.
        """
        if inp_obj.calctype not in self.supported_calctypes:
            raise AdapterInputError(
                program=self.program,
                message=(
                    f"The {self.program} adapter does not yet support "
                    f"'{inp_obj.calctype.value}' calculations. This adaptor can "
                    f"compute: {[ct.value for ct in self.supported_calctypes]}"
                ),
            )
        if inp_obj.files and not self.uses_files:
            raise AdapterInputError(
                program=self.program,
                message=(
                    f"The {self.program} adapter does not support files as additional "
                    "inputs. Remove the files from your input."
                ),
            )
