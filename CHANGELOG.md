# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.9.7] - 2025-02-25

### Changed

- Only add identifiers from the input structure to CREST's generated conformer and rotamers if `topo: True` meaning CREST prohibited topology changes.
- Updated `poetry.lock` package dependencies.

### Fixed

- CREST Adapter's call to `Structure.add_identifiers()` need to pass kwargs and not a dictionary due to an update to the `qcio` API.

## [0.9.6] - 2025-02-07

### Added

- `Try/Except` statement for TeraChem version parsing. If `libcuda.so.1` is not found, TeraChem will not print the version string to `stdout`. This will no longer throw an exception and will return `Could not parse version` instead.

## [0.9.5] - 2025-02-07

### Changed

- Loosened `tcpb` dependency from `^0.14.1` to `>=0.14.1`.

## [0.9.4] - 2025-01-15

### Changed

- More flexibly defined `qcparse` dependency from `^0.6.4` to `>=0.6.4`.

## [0.9.3] - 2025-01-15

### Changed

- More flexibly defined `qcio` dependency from `^0.11.8` to `>=0.11.8`.

## [0.9.2] - 2024-10-01

### Added

- `energy`, `gradient`, `hessian`, and `optimization` support the the `CRESTAdapter`.

## [0.9.1] - 2024-09-12

### Added

- `CalcType.optimization` support for TeraChem.
- `typos` pre-commit check.

## [0.9.0] - 2024-09-11

### Changed

- 🚨: Bumped minimum python version from 3.8 -> 3.9 (needed for compatibility with `tcpb`).
- Updated type annotations to use `dict`, `list`, `tuple` instead of `typing.Dict`, etc.

### Removed

- `black` and `isort` in favor of modern `ruff`.

### Added

- TeraChem protocol buffer server (and frontend) adapters.

## [0.8.1] - 2024-08-13

### Added

- `CRESTAdapter` that supports `CalcType.conformer_search`.
- `mkdocs` documentation.

## [0.8.0] - 2024-07-19

### Changed

