from typing import Optional

import numpy as np
import pytest
from qcio import (
    CalcType,
    DualProgramInput,
    Molecule,
    ProgramInput,
    QCProgramArgs,
    SinglePointOutput,
    SinglePointResults,
)

from qcop.adapters.base import ProgramAdapter
from qcop.utils import prog_available


@pytest.fixture(scope="session")
def hydrogen():
    """Create a Hydrogen molecule object."""
    return Molecule(
        symbols=["H", "H"],
        # Integration test depend upon this geometry; do not change
        geometry=[[0, 0, 0], [0, 0, 1.4]],
    )


@pytest.fixture(scope="session")
def water():
    """Create a water molecule object."""
    return Molecule(
        symbols=["O", "H", "H"],
        # Integration test depend upon this geometry; do not change
        geometry=[
            [0.0, 0.0, 0.0],
            [0.524, 1.687, 0.480],
            [1.146, -0.450, -1.354],
        ],
    )


@pytest.fixture(scope="session")
def prog_inp(hydrogen):
    """Create a function that returns a ProgramInput object with a specified
    calculation type."""

    def create_prog_input(calctype):
        return ProgramInput(
            molecule=hydrogen,
            calctype=calctype,
            # Integration tests depend up this model; do not change
            model={"method": "hf", "basis": "sto-3g"},
            # Tests depend upon these keywords; do not change
            keywords={
                "purify": "no",
                "some-bool": False,
            },
        )

    return create_prog_input


@pytest.fixture(scope="function")
def dual_prog_inp(hydrogen):
    def create_prog_input(calctype):
        return DualProgramInput(
            calctype=calctype,
            molecule=hydrogen,
            subprogram="test",
            subprogram_args=QCProgramArgs(
                model={"method": "hf", "basis": "sto-3g"},
            ),
        )

    return create_prog_input


@pytest.fixture
def sp_output(prog_inp):
    """Create SinglePointOutput object"""
    sp_inp_energy = prog_inp("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.molecule.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    return SinglePointOutput(
        input_data=sp_inp_energy,
        stdout="program standard out...",
        results={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture(scope="session")
def sp_test_adapter():
    class TestAdapter(ProgramAdapter):
        # Both program and supported_driver defined
        program = "test"
        supported_calctypes = [CalcType.energy]

        def compute_results(
            self, inp_obj, update_func=None, update_interval=None, **kwargs
        ):
            return SinglePointResults(energy=0.0), "Some stdout."

        def program_version(self, stdout: Optional[str] = None) -> str:
            return "v1.0.0"

    return TestAdapter()


def skipif_program_not_available(program_name: str):
    """Skip a test if the given program is not available."""
    return pytest.mark.skipif(
        not prog_available(program_name), reason=f"{program_name} is not installed."
    )
