import numpy as np
import pytest
from qcio import CalcSpec, Structure

from qcop import compute
from tests.conftest import skipif_program_not_available


@pytest.mark.integration
@skipif_program_not_available("crest")
def test_crest():
    input_data = CalcSpec(
        structure=Structure(
            symbols=["O", "H", "H"],
            # Integration test depend upon this geometry; do not change
            geometry=[
                [0.0, 0.0, 0.0],
                [0.524, 1.687, 0.480],
                [1.146, -0.450, -1.354],
            ],
        ),
        calctype="conformer_search",
        # Integration tests depend up this model; do not change
        model={"method": "gfnff"},
        # assertions depend upon these keywords; do not change
        keywords={"calculation": {"level": [{"alpb": "acetonitrile"}]}},
    )

    prog_output = compute("crest", input_data)

    assert len(prog_output.results.conformers) == 1
    assert np.isclose(prog_output.results.conformer_energies[0], -0.33568982, atol=1e-4)
    # Solvent getting passed correctly
    assert "alpb" in prog_output.stdout
    assert "acetonitrile" in prog_output.stdout
