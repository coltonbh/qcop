The QCEngine Adapter enables calculations using all [QCEngine supported programs](https://molssi.github.io/QCEngine/program_overview.html). This engine is used as a fallback for when `qccompute` does not have an `Adapter` of its own for a given program. Using QCEngine as a fallback can be deactivated by passing `qcng_fallback=False` to `qccompute.compute()`.

::: qccompute.adapters.qcengine.QCEngineAdapter
