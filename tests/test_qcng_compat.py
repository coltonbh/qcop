import pytest

from qcop import compute
from qcop.adapters import registry
from qcop.exceptions import AdapterNotFoundError, ProgramNotFoundError, QCEngineError
from qcop.utils import check_qcng_support


def test_compute_raises_adapter_not_found_if_no_adapter_in_qcng():
    with pytest.raises(AdapterNotFoundError):
        check_qcng_support("not-a-real-program")


def test_compute_raises_program_not_found_if_adapter_but_no_program_in_qcng():
    with pytest.raises(ProgramNotFoundError):
        check_qcng_support("mrchem")  # Assumes mrchem is not installed


def test_qcng_fallback_tried_if_adapter_not_in_qcop(mocker, prog_inp):
    # WOW: Just a crazy note. This test takes ~1.2 to execute, this is the startup
    # overhead cost of qcng.compute(). Absolutely crazy! It comes from the very slow
    # get_program() call, which takes >1s to execute.

    # So qcng thinks this program is installed and has a harness
    qcng_spy = mocker.patch("qcengine.get_program")

    qcng_adapter_cls = registry["qcengine"]
    compute_spy = mocker.spy(qcng_adapter_cls, "compute")
    # Mock the "program_version" method and set its return value
    mocker.patch.object(
        qcng_adapter_cls, "program_version", return_value="fake-version"
    )

    energy_inp = prog_inp("energy")
    compute("mrchem", energy_inp)  # Program not in qcop, but in qcng

    assert qcng_spy.call_count == 1
    assert compute_spy.call_count == 1


def test_qcng_compute_not_called_if_adapter_in_qcop(mocker, prog_inp, test_adapter):
    qcng_spy = mocker.patch("qcengine.compute")

    test_adapter = registry["test"]
    compute_spy = mocker.spy(test_adapter, "compute")

    energy_inp = prog_inp("energy")
    compute("test", energy_inp)

    assert qcng_spy.call_count == 0  # qcng.compute() not called
    assert compute_spy.call_count == 1  # adaptor.compute() called


def test_qcng_exception_wrapping_raise_exc_true(mocker, prog_inp):
    # So system check passes for harness and program installation
    mocker.patch("qcop.utils.check_qcng_support")
    # qcng_spy = mocker.patch("qcengine.compute")
    # qcng_spy.side_effect = QCEngineException("QCEngine Failed!")

    energy_inp = prog_inp("energy")
    # Program not in qcop, but in qcng
    with pytest.raises(QCEngineError):
        compute("mrchem", energy_inp, raise_exc=True)


def test_qcng_exception_wrapping_raise_exc_false(mocker, prog_inp):
    # So system check passes for harness and program installation
    mocker.patch("qcop.utils.check_qcng_support")
    qcng_adapter = registry["qcengine"]
    mocker.spy(qcng_adapter, "compute")
    # Mock the "program_version" method and set its return value
    mocker.patch.object(qcng_adapter, "program_version", return_value="fake-version")

    energy_inp = prog_inp("energy")
    # Program not in qcop, but in qcng
    output = compute("mrchem", energy_inp, raise_exc=False)
    assert output.success is False
    assert isinstance(output.traceback, str)
    assert output.input_data == energy_inp
