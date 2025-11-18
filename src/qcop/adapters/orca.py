import shutil
from collections.abc import Callable
from pathlib import Path

import qccodec
from qccodec import exceptions as qccodec_exceptions
from qccodec.parsers.orca import parse_version
from qcio import CalcType, ProgramInput, SinglePointData

from qcop.exceptions import AdapterInputError, ExternalProgramError

from .base import ProgramAdapter
from .utils import execute_subprocess


class OrcaAdapter(ProgramAdapter[ProgramInput, SinglePointData]):
    """Adapter for Orca."""

    supported_calctypes = [
        CalcType.energy,
        CalcType.gradient,
        CalcType.hessian,
        CalcType.optimization,
        CalcType.transition_state,
    ]
    program = "orca"

    def program_version(self, stdout: str | None = None) -> str:
        """Get the program version.

        Args:
            stdout: The stdout from the program.

        Returns:
            The program version.
        """
        try:
            return parse_version(stdout)
        except qccodec_exceptions.ParserError:
            return "Could not parse version"

    def compute_data(
        self,
        input_data: ProgramInput,
        update_func: Callable | None = None,
        update_interval: float | None = None,
        **kwargs,
    ) -> tuple[SinglePointData, str]:
        """Execute Orca on the given input.

        Args:
            input_data: The qcio ProgramInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointData and the stdout str.
        """
        # Construct TeraChem native input files
        try:
            native_input = qccodec.encode(input_data, self.program)
        except qccodec.exceptions.EncoderError as e:
            raise AdapterInputError(program=self.program) from e

        # Write the input files to disk
        input_filename = "orca.inp"
        Path(input_filename).write_text(native_input.input_file)
        Path(native_input.geometry_filename).write_text(native_input.geometry_file)

        # Execute Orca
        # (A quirk of Orca: One must use the full executable path when running
        # in parallel. See:
        # https://www.faccts.de/docs/orca/6.1/tutorials/first_steps/parallel.html)
        full_orca_path = shutil.which(self.program)
        stdout = execute_subprocess(
            full_orca_path, [input_filename], update_func, update_interval
        )

        # Parse output
        try:
            results = qccodec.decode(
                self.program,
                input_data.calctype,
                stdout=stdout,
                directory=Path.cwd(),
                input_data=input_data,
            )
        except qccodec_exceptions.ParserError as e:
            raise ExternalProgramError(
                program="qccodec",
                message="Failed to parse Orca output.",
                logs=stdout,
                original_exception=e,
            ) from e
        return results, stdout
