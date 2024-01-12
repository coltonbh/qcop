"""Many of these tests are really testing the BaseAdapter.compute() method because I 
refactored the compute() method to be in the BaseAdapter class. This works for now.
"""
from pathlib import Path
from typing import Callable

import pytest
from qcio import FileInput, FileOutput, Files, ProgramFailure, ProgramInput

from qcop.adapters import registry
from qcop.exceptions import AdapterInputError, AdapterNotFoundError, QCOPBaseError
from qcop.main import compute, compute_args


def test_file_adapter_works_inside_top_level_compute_function():
    # Create FileInput
    file_inp = FileInput(cmdline_args=["hello_world.py"])
    file_inp.files["hello_world.py"] = "print('hello world')"
    result = compute("python", file_inp)
    isinstance(result, FileOutput)
    assert result.stdout == "hello world\n"


def test_compute_raises_adapter_not_found_error(prog_inp):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    energy_inp = prog_inp("energy")
    with pytest.raises(AdapterNotFoundError):
        # Will check qcop and qcng
        compute("not-a-real-program", energy_inp)


def test_compute_raises_adapter_not_found_error_no_qcng_fallback(prog_inp):
    """Test that compute raises an AdapterNotFoundError if the adapter is not
    found."""
    energy_inp = prog_inp("energy")
    with pytest.raises(AdapterNotFoundError):
        compute("not-a-real-program", energy_inp, qcng_fallback=False)


def test_print_stdout(test_adapter, prog_inp, mocker):
    energy_inp = prog_inp("energy")

    spy = mocker.spy(type(test_adapter), "compute_results")

    compute("test", energy_inp)
    assert spy.call_args.args[2] is None  # update_func
    compute("test", energy_inp, print_stdout=True)
    assert isinstance(spy.call_args.args[2], Callable)  # update_func passed
    assert isinstance(spy.call_args.args[3], float)  # update_interval passed


def test_update_func_preferred_over_print_stdout(test_adapter, prog_inp, mocker):
    energy_inp = prog_inp("energy")

    spy = mocker.spy(type(test_adapter), "compute_results")

    def update_func(stdout, stderr):
        pass

    compute("test", energy_inp, update_func=update_func, print_stdout=True)
    assert spy.call_args.args[2] == update_func  # update_func passed
    assert spy.call_args.args[3] is None


def test_compute_write_files_if_adaptor_write_files_set(prog_inp):
    """Test that compute writes files if the adaptor has write_files set to True."""

    # Set adapter.write_files is True by default
    energy_inp = prog_inp("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    energy_inp.files[filename] = contents

    result = compute("test", energy_inp, rm_scratch_dir=False)
    with open(Path(result.provenance.scratch_dir) / filename) as f:
        assert f.read() == contents


def test_compute_does_not_write_files_if_adaptor_write_files_set(prog_inp):
    """Test that compute writes files if the adaptor has write_files set to True."""

    # Set adapter.write_files to False
    adapter = registry["test"]
    adapter.write_files = False

    energy_inp = prog_inp("energy")
    filename, contents = "hello_world.py", "print('hello world')"
    energy_inp.files[filename] = contents

    result = compute("test", energy_inp, rm_scratch_dir=False)
    assert not (Path(result.provenance.scratch_dir) / filename).exists()


def test_compute_raises_exception_if_program_fails_raise_exec_true(prog_inp):
    """Test that compute raises an exception if the program fails."""
    opt_input = prog_inp("optimization")

    with pytest.raises(AdapterInputError):
        compute("test", opt_input, raise_exc=True)


def test_compute_does_not_raise_exception_if_raise_exec_false(prog_inp, mocker):
    """Test that compute does not raise an exception if the program fails."""
    grad_input = prog_inp("energy")
    adapter = registry["test"]
    mocker.patch.object(
        adapter,
        "compute_results",
        side_effect=QCOPBaseError("Something failed!"),
    )
    assert isinstance(compute("test", grad_input), ProgramFailure)


def test_qcengine_import_error(mocker, prog_inp):
    """Test that an ImportError is raised when qcengine is not installed."""
    # Mock sys.modules to simulate qcengine not being installed
    mocker.patch.dict("sys.modules", {"qcengine": None})

    with pytest.raises(ModuleNotFoundError):
        # The code that attempts to import qcengine goes here
        energy_inp = prog_inp("energy")
        compute("no-adaptor-for-program", energy_inp, qcng_fallback=True)


def test_compute_args(hydrogen, mocker):
    """Test that compute_args correctly constructs input object and calls compute."""
    # Spy on top level compute function
    compute_spy = mocker.patch("qcop.main.compute")
    values_dict = {
        "molecule": hydrogen,
        "calctype": "energy",
        "model": {"method": "HF", "basis": "sto-3g"},
        "keywords": {"fake": "things"},
        "files": {"fake.py": "print('hello world')"},
        "extras": {"fake": "things"},
    }
    compute_args("test", extra_thing=123, **values_dict)
    compute_spy.assert_called_once_with(
        "test", ProgramInput(**values_dict), extra_thing=123
    )


def test_compute_args_file_object_passed(hydrogen, mocker):
    """Test that compute_args correctly constructs input object and calls compute."""
    # Spy on top level compute function
    compute_spy = mocker.patch("qcop.main.compute")
    values_dict = {
        "molecule": hydrogen,
        "calctype": "energy",
        "model": {"method": "HF", "basis": "sto-3g"},
        "keywords": {"fake": "things"},
        "files": Files(files={"fake.py": "print('hello world')"}),
        "extras": {"fake": "things"},
    }
    compute_args("test", extra_thing=123, **values_dict)
    # Convert back for ProgramInput instantiation
    values_dict["files"] = {"fake.py": "print('hello world')"}
    compute_spy.assert_called_once_with(
        "test", ProgramInput(**values_dict), extra_thing=123
    )
