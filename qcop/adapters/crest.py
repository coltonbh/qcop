"""Adapter for CREST package. https://crest-lab.github.io/crest-docs/"""

import copy
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import tomli_w
from qcio import (
    AnnotatedStructure,
    CalcType,
    ConformerSearchResults,
    ProgramInput,
    SinglePointResults,
    Structure,
)
from qcparse.parsers.crest import parse_version_string

from qcop.exceptions import AdapterInputError

from .base import ProgramAdapter
from .utils import execute_subprocess


class CRESTAdapter(ProgramAdapter[ProgramInput, ConformerSearchResults]):
    """Adapter for CREST.

    Note:
        The `ProgramInput.keywords` attribute is used to create the input file for
        CREST. This means that the structure of the `keywords` attribute should match
        that of [CREST's input specification](https://crest-lab.github.io/crest-docs/page/documentation/inputfiles.html).
        Keywords such as method, charge, and uhf (which are stored on the `Model` and
        `Structure`; uhf is `multiplicity - 1`) will be added to the input file
        automatically.
    """

    supported_calctypes = [CalcType.conformer_search]
    program = "crest"

    def program_version(self, stdout: Optional[str] = None) -> str:
        """Get the program version.

        Args:
            stdout: The stdout from the program.

        Returns:
            The program version.
        """
        if not stdout:
            stdout = execute_subprocess(self.program, ["--version"])
        return parse_version_string(stdout)

    def validate_input(self, inp_obj: ProgramInput) -> None:
        """Validate the input for CREST."""
        super().validate_input(inp_obj)
        # These values come from other parts of the ProgramInput and should not be set
        # in the keywords.
        non_allowed_keywords = ["charge", "uhf", "runtype"]
        for keyword in non_allowed_keywords:
            if keyword in inp_obj.keywords:
                raise AdapterInputError(
                    self.program,
                    f"{keyword} should not be set in keywords. It is already set on "
                    "the Structure or ProgramInput elsewhere.",
                )

    def _toml_dict(self, inp_obj: ProgramInput) -> dict:
        """Converts a ProgramInput into the TOML dictionary required by CREST."""
        toml_dict = copy.deepcopy(inp_obj.keywords)

        # Top level keywords
        # Logical cores was 10% faster than physical cores, so not using psutil
        toml_dict.setdefault("threads", os.cpu_count())

        # Side effect of saving the structure to disk
        inp_obj.structure.save("structure.xyz")
        toml_dict["input"] = "structure.xyz"

        # TODO: May need to deal with non-covalent mode at some point
        toml_dict["runtype"] = "imtd-gc"

        # Calculation level keywords
        calculation = toml_dict.pop("calculation", {})
        calculation_level = calculation.pop("level", [])
        if len(calculation_level) == 0:
            calculation_level.append({})
        for level_dict in calculation_level:
            level_dict["method"] = inp_obj.model.method
            level_dict["charge"] = inp_obj.structure.charge
            level_dict["uhf"] = inp_obj.structure.multiplicity - 1

        calculation["level"] = calculation_level
        toml_dict["calculation"] = calculation
        return toml_dict

    def compute_results(
        self,
        inp_obj: ProgramInput,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        collect_rotamers: bool = False,
        **kwargs,
    ) -> Tuple[ConformerSearchResults, str]:
        """Execute CREST on the given input.

        Args:
            inp_obj: The qcio ProgramInput object for a computation.
            update_func: A function to call with the stdout at regular intervals.
            update_interval: The interval at which to call the update function.
            collect_rotamers: Collect rotamers if doing a conformer_search. Defaults to
                False since rotamers are usually not of interest and there will be many.

        Returns:
            A tuple of ConformerSearchResults and the stdout str.
        """
        toml_dict = self._toml_dict(inp_obj)
        # Write the input file to disk
        filepath = Path("input.toml")
        filepath.write_text(tomli_w.dumps(toml_dict))

        print(toml_dict)
        print(filepath.read_text())

        # Execute CREST
        stdout = execute_subprocess(
            self.program, [filepath.name], update_func, update_interval
        )
        # Parse the output
        conformers = self._collect_structures("crest_conformers.xyz")

        rotamers = []
        if collect_rotamers:
            rotamers = self._collect_structures("crest_rotamers.xyz")

        return ConformerSearchResults(conformers=conformers, rotamers=rotamers), stdout

    def _collect_structures(self, file_name: str) -> List[AnnotatedStructure]:
        """Collect structures from a file generated by CREST."""
        try:
            structures = Structure.open(file_name)
            if not isinstance(structures, list):  # single structure
                structures = [structures]
        except FileNotFoundError:
            return []  # No structures created
        else:
            # Create Annotated Structures
            return [
                AnnotatedStructure(
                    results=SinglePointResults(
                        energy=struct.extras[Structure._xyz_comment_key][0]
                    ),
                    **struct.model_dump(),
                )
                for struct in structures
            ]
