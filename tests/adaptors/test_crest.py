import pytest
from qcio import ProgramInput

from qcop.adapters import CRESTAdapter
from qcop.exceptions import AdapterInputError


def test_validate_input(prog_inp):
    adapter = CRESTAdapter()
    inp_obj = prog_inp("conformer_search")
    adapter.validate_input(inp_obj)

    with pytest.raises(AdapterInputError):
        inp_obj.keywords["charge"] = -1
        adapter.validate_input(inp_obj)

    with pytest.raises(AdapterInputError):
        inp_obj.keywords["uhf"] = 0
        adapter.validate_input(inp_obj)

    with pytest.raises(AdapterInputError):
        inp_obj.keywords["runtype"] = "imtd-gc"
        adapter.validate_input(inp_obj)


def test_toml_dict(water):
    """Test converting a ProgramInput object to a TOML dictionary for CREST."""
    adapter = CRESTAdapter()

    weird_water = water.model_copy(update={"charge": -1, "multiplicity": 2})
    inp_obj = ProgramInput(
        structure=weird_water,
        calctype="conformer_search",
        model={"method": "gfn2"},
        keywords={"calculation": {"level": [{"alpb": "acetonitrile"}]}},
    )
    toml_dict = adapter._toml_dict(inp_obj)
    assert toml_dict["input"] == "structure.xyz"
    assert toml_dict["runtype"] == "imtd-gc"
    assert toml_dict.get("threads") is not None  # added implicitly if not set
    assert toml_dict["calculation"]["level"][0]["method"] == "gfn2"
    assert toml_dict["calculation"]["level"][0]["charge"] == -1
    assert toml_dict["calculation"]["level"][0]["uhf"] == 1
    assert toml_dict["calculation"]["level"][0]["alpb"] == "acetonitrile"

    # Respects explicitly set threads
    inp_obj = ProgramInput(
        structure=weird_water,
        calctype="conformer_search",
        model={"method": "gfn2"},
        keywords={"calculation": {"level": [{"alpb": "acetonitrile"}]}, "threads": 2},
    )

    toml_dict = adapter._toml_dict(inp_obj)
    assert toml_dict["threads"] == 2
