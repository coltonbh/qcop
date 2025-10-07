
import numpy as np
import pytest
from qcio import (
    CalcSpec,
    CalcType,
    CompositeCalcSpec,
    CoreSpec,
    Results,
    SinglePointData,
    Structure,
)

from qcop.adapters.base import ProgramAdapter
from qcop.utils import prog_available


@pytest.fixture(scope="session")
def hydrogen():
    """Create a Hydrogen structure object."""
    return Structure(
        symbols=["H", "H"],
        # Integration test depend upon this geometry; do not change
        geometry=[[0, 0, 0], [0, 0, 1.4]],
    )


@pytest.fixture(scope="session")
def water():
    """Create a water structure object."""
    return Structure(
        symbols=["O", "H", "H"],
        # Integration test depend upon this geometry; do not change
        geometry=[
            [0.0, 0.0, 0.0],
            [0.524, 1.687, 0.480],
            [1.146, -0.450, -1.354],
        ],
    )


@pytest.fixture(scope="session")
def calcspec(hydrogen):
    """Create a function that returns a CalcSpec object with a specified
    calculation type."""

    def create_prog_input(calctype):
        return CalcSpec(
            structure=hydrogen,
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
def ccalcspec(hydrogen):
    def create_prog_input(calctype):
        return CompositeCalcSpec(
            calctype=calctype,
            structure=hydrogen,
            subprogram="test",
            subprogram_spec=CoreSpec(
                model={"method": "hf", "basis": "sto-3g"},
            ),
        )

    return create_prog_input


@pytest.fixture
def results(calcspec):
    """Create Results object"""
    sp_inp_energy = calcspec("energy")
    energy = 1.0
    n_atoms = len(sp_inp_energy.structure.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    return Results[CalcSpec, SinglePointData](
        input_data=sp_inp_energy,
        success=True,
        logs="program standard out...",
        data={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcio-test-suite", "scratch_dir": "/tmp/qcio"},
        extras={"some_extra": 1},
    )


@pytest.fixture(scope="session")
def test_adapter():
    class TestAdapter(ProgramAdapter):
        # Both program and supported_driver defined
        program = "test"
        supported_calctypes = [CalcType.energy, CalcType.gradient]

        def compute_data(
            self, input_data, update_func=None, update_interval=None, **kwargs
        ):
            return SinglePointData(energy=0.0), "Some stdout."

        def program_version(self, stdout: str | None = None) -> str:
            return "v1.0.0"

    return TestAdapter()


def skipif_program_not_available(program_name: str):
    """Skip a test if the given program is not available."""
    return pytest.mark.skipif(
        not prog_available(program_name), reason=f"{program_name} is not installed."
    )
