# Dev Decisions and Research

## Exception Handing

- In ChemCloud, I need to construct the `ProgramOutput` object to return to users when calculations fail. This is not possible outside of the `qcop` stack because the exception will not contain the required `input_data` object, nor can I construct the `Provenance` object from the exception data because I am missing the `program` name, I could construct the `traceback` string from the exception itself (raised by `bigchem`). So I decided in the `BaseAdapter.compute()` method to construct the `ProgramOutput` object even if `raise_exc=True` and then add it to the raised exception at `exc.program_output`. This way I can choose whether to raise exceptions or not but still capture all information available about a calculation for later debugging. Not having this option in QCEngine was often annoying because I'd prefer to raise exceptions but then I'd be missing critical data for debugging.

## Open Questions

- Consider changing signature of `BaseAdaptor.compute` to `def compute(inp_obj: InputBase, **kwargs)` to make things less redundant across adaptors. Loose some clarity, save a bunch of redundancy in specifying a signature over and over again. This caused issues.
  - Actually, I think what I need to do is

## Future Work

- Could avoid creating temporary directories for adapters that do not use disk. Could set `AdapterBase.disk = False` and then skip the `with tmpdir(...)` block in `BaseAdapter.compute()`. This would save at most < a few milliseconds per calculation. Not critical. _Might_ be useful for super fast calls like `xtb` or `rdkit` on super small structures?
- I think I need a generic wrapper for capturing stdout logs from subprograms, `xtb`-like programs, `geomeTRIC`, etc. and then work with the object in the `BaseAdapter.compute()` level with the `update_func` rather than passing this all the way down the stack, which is messy and each program requires log capture in different ways. Starting a `Thread` only adds about `0.0002` seconds of overhead (on my laptop). Something like this (basically copy logic from `execute_subprocess` into `BaseAdapter.compute()`):

```python
with capture_logs(...) as logs_io:
    # Run the program in a thread
    thread = Thread(target=adapter.compute_results, args=(...)).start()
    # Asynchronously run update_func on the logs_io (likely StringIO) object.
    while thread.is_alive():
        # Run update_func logic
        update_func(logs_io)
    # Continue with the rest of the calculation
```

- Because the numpy arrays (e.g., `Structure.geometry` or `SinglePointResults.hessian`) are only typeable down to `np.typing.NDarray[dtype]` their shapes cannot be statically type checked. For importantly, because SinglePointResults.results is `Optional` and so are the `.energy`, `.gradient.` and `.hessian` values, I have to add assert statements like this to make this code type safe. I may want to consider using Generics or TypeVars to make this more type safe by having `SinglePointResult` be generic over the type of results it contains to guarantee that the results are not `None` and that the values are not `None`. For now I'll live with the assert statements and the `SinglePointResult`/`ProgramOutput` validators to guarantee the data is correct. Going with `# type: ignore` for now since I know these values will exist due to `Pydantic` validation.

  ```python
  for i, (forward, backward) in enumerate(zip_longest(*[iter(gradients)] * 2)):
      assert forward.results is not None, "Missing results object"  # mypy
      assert backward.results is not None, "Missing results object"  # mypy
      assert forward.results.gradient is not None, "Missing gradient value"  # mypy
      assert backward.results.gradient is not None, "Missing gradient value"  # mypy
      val = (forward.results.gradient - backward.results.gradient) / (dh * 2)
      hessian[i] = val.flatten()
  ```

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push`
- `git push --tags`
