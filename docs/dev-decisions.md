# Dev Decisions and Research

## Exception Handing

- When using BigChem I want to always call `compute(..., raise_exc=True)` so that if a task fails (e.g., alone or in a group/chain) I want to be able to use Celery's default retry logic and not have celery execute subsequent chained tasks because it knows an exception was raised. This is much cleaner than what I did with QCEngine where I had checks for `FailedOperation` objects in each BigChem task. This means that if a calculation fails, BigChem will not return `ProgramFailure` objects, but rather will just raise an exception when `future_result.get()` is called. In ChemCloud, I need to construct the `ProgramFailure` object to return to users. This is not possible outside of the `qcop` stack because the exception will not contain the required `input_data` object, nor can I construct the `Provenance` object from the exception data, nor the `traceback` string outside of the context of the exception itself. So I decided in the `BaseAdapter.compute()` method to construct the `ProgramFailure` object even if `raise_exc=True` and then add it to the raised exception at `exc.program_failure`. This way I can choose whether to raise exceptions or not but still capture all information available about a calculation for later debugging. Not having this option in QCEngine was often annoying because I'd prefer to raise exceptions but then I'd be missing critical data for debugging.

## Open Questions

- Consider changing signature of `BaseAdaptor.compute` to `def compute(inp_obj: InputBase, **kwargs)` to make things less redundant across adaptors. Loose some clarity, save a bunch of redundancy in specifying a signature over and over again. This caused issues.

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push`
- `git push --tags`
