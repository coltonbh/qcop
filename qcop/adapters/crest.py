"""Adapter for CREST package. https://crest-lab.github.io/crest-docs/"""

from pathlib import Path
from typing import Callable, Optional, Tuple

import qcparse
from qcio import CalcType, ConformerSearchResults, ProgramInput
from qcparse.parsers import crest

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
        return crest.parse_version_string(stdout)

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
        # Create CREST native input files
        try:
            native_inp = qcparse.encode(inp_obj, self.program)
        except qcparse.exceptions.EncoderError as e:
            raise AdapterInputError(self.program, "Invalid input for CREST") from e

        # Write the input files to disk
        inp_file, struct_file = Path("input.toml"), Path(native_inp.geometry_filename)
        inp_file.write_text(native_inp.input_file)
        struct_file.write_text(native_inp.geometry_file)

        # Execute CREST
        stdout = execute_subprocess(
            self.program, [inp_file.name], update_func, update_interval
        )

        # Parse the output
        csr = crest.parse_conformer_search_dir(
            ".",
            charge=inp_obj.structure.charge,
            multiplicity=inp_obj.structure.multiplicity,
            collect_rotamers=collect_rotamers,
        )

        # Add identifiers to the conformers and rotamers
        ids = inp_obj.structure.identifiers.model_dump()
        for struct_type in ["conformers", "rotamers"]:
            for struct in getattr(csr, struct_type):
                struct.add_identifiers(ids)

        return csr, stdout
