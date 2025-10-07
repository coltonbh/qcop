Calculations are run by calling the `qcop.compute()` function with the relevant arguments and keywords like this:

```python
from qcio import Structure, CalcSpec
from qcop import compute

# Create the Structure
structure = Structure(
    symbols=["O", "H", "H"],
    geometry=[  # type: ignore
        [0.0, 0.0, 0.0],
        [0.52421003, 1.68733646, 0.48074633],
        [1.14668581, -0.45032174, -1.35474466],
    ],
)

# Define the program input
prog_input = CalcSpec(
    structure=h2o,
    calctype="energy",
    model={"method": "hf", "basis": "sto-3g"},
    keywords={"purify": "no", "restricted": False},
)

# Run the calculation; will return ProgramOutput or raise an exception
prog_output = compute("terachem", prog_input, collect_files=True)
```

The `compute` selects the correct program adapter and then calls `adapter.compute()`. The available arguments and keywords for the top level `compute()` function match those shown here:

::: qcop.adapters.BaseAdapter.compute

```

```
