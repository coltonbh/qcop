# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

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

- Upgraded to `qcio>=0.8.1` to fix QCElemental behavior that auto-rotates Molecules without user consent.
- Modified all example scripts to be standalone without referencing an external `.xyz` file and to use `try/except` statements now that `raise_exc=True` is the default.

### Added

- `py.typed` file to enable type checking in other projects that use `qcop`.

## [0.5.0] - 2024-03-16

### Changed

- Changed default `compute` behavior to `raise_exc=True` instead of `raise_exc=False`.

### Removed

- Non operational placeholder `psi4` integration test.

## [0.4.8] - 2024-01-12

### Changed

- `QCEngineError` now a subclass of `ExternalProgramError` instead of `QCOPBaseError`.
- `ExternalProgramExecutionError` renamed to `ExternalSubprocessError` to better reflect its purpose.

### Added

- `GeometricError` to `qcop.exceptions` module. Without this when `geometric` raised an exception it wouldn't be caught by the `except QCOPBaseError` block in `adapter.compute()` and the `ProgramFailure` object wouldn't be returned to the user. This fixes a 500 error in ChemCloud Server when `geometric` fails to converge and raises an exception (a `geometric` exception) that isn't found by the server.

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

### Changed

- Updated `qcio` from `>=0.5.0` to `>=0.6.0`.
- Dropped multiple inheritance on `ExternalProgramExecutionError` by removing `CalledProcessError`. Retained the original attributes.

### Added

- Added `ProgramFailure` object to `exception.args` in `BaseAdapter.compute()` method so that Celery will correctly serialize the object and pass the `exception.program_failure` object from workers to clients.

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

### Addedp

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

[unreleased]: https://github.com/coltonbh/qcop/compare/0.5.3...HEAD
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
