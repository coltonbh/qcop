"""Many of these tests are really testing the BaseAdapter.compute() method because I 
refactored the compute() method to be in the BaseAdapter class. This works for now.
"""

from pathlib import Path
from typing import Callable

import pytest
from qcio import CalcSpec, Files, FileSpec, Results

from qcop.adapters import registry
from qcop.exceptions import AdapterInputError, AdapterNotFoundError, QCOPBaseError
from qcop.main import compute, compute_args


def test_file_adapter_works_inside_top_level_compute_function():
    # Create FileSpec
    file_inp = FileSpec(cmdline_args=["hello_world.py"])
    file_inp.files["hello_world.py"] = "print('hello world')"
    result = compute("python", file_inp)
    isinstance(result, Results)
    assert result.stdout == "hello world\n"


def test_compute_raises_adapter_not_found_error(calcspec):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    energy_inp = calcspec("energy")
    with pytest.raises(AdapterNotFoundError):
        # Will check qcop and qcng
        compute("not-a-real-program", energy_inp)


def test_compute_raises_adapter_not_found_error_no_qcng_fallback(calcspec):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    energy_inp = calcspec("energy")
    with pytest.raises(AdapterNotFoundError):
        compute("not-a-real-program", energy_inp, qcng_fallback=False)


def test_print_stdout(test_adapter, calcspec, mocker):
    energy_inp = calcspec("energy")

    spy = mocker.spy(type(test_adapter), "compute_results")

    compute("test", energy_inp)
    assert spy.call_args.args[2] is None  # update_func
    compute("test", energy_inp, print_stdout=True)
    assert isinstance(spy.call_args.args[2], Callable)  # update_func passed
    assert isinstance(spy.call_args.args[3], float)  # update_interval passed


def test_update_func_preferred_over_print_stdout(test_adapter, calcspec, mocker):
    energy_inp = calcspec("energy")

    spy = mocker.spy(type(test_adapter), "compute_results")

    def update_func(stdout, stderr):
        pass

    compute("test", energy_inp, update_func=update_func, print_stdout=True)
    assert spy.call_args.args[2] == update_func  # update_func passed
    assert spy.call_args.args[3] is None


def test_compute_uses_files_if_adaptor_uses_files_set(calcspec):
    """Test that compute writes files if the adaptor has uses_files set to True."""

    # Set adapter.uses_files is True by default
    energy_inp = calcspec("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    energy_inp.files[filename] = contents

    result = compute("test", energy_inp, rm_scratch_dir=False)
    with open(Path(result.provenance.scratch_dir) / filename) as f:
        assert f.read() == contents


def test_compute_does_not_uses_files_if_adaptor_uses_files_set(calcspec):
    """Test that compute writes files if the adaptor has uses_files set to True."""

    # Set adapter.uses_files to False
    adapter = registry["test"]
    adapter.uses_files = False

    energy_inp = calcspec("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    energy_inp.files[filename] = contents
    with pytest.raises(AdapterInputError):
        compute("test", energy_inp, rm_scratch_dir=False)


def test_compute_raises_exception_if_program_fails_raise_exec_true(calcspec):
    """Test that compute raises an exception if the program fails."""
    opt_input = calcspec("optimization")

    with pytest.raises(AdapterInputError):
        compute("test", opt_input, raise_exc=True)


def test_compute_does_not_raise_exception_if_raise_exec_false(calcspec, mocker):
    """Test that compute does not raise an exception if the program fails."""
    grad_input = calcspec("energy")
    adapter = registry["test"]
    mocker.patch.object(
        adapter,
        "compute_results",
        side_effect=QCOPBaseError("Something failed!"),
    )
    po = compute("test", grad_input, raise_exc=False)
    assert po.success is False


def test_qcengine_import_error(mocker, calcspec):
    """Test that an ImportError is raised when qcengine is not installed."""
    # Mock sys.modules to simulate qcengine not being installed
    mocker.patch.dict("sys.modules", {"qcengine": None})

    with pytest.raises(ModuleNotFoundError):
        # The code that attempts to import qcengine goes here
        energy_inp = calcspec("energy")
        compute("no-adaptor-for-program", energy_inp, qcng_fallback=True)


def test_compute_args(hydrogen, mocker):
    """Test that compute_args correctly constructs input object and calls compute."""
    # Spy on top level compute function
    compute_spy = mocker.patch("qcop.main.compute")
    values_dict = {
        "structure": hydrogen,
        "calctype": "energy",
        "model": {"method": "HF", "basis": "sto-3g"},
        "keywords": {"fake": "things"},
        "files": {"fake.py": "print('hello world')"},
        "extras": {"fake": "things"},
    }
    compute_args("test", extra_thing=123, **values_dict)
    compute_spy.assert_called_once_with(
        "test", CalcSpec(**values_dict), extra_thing=123
    )


def test_compute_args_file_object_passed(hydrogen, mocker):
    """Test that compute_args correctly constructs input object and calls compute."""
    # Spy on top level compute function
    compute_spy = mocker.patch("qcop.main.compute")
    values_dict = {
        "structure": hydrogen,
        "calctype": "energy",
        "model": {"method": "HF", "basis": "sto-3g"},
        "keywords": {"fake": "things"},
        "files": Files(files={"fake.py": "print('hello world')"}),
        "extras": {"fake": "things"},
    }
    compute_args("test", extra_thing=123, **values_dict)
    # Convert back for CalcSpec instantiation
    values_dict["files"] = {"fake.py": "print('hello world')"}
    compute_spy.assert_called_once_with(
        "test", CalcSpec(**values_dict), extra_thing=123
    )
