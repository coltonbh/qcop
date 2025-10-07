import pytest
from qcio import (
    CalcSpec,
    CalcType,
    CoreSpec,
    OptimizationData,
    Results,
    SinglePointData,
)

from qcop.adapters import GeometricAdapter
from qcop.adapters.utils import tmpdir
from qcop.exceptions import (
    ExternalProgramError,
    ProgramNotFoundError,
)


def test_ensure_geometric():
    # Test successful import
    try:
        import geometric

        is_geometric_available = True
    except ImportError:
        is_geometric_available = False

    if is_geometric_available:
        result = GeometricAdapter()._ensure_geometric_installed()
        assert result == geometric
    else:
        # Test when geometric is not available
        with pytest.raises(ProgramNotFoundError) as excinfo:
            GeometricAdapter()._ensure_geometric_installed()
        assert "geometric" in str(excinfo.value)


@pytest.mark.parametrize(
    "calctype, expected",
    [
        (CalcType.transition_state, True),
        (CalcType.optimization, False),
    ],
)
def test_update_input_data(calctype, expected, ccalcspec):
    adapter = GeometricAdapter()
    prog_inp = ccalcspec(calctype)
    adapter._update_input_data(prog_inp)
    assert prog_inp.keywords["transition"] is expected


def test_create_geometric_molecule(hydrogen):
    adapter = GeometricAdapter()

    with tmpdir() as scratch_dir:
        geometric_molecule = adapter._create_geometric_molecule(hydrogen)

        # assertions
        assert isinstance(geometric_molecule, adapter.geometric.molecule.Molecule)
        assert not any(scratch_dir.iterdir())  # check that the file was deleted


def test_qcio_geometric_engine_exception_handling(
    test_adapter, hydrogen, results, mocker
):
    adapter = GeometricAdapter()  # Just for using helper methods below
    QCIOGeometricEngine = adapter._geometric_engine()
    geometric_hydrogen = adapter._create_geometric_molecule(hydrogen)

    engine = QCIOGeometricEngine(
        test_adapter,
        CoreSpec(**{"model": {"method": "hf", "basis": "sto-3g"}}),
        hydrogen,
        geometric_hydrogen,
    )

    # Set trajectory
    engine.qcio_trajectory = [results]

    # Create a failed Results object
    po_dict = results.model_dump()
    po_dict.update({"success": False, "traceback": "fake traceback"})
    po_failure = Results[CalcSpec, SinglePointData](**po_dict)

    # Mock adapter to raise ExternalProgramExecutionError
    mocker.patch.object(
        test_adapter,
        "compute",
        side_effect=ExternalProgramError(
            program="terachem",
            stdout="some stdout",
            program_output=po_failure,
        ),
    )

    with pytest.raises(ExternalProgramError) as excinfo:
        # Random coordinates for testing
        coords = hydrogen.geometry
        engine.calc_new(coords)

    assert excinfo.value.results == OptimizationData(
        trajectory=[results, po_failure]
    )


def test_geometric_exceptions_converted_to_qcop_exceptions(mocker, ccalcspec):
    adapter = GeometricAdapter()

    # cause .optimizeGeometry to raise a geomeTRIC exception
    mocker.patch(
        "geometric.optimize.Optimizer.optimizeGeometry",
        side_effect=adapter.geometric.errors.Error("Some geomeTRIC exception."),
    )

    prog_inp = ccalcspec(CalcType.optimization)
    with pytest.raises(ExternalProgramError):
        adapter.compute_data(prog_inp, propagate_wfn=False)
