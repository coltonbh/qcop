from pathlib import Path

import pytest
from qccodec.encoders.terachem import XYZ_FILENAME

from qcop.adapters import TeraChemAdapter
from qcop.adapters.utils import tmpdir
from qcop.exceptions import AdapterError, AdapterInputError


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
    mock_parse_version = mocker.patch(
        "qcop.adapters.terachem.parse_version"
    )

    adapter.program_version("some stdout data")

    # Assert that parse_version_string was called once
    mock_parse_version.assert_called_once()


def test_propagate_wfn(prog_inp, prog_output):
    """Test propagate_wavefunction method."""
    prog_input = prog_inp("energy")
    adapter = TeraChemAdapter()

    # Raises error if output does not contain wavefunction data
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(prog_output, prog_input)

    # TeraChem Output conventions
    scr_postfix = XYZ_FILENAME.split(".")[0]
    scr_dir = f"scr.{scr_postfix}"

    # Add restricted wavefunction data to output
    prog_output.results.files[f"{scr_dir}/c0"] = "some file"
    adapter.propagate_wfn(prog_output, prog_input)
    assert prog_input.files["c0"] == "some file"
    assert prog_input.keywords["guess"] == "c0"
    prog_output.results.files.pop(f"{scr_dir}/c0")  # Remove c0 from output

    # Add unrestricted wavefunction data to output
    prog_input = prog_inp("energy")
    prog_output.results.files[f"{scr_dir}/ca0"] = "some alpha file"
    prog_output.results.files[f"{scr_dir}/cb0"] = "some beta file"
    adapter.propagate_wfn(prog_output, prog_input)
    assert prog_input.files["ca0"] == "some alpha file"
    assert prog_input.files["cb0"] == "some beta file"
    assert prog_input.keywords["guess"] == "ca0 cb0"

    # Assert error raised if only alpha or beta wavefunction data is present
    prog_output.results.files.pop(f"{scr_dir}/cb0")
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(prog_output, prog_input)

    prog_output.results.files.pop(f"{scr_dir}/ca0")
    prog_output.results.files[f"{scr_dir}/cb0"] = "some beta file"
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(prog_output, prog_input)


def test_collect_wfn(prog_output):
    # Raises AdapterError if not wavefunction data in output
    adapter = TeraChemAdapter()
    with pytest.raises(AdapterError):
        adapter.collect_wfn()

    # Check collection of c0
    scr_dir_str = f"scr.{XYZ_FILENAME.split('.')[0]}"
    with tmpdir():
        scr_dir = Path(scr_dir_str)
        scr_dir.mkdir()
        (scr_dir / "c0").write_bytes(b"some data")
        wfns = adapter.collect_wfn()
        assert wfns[f"{scr_dir_str}/c0"] == b"some data"

    with tmpdir():
        scr_dir = Path(scr_dir_str)
        scr_dir.mkdir()
        (scr_dir / "ca0").write_bytes(b"some alpha data")
        (scr_dir / "cb0").write_bytes(b"some beta data")
        wfns = adapter.collect_wfn()
        assert wfns[f"{scr_dir_str}/ca0"] == b"some alpha data"
        assert wfns[f"{scr_dir_str}/cb0"] == b"some beta data"
