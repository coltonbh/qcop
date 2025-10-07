import pytest
from qcio import CalcType, CompositeCalcSpec, OptimizationResults, ProgramOutput

from qcop.adapters import GeometricAdapter
from tests.conftest import skipif_program_not_available


@pytest.mark.integration
@skipif_program_not_available("terachem")
def test_full_optimization(dual_prog_inp):
    prog_inp = dual_prog_inp(CalcType.optimization)
    prog_inp_dict = prog_inp.model_dump()
    prog_inp_dict["subprogram"] = "terachem"
    prog_inp = CompositeCalcSpec(**prog_inp_dict)

    adapter = GeometricAdapter()
    output = adapter.compute(prog_inp, propagate_wfn=True)
    assert isinstance(output, ProgramOutput)
    assert isinstance(output.input_data, CompositeCalcSpec)
    assert isinstance(output.results, OptimizationResults)
    # Ensure wavefunction was propagated
    assert (
        "Initial guess will be loaded from c0" in output.results.trajectory[-1].stdout
    )
    # Ensure energy went downhill
    assert output.results.energies[0] > output.results.energies[-1]


@pytest.mark.integration
@skipif_program_not_available("terachem")
def test_full_transition_state(dual_prog_inp, water):
    """This test lacks any test of correctness, but it does ensure that the
    transition state search does not fail.
    """
    # Must use water or else the transition state search will fail
    prog_inp = dual_prog_inp(CalcType.transition_state)
    prog_inp_dict = prog_inp.model_dump()
    prog_inp_dict["subprogram"] = "terachem"
    prog_inp_dict["structure"] = water
    prog_inp = CompositeCalcSpec(**prog_inp_dict)

    adapter = GeometricAdapter()
    # Ensure output was produced
    output = adapter.compute(prog_inp, propagate_wfn=True)
    assert isinstance(output, ProgramOutput)
    assert isinstance(output.input_data, CompositeCalcSpec)
    assert isinstance(output.results, OptimizationResults)
    # Ensure wavefunction was propagated
    assert (
        "Initial guess will be loaded from c0" in output.results.trajectory[-1].stdout
    )
