import numpy as np
import pytest
from qcio import CalcType, Molecule, ProgramInput

from qcop import compute
from qcop.adapters import XTBAdapter
from qcop.exceptions import AdapterInputError
from tests.conftest import skipif_program_not_available


def test_validate_input(mocker, prog_inp):
    valid_method = "GFN2xTB"
    inp_dict = prog_inp(CalcType.gradient).model_dump()
    inp_dict["model"]["method"] = "some_invalid_method"
    invalid_method = ProgramInput(**inp_dict)

    adapter = XTBAdapter()

    with pytest.raises(AdapterInputError):
        adapter.validate_input(invalid_method)

    inp_dict["model"]["method"] = valid_method
    valid_method = ProgramInput(**inp_dict)
    adapter.validate_input(valid_method)


@pytest.mark.integration
@skipif_program_not_available("xtb")
def test_xtb():
    inp_obj = ProgramInput(
        molecule=Molecule(
            symbols=["O", "H", "H"],
            # Integration test depend upon this geometry; do not change
            geometry=[
                [0.0, 0.0, 0.0],
                [0.524, 1.687, 0.480],
                [1.146, -0.450, -1.354],
            ],
        ),
        calctype="gradient",
        # Integration tests depend up this model; do not change
        model={"method": "GFN2xTB"},
        # Tests depend upon these keywords; do not change
        keywords={},
    )

    output = compute("xtb", inp_obj)
    assert np.isclose(output.results.energy, -5.070218272184619, atol=1e-6)
    assert np.allclose(
        output.results.gradient,
        np.array(
            [
                [-0.01079716, -0.0081492, 0.00556273],
                [0.00481361, 0.00628781, -0.00093842],
                [0.00598355, 0.00186139, -0.00462431],
            ]
        ),
        atol=1e-6,
    )
