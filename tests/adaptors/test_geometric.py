import pytest
from qcio import CalcType, OptimizationResults, QCProgramArgs

from qcop.adapters import GeometricAdapter
from qcop.adapters.utils import tmpdir
from qcop.exceptions import ExternalProgramExecutionError, ProgramNotFoundError


def test_ensure_geometric():
    # Test successful import
    try:
        import geometric

        is_geometric_available = True
    except ImportError:
        is_geometric_available = False

    if is_geometric_available:
        result = GeometricAdapter()._ensure_geometric()
        assert result == geometric
    else:
        # Test when geometric is not available
        with pytest.raises(ProgramNotFoundError) as excinfo:
            GeometricAdapter()._ensure_geometric()
        assert "geometric" in str(excinfo.value)


@pytest.mark.parametrize(
    "calctype, expected",
    [
        (CalcType.transition_state, True),
        (CalcType.optimization, False),
    ],
)
def test_update_inp_obj(calctype, expected, dual_prog_inp):
    adapter = GeometricAdapter()
    prog_inp = dual_prog_inp(calctype)
    adapter._update_inp_obj(prog_inp)
    assert prog_inp.keywords["transition"] is expected


def test_create_geometric_molecule(hydrogen):
    adapter = GeometricAdapter()

    with tmpdir() as scratch_dir:
        geometric_molecule = adapter._create_geometric_molecule(hydrogen)

        # assertions
        assert isinstance(geometric_molecule, adapter.geometric.molecule.Molecule)
        assert not any(scratch_dir.iterdir())  # check that the file was deleted


def test_qcio_geometric_engine_exception_handling(
    test_adapter, hydrogen, sp_output, mocker
):
    adapter = GeometricAdapter()  # Just for using helper methods below
    QCIOGeometricEngine = adapter._geometric_engine()
    geometric_hydrogen = adapter._create_geometric_molecule(hydrogen)

    engine = QCIOGeometricEngine(
        test_adapter,
        QCProgramArgs(**{"model": {"method": "hf", "basis": "sto-3g"}}),
        hydrogen,
        geometric_hydrogen,
    )

    # Set trajectory
    engine.qcio_trajectory = [sp_output]

    # Mock adapter to raise ExternalProgramExecutionError
    mocker.patch.object(
        test_adapter,
        "compute",
        side_effect=ExternalProgramExecutionError(
            1, "terachem tc.in", stdout="some stdout"
        ),
    )

    with pytest.raises(ExternalProgramExecutionError) as excinfo:
        # Random coordinates for testing
        coords = hydrogen.geometry
        engine.calc_new(coords)

    assert excinfo.value.results == OptimizationResults(trajectory=[sp_output])
