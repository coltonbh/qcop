from pathlib import Path
from typing import Any, Optional

import toml
import typer
from pydantic import BaseModel
from qcio import ProgramInput

app = typer.Typer()


# NOTE: This is not working. Just an initial idea from ChatGPT.
def create_empty_dict_from_model(model_class: Any) -> dict:
    empty_model = {}
    for field_name, field in model_class.model_fields.items():
        field_type = field.annotation.__class__
        if issubclass(field_type, BaseModel):
            # If it's a nested model, recursively process it
            empty_model[field_name] = create_empty_dict_from_model(field_type)
        else:
            # Set to None, an empty string, or a suitable default
            empty_model[field_name] = ""
    return empty_model


@app.command()
def new(filename: Optional[Path] = "input.toml", dual_program: bool = False):
    """Create a new program input file."""
    count = 1
    while filename.exists():
        typer.echo(f"File already exists: {filename}")
        filename = f"{filename.stem}_{count}{filename.suffix}"
        count += 1

    typer.echo(f"Creating a new input file: {filename}")
    model_dict = create_empty_dict_from_model(ProgramInput)
    # Convert to TOML and write to file
    import pdb

    pdb.set_trace()
    with open("empty_model.toml", "w") as file:
        toml.dump(model_dict, file)


@app.command()
def two():
    pass


if __name__ == "__main__":
    app()
