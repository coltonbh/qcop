from abc import ABC, abstractmethod
from typing import Callable, Optional, Union

from qcio import FileInput
from qcio.abc_io import InputBase, OutputBase


class BaseAdaptor(ABC):
    """Base class for all adaptors."""

    @abstractmethod
    def compute(
        self,
        inp_obj: InputBase,
        update_func: Optional[Callable] = None,
        update_interval: float = 0.5,
    ) -> OutputBase:
        """Compute the given program on the given files.

        Implementations of this function can assume:
            - All input files have already been written to the working directory.
            - Any requested output files will be collected automatically.

        Args:
            inp_obj: The qcio input object for a computation.
            update_func: A function to call with the current progress. The function must
                take the entire stdout/stderr output as a string for its first
                    argument.
            update_interval: The minimum time in seconds between calls to the
                update_func.


        Returns:
            The qcio output object for a computation. Will either be a FailedOperation
                object or the corresponding output object for the input object.
        """
        pass
