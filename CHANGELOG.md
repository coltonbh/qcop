# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Added

- `GeometricEngine` now appends all computed trajectory results to the raised exception if subprogram crashes so a user can inspect the failed results.

## [0.3.0]

### Fixed

- Tiny bug in `ensure_geometric` test.

## [0.3.0]

### Added

- `GeometricAdapter`
- Added `.collect_wfn` and `.propagate_wfn` methods to adapters to facilitate wavefunction passing for sequential program adapters--like geomeTRIC.

### Changed

- Refactored top level `main.compute()` function to mostly live in `BaseAdapter.compute()`. This makes consumption of adapters by dual program adapters, like `GeometricAdapter`, much cleaner.

## [0.2.0]

### Changed

- Updated to flattened `qcio v0.3.0` data models.
- Changed order of args to `compute()` to allow for the same pattern to `compute_args`.

## [0.1.0]

### Added

- Core compute capabilities exposed in top-level `compute()` function, including `QCEngine` fallback for programs without a `qcop` adapter.
- Created adapter for TeraChem.
- Exposed general purpose computing for any subprocess with `FileAdaptor`

[unreleased]: https://github.com/coltonbh/qcop/compare/0.3.1...HEAD
[0.3.1]: https://github.com/coltonbh/qcop/releases/tag/0.3.1
[0.3.0]: https://github.com/coltonbh/qcop/releases/tag/0.3.0
[0.2.0]: https://github.com/coltonbh/qcop/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcop/releases/tag/0.1.0
