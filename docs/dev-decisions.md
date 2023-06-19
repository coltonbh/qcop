# Dev Decisions and Research

## Switching to pydantic v2

- geomeTRIC does not rely up on any QCElemental objects--only a dictionary with the corresponding structure. So I don't loose `geometric_run_json` support if I drop `qcel`.
- `psi4` does use `pydantic` and specifically the `qcel` `ProtoObject` and `pydantic` `validator` in its `driver` code `psi4/driver/task_base.py` and other `psi4/driver/*` files. It's not clear if this code gets executed if you run `psi4` in executable mode rather than python API mode.

## Parsing Output files

- `QChem` requires text parsing, no structured output according to Dip. This leads me to think `tcparse` needs to become `qcparse` and work for more packages.

## Open Questions

- Consider changing signature of `BaseAdaptor.compute` to `def compute(inp_obj: InputBase, **kwargs)` to make things less redundant across adaptors. Loose some clarity, save a bunch of redundancy in specifying a signature over and over again. This caused issues

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push`
- `git push --tags`
