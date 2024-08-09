!!! danger
    Solvation using CREST's new default runtime, `tblite`, is current buggy. For details see [this issue](https://github.com/crest-lab/crest/issues/312). According to [this comment](https://github.com/crest-lab/crest/issues/329#issuecomment-2275971685) only `gfnff` and `gfn0` work correctly with either `alpb` or `gbsa` solvent option. If you want to use solvation you need to use the `--legacy` mode which uses `xtb` instead of `tblite` for the calculation backend. Some progress is being made on this issue in [this PR](https://github.com/tblite/tblite/pull/142).

::: qcop.adapters.crest.CRESTAdapter
