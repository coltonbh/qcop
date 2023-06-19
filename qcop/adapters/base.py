from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from qcio.models.base_io import ComputedPropertiesBase, InputBase
from qcio.models.single_point import SinglePointComputedProperties

from qcop.exceptions import UnsupportedCalcTypeError

__all__ = ["BaseAdapter", "registry"]

# Registry for all Adaptors
registry = {}


class BaseAdapter(ABC):
    """Base class for all adapters."""

    # Whether to write files from inp_obj to disk before executing program.
    # If True, the adapter will write all files from inp_obj to disk before executing
    # the program. If False, the adapter must handle input files itself in some other
    # way. Generally this should be True for most adapters unless the program can
    # handle input files directly from memory, stdin, or some other mechanism that is
    # more efficient than writing to disk.
    write_files = True

    @abstractmethod
    def compute(
        self,
        inp_obj: InputBase,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
    ) -> ComputedPropertiesBase:
        """Compute the given program on the given files.

        Implementations of this function can assume:
            - All input files have already been written to the working directory.
            - Output files requested as output will be collected automatically.

        Args:
            inp_obj: The qcio input object for a computation.
            update_func: A function to call with the current progress. The function must
                take the entire stdout/stderr output as a string for its first
                    argument.
            update_interval: The minimum time in seconds between calls to the
                update_func.


        Returns:
            The computed properties object for a computation.
        """


class QCOPProgramAdapter(BaseAdapter):
    """Base adapter for all program adapters."""

    program: str  # All subclasses must specify program name

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Ensure that subclasses define the required class attributes
        if not getattr(cls, "program", None):
            raise NotImplementedError(
                f"Subclasses of QCOPProgramAdapter must define a program string. "
                f"{cls.__name__} does not meet this requirement."
            )

        # Automatically register all subclasses
        registry[cls.program] = cls

    @abstractmethod
    def program_version(self, stdout: Optional[str]) -> str:
        """Get the version of the program.

        Args:
            stdout: The stdout from the program. Because running "program --version"
                can be extremely slow for some programs, the stdout from the program
                is passed in here so that the version can be extracted from it if
                possible. If the version cannot be extracted from the stdout, then
                this function should extract the program version in some other way.
        """


class QCOPSinglePointAdapter(QCOPProgramAdapter):
    # TODO: This is a hack. Remove!
    program = "fake program"
    supported_calc_types: List[str]  # All subclasses must specify supported drivers

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not getattr(cls, "supported_calc_types", None):
            raise NotImplementedError(
                f"Subclasses of QCOPProgramAdapter must define a nonempty "
                f"supported_calc_types list. {cls.__name__} does not meet this "
                "requirement."
            )

    def compute(
        self,
        inp_obj: InputBase,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
    ) -> SinglePointComputedProperties:
        """Single point compute method."""
        if inp_obj.program_args.calc_type not in self.supported_calc_types:
            raise UnsupportedCalcTypeError(
                program=self.program,
                calc_type=inp_obj.program_args.calc_type,
                supported_calc_types=self.supported_calc_types,
            )
        return self._compute(inp_obj, update_func, update_interval)

    @abstractmethod
    def _compute(
        self,
        inp_obj: InputBase,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
    ) -> SinglePointComputedProperties:
        """Subclasses should implement this method with custom compute logic."""
