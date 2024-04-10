"""Adaptor for xtb-python package.

Great overview of how to implement this adaptor:
https://github.com/grimme-lab/xtb-python/blob/main/xtb/qcschema/harness.py
"""

import importlib
from pathlib import Path
from typing import Callable, Optional, Tuple

import numpy as np
from qcio import CalcType, ProgramInput, SinglePointResults, Wavefunction
from qcio.constants import ELEMENTS

from qcop.exceptions import (
    AdapterInputError,
    ExternalProgramError,
    ProgramNotFoundError,
)

from .base import ProgramAdapter


class XTBAdapter(ProgramAdapter):
    """Adapter for xtb-python."""

    supported_calctypes = [CalcType.energy, CalcType.gradient]
    program = "xtb"

    def __init__(self):
        super().__init__()
        # Check that xtb-python is installed.
        self.xtb = self._ensure_xtb()

    def validate_input(self, inp_obj: ProgramInput) -> None:
        """Validate the input for xtb-python."""
        super().validate_input(inp_obj)
        # Check that xtb supports the model.
        supported_methods = self.xtb.interface.Param.__members__.keys()
        if inp_obj.model.method not in supported_methods:
            raise AdapterInputError(
                self.program,
                f"Unsupported model '{inp_obj.model.method}'. "
                f"Supported methods include: {supported_methods}",
            )

    def program_version(self, stdout: Optional[str] = None) -> str:
        """Get the program version.

        Args:
            stdout: The stdout from the program.

        Returns:
            The program version.
        """
        return self.xtb.__version__

    @staticmethod
    def _ensure_xtb():
        try:
            xtb = importlib.import_module("xtb")
            # xtb import structure is screwed up so I have to do this too
            importlib.import_module("xtb.interface")
            importlib.import_module("xtb.libxtb")

            return xtb
        except ModuleNotFoundError:
            raise ProgramNotFoundError("xtb")

    def compute_results(
        self,
        inp_obj: ProgramInput,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        **kwargs,
    ) -> Tuple[SinglePointResults, str]:
        """Execute xtb on the given input.

        Args:
            inp_obj: The qcio ProgramInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointComputedProps and the stdout str.
        """
        try:
            # Create Calculator
            atomic_numbers = np.array(
                [ELEMENTS[sym] for sym in inp_obj.molecule.symbols]
            )
            calc = self.xtb.interface.Calculator(
                getattr(self.xtb.interface.Param, inp_obj.model.method),
                atomic_numbers,
                inp_obj.molecule.geometry,
            )
            # Set Keywords
            for key, value in inp_obj.keywords.items():
                # TODO: Need to handle external_charges and solvent
                getattr(calc, f"set_{key}")(value)

            # Always set verbosity high
            calc.set_verbosity(self.xtb.libxtb.VERBOSITY_FULL)
            logs = "logs.out"
            calc.set_output(logs)

            # Perform Calculation
            res = calc.singlepoint()
            # Collect logs
            stdout = Path(logs).read_text()
        except self.xtb.interface.XTBException as e:
            raise ExternalProgramError("Something went wrong with xtb-python.") from e
        else:
            # Collect results
            # TODO: Collect other results like
            results = SinglePointResults(
                energy=res.get_energy(),
                gradient=res.get_gradient(),
                scf_dipole_moment=res.get_dipole(),
                wavefunction=Wavefunction(
                    scf_eigenvalues_a=res.get_orbital_eigenvalues(),
                ),
            )
        return results, stdout
