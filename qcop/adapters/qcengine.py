from pathlib import Path
from typing import Tuple

from qcio import CalcType, SinglePointResults
from qcio.qcel import from_qcel_output_results, to_qcel_input

from qcop.exceptions import QCEngineError

from .base import ProgramAdapter


class QCEngineAdapter(ProgramAdapter):
    """Adapter for all programs supported by QCEngine."""

    program = "qcengine"
    supported_calctypes = [CalcType.energy, CalcType.gradient, CalcType.hessian]

    def __init__(self, external_program: str) -> None:
        super().__init__()
        self.external_program = external_program

    def program_version(self, *args) -> str:
        """Get the program version."""
        from qcengine import get_program
        from qcengine.exceptions import QCEngineException

        try:
            adapter = get_program(self.external_program)
            return adapter.get_version()
        except QCEngineException as e:
            raise QCEngineError(
                f"Could not get version for program {self.external_program}."
            ) from e

    def compute_results(
        self, inp_obj, *args, propagate_wfn=False, **kwargs
    ) -> Tuple[SinglePointResults, str]:
        from qcengine import compute as qcng_compute
        from qcengine.exceptions import QCEngineException

        task_config = kwargs.pop("task_config", {})
        # Use qcio selected working_directory
        task_config["scratch_directory"] = str(Path.cwd())
        # Keep scratch files so qcio can collect them
        task_config["scratch_messy"] = True

        try:
            qcng_output = qcng_compute(
                to_qcel_input(inp_obj),
                self.external_program,
                raise_error=True,  # Always raise exceptions
                return_dict=True,  # qcio works with dicts for qcel i/o
                task_config=task_config,
                **kwargs,
            )

        except QCEngineException as e:  # Base exception for all QCEngine
            raise QCEngineError(self.external_program) from e

        else:
            return from_qcel_output_results(qcng_output), qcng_output["stdout"]
