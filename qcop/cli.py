import json
import tempfile
from pathlib import Path
from typing import Annotated, Any, Optional

import toml
import typer
import yaml
from pydantic import ValidationError
from qcio import DualProgramInput, ProgramInput, Structure, utils
from rich import print as rprint

from qcop import compute as qcop_compute

app = typer.Typer()


def _serialize_data(data: Any, filename: Path):
    kwargs = {}
    if filename.suffix == ".toml":
        dump = toml.dump
    elif filename.suffix == ".yaml" or filename.suffix == ".yml":
        dump = yaml.dump
    elif filename.suffix == ".json":
        dump = json.dump
        kwargs = {"indent": 2}
    else:
        raise ValueError(f"Unsupported file extension: {filename.suffix}")
    with open(filename, "w") as f:
        dump(data, f, **kwargs)


def _deserialize_data(filename: Path) -> Any:
    if filename.suffix == ".toml":
        load = toml.load
    elif filename.suffix == ".yaml" or filename.suffix == ".yml":
        load = yaml.load
    elif filename.suffix == ".json":
        load = json.load
    else:
        raise ValueError(f"Unsupported file extension: {filename.suffix}")
    with open(filename, "r") as f:
        return load(f)


@app.command()
def new(
    filename: Path,
    dual_program: Annotated[
        bool, typer.Option("--dual-program", "-dp", help="Create a DualProgramInput")
    ] = False,
    calctype: Annotated[
        str, typer.Option("--calctype", "-c", help="calctype for the input file")
    ] = "energy",
    no_structure: Annotated[
        bool,
        typer.Option(
            "--no-structure", "-ns", help="Exclude the structure from the input file"
        ),
    ] = False,
):
    """Create a new program input file."""

    rprint(f"Creating a new input file: {filename}")
    if not dual_program:
        prog_inp = ProgramInput(
            calctype=calctype,
            structure=utils.water,
            model={"method": "b3lyp", "basis": "6-31g"},
            keywords={"key1": "value1"},
        )
    else:
        prog_inp = DualProgramInput(
            calctype=calctype,
            structure=utils.water,
            subprogram="subprogram_name",
            keywords={"key1": "value1"},
            subprogram_args={
                "model": {"method": "b3lyp", "basis": "6-31g"},
                "keywords": {"key1": "value1"},
            },
        )

    # Serialize data
    serialized_data = prog_inp.model_dump(exclude_unset=True, exclude_none=True)
    serialized_data["structure"].pop("connectivity")
    if no_structure:
        serialized_data.pop("structure")

    _serialize_data(serialized_data, filename)


@app.command()
def compute(
    input_filename: Path,
    output_filename: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output filename"),
    ],
    program: Annotated[
        str, typer.Option("--program", "-p", help="Program name for the input file")
    ],
    structure: Optional[Path] = None,
):
    """Compute the input file and save the results to the output_filename."""
    rprint(f"Computing {input_filename} and saving to {output_filename}")

    if structure is not None:
        rprint(f"Using the structure file: {structure}")
        struct = Structure.open(structure)
        prog_inp_dict = _deserialize_data(input_filename)
        prog_inp_dict["structure"] = struct.model_dump()
        input_filename = Path(
            tempfile.NamedTemporaryFile(delete=True, suffix=".toml").name
        )
        _serialize_data(prog_inp_dict, input_filename)

    try:
        prog_inp = ProgramInput.open(input_filename)
    except ValidationError:
        try:
            prog_inp = DualProgramInput.open(input_filename)
        except ValidationError:
            rprint(f"Invalid input file: {input_filename}")
            raise typer.Exit(1)

    prog_output = qcop_compute(program, prog_inp, print_stdout=True, raise_exc=False)

    if prog_output.success:
        rprint("[bold green]Computation successful![/bold green]")
    else:
        rprint(prog_output.traceback)
        rprint("[bold red]Computation failed![/bold red]")

    rprint(f"Saving the results to {output_filename}")
    _serialize_data(prog_output.model_dump(), output_filename)


if __name__ == "__main__":
    app()
