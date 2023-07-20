import pytest
from qcio import CalcType

from qcop.adapters import GeometricAdapter
from qcop.adapters.utils import tmpdir
from qcop.exceptions import ProgramNotFoundError


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
        assert str(excinfo.value) == "geometric"


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


def test_create_geometric_molecule(dual_prog_inp):
    adapter = GeometricAdapter()

    prog_inp = dual_prog_inp(CalcType.optimization)
    with tmpdir() as scratch_dir:
        geometric_molecule = adapter._create_geometric_molecule(prog_inp)

        # assertions
        assert isinstance(geometric_molecule, adapter.geometric.molecule.Molecule)
        assert not any(scratch_dir.iterdir())  # check that the file was deleted
