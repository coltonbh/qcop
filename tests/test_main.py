from pathlib import Path
from typing import Callable

import pytest
from qcio import FileInput, FileSuccessfulOutput, SinglePointFailedOutput

from qcop.adapters import registry
from qcop.exceptions import AdapterNotFoundError, UnsupportedCalcTypeError
from qcop.main import compute


def test_file_adapter_works_inside_top_level_compute_function():
    # Create FileInput
    file_inp = FileInput(**{"program_args": {"cmdline_args": ["hello_world.py"]}})
    file_inp.program_args.files["hello_world.py"] = "print('hello world')"
    output = compute(file_inp, "python")
    isinstance(output, FileSuccessfulOutput)
    assert output.stdout == "hello world\n"


def test_compute_raises_adapter_not_found_error(sp_input):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    sp_energy_input = sp_input("energy")
    with pytest.raises(AdapterNotFoundError):
        # Will check qcop and qcng
        compute(sp_energy_input, "not_a_real_program")


def test_compute_raises_adapter_not_found_error_no_qcng_fallback(sp_input):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    sp_energy_input = sp_input("energy")
    with pytest.raises(AdapterNotFoundError):
        compute(sp_energy_input, "not_a_real_program", qcng_fallback=False)


def test_print_stdout(sp_test_adapter, sp_input, mocker):
    sp_energy_input = sp_input("energy")

    spy = mocker.spy(type(sp_test_adapter), "_compute")

    compute(sp_energy_input, "test")
    assert spy.call_args.args[2] is None  # update_func
    compute(sp_energy_input, "test", print_stdout=True)
    assert isinstance(spy.call_args.args[2], Callable)  # update_func passed
    assert isinstance(spy.call_args.args[3], float)  # update_interval passed


def test_update_func_preferred_over_print_stdout(sp_test_adapter, sp_input, mocker):
    sp_energy_input = sp_input("energy")

    spy = mocker.spy(type(sp_test_adapter), "_compute")

    def update_func(stdout, stderr):
        pass

    compute(sp_energy_input, "test", update_func=update_func, print_stdout=True)
    assert spy.call_args.args[2] == update_func  # update_func passed
    assert spy.call_args.args[3] is None


def test_compute_write_files_if_adaptor_write_files_set(sp_test_adapter, sp_input):
    """Test that compute writes files if the adaptor has write_files set to True."""

    # Set adapter.write_files is True by default
    sp_energy_input = sp_input("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    sp_energy_input.program_args.files[filename] = contents

    output = compute(sp_energy_input, "test", rm_working_dir=False)
    with open(Path(output.provenance.working_dir) / filename) as f:
        assert f.read() == contents


def test_compute_does_not_write_files_if_adaptor_write_files_set(
    sp_test_adapter, sp_input
):
    """Test that compute writes files if the adaptor has write_files set to True."""

    # Set adapter.write_files to False
    adapter = registry["test"]
    adapter.write_files = False

    sp_energy_input = sp_input("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    sp_energy_input.program_args.files[filename] = contents

    output = compute(sp_energy_input, "test", rm_working_dir=False)
    assert not (Path(output.provenance.working_dir) / filename).exists()


def test_compute_raises_exception_if_program_fails_raise_exec_true(
    sp_test_adapter, sp_input
):
    """Test that compute raises an exception if the program fails."""
    sp_grad_input = sp_input("gradient")

    with pytest.raises(UnsupportedCalcTypeError):
        compute(sp_grad_input, "test", raise_exc=True)


def test_compute_does_not_raises_exception_if_program_fails_raise_exec_false(
    sp_test_adapter, sp_input
):
    """Test that compute does not raise an exception if the program fails."""
    sp_grad_input = sp_input("gradient")

    assert isinstance(compute(sp_grad_input, "test"), SinglePointFailedOutput)


def test_qcengine_import_error(mocker, sp_input):
    """Test that an ImportError is raised when qcengine is not installed."""
    # Mock sys.modules to simulate qcengine not being installed
    mocker.patch.dict("sys.modules", {"qcengine": None})

    with pytest.raises(ModuleNotFoundError):
        # The code that attempts to import qcengine goes here
        sp_energy_input = sp_input("energy")
        compute(sp_energy_input, "no-adaptor", qcng_fallback=True)
