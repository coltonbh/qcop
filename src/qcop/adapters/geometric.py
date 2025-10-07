"""Adapter for geomeTRIC program."""

from collections.abc import Callable
from pathlib import Path

import numpy as np
from qcio import (
    CalcSpec,
    CalcType,
    CompositeCalcSpec,
    CoreSpec,
    OptimizationData,
    Results,
    SinglePointData,
    Structure,
)

from qcop.exceptions import (
    AdapterInputError,
    ExternalProgramError,
    ProgramNotFoundError,
    QCOPBaseError,
)
from qcop.utils import get_adapter

from .base import ProgramAdapter
from .utils import capture_logs


class GeometricAdapter(ProgramAdapter[CompositeCalcSpec, OptimizationData]):
    """Adapter for geomeTRIC."""

    program = "geometric"
    supported_calctypes = [CalcType.optimization, CalcType.transition_state]
    """Supported calculation types."""

    def __init__(self):
        super().__init__()
        # Check that geomeTRIC is installed
        self.geometric = self._ensure_geometric_installed()
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

    @staticmethod
    def _ensure_geometric_installed():
        try:
            import geometric
        except ModuleNotFoundError as e:
            raise ProgramNotFoundError("geometric") from e
        else:
            return geometric

    def program_version(self, *args) -> str:
        """Get the program version."""
        return self.geometric.__version__

    def compute_data(
        self,
        input_data: CompositeCalcSpec,
        update_func: Callable | None = None,
        update_interval: float | None = None,
        propagate_wfn: bool = True,
        **kwargs,
    ) -> tuple[OptimizationData, str]:
        """Compute the requested calculation.

        Args:
            input_data: The qcio CompositeCalcSpec object for a computation.
            propagate_wfn: Whether to propagate the wavefunction between steps of the
                optimization.
        """
        # Update the input object based on its calctype
        self._update_input_data(input_data)
        geometric_molecule = self._create_geometric_molecule(input_data.structure)
        internal_coords_sys = self._setup_coords(input_data, geometric_molecule)

        qcio_adapter = get_adapter(
            input_data.subprogram, input_data, qcng_fallback=True
        )
        optimizer = self._construct_optimizer(
            input_data,
            geometric_molecule,
            internal_coords_sys,
            qcio_adapter,
            propagate_wfn=propagate_wfn,
            update_func=update_func,
            update_interval=update_interval,
            **kwargs,
        )

        # Haven't update DualOutputHandler to send logs using arbitrary update funcs.
        with capture_logs("geometric", update_func, update_interval) as (_, log_string):
            try:
                optimizer.optimizeGeometry()
            except self.geometric.errors.Error as e:
                raise ExternalProgramError(
                    program=self.program,
                    message="geomeTRIC optimization failed. See the traceback above for details.",
                ) from e

        return (
            OptimizationData(
                trajectory=optimizer.engine.qcio_trajectory,
            ),
            log_string.getvalue(),
        )

    def _update_input_data(self, input_data: CompositeCalcSpec) -> None:
        """Update the input_data based on its calctype

        Args:
            input_data: The qcio CompositeCalcSpec object for a computation.

        Returns:
            None. The input_data is updated in place.
        """
        if input_data.calctype == CalcType.transition_state:
            input_data.keywords["transition"] = True
        else:
            input_data.keywords["transition"] = False

    def _create_geometric_molecule(self, structure: Structure):
        """Create a geomeTRIC Structure from the input object.

        Args:
            structure: The qcio Structure object for a computation.

        Returns:
            The geomeTRIC Structure object.
        """
        xyz_path = "initial_geometry.xyz"
        structure.save(xyz_path)
        geometric_structure = self.geometric.molecule.Molecule(fnm=xyz_path)
        # Delete file
        Path(xyz_path).unlink()
        return geometric_structure

    def _construct_optimizer(
        self,
        input_data,
        geometric_molecule,
        internal_coords_sys,
        qcio_adapter,
        propagate_wfn: bool = False,
        update_func: Callable | None = None,
        update_interval: float | None = None,
        **kwargs,
    ):
        """Construct the geomeTRIC optimizer object

        Args:
            input_data: The qcio CompositeCalcSpec object for a computation.
            geometric_molecule: The geomeTRIC Molecule object.
            internal_coords_sys: The geomeTRIC internal coordinate system.
            qcio_adapter: The qcio adapter for the subprogram.

        Returns:
            The geomeTRIC optimizer object.
        """
        return self.geometric.optimize.Optimizer(
            input_data.structure.geometry.flatten(),
            geometric_molecule,
            internal_coords_sys,
            engine=self._geometric_engine()(
                qcio_adapter,
                input_data.subprogram_spec,
                input_data.structure,
                geometric_molecule,
                propagate_wfn,
                update_func,
                update_interval,
            ),
            dirname=Path.cwd(),
            # Must declare xyzout here to avoid a bug in geomeTRIC
            # This file will contain every geometry in the optimization as a
            # multi-structure .xyz file with the energy of each step as a comment.
            params=self.geometric.params.OptParams(
                xyzout="qcio_optim.xyz", **input_data.keywords
            ),
        )

    def _setup_coords(self, input_data, geometric_structure):
        """Setup the internal coordinate system.

        Args:
            input_data: The qcio CompositeCalcSpec object for a computation.
            geometric_structure: The geomeTRIC Structure object.

        Returns:
            The geomeTRIC internal coordinate system with constraints applied.
        """

        # Default to internal coords
        coords_sys = input_data.keywords.get("coordsys", "tric")
        coords_cls, connect, addcart = self.coordsys_params[coords_sys]

        # Handle constraints; see geometric.run_json, it's a mess!
        # NOTE: From documentation says constraints may be 1-indexed instead of
        # 0-indexed; however, in practice they are 0-indexed.
        # https://geometric.readthedocs.io/en/latest/constraints.html
        constraints, constraint_vals = None, None
        constraints_dict = input_data.keywords.pop("constraints", None)
        if constraints_dict:
            if "scan" in constraints_dict:
                raise AdapterInputError(
                    "The constraint 'scan' keyword is not yet supported by the JSON "
                    "interface, reports geometric!",
                    program=self.program,
                )
            constraints_string = self.geometric.run_json.make_constraints_string(
                constraints_dict
            )

            constraints, constraint_vals = self.geometric.prepare.parse_constraints(
                geometric_structure, constraints_string
            )

        return coords_cls(
            geometric_structure,
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
                qcio_program_args: CoreSpec,
                qcio_structure: Structure,
                geometric_structure,
                propagate_wfn: bool = False,
                update_func: Callable | None = None,
                update_interval: float | None = None,
            ):
                super().__init__(geometric_structure)
                self.qcio_adapter = qcio_adapter
                self.qcio_program_args = qcio_program_args
                self.qcio_structure = qcio_structure
                self.propagate_wfn = propagate_wfn
                self.qcio_trajectory: list[Results] = []
                self.update_func = update_func
                self.update_interval = update_interval

            def calc_new(self, coords, *args) -> dict[str, float | np.ndarray]:
                """Calculate the energy and gradient for a given geometry.

                Args:
                    coords: The geometry to evaluate in bohr.

                Returns:
                    A dictionary of {"energy": float, "gradient": ndarray}.
                """
                # Merge new coordinates into structure
                structure = Structure(
                    **{**self.qcio_structure.model_dump(), "geometry": coords}
                )
                calcspec = CalcSpec(
                    calctype=CalcType.gradient,
                    structure=structure,
                    **self.qcio_program_args.model_dump(),
                )

                # Propagate wavefunction
                if (
                    self.qcio_trajectory  # Not the first step
                    and self.propagate_wfn
                    and hasattr(self.qcio_adapter, "propagate_wfn")
                ):
                    self.qcio_adapter.propagate_wfn(
                        self.qcio_trajectory[-1], calcspec
                    )

                # Calculate energy and gradient
                try:
                    results: Results[CalcSpec, SinglePointData] = (
                        self.qcio_adapter.compute(
                            calcspec,
                            raise_exc=True,
                            collect_wfn=self.propagate_wfn,
                            update_func=self.update_func,
                            update_interval=self.update_interval,
                        )
                    )
                except QCOPBaseError as e:
                    if e.results:  # For mypy
                        # Append error output
                        self.qcio_trajectory.append(e.results)
                    data = OptimizationData(trajectory=self.qcio_trajectory)
                    e.data = data
                    # TODO: Add args/kwargs update for Celery serialization?
                    # Maybe not because .data is folded into e.results in
                    # BaseAdapter.compute()?
                    raise e

                else:
                    self.qcio_trajectory.append(results)

                assert (  # for mypy
                    results.data is not None
                    and results.data.energy is not None
                    and results.data.gradient is not None
                    and isinstance(results.data.gradient, np.ndarray)
                )
                return {
                    "energy": results.data.energy,
                    # geomeTRIC requires 1D array
                    "gradient": results.data.gradient.flatten(),
                }

        return QCOPGeometricEngine
