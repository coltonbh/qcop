import pytest
from qcio import CalcType, DualProgramInput, OptimizationResults, Results

from qcop.adapters import GeometricAdapter
from tests.conftest import skipif_program_not_available


@pytest.mark.integration
@skipif_program_not_available("terachem")
def test_full_optimization(dual_prog_input_factory):
    prog_input = dual_prog_input_factory(CalcType.optimization)
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["subprogram"] = "terachem"
    prog_input = DualProgramInput(**prog_input_dict)

    adapter = GeometricAdapter()
    output = adapter.compute(prog_input, propagate_wfn=True)
    assert isinstance(output, Results)
    assert isinstance(output.input_data, DualProgramInput)
    assert isinstance(output.data, OptimizationResults)
    # Ensure wavefunction was propagated
    assert (
        "Initial guess will be loaded from c0" in output.data.trajectory[-1].logs
    )
    # Ensure energy went downhill
    assert output.data.energies[0] > output.data.energies[-1]


@pytest.mark.integration
@skipif_program_not_available("terachem")
def test_full_transition_state(dual_prog_input_factory, water):
    """This test lacks any test of correctness, but it does ensure that the
    transition state search does not fail.
    """
    # Must use water or else the transition state search will fail
    prog_input = dual_prog_input_factory(CalcType.transition_state)
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["subprogram"] = "terachem"
    prog_input_dict["structure"] = water
    prog_input = DualProgramInput(**prog_input_dict)

    adapter = GeometricAdapter()
    # Ensure output was produced
    output = adapter.compute(prog_input, propagate_wfn=True)
    assert isinstance(output, Results)
    assert isinstance(output.input_data, DualProgramInput)
    assert isinstance(output.data, OptimizationResults)
    # Ensure wavefunction was propagated
    assert (
        "Initial guess will be loaded from c0" in output.data.trajectory[-1].logs
    )
