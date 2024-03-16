"""Test utils functions."""

import builtins
from pathlib import Path

import pytest

from qcop.adapters.utils import capture_logs, execute_subprocess, tmpdir
from qcop.exceptions import ExternalSubprocessError, ProgramNotFoundError
from qcop.utils import available_programs, prog_available


def test_tmpdir_makes_dir_by_default():
    """Test that tmpdir makes a directory by default."""
    with tmpdir() as working_dir:
        assert working_dir.is_dir()


def test_tmpdir_makes_dir_in_specified_dir(tmp_path):
    """Test that tmpdir makes a directory in the specified directory."""
    with tmpdir(tmp_path) as working_dir:
        working_dir == tmp_path


def test_tmpdir_removes_dir_by_default():
    """Test that tmpdir removes the directory by default."""
    with tmpdir() as working_dir:
        assert working_dir.is_dir()
    assert not working_dir.is_dir()


def test_tmpdir_does_not_remove_dir_if_specified():
    """Test that tmpdir does not remove the directory if specified."""
    with tmpdir(rmdir=False) as working_dir:
        assert working_dir.is_dir()
    assert working_dir.is_dir()


def test_tmpdir_changes_working_dir_to_tmpdir():
    """Test that tmpdir changes the working directory to the tmpdir."""
    cwd = Path.cwd()
    with tmpdir() as working_dir:
        # Have changed working directory
        assert working_dir != cwd and working_dir == Path.cwd()

    assert cwd == Path.cwd()


def test_execute_subprocess_using_python():
    """Test that execute_subprocess can run a python script."""
    output = execute_subprocess("python", ["-c" "print('Hello World!')"])
    assert output == "Hello World!\n"


def test_execute_subprocess_using_python_with_no_stdout():
    """Test that execute_subprocess can run a python script with no stdout."""
    output = execute_subprocess("python", ["-c" "import sys"])
    assert output == ""


def test_execute_subprocess_with_update_func(mocker):
    """Test that execute_subprocess can run a python script with an update function."""
    # Create a mock using mocker
    mock_update_func = mocker.MagicMock()

    # Call 'execute_subprocess', passing 'mock_update_func' as the 'update_func'
    execute_subprocess(
        "python",
        ["-u", "-c", "import time; time.sleep(0.01); print('Hello World!')"],
        update_func=mock_update_func,
        update_interval=0.005,  # Update interval needs to be shorter than sleep time
    )

    # Check that 'mock_update_func' was called once with the expected output.
    mock_update_func.assert_called_once_with("Hello World!\n", "Hello World!\n")


def test_execute_subprocess_interval_with_update_func(mocker):
    """Test that execute_subprocess can run a python script with an update function."""
    # Create a mock using mocker
    mock_update_func = mocker.MagicMock()
    execute_subprocess(
        "python",
        [
            "-u",
            "-c",
            "import time;print('Hello World!');time.sleep(0.01); print('After sleep')",
        ],
        update_func=mock_update_func,
        update_interval=0.0001,
    )

    # Check that 'mock_update_func' was called with the expected output.
    calls = mock_update_func.call_args_list
    assert calls[0] == mocker.call("Hello World!\n", "Hello World!\n")
    assert calls[1] == mocker.call("Hello World!\nAfter sleep\n", "After sleep\n")


def test_execute_subprocess_raises_exception_if_program_not_found():
    """Test that execute_subprocess raises an exception if the program is not found."""
    with pytest.raises(ProgramNotFoundError):
        execute_subprocess("does_not_exist", ["-c", "print('Hello World!')"])


def test_execute_subprocess_raises_external_program_execution_error_if_program_fails():
    """Test that execute_subprocess raises an exception if the program fails."""
    cmd = ["python", "-c", "raise Exception('Hello World!')"]
    with pytest.raises(ExternalSubprocessError):
        execute_subprocess(cmd[0], cmd[1:])

    try:
        execute_subprocess(cmd[0], cmd[1:])
    except ExternalSubprocessError as e:
        assert e.returncode == 1
        assert e.cmd == " ".join(cmd)
        assert isinstance(e.stdout, str)


def test_prog_available():
    """Test that prog_available returns True if the program is available."""
    assert prog_available("python")
    assert not prog_available("does_not_exist")


def test_prog_available_pyenv(mocker):
    """Test that prog_available returns True if the program is available."""
    mocker.patch("shutil.which", lambda x: "/home/some-guy/.pyenv/shims/myprog")
    mocker.spy(builtins, "print")
    assert prog_available("myprog") is False


def test_available_programs():
    """Test that available_programs returns an array of programs on the system."""
    assert isinstance(available_programs(), list)


def test_capture_logs():
    """Test that capture_logs captures logs."""
    import logging

    with capture_logs("") as (logger, log_capture_string):
        logging.info("Hello World!")
    assert "Hello World!" in log_capture_string.getvalue()
