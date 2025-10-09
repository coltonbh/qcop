import importlib
from collections.abc import Callable

from qcio import CalcType, ProgramInput, SinglePointData

from qcop.exceptions import ExternalProgramError, ProgramNotFoundError

from .base import ProgramAdapter


class TeraChemFEAdapter(ProgramAdapter[ProgramInput, SinglePointData]):
    """Adapter for TeraChem's Protocol Buffer Server and Frontend file server."""

    supported_calctypes = [CalcType.energy, CalcType.gradient]
    """Supported calculation types."""
    program = "terachem-fe"

    def __init__(self):
        super().__init__()
        # Check that xtb-python is installed.
        self.tcpb = self._ensure_tcpb()
        self.client = self.tcpb.TCFrontEndClient

    @staticmethod
    def _ensure_tcpb():
        try:
            return importlib.import_module("tcpb")
        except ModuleNotFoundError:
            raise ProgramNotFoundError(
                "tcpb",
                install_msg=(
                    "Program not found: 'tcpb'. To use tcpb please install it with "
                    "pip install qcop[tcpb] or add '' if your shell requires it. "
                    "e.g., pip install 'qcop[tcpb]'."
                ),
            )

    def program_version(self, stdout: str | None = None) -> str:
        """Program version is not available via the PB server."""
        return ""

    def compute_data(
        self,
        input_data: ProgramInput,
        update_func: Callable | None = None,
        update_interval: float | None = None,
        **kwargs,
    ) -> tuple[SinglePointData, str]:
        """Execute TeraChem on the given input.

        Args:
            input_data: The qcio ProgramInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointData and the stdout str.
        """
        try:
            with self.client() as client:
                prog_output = client.compute(input_data)
        except self.tcpb.exceptions.TCPBError as e:
            exc = ExternalProgramError(
                program=self.program,
                # Pass logs to .compute() via the exception
                # Will only exist for TeraChemFrontendAdapter
                logs=e.results.logs,
            )

            raise exc

        else:
            # Write files to disk to be collected by BaseAdapter.compute()
            # Used only for TeraChemFrontendAdapter
            prog_output.data.save_files()

        return prog_output.data, prog_output.logs
