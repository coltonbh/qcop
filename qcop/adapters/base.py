import traceback
from abc import ABC, abstractmethod
from time import time
from typing import Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from qcio import (
    CalcType,
    FileInput,
    InputBase,
    OptimizationOutput,
    OutputBase,
    ProgramFailure,
    ResultsBase,
    SinglePointOutput,
)
from qcio.helper_types import StrOrPath
from qcio.models.base_models import QCIOModelBase
from qcio.models.inputs_base import StructuredInputBase
from qcio.utils import calctype_to_output

from qcop.exceptions import AdapterInputError, QCOPBaseError

from .utils import construct_provenance, tmpdir

__all__ = ["BaseAdapter", "registry"]

# Registry for all Adaptors.
# NOTE: Registry stores class objects, not instances.
# Use registry[program]() to instantiate an adaptor
# Or use the higher level qcop.utils.get_adapter() function.
registry = {}

InputType = TypeVar("InputType", bound=InputBase)
OutputType = TypeVar("OutputType", bound=OutputBase)
ResultsType = TypeVar("ResultsType", bound=ResultsBase)


class BaseAdapter(ABC, Generic[InputType, OutputType, ResultsType]):
    """Base class for all adapters."""

    # Whether to write files from inp_obj to disk before executing program.
    # If True, the adapter will write all files from inp_obj to disk before executing
    # the program. If False, the adapter must handle input files itself in some other
    # way. Generally this should be True for most adapters unless the program can
    # handle input files directly from memory, stdin, or some other mechanism that is
    # more efficient than writing to disk.
    write_files = True
    program: str  # All subclasses must define this attribute.

    def program_version(self, stdout: Optional[str]) -> Optional[str]:
        """Return program version. Adapters should override this method."""
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
    ) -> Tuple[Optional[ResultsType], str]:
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
        **kwargs,
    ) -> OutputType:
        """Compute the given input using the adapter's program.

        Args:
            inp_obj: A qcio input object for a computation. A subclass of InputBase.
                E.g. FileInput, FileInput, DualProgramInput.
            scratch_dir: The scratch directory for the program. If None, a new directory
                is created in the system default temporary directory. If rm_scratch_dir
                is True this directory will be deleted after the program finishes.
            rm_scratch_dir: Delete the scratch directory after the program exits.
            collect_stdout: Whether to collect stdout/stderr from the program as output.
                Failed computations will always collect stdout/stderr.
            collect_files: Collect all files generated by the QC program as output.
            collect_wavefunction: Collect the wavefunction file(s) from the calculation.
                Not every program will support this. Use collect_files to collect
                all files including the wavefunction.
            update_func: A function to call as the program executes. The function must
                accept the in-process stdout/stderr output as a string for its first
                argument.
            update_interval: The minimum time in seconds between calls to the
                update_func.
            print_stdout: Whether to print stdout/stderr to the terminal in real time as
                the program executes. Will be ignored if an update_func passed.
            raise_exc: If False, qcop will return a ProgramFailure object when the QC
                program fails rather than raise an exception. qcop exceptions not
                related to the external program failure will always be raised.
            propagate_wfn: For any adapter performing a sequential task, such
                as a geometry optimization, propagate the wavefunction from the previous
                step to the next step. This is useful for accelerating convergence by
                using a previously computed wavefunction as a starting guess. If an
                adapter does not support wavefunction propagation, an AdapterInputError
                will be raised.
            **kwargs: Additional keyword arguments to pass to the adapter or
                qcng.compute().

        Returns:
            The qcio output object for a calctype. A subclass of OutputBase. Will either
            be a ProgramFailure object or the corresponding output object for the
            calctype type. E.g., "energy" -> SinglePointOutput. "optimization" ->
            OptimizationOutput.

        Raises:
            AdapterNotFoundError: If the program is not supported (i.e., no Adapter
                is implemented for it in qcop or qcengine).
            ProgramNotFoundError: If the program executable is not found on the
                system at execution time. This likely means the program is not installed
                on the system.
            AdapterInputError: If the input is invalid for the adapter.
            ExternalProgramExecutionError: If the program fails during execution and
                raise_exc=True.
            QCEngineError: If QCEngine performed the computation, fails and
                raise_exc=True.
        """
        self.validate_input(inp_obj)
        # Set update_func if print_stdout is True and update_func is None
        if print_stdout and update_func is None:
            update_func, update_interval = (
                lambda _, stdout_new: print(stdout_new),
                0.1,
            )

        # Change cwd to a temporary directory to run the program.
        with tmpdir(scratch_dir, rm_scratch_dir) as final_scratch_dir:
            if self.write_files:  # Write non structured input files to disk.
                inp_obj.save_files()

            output_dict: Dict[str, Optional[Union[str, QCIOModelBase]]] = {}
            stdout: Optional[str]

            start = time()
            qcop_exception = None
            results: Optional[ResultsBase]
            try:
                # Execute the program; return results and stdout
                results, stdout = self.compute_results(
                    inp_obj,
                    update_func,
                    update_interval,
                    propagate_wfn=propagate_wfn,
                    **kwargs,
                )
                # None value covers FileInput case
                output_cls = calctype_to_output(getattr(inp_obj, "calctype", None))
            except QCOPBaseError as e:
                qcop_exception = e
                # Set variables to construct a ProgramFailure object.
                output_cls = ProgramFailure
                results = getattr(e, "results", None)  # Any half-completed results
                stdout = getattr(e, "stdout", None)
                # For mypy because e.stdout is not of a known type
                stdout = str(stdout) if stdout is not None else None
                output_dict["traceback"] = traceback.format_exc()

            # Construct Provenance object
            wall_time = time() - start
            provenance = construct_provenance(
                self.program, self.program_version(stdout), final_scratch_dir, wall_time
            )

            # Construct output object
            stdout = (  # Always collect for failures; otherwise obey collect_stdout
                None if output_cls != ProgramFailure and not collect_stdout else stdout
            )

            # Ensure results is not None to maintain interface
            results = results if results is not None else ResultsBase()
            output_dict.update(
                {
                    "input_data": inp_obj,
                    "stdout": stdout,
                    "results": results,
                    "provenance": provenance,
                }
            )

            output_obj = output_cls(**output_dict)

            # Optionally collect output files
            if collect_files or isinstance(inp_obj, FileInput):
                # Collect output files from the calc_dir
                output_obj.open_files(
                    final_scratch_dir, recursive=True, exclude=inp_obj.files.keys()
                )

            # Optionally collect wavefunction file
            if collect_wfn and not collect_files:
                # Collect wavefunction file from the calc_dir
                self.collect_wfn(output_obj)

        # Append ProgramFailures to exception and raise if raise_exc=True
        # Helpful for BigChem exception handling
        if raise_exc and qcop_exception:
            qcop_exception.program_failure = output_obj
            # Updating .args is necessary for Celery to properly serialize the exception
            qcop_exception.args = (*qcop_exception.args, output_obj)
            raise qcop_exception

        return output_obj

    def collect_wfn(self, output: SinglePointOutput) -> None:
        """Collect the wavefunction file(s) from the scratch_dir.

        Args:
            output: The output object to add the wavefunction file(s) to.

        Returns:
            None. The output is modified in place.

        """
        # Collect wavefunction file from the calc_dir
        raise AdapterInputError(
            self.program,
            f"Adapter for {self.program} does not support wavefunction collection.",
        )


StructuredInputType = TypeVar("StructuredInputType", bound=StructuredInputBase)


class ProgramAdapter(
    BaseAdapter[
        StructuredInputType, Union[SinglePointOutput, OptimizationOutput], ResultsType
    ],
    Generic[StructuredInputType, OutputType, ResultsType],
):
    """Base adapter for all program adapters (all but FileAdaptor)."""

    supported_calctypes: List[
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

    def validate_input(self, inp_obj: StructuredInputBase) -> None:
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
