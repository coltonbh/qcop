from typing import Callable, Optional, Tuple

from qcio.models.single_point import (
    SinglePointComputedProperties,
    SinglePointInput,
    SPCalcType,
)
from qcparse import parse_computed_props
from qcparse.parsers.terachem import parse_version_string

from qcop.exceptions import AdapterInputError
from qcop.utils import execute_subprocess

from .base import QCOPSinglePointAdapter


class TeraChemAdapter(QCOPSinglePointAdapter):
    """Adapter for TeraChem."""

    supported_calc_types = [SPCalcType.energy, SPCalcType.gradient, SPCalcType.hessian]
    program = "terachem"
    padding = 20  # padding between keyword and value in tc.in

    def program_version(self, stdout: Optional[str] = None) -> str:
        """Get the program version.

        Args:
            stdout: The stdout from the program.

        Returns:
            The program version.
        """
        if stdout:
            return parse_version_string(stdout)
        else:
            # Cut out "TeraChem version " (17 chars) from the output
            return execute_subprocess(self.program, ["--version"])[17:]

    def prepare_inputs(self, inp_obj: SinglePointInput) -> str:
        """Translate qcio objects into TeraChem inputs files. Write files to disk.

        Args:
            inp_obj: The qcio SinglePointInput object for a computation.

        Returns:
            Filename of input file (tc.in).
        """
        # Write molecule to disk
        xyz_filename = "geom.xyz"
        inp_obj.molecule.save(xyz_filename)

        # Write input file
        inp_filename = "tc.in"

        with open(inp_filename, "w") as f:
            # calc_type
            if inp_obj.program_args.calc_type == "hessian":
                calc_type = "frequencies"
            else:
                calc_type = inp_obj.program_args.calc_type
            f.write(f"{'run':<{self.padding}} {calc_type}\n")
            # Molecule
            f.write(f"{'coordinates':<{self.padding}} {xyz_filename}\n")
            f.write(f"{'charge':<{self.padding}} {inp_obj.molecule.charge}\n")
            f.write(f"{'spinmult':<{self.padding}} {inp_obj.molecule.multiplicity}\n")
            # Model
            f.write(f"{'method':<{self.padding}} {inp_obj.program_args.model.method}\n")
            f.write(f"{'basis':<{self.padding}} {inp_obj.program_args.model.basis}\n")

            # Keywords
            non_keywords = {
                "charge": ".molecule.charge",
                "spinmult": ".molecule.multiplicity",
                "run": ".program_args.calc_type",
                "basis": ".program_args.model.basis",
                "method": ".program_args.model.method",
            }
            for key, value in inp_obj.program_args.keywords.items():
                # Check for keywords that should be passed as structured data
                if key in non_keywords:
                    raise AdapterInputError(
                        program=self.program,
                        message=f"Keyword '{key}' should not be set as a keyword. It "
                        f"should be set at '{non_keywords[key]}'",
                    )
                # Lowercase booleans
                f.write(f"{key:<{self.padding}} {str(value).lower()}\n")
        return inp_filename

    # TODO: Need command line options for TeraChem e.g., -g 1 for GPUs MAYBE?
    # Try using it for a while without and see what roadblocks we run into
    def _compute(
        self,
        inp_obj,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
    ) -> Tuple[SinglePointComputedProperties, str]:
        """Execute TeraChem on the given input.

        Args:
            inp_obj: The qcio SinglePointInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointComputedProperties and the stdout str.
        """
        tc_in = self.prepare_inputs(inp_obj)
        stdout = execute_subprocess(self.program, [tc_in], update_func, update_interval)
        # Hardcoding "terachem" so "terachemd" isn't passed to parse
        parsed_output = parse_computed_props(stdout, "terachem", "stdout")
        return parsed_output, stdout


class TeraChemDockerAdapter(TeraChemAdapter):
    """Adapter for TeraChem executable running in Docker."""

    program = "terachemd"
