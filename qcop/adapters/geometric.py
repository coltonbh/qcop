"""Adapter for geomeTRIC program."""
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from qcio import (
    CalcType,
    DualProgramInput,
    Molecule,
    OptimizationResults,
    ProgramInput,
    QCProgramArgs,
    SinglePointOutput,
)

from qcop.exceptions import AdapterInputError, ProgramNotFoundError
from qcop.utils import get_adapter

from .base import ProgramAdapter
from .utils import capture_logs


class GeometricAdapter(ProgramAdapter):
    program = "geometric"
    supported_calctypes = [CalcType.optimization, CalcType.transition_state]

    def __init__(self):
        super().__init__()
        self.geometric = self._ensure_geometric()
        # Dictionary from geometric.run_json; copying QCSchema workflow
        self.coordsys_params = {
            "cart": (self.geometric.internal.CartesianCoordinates, False, False),
            "prim": (self.geometric.internal.PrimitiveInternalCoordinates, True, False),
            "dlc": (
                self.geometric.internal.DelocalizedInternalCoordinates,
                True,
                False,
            ),
            "hdlc": (
                self.geometric.internal.DelocalizedInternalCoordinates,
                False,
                True,
            ),
            "tric": (
                self.geometric.internal.DelocalizedInternalCoordinates,
                False,
                False,
            ),
        }

    def _ensure_geometric(self):
        try:
            import geometric

            return geometric
        except ImportError:
            raise ProgramNotFoundError("geometric")

    def program_version(self, *args) -> str:
        """Get the program version."""
        return self.geometric.__version__

    def compute_results(
        self,
        inp_obj: DualProgramInput,
        update_func: Optional[Callable] = None,
        update_interval: Optional[float] = None,
        propagate_wfn: bool = False,
        **kwargs,
    ) -> Tuple[OptimizationResults, str]:
        """Compute the requested calculation.

        Args:
            inp_obj: The qcio DualProgramInput object for a computation.
            propagate_wfn: Whether to propagate the wavefunction between steps of the
                optimization.
        """

        # Update the input object based on its calctype
        self._update_inp_obj(inp_obj)
        geometric_molecule = self._create_geometric_molecule(inp_obj)
        internal_coords_sys = self._setup_coords(inp_obj, geometric_molecule)

        qcio_adapter = get_adapter(inp_obj.subprogram, inp_obj, qcng_fallback=True)
        optimizer = self._construct_optimizer(
            inp_obj,
            geometric_molecule,
            internal_coords_sys,
            qcio_adapter,
            propagate_wfn=propagate_wfn,
            **kwargs,
        )

        with capture_logs("geometric") as (_, log_capture_io):
            optimizer.optimizeGeometry()

        return (
            OptimizationResults(
                trajectory=optimizer.engine.qcio_trajectory,
            ),
            log_capture_io.getvalue(),
        )

    def _update_inp_obj(self, inp_obj: DualProgramInput) -> None:
        """Update the input object based on its calctype

        Args:
            inp_obj: The qcio DualProgramInput object for a computation.

        Returns:
            None. The input object is updated in place.
        """
        if inp_obj.calctype == CalcType.transition_state:
            inp_obj.keywords["transition"] = True
        else:
            inp_obj.keywords["transition"] = False

    def _create_geometric_molecule(self, inp_obj: DualProgramInput):
        """Create a geomeTRIC Molecule from the input object.

        Args:
            inp_obj: The qcio DualProgramInput object for a computation.

        Returns:
            The geomeTRIC Molecule object.
        """
        xyz_path = "initial_geometry.xyz"
        inp_obj.molecule.save(xyz_path)
        geometric_molecule = self.geometric.molecule.Molecule(fnm=xyz_path)
        # Delete file
        Path(xyz_path).unlink()
        return geometric_molecule

    def _construct_optimizer(
        self,
        inp_obj,
        geometric_molecule,
        internal_coords_sys,
        qcio_adapter,
        propagate_wfn: bool = False,
        **kwargs,
    ):
        """Construct the geomeTRIC optimizer object

        Args:
            inp_obj: The qcio DualProgramInput object for a computation.
            geometric_molecule: The geomeTRIC Molecule object.
            internal_coords_sys: The geomeTRIC internal coordinate system.
            qcio_adapter: The qcio adapter for the subprogram.

        Returns:
            The geomeTRIC optimizer object.
        """
        return self.geometric.optimize.Optimizer(
            inp_obj.molecule.geometry.flatten(),
            geometric_molecule,
            internal_coords_sys,
            engine=self._geometric_engine()(
                qcio_adapter,
                inp_obj.subprogram_args,
                inp_obj.molecule,
                geometric_molecule,
                propagate_wfn,
            ),
            dirname=Path.cwd(),
            # Must declare xyzout here to avoid a bug in geomeTRIC
            # This file will contain every geometry in the optimization as a
            # multi-structure .xyz file with the energy of each step as a comment.
            params=self.geometric.params.OptParams(
                xyzout="qcio_optim.xyz", **inp_obj.keywords
            ),
        )

    def _setup_coords(self, inp_obj, geometric_molecule):
        """Setup the internal coordinate system.

        Args:
            inp_obj: The qcio DualProgramInput object for a computation.
            geometric_molecule: The geomeTRIC Molecule object.

        Returns:
            The geomeTRIC internal coordinate system with constraints applied.
        """

        # Default to internal coords
        coords_sys = inp_obj.keywords.get("coordsys", "tric")
        coords_cls, connect, addcart = self.coordsys_params[coords_sys]

        # Handle constraints; see geometric.run_json, it's a mess!
        # NOTE: From documentation says constraints may be 1-indexed instead of
        # 0-indexed; however, in practice they are 0-indexed.
        # https://geometric.readthedocs.io/en/latest/constraints.html
        constraints, constraint_vals = None, None
        constraints_dict = inp_obj.keywords.pop("constraints", None)
        if constraints_dict:
            if "scan" in constraints_dict:
                raise AdapterInputError(
                    "The constraint 'scan' keyword is not yet supported by the JSON "
                    "interface, reports geometric!"
                )
            constraints_string = self.geometric.run_json.make_constraints_string(
                constraints_dict
            )

            constraints, constraint_vals = self.geometric.prepare.parse_constraints(
                geometric_molecule, constraints_string
            )

        return coords_cls(
            geometric_molecule,
            build=True,
            connect=connect,
            addcart=addcart,
            constraints=constraints,
            # No idea why we truncate the list here...
            cvals=constraint_vals[0] if constraint_vals is not None else None,
        )

    def _geometric_engine(self):
        """Return the qcop geomeTRIC engine class."""

        class QCOPGeometricEngine(self.geometric.engine.Engine):
            """QCOP Engine for Geometric"""

            def __init__(
                self,
                qcio_adapter: ProgramAdapter,
                qcio_program_args: QCProgramArgs,
                qcio_molecule: Molecule,
                geometric_molecule,
                propagate_wfn: bool = False,
            ):
                super().__init__(geometric_molecule)
                self.qcio_adapter = qcio_adapter
                self.qcio_program_args = qcio_program_args
                self.qcio_molecule = qcio_molecule
                self.propagate_wfn = propagate_wfn
                self.qcio_trajectory: List[SinglePointOutput] = []

            def calc_new(self, coords, *args) -> Dict[str, Union[float, np.ndarray]]:
                """Calculate the energy and gradient for a given geometry.

                Args:
                    coords: The geometry to evaluate in bohr.

                Returns:
                    A dictionary of {"energy": float, "gradient": ndarray}.
                """
                prog_input = ProgramInput(
                    calctype=CalcType.gradient,
                    molecule=Molecule(
                        symbols=self.qcio_molecule.symbols,
                        geometry=coords,
                    ),
                    **self.qcio_program_args.dict(),
                )

                # Propagate wavefunction
                if (
                    self.qcio_trajectory  # Not the first step
                    and self.propagate_wfn  # Wfn propagation requested
                    and hasattr(
                        self.qcio_adapter, "propagate_wfn"
                    )  # Adapter supports propagation
                ):
                    self.qcio_adapter.propagate_wfn(
                        self.qcio_trajectory[-1], prog_input
                    )
                # raise_exc=True so ProgramFailure objects don't get returned
                output = self.qcio_adapter.compute(
                    prog_input,
                    raise_exc=True,
                    collect_wfn=self.propagate_wfn,
                )
                self.qcio_trajectory.append(output)
                # geomeTRIC requires 1D array
                return {
                    "energy": output.results.energy,
                    "gradient": output.results.gradient.flatten(),
                }

        return QCOPGeometricEngine