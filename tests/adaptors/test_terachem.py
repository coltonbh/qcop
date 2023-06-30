from pathlib import Path

import pytest

from qcop.adapters import TeraChemAdapter
from qcop.exceptions import AdapterInputError
from qcop.utils import tmpdir


def test_write_input_files(sp_input):
    """Test write_input_files method."""
    sp_input = sp_input("energy")
    with tmpdir():
        tc_adapter = TeraChemAdapter()
        input_filename = tc_adapter.prepare_inputs(sp_input)
        assert Path("geom.xyz").is_file()
        assert Path(input_filename).is_file()

        with open("tc.in", "r") as f:
            text = f.read()
    # Testing that we capture:
    # 1. Driver
    # 2. Molecule
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)
    assert text == (
        f"{'run':<{tc_adapter.padding}} {sp_input.program_args.calc_type}\n"
        f"{'coordinates':<{tc_adapter.padding}} geom.xyz\n"
        f"{'charge':<{tc_adapter.padding}} {sp_input.molecule.charge}\n"
        f"{'spinmult':<{tc_adapter.padding}} {sp_input.molecule.multiplicity}\n"
        f"{'method':<{tc_adapter.padding}} {sp_input.program_args.model.method}\n"
        f"{'basis':<{tc_adapter.padding}} {sp_input.program_args.model.basis}\n"
        f"{'maxiter':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['maxiter']}\n"
        f"{'purify':<{tc_adapter.padding}} {sp_input.program_args.keywords['purify']}\n"
        f"{'some-bool':<{tc_adapter.padding}} "
        f"{str(sp_input.program_args.keywords['some-bool']).lower()}\n"
        f"{'displacement':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['displacement']}\n"
        f"{'thermo_temp':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['thermo_temp']}\n"
    )


def test_write_input_files_renames_hessian_to_frequencies(sp_input):
    """Test write_input_files method for hessian."""
    # Modify input to be a hessian calculation
    sp_input = sp_input("hessian")

    with tmpdir():
        tc_adapter = TeraChemAdapter()
        input_filename = tc_adapter.prepare_inputs(sp_input)
        assert Path("geom.xyz").is_file()
        assert Path(input_filename).is_file()

        with open("tc.in", "r") as f:
            text = f.read()
    # Testing that we capture:
    # 1. CalcType
    # 2. Molecule
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)
    assert text == (
        f"{'run':<{tc_adapter.padding}} frequencies\n"
        f"{'coordinates':<{tc_adapter.padding}} geom.xyz\n"
        f"{'charge':<{tc_adapter.padding}} {sp_input.molecule.charge}\n"
        f"{'spinmult':<{tc_adapter.padding}} {sp_input.molecule.multiplicity}\n"
        f"{'method':<{tc_adapter.padding}} {sp_input.program_args.model.method}\n"
        f"{'basis':<{tc_adapter.padding}} {sp_input.program_args.model.basis}\n"
        f"{'maxiter':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['maxiter']}\n"
        f"{'purify':<{tc_adapter.padding}} {sp_input.program_args.keywords['purify']}\n"
        f"{'some-bool':<{tc_adapter.padding}} "
        f"{str(sp_input.program_args.keywords['some-bool']).lower()}\n"
        f"{'displacement':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['displacement']}\n"
        f"{'thermo_temp':<{tc_adapter.padding}} "
        f"{sp_input.program_args.keywords['thermo_temp']}\n"
    )


def test_get_version_no_stdout(monkeypatch):
    """Test get_version method."""
    adapter = TeraChemAdapter()
    # Monkey patch execute_subprocess to return a version string
    monkeypatch.setattr(
        "qcop.adapters.terachem.execute_subprocess",
        lambda *args: (
            "TeraChem version 1.9-2021.12-dev "
            "[cc068f92bd92d3e9009c54834f0d63e9cfec3273]"
        ),
    )
    assert (
        adapter.program_version()
        == "1.9-2021.12-dev [cc068f92bd92d3e9009c54834f0d63e9cfec3273]"
    )


def test_get_version_stdout(mocker):
    """Test get_version method."""
    adapter = TeraChemAdapter()
    # Create a mock for parse_version_string
    mock_parse_version_string = mocker.patch(
        "qcop.adapters.terachem.parse_version_string"
    )

    adapter.program_version("some stdout data")

    # Assert that parse_version_string was called once
    mock_parse_version_string.assert_called_once()


def test_prepare_inputs_raises_error_qcio_args_passes_as_keywords(sp_input):
    """These keywords should not be in the .keywords dict. They belong on structured
    qcio objects instead."""
    qcio_keywords_from_terachem = ["charge", "spinmult", "method", "basis", "run"]
    sp_input = sp_input("energy")
    adapter = TeraChemAdapter()
    for keyword in qcio_keywords_from_terachem:
        sp_input.program_args.keywords[keyword] = "some value"
        with pytest.raises(AdapterInputError):
            adapter.prepare_inputs(sp_input)
