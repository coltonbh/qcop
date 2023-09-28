# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

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

[unreleased]: https://github.com/coltonbh/qcop/compare/0.4.6...HEAD
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
