The `File Input` can be used as an escape hatch when you want to perform a calculation type that is not yet supported by `qccompute` or use a program not yet supported by `qccompute`. You can submit the program's native input files to the program and `qccompute` will execute the program, collect all the outputs, and return them to you. These calculations could be an MD run, some unique calculation type not supported by `qccompute`, or any arbitrary command you can send to any command-line executable program.

```python
{!examples/file_input.py!}
```
