import importlib
from typing import Callable, Optional

from qcio import CalcType, ProgramInput, SinglePointResults

from qcop.exceptions import AdapterError, ProgramNotFoundError

from .base import ProgramAdapter


class TeraChemFEAdapter(ProgramAdapter[ProgramInput, SinglePointResults]):
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

    def program_version(self, stdout: Optional[str] = None) -> str:
        """Program version is not available via the PB server."""
        return ""

    def compute_results(
        self,
        inp_obj: ProgramInput,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        **kwargs,
    ) -> tuple[SinglePointResults, str]:
        """Execute TeraChem on the given input.

        Args:
            inp_obj: The qcio ProgramInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointResults and the stdout str.
        """
        try:
            with self.client() as client:
                prog_output = client.compute(inp_obj)
        except self.tcpb.exceptions.TCPBError as e:
            exc = AdapterError("An error occurred with TeraChem PBS")
            # Pass stdout to .compute() via the exception
            # Will only exist for TeraChemFrontendAdapter
            exc.stdout = e.program_output.stdout
            raise exc

        else:
            # Write files to disk to be collected by BaseAdapter.compute()
            # Used only for TeraChemFrontendAdapter
            prog_output.results.save_files()

        return prog_output.results, prog_output.stdout
