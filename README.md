# Quantum Chemistry Operate

A package for operating Quantum Chemistry programs using [qcio](https://github.com/coltonbh/qcio) standardized data structures. Compatible with `TeraChem`, `psi4`, `QChem`, `NWChem`, `ORCA`, `Molpro`, `geomeTRIC` and many more.

[![image](https://img.shields.io/pypi/v/qcop.svg)](https://pypi.python.org/pypi/qcop)
[![image](https://img.shields.io/pypi/l/qcop.svg)](https://pypi.python.org/pypi/qcop)
[![image](https://img.shields.io/pypi/pyversions/qcop.svg)](https://pypi.python.org/pypi/qcop)
[![Actions status](https://github.com/coltonbh/qcop/workflows/Tests/badge.svg)](https://github.com/coltonbh/qcop/actions)
[![Actions status](https://github.com/coltonbh/qcop/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/coltonbh/qcop/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

`qcop` works in harmony with a suite of other quantum chemistry tools for fast, structured, and interoperable quantum chemistry.

## The QC Suite of Programs

- [qcio](https://github.com/coltonbh/qcio) - Beautiful and user friendly data structures for quantum chemistry.
- [qcparse](https://github.com/coltonbh/qcparse) - A library for efficient parsing of quantum chemistry data into structured `qcio` objects.
- [qcop](https://github.com/coltonbh/qcop) - A package for operating quantum chemistry programs using `qcio` standardized data structures. Compatible with `TeraChem`, `psi4`, `QChem`, `NWChem`, `ORCA`, `Molpro`, `geomeTRIC` and many more.
- [BigChem](https://github.com/mtzgroup/bigchem) - A distributed application for running quantum chemistry calculations at scale across clusters of computers or the cloud. Bring multi-node scaling to your favorite quantum chemistry program.
- `ChemCloud` - A [web application](https://github.com/mtzgroup/chemcloud-server) and associated [Python client](https://github.com/mtzgroup/chemcloud-client) for exposing a BigChem cluster securely over the internet.

## Installation

```sh
pip install qcop
```

## Quickstart

`qcop` uses the `qcio` data structures to drive quantum chemistry programs in a standardized way. This allows for a simple and consistent interface to a wide variety of quantum chemistry programs. See the [qcio](https://github.com/coltonbh/qcio) library for documentation on the input and output data structures.

The `compute` function is the main entry point for the library and is used to run a calculation.

```python
from qcio import Structure, ProgramInput
from qcop import compute
from qcop.exceptions import ExternalProgramError
# Create the Structure
h2o = Structure.open("h2o.xyz")

# Define the program input
prog_input = ProgramInput(
    structure=h2o,
    calctype="energy",
    model={"method": "hf", "basis": "sto-3g"},
    keywords={"purify": "no", "restricted": False},
)

# Run the calculation; will return ProgramOutput or raise an exception
try:
    po = compute("terachem", prog_input, collect_files=True)
except ExternalProgramError as e:
    # External QQ program failed in some way
    po = e.program_output
    po.input_data # Input data used by the QC program
    po.success # Will be False
    po.results # Any half-computed results before the failure
    po.traceback # Stack trace from the calculation
    po.ptraceback # Shortcut to print out the traceback in human readable format
    po.stdout # Stdout log from the calculation
    raise e
else:
    # Calculation succeeded
    po.input_data # Input data used by the QC program
    po.success # Will be True
    po.results # All structured results from the calculation
    po.stdout # Stdout log from the calculation
    po.pstdout # Shortcut to print out the stdout in human readable format
    po.files # Any files returned by the calculation
    po.provenance # Provenance information about the calculation
    po.extras # Any extra information not in the schema

```

One may also call `compute(..., raise_exc=False)` to return a `ProgramOutput` object rather than raising an exception when a calculation fails. This may allow easier handling of failures in some cases.

```python
from qcio import Structure, ProgramInput
from qcop import compute
from qcop.exceptions import ExternalProgramError
# Create the Structure
h2o = Structure.open("h2o.xyz")

# Define the program input
prog_input = ProgramInput(
    structure=h2o,
    calctype="energy",
    model={"method": "hf", "basis": "sto-3g"},
    keywords={"purify": "no", "restricted": False},
)

# Run the calculation; will return a ProgramOutput objects
po = compute("terachem", prog_input, collect_files=True, raise_exc=False)
if not po.success:
    # External QQ program failed in some way
    po.input_data # Input data used by the QC program
    po.success # Will be False
    po.results # Any half-computed results before the failure
    po.traceback # Stack trace from the calculation
    po.ptraceback # Shortcut to print out the traceback in human readable format
    po.stdout # Stdout log from the calculation

else:
    # Calculation succeeded
    po.input_data # Input data used by the QC program
    po.success # Will be True
    po.results # All structured results from the calculation
    po.stdout # Stdout log from the calculation
    po.pstdout # Shortcut to print out the stdout in human readable format
    po.files # Any files returned by the calculation
    po.provenance # Provenance information about the calculation
    po.extras # Any extra information not in the schema

```

Alternatively, the `compute_args` function can be used to run a calculation with the input data structures passed in as arguments rather than as a single `ProgramInput` object.

```python
from qcio import Structure
from qcop import compute_args
# Create the Structure
h2o = Structure.open("h2o.xyz")

# Run the calculation
output = compute_args(
    "terachem",
    h2o,
    calctype="energy",
    model={"method": "hf", "basis": "sto-3g"},
    keywords={"purify": "no", "restricted": False},
    files={...},
    collect_files=True
)
```

The behavior of `compute()` and `compute_args()` can be tuned by passing in keyword arguments like `collect_files` shown above. Keywords can modify which scratch directory location to use, whether to delete or keep the scratch files after a calculation completes, what files to collect from a calculation, whether to print the program stdout in real time as the program executes, and whether to propagate a wavefunction through a series of calculations. Keywords also include hooks for passing in update functions that can be called as a program executes in real time. See the [compute method docstring](https://github.com/coltonbh/qcop/blob/83868df51d241ffae3497981dfc3c72235319c6e/qcop/adapters/base.py#L57-L123) for more details.

See the [/examples](https://github.com/coltonbh/qcop/tree/master/examples) directory for more examples.

## Support

If you have any issues with `qcop` or would like to request a feature, please open an [issue](https://github.com/coltonbh/qcop/issues).
