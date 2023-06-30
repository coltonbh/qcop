from typing import List, Optional

import pytest
from qcio import Molecule, SinglePointComputedProperties, SinglePointInput, SPCalcType

from qcop.adapters.base import QCOPSinglePointAdapter
from qcop.utils import prog_available


# Create fixture for Molecule object
@pytest.fixture(scope="session")
def hydrogen_mol():
    """Create a molecule object."""
    return Molecule(
        symbols=["H", "H"],
        # Integration test depend upon this geometry; do not change
        geometry=[[0, 0, 0], [0, 0, 0.7414]],
        charge=0,
        multiplicity=1,
    )


@pytest.fixture(scope="session")
def sp_input(hydrogen_mol):
    """Create a function that returns a SinglePointInput object with a specified
    calculation type."""

    def _create_sp_input(calc_type):
        return SinglePointInput(
            molecule=hydrogen_mol,
            program_args={
                "calc_type": calc_type,
                # Integration tests depend up this model; do not change
                "model": {"method": "hf", "basis": "sto-3g"},
                "keywords": {
                    "maxiter": 100,
                    "purify": "no",
                    "some-bool": False,
                    "displacement": 1e-3,
                    "thermo_temp": 298.15,
                },
            },
        )

    return _create_sp_input


@pytest.fixture(scope="session")
def sp_test_adapter():
    class TestAdapter(QCOPSinglePointAdapter):
        # Both program and supported_driver defined
        program = "test"
        supported_calc_types = [SPCalcType.energy]

        def _compute(self, inp_obj, update_func=None, update_interval=None):
            return SinglePointComputedProperties(energy=0.0), "Some stdout."

        def program_version(self, stdout: Optional[str] = None) -> str:
            return "v1.0.0"

    return TestAdapter()


def skipif_program_not_available(program_name: str):
    """Skip a test if the given program is not available."""
    return pytest.mark.skipif(
        not prog_available(program_name), reason=f"{program_name} is not installed."
    )


def skipif_no_programs_available(programs: List[str]):
    """Skip a test if the given program is not available."""
    for program in programs:
        if prog_available(program):
            return pytest.mark.skipif(
                False, reason=f"None of {programs} are installed."
            )
    return pytest.mark.skipif(True, reason=f"None of {programs} are installed.")