- Updated to [qcio 0.11.0](https://github.com/coltonbh/qcio/releases/tag/0.10.5) which removed `NoResults` and requires explicit passing of a `.results` value to `ProgramOutput` rather than implicitly passing `None` and having `qcio` set `.results = NoResult`. It also moved `.files` from `ProgramOutput` to the `results` objects.

## [0.7.5] - 2024-07-17

### Changed

- Only respect `collect_file` for for `Adapter.compute` if the adapter has `.uses_files=True`.
- Moved the `program_version = self.program_version(stdout)` call from `BaseAdapter.compute(...)` to outside the `try` block so that program version is collected even if the calculation fails.
- Cleaned up `xtb` cached version implementation.
- Added `confirm_version` check to `release.py`.

## [0.7.4] - 2024-07-16

### Changed

- Added `threading.Lock()` to `capture_sys_stdout` so that it is thread safe.
- Cached `XTBAdapter.program_version` result since calls to `importlib.metadata.version(...)` call `os.listdir()` and when doing very many `xtb` calls these became substantial (almost 1/2 the execution time). We have to use `importlib.metadata.version` rather than `xtb.__version__` directly because their `__version__` string is wrong.

## [0.7.3] - 2024-07-12

### Added

- `release.py` script for automated releases.

### Changed

- Upgraded to `qcio 0.10.2` which reverts back to the default of `Structure.identifiers` instead of `Structure.ids`.
- Fix depreciated call to `qcparse.parse_results` for the TeraChem adapter.

## [0.7.2] - 2024-07-12

### Added

- `xtb` to optional installs and error message for `XtbAdapter` to indicate it can be installed with `pip install qcop[xtb]`.
- `qcop.adapters.utils.set_env_variable` context manager to address the fact that one must set the env var `OMP_NUM_THREADS=1` _before_ importing any of the `xtb` library or else performance is severely impacted (around 10x). They spawn threads within threads so if you leave the default value (which is the number of cores on your machine) you get way more threads than this! E.g., on my 16 core machine I'll get 47 threads spawned for a single calculation. If I set this to `1` I actually get the correct number of threads, which is `16`. One must set this value _before_ importing any piece of the `xtb` library, so if your script imports anything from `xtb` before calling `qcop.compute("xtb", ...)` wrap this import with the `qcop.adapters.utils.set_env_variable` wrapper like this:

  ```python
  from qcop.adapters.utils import set_env_variable

  with set_env_variable("OMP_NUM_THREADS", "1"):
      import xtb
      import xtb.interface
      import xtb.libxtb
      from xtb.utils import Solvent

  ### The rest of your script
  ```

## [0.7.1] - 2024-07-10

### Fixed

- Incorrect check in `BaseAdapter.compute()` using `isinstance(inp_obj, FileInput)`. Updated to `type(inp_obj) is FileInput` to work with updated `qcio` inheritance hierarchy.

## [0.7.0] - 2024-07-10

### Added

- Added validation check for programs that do not support file inputs if files are passed as an input.

### Changed

- 🚨 Updated to `qcio 0.10.1` which uses `Structure` in place of `Molecule`.
- Changed `Adapter.write_files` to `Adapter.uses_files` to more clearly define purpose of this variable.
- `tmpdir` context manager only creates a temporary directory if `mkdir` is passed as the first argument. This works in conjunction with `Adapter.uses_files` so that adapters that do not use file I/O (e.g., pure Python programs) do not have the additional overhead of creating and removing temporary directories for their calculations.

## [0.6.2] - 2024-06-13

### Added

- `try/except` to top-level `compute` function that will append the `.program_output` to the exception if the `get_adapter` function raises an exception.

### Changed

- Modified exception hierarchy to include fewer `**kwarg` arguments, use mostly `args` instead, and fixed issue where some exceptions still didn't have `.program_output` set on them.

## [0.6.1] - 2024-06-10

### Fixed

- `*args` and `**kwargs` passing to parent classes in `AdapterError` and subclasses to fix celery serialization issues in BigChem.

### Changed

- 🚨 Changed `compute` kwarg `collect_wavefunction` to `collect_wfn` to match `BaseAdapter` nomenclature. (Cheating in this breaking change since I don't think this feature is used by outsiders yet...)

## [0.6.0] - 2024-04-23

### Fixed

- Fixed all mypy errors that were previously not raised because `qcio` did not contain a `py.types` file.

### Changed

- Updated to latest `qcio` data structures eliminating `SinglePointOutput`, `OptimizationOutput`, and `ProgramFailure` in favor of a Generic `ProgramOutput` object. Backwards compatibility is maintained by `qcio` so that old `SinglePointOutput`, `OptimizationOutput`, and `ProgramFailure` objects are still accepted in end user code with `FutureWarning` messages.
- `BaseAdapter` is generic over `InputType` and `ResultsType`.
- `ProgramAdapter` is generic over `StructuredInputType` and `ResultsType`.
- Adapters now inherit from these Generic classes and specify compatible types explicitly.
- Updated examples and tests to reflect the new `qcio` data structures nomenclature, emphasizing `pi` for `ProgramInput` and `po` for `ProgramOutput` objects.

## [0.5.5] - 2024-04-12

### Added

- `AttributeError` check to `capture_sys_stdout` so that when running inside celery and `sys.stdout` is `LoggingProxy` object, we can still capture the stdout correctly.

## [0.5.4] - 2024-04-12

### Added

- `try/finally` blocks to `tmpdir` context managers to ensure that temporary directories are always cleaned up and the original `cwd` is restored, even if an exception is raised.
- Properly capture `qcparse` encoder/parser exceptions in `TeraChemAdapter` and raise `qcop.AdapterInputError`.

### Changed

- Moved `self.validate_input(inp_obj)`, `self.program_version(stdout)`, and `self.collect_wfn(...)` inside of `try/except`block in`BaseAdapter.compute()`. This is more correct by catching all possible qcop exceptions and returning a `ProgramFailure` object on the raised exception. This helps eliminate 500 errors in ChemCloud when a user passes an invalid input object to a program adapter or requests a wavefunction from a program that doesn't support it.
- Redefined signature to `collect_wfn` to `collect_wfn() -> Dict[str: Union[str, bytes]]` so that it can run before constructing the `ProgramFailure` object in `BaseAdapter.compute()`.

## [0.5.3] - 2024-04-11

### Added

- `capture_sys_stdout` context manager to capture `stdout` from non-python libraries (e.g., C/C++). This is necessary for processes that do not write to Python's `sys.stdout` object, such as `xtb`.
- `xtb` to developer dependencies and a `xtb` tests to the test suite.

### Changed

- `xtb` does not close file handles correctly so we'd get `OSError: [Errno 24] Too many open files` after running a few hundred jobs. `XTBAdapter` now uses the new `capture_sys_stdout` context manager to capture `stdout`.
- `xtb.program_version` now returns `importlib.metadata('xtb')` because `xtb` incorrectly hardcodes the version in the `__init__.py` file. Issue [here](https://github.com/grimme-lab/xtb-python/issues/108).

## [0.5.2] - 2024-04-10

### Added

- Added `xtb` adapter. `qcengine.get_program` adds almost >1 second of overhead to each call, which makes `xtb` unusable via `qcengine` since a single `xtb` execution make take only ~0.003 seconds.

## [0.5.1] - 2024-03-29

### Changed

- Upgraded to `qcio>=0.8.1` to fix QCElemental behavior that auto-rotates Structures without user consent.
- Modified all example scripts to be standalone without referencing an external `.xyz` file and to use `try/except` statements now that `raise_exc=True` is the default.

### Added

- `py.typed` file to enable type checking in other projects that use `qcop`.

## [0.5.0] - 2024-03-16

### Changed

- Changed default `compute` behavior to `raise_exc=True` instead of `raise_exc=False`.

### Removed

- Non operational placeholder `psi4` integration test.

## [0.4.8] - 2024-01-12

### Added

- `GeometricError` to `qcop.exceptions` module. Without this when `geometric` raised an exception it wouldn't be caught by the `except QCOPBaseError` block in `adapter.compute()` and the `ProgramFailure` object wouldn't be returned to the user. This fixes a 500 error in ChemCloud Server when `geometric` fails to converge and raises an exception (a `geometric` exception) that isn't found by the server.

### Changed

- `QCEngineError` now a subclass of `ExternalProgramError` instead of `QCOPBaseError`.
- `ExternalProgramExecutionError` renamed to `ExternalSubprocessError` to better reflect its purpose.

## [0.4.7] - 2023-09-27

### Changed

- Removed TeraChem input file encoding as this was refactored to the `qcparse` library.
- Updated `qcparse` dependency from `>=0.5.1` to `>=0.5.2` to support the new encoding API.
- Updated `qcio` dependency to reflect the same minimum version as `qcparse`.

## [0.4.6] - 2023-09-22

### Changed

- `adapter.collect_wfn()` now raises `AdapterInputError` rather than `NotImplementedError` if `propagate_wfn=True` is passed. This change allows these errors to be captured by the `except QCOPBaseError as e:` block in `adapter.compute()` so that the `ProgramFailure` object can be returned to the user. This fixes a 500 error in ChemCloud Server when a user passes `propagate_wfn=True` to a program that doesn't support it.

## [0.4.5] - 2023-09-19

### Added

- `README.md` documentation.

### Changed

- Dropped Python version from `^3.8.1` to `3.8`.
- Updated `qcparse` dependency from `>=0.5.0` to `>=0.5.1` to support Python `^3.8` change.

## [0.4.4] - 2023-09-08

### Added

- Added `ProgramFailure` object to `exception.args` in `BaseAdapter.compute()` method so that Celery will correctly serialize the object and pass the `exception.program_failure` object from workers to clients.

### Changed

- Updated `qcio` from `>=0.5.0` to `>=0.6.0`.
- Dropped multiple inheritance on `ExternalProgramExecutionError` by removing `CalledProcessError`. Retained the original attributes.

## [0.4.3] - 2023-09-03

### Fixed

- Extras specification in pyproject.toml so that `qcengine`, `qcelemental`, and `geometric` don't get installed by default but may be optionally installed if compatibility is desired.

## [0.4.2] - 2023-09-02

###

- TeraChem adapter was writing `CalcType.energy` instead of `energy` for `runtype` in `tc.in` file.

## [0.4.1] - 2023-09-02

### Added

- Added a `ProgramFailure` object to all program related exceptions raised by `adapter.compute()`. Now every exception returned from `.compute()` will have the full traceback context and provenance data for error handling. Very helpful so that BigChem can operate on a `raise_exc=True` paradigm to take advantage of python standard failure/retry logic based on exceptions but still return the entire `ProgramFailure` object for returning to end users via ChemCloud.

### Fixed

- `stdout` now gets correctly added to `ProgramFailure` object.

## [0.4.0] - 2023-08-31

### Changed

- Updated pydantic from `v1` -> `v2`.

## [0.3.2] - 2023-08-18

### Added

- `GeometricEngine` now appends all computed trajectory results to the raised exception if subprogram crashes so a user can inspect the failed results.

## [0.3.1] - 2023-07-19

### Fixed

- Tiny bug in `ensure_geometric` test.

## [0.3.0] - 2023-07-19

### Added

- `GeometricAdapter`
- Added `.collect_wfn` and `.propagate_wfn` methods to adapters to facilitate wavefunction passing for sequential program adapters--like geomeTRIC.

### Changed

- Refactored top level `main.compute()` function to mostly live in `BaseAdapter.compute()`. This makes consumption of adapters by dual program adapters, like `GeometricAdapter`, much cleaner.

## [0.2.0] - 2023-07-17

### Changed

- Updated to flattened `qcio v0.3.0` data models.
- Changed order of args to `compute()` to allow for the same pattern to `compute_args`.

## [0.1.0] - 2023-06-29

### Added

- Core compute capabilities exposed in top-level `compute()` function, including `QCEngine` fallback for programs without a `qcop` adapter.
- Created adapter for TeraChem.
- Exposed general purpose computing for any subprocess with `FileAdaptor`

[unreleased]: https://github.com/coltonbh/qcop/compare/0.9.7...HEAD
[0.9.7]: https://github.com/coltonbh/qcop/releases/tag/0.9.7
[0.9.6]: https://github.com/coltonbh/qcop/releases/tag/0.9.6
[0.9.5]: https://github.com/coltonbh/qcop/releases/tag/0.9.5
[0.9.4]: https://github.com/coltonbh/qcop/releases/tag/0.9.4
[0.9.3]: https://github.com/coltonbh/qcop/releases/tag/0.9.3
[0.9.2]: https://github.com/coltonbh/qcop/releases/tag/0.9.2
[0.9.1]: https://github.com/coltonbh/qcop/releases/tag/0.9.1
[0.9.0]: https://github.com/coltonbh/qcop/releases/tag/0.9.0
[0.8.1]: https://github.com/coltonbh/qcop/releases/tag/0.8.1
[0.8.0]: https://github.com/coltonbh/qcop/releases/tag/0.8.0
[0.7.5]: https://github.com/coltonbh/qcop/releases/tag/0.7.5
[0.7.4]: https://github.com/coltonbh/qcop/releases/tag/0.7.4
[0.7.3]: https://github.com/coltonbh/qcop/releases/tag/0.7.3
[0.7.2]: https://github.com/coltonbh/qcop/releases/tag/0.7.2
[0.7.1]: https://github.com/coltonbh/qcop/releases/tag/0.7.1
[0.7.0]: https://github.com/coltonbh/qcop/releases/tag/0.7.0
[0.6.2]: https://github.com/coltonbh/qcop/releases/tag/0.6.2
[0.6.1]: https://github.com/coltonbh/qcop/releases/tag/0.6.1
[0.6.0]: https://github.com/coltonbh/qcop/releases/tag/0.6.0
[0.5.5]: https://github.com/coltonbh/qcop/releases/tag/0.5.5
[0.5.4]: https://github.com/coltonbh/qcop/releases/tag/0.5.4
[0.5.3]: https://github.com/coltonbh/qcop/releases/tag/0.5.3
[0.5.2]: https://github.com/coltonbh/qcop/releases/tag/0.5.2
[0.5.1]: https://github.com/coltonbh/qcop/releases/tag/0.5.1
[0.5.0]: https://github.com/coltonbh/qcop/releases/tag/0.5.0
[0.4.8]: https://github.com/coltonbh/qcop/releases/tag/0.4.8
[0.4.7]: https://github.com/coltonbh/qcop/releases/tag/0.4.7
[0.4.6]: https://github.com/coltonbh/qcop/releases/tag/0.4.6
[0.4.5]: https://github.com/coltonbh/qcop/releases/tag/0.4.5
[0.4.4]: https://github.com/coltonbh/qcop/releases/tag/0.4.4
[0.4.3]: https://github.com/coltonbh/qcop/releases/tag/0.4.3
[0.4.2]: https://github.com/coltonbh/qcop/releases/tag/0.4.2
[0.4.1]: https://github.com/coltonbh/qcop/releases/tag/0.4.1
[0.4.0]: https://github.com/coltonbh/qcop/releases/tag/0.4.0
[0.3.2]: https://github.com/coltonbh/qcop/releases/tag/0.3.2
[0.3.1]: https://github.com/coltonbh/qcop/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcop/releases/tag/0.3.0
[0.2.0]: https://github.com/coltonbh/qcop/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcop/releases/tag/0.1.0
