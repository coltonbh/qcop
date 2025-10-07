from pathlib import Path

from qcio import CalcType, SinglePointData
from qcio.qcel import from_qcel_output_results, to_qcel_input

from qcop.exceptions import ExternalProgramError

from .base import ProgramAdapter


class QCEngineAdapter(ProgramAdapter):
    """Adapter for all programs supported by QCEngine."""

    program = "qcengine"
    supported_calctypes = [CalcType.energy, CalcType.gradient, CalcType.hessian]
    """Supported calculation types."""

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
            raise ExternalProgramError(
                program=self.program,
                message=f"QCEngine could not get version for program {self.external_program}.",
            ) from e

    def compute_data(
        self, input_data, *args, propagate_wfn=False, **kwargs
    ) -> tuple[SinglePointData, str]:
        from qcengine import compute as qcng_compute
        from qcengine.exceptions import QCEngineException

        task_config = kwargs.pop("task_config", {})
        # Use qcio selected working_directory
        task_config["scratch_directory"] = str(Path.cwd())
        # Keep scratch files so qcio can collect them
        task_config["scratch_messy"] = True

        # Remove qcop-specific kwargs
        kwargs.pop("collect_rotamers", None)
        
        try:
            qcng_output = qcng_compute(
                to_qcel_input(input_data),
                self.external_program,
                raise_error=True,  # Always raise exceptions
                return_dict=True,  # qcio works with dicts for qcel i/o
                task_config=task_config,
                **kwargs,
            )

        except QCEngineException as e:  # Base exception for all QCEngine
            raise ExternalProgramError(
                program=self.program,
                message=f"QCEngine could not compute results for {self.external_program}.",
            ) from e

        else:
            return from_qcel_output_results(qcng_output), qcng_output["stdout"]
