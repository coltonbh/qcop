from typing import Callable, Optional, Tuple

from qcio import FileInput, FileOutput

from qcop.adapters.base import BaseAdapter

from .utils import execute_subprocess


class FileAdapter(BaseAdapter):
    """adapter for running a program on files."""

    def __init__(self, program: str) -> None:
        super().__init__()
        self.program = program

    def compute(
        self,
        inp_obj: FileInput,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
    ) -> Tuple[FileOutput, str]:
        """Compute the given program on the given files.

        Args:
            inp_obj: The qcio FileInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
            update_func.

        Returns:
            Tuple of None and FileOutput object for a computation. None is
                returned because no computed properties are returned for a file
                computation.

        Raises:
            ProgramNotFoundException: If the program is not found.

        """
        stdout = execute_subprocess(
            self.program, inp_obj.cmdline_args, update_func, update_interval
        )
        return None, stdout
