# Contributing

## Running Test

- Run all tests (except integration test). See coverage report afterwards by opening `htmlcov/index.html`

```sh
bash scripts/tests.sh
```

- To run integration test:

```sh
pytest -m integration
```

- To run all tests + integration tests (skipping those where `program` is not installed)

```sh
pytest -m 'not not_integration'
```
