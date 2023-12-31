from pathlib import Path

import pytest
from qcparse.encoders.terachem import XYZ_FILENAME

from qcop.adapters import TeraChemAdapter
from qcop.adapters.utils import tmpdir
from qcop.exceptions import AdapterInputError


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


def test_propagate_wfn(prog_inp, sp_output):
    """Test propagate_wavefunction method."""
    new_inp = prog_inp("energy")
    adapter = TeraChemAdapter()

    # Raises error if output does not contain wavefunction data
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(sp_output, new_inp)

    # TeraChem Output conventions
    scr_postfix = XYZ_FILENAME.split(".")[0]
    scr_dir = f"scr.{scr_postfix}"

    # Add restricted wavefunction data to output
    sp_output.files[f"{scr_dir}/c0"] = "some file"
    adapter.propagate_wfn(sp_output, new_inp)
    assert new_inp.files["c0"] == "some file"
    assert new_inp.keywords["guess"] == "c0"
    sp_output.files.pop(f"{scr_dir}/c0")  # Remove c0 from output

    # Add unrestricted wavefunction data to output
    new_inp = prog_inp("energy")
    sp_output.files[f"{scr_dir}/ca0"] = "some alpha file"
    sp_output.files[f"{scr_dir}/cb0"] = "some beta file"
    adapter.propagate_wfn(sp_output, new_inp)
    assert new_inp.files["ca0"] == "some alpha file"
    assert new_inp.files["cb0"] == "some beta file"
    assert new_inp.keywords["guess"] == "ca0 cb0"

    # Assert error raised if only alpha or beta wavefunction data is present
    sp_output.files.pop(f"{scr_dir}/cb0")
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(sp_output, new_inp)

    sp_output.files.pop(f"{scr_dir}/ca0")
    sp_output.files[f"{scr_dir}/cb0"] = "some beta file"
    with pytest.raises(AdapterInputError):
        adapter.propagate_wfn(sp_output, new_inp)


def test_collect_wfn(sp_output):
    # Raises AdapterInputError if not wavefunction data in output
    adapter = TeraChemAdapter()
    with pytest.raises(AdapterInputError):
        adapter.collect_wfn(sp_output)

    # Check collection of c0
    scr_dir_str = f"scr.{XYZ_FILENAME.split('.')[0]}"
    with tmpdir():
        scr_dir = Path(scr_dir_str)
        scr_dir.mkdir()
        (scr_dir / "c0").write_bytes(b"some data")
        adapter.collect_wfn(sp_output)
        assert sp_output.files[f"{scr_dir_str}/c0"] == b"some data"
        sp_output.files.pop(f"{scr_dir_str}/c0")

    with tmpdir():
        scr_dir = Path(scr_dir_str)
        scr_dir.mkdir()
        (scr_dir / "ca0").write_bytes(b"some alpha data")
        (scr_dir / "cb0").write_bytes(b"some beta data")
        adapter.collect_wfn(sp_output)
        assert sp_output.files[f"{scr_dir_str}/ca0"] == b"some alpha data"
        assert sp_output.files[f"{scr_dir_str}/cb0"] == b"some beta data"
