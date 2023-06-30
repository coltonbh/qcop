import pytest
from qcengine.exceptions import QCEngineException

from qcop import compute
from qcop.exceptions import AdapterNotFoundError, ProgramNotFoundError, QCEngineError
from qcop.utils import qcng_get_program


def test_compute_raises_adapter_not_found_if_no_adapter_in_qcng():
    with pytest.raises(AdapterNotFoundError):
        qcng_get_program("not_a_real_program")


def test_compute_raises_program_not_found_if_adapter_but_no_program_in_qcng():
    with pytest.raises(ProgramNotFoundError):
        qcng_get_program("mrchem")


def test_qcng_compute_called_if_adapter_not_in_qcop(mocker, sp_input):
    # WOW: Just a crazy note. This test takes ~1.2 to execute, this is the startup
    # overhead cost of qcng.compute(). Absolutely crazy! It comes from the very slow
    # get_program() call, which takes >1s to execute.

    # So system check passes for harness and program installation
    mocker.patch("qcop.utils.qcng_get_program")

    spy = mocker.patch("qcio.SinglePointInput.to_output_from_qcel")
    sp_energy_input = sp_input("energy")
    compute(sp_energy_input, "mrchem")
    assert spy.call_count == 1


def test_qcng_compute_not_called_if_adapter_in_qcop(mocker, sp_input):
    # So system check passes for harness and program installation
    mocker.patch("qcop.utils.qcng_get_program")
    qcng_spy = mocker.patch("qcio.SinglePointInput.to_output_from_qcel")
    compute_spy = mocker.patch("tests.test_qcng_compat.compute")

    sp_energy_input = sp_input("energy")
    compute(sp_energy_input, "terachem")

    assert qcng_spy.call_count == 0
    assert compute_spy.call_count == 1


def test_qcng_exception_wrapping(mocker, sp_input):
    # So system check passes for harness and program installation
    mocker.patch("qcop.utils.qcng_get_program")
    qcng_spy = mocker.patch("qcengine.compute")
    qcng_spy.side_effect = QCEngineException("QCEngine Failed!")

    sp_energy_input = sp_input("energy")
    with pytest.raises(QCEngineError):
        compute(sp_energy_input, "fake")

    # assert "test" in str(exc.value)
