from pathlib import Path
from typing import Callable, Optional, Tuple

from qcio import CalcType, ProgramInput, SinglePointOutput, SinglePointResults
from qcparse import parse_results
from qcparse.parsers.terachem import parse_version_string

from qcop.exceptions import AdapterInputError

from .base import ProgramAdapter
from .utils import execute_subprocess


class TeraChemAdapter(ProgramAdapter):
    """Adapter for TeraChem."""

    supported_calctypes = [CalcType.energy, CalcType.gradient, CalcType.hessian]
    program = "terachem"
    padding = 20  # padding between keyword and value in tc.in
    xyz_filename = "geom.xyz"

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

    def prepare_inputs(self, inp_obj: ProgramInput) -> str:
        """Translate qcio objects into TeraChem inputs files. Write files to disk.

        Args:
            inp_obj: The qcio ProgramInput object for a computation.

        Returns:
            Filename of input file (tc.in).
        """
        # Write molecule to disk
        inp_obj.molecule.save(self.xyz_filename)

        # Write input file
        inp_filename = "tc.in"

        with open(inp_filename, "w") as f:
            # calctype
            if inp_obj.calctype.value == CalcType.hessian:
                calctype = "frequencies"
            else:
                calctype = inp_obj.calctype.value
            f.write(f"{'run':<{self.padding}} {calctype}\n")
            # Molecule
            f.write(f"{'coordinates':<{self.padding}} {self.xyz_filename}\n")
            f.write(f"{'charge':<{self.padding}} {inp_obj.molecule.charge}\n")
            f.write(f"{'spinmult':<{self.padding}} {inp_obj.molecule.multiplicity}\n")
            # Model
            f.write(f"{'method':<{self.padding}} {inp_obj.model.method}\n")
            f.write(f"{'basis':<{self.padding}} {inp_obj.model.basis}\n")

            # Keywords
            non_keywords = {
                "charge": ".molecule.charge",
                "spinmult": ".molecule.multiplicity",
                "run": ".calctype",
                "basis": ".model.basis",
                "method": ".model.method",
            }
            for key, value in inp_obj.keywords.items():
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
    def compute_results(
        self,
        inp_obj,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        **kwargs,
    ) -> Tuple[SinglePointResults, str]:
        """Execute TeraChem on the given input.

        Args:
            inp_obj: The qcio ProgramInput object for a computation.
            update_func: A callback function to call as the program executes.
            update_interval: The minimum time in seconds between calls to the
                update_func.

        Returns:
            A tuple of SinglePointComputedProps and the stdout str.
        """
        tc_in = self.prepare_inputs(inp_obj)
        stdout = execute_subprocess(self.program, [tc_in], update_func, update_interval)
        parsed_output = parse_results(stdout, self.program, "stdout")
        return parsed_output, stdout

    def collect_wfn(self, output: SinglePointOutput) -> None:
        """Append wavefunction data to the output.

        Args:
            output: SinglePointOutput object on which to append wavefunction data.

        Returns:
            None. Modifies the output object in place.
        """

        # Naming conventions from TeraChem uses xyz filename as scratch dir postfix
        scr_postfix = self.xyz_filename.split(".")[0]

        # Wavefunction filenames
        wfn_filenames = ("c0", "ca0", "cb0")
        wfn_paths = [Path(f"scr.{scr_postfix}/{fn}") for fn in wfn_filenames]
        if not any(wfn_path.exists() for wfn_path in wfn_paths):
            raise AdapterInputError(
                program=self.program,
                message=f"No wavefunction files found in {Path.cwd()}",
            )
        for wfn_path in wfn_paths:
            if wfn_path.exists():
                output.files[str(wfn_path)] = wfn_path.read_bytes()

    def propagate_wfn(self, output: SinglePointOutput, prog_inp: ProgramInput) -> None:
        """Propagate the wavefunction from the previous calculation.

        Args:
            output: The output from a previous calculation containing wavefunction data.
            prog_inp: The ProgramInput object on which to place the wavefunction data.

        Returns:
            None. Modifies the prog_inp object in place.
        """

        # Naming conventions from TeraChem uses xyz filename as scratch dir postfix
        scr_postfix = self.xyz_filename.split(".")[0]

        # Wavefunction filenames
        c0, ca0, cb0 = "c0", "ca0", "cb0"

        c0_bytes = output.files.get(f"scr.{scr_postfix}/{c0}")
        ca0_bytes = output.files.get(f"scr.{scr_postfix}/{ca0}")
        cb0_bytes = output.files.get(f"scr.{scr_postfix}/{cb0}")

        if not c0_bytes and not (ca0_bytes and cb0_bytes):
            raise AdapterInputError(
                program=self.program,
                message="Could not find c0 or ca/b0 files in output.",
            )

        # Load wavefunction data onto ProgramInput object

        if c0_bytes:
            prog_inp.files[c0] = c0_bytes
            prog_inp.keywords["guess"] = c0

        else:  # ca0_bytes and cb0_bytes
            prog_inp.files[ca0] = ca0_bytes
            prog_inp.files[cb0] = cb0_bytes
            prog_inp.keywords["guess"] = f"{ca0} {cb0}"
