import pytest
from qcio import FileInput

from qcop.adapters import FileAdapter
from qcop.exceptions import ProgramNotFoundError
from qcop.utils import tmpdir


def test_file_adapter_compute(tmp_path):
    # Create FileInput
    file_inp = FileInput(**{"program_args": {"cmdline_args": ["hello_world.py"]}})
    file_inp.program_args.files["hello_world.py"] = "print('hello world')"
    with tmpdir() as path:
        file_inp.program_args.write_files(path)
        _, stdout = FileAdapter("python").compute(file_inp)
    assert stdout == "hello world\n"


def test_file_adapter_raises_exception_if_program_fails():
    # Create FileInput
    file_inp = FileInput()
    with pytest.raises(ProgramNotFoundError):
        FileAdapter("does_not_exist").compute(file_inp)
