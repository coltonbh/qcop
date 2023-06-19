from typing import Callable, Optional
import subprocess

from qcio import FileInput, FileOutput

from qcop.adaptors.base import BaseAdaptor
from qcop.helpers import execute_subprocess


class FileAdaptor(BaseAdaptor):
    """Adaptor for running a program on files."""

    def __init__(self, program: str) -> None:
        super().__init__()
        self.program = program

    def compute(
        self,
        inp_obj: FileInput,
        update_func: Optional[Callable] = None,
        update_interval: float = 0.5,
    ) -> FileOutput:
        try:
            stdout = execute_subprocess(
                self.program, inp_obj.args.cmdline_args, update_func, update_interval
            )
        except subprocess.CalledProcessError as e:
            return FileOutput.from_error(e.stderr)
        return FileOutput(input_data=inp_obj, stdout=stdout)
