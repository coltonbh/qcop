import pytest
from qcio import CalcType, Results

from qcop.adapters import base, registry
from qcop.exceptions import AdapterInputError, ExternalProgramError


def test_adapter_subclasses_must_define_program():
    """Test that subclasses of QCOPProgramAdapter must define a nonempty
    program list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # supported_calctypes defined but program not defined
            supported_calctypes = [CalcType.energy]

            def compute_data(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_supported_calctypes():
    """Test that subclasses of QCOPSinglePointAdapter must define a nonempty
    supported_calctypes list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # program defined but supported_calctypes not defined
            program = "test"

            def compute_data(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_compute_method():
    """Test that subclasses of QCOPProgramAdapter defining a nonempty program
    list and supported_calctypes list can be instantiated."""

    class TestAdapter(base.ProgramAdapter):
        # Both program and supported_calctypes defined
        program = "test"
        supported_calctypes = [CalcType.energy]

    with pytest.raises(TypeError):
        TestAdapter()


def test_adapter_subclasses_defining_program_and_supported_calctypes():
    """Test that subclasses of QCOPProgramAdapter defining a nonempty program
    list and supported_calctypes list can be instantiated."""

    class TestAdapter(base.ProgramAdapter):
        # Both program and supported_calctypes defined
        program = "test"
        supported_calctypes = [CalcType.energy]

        def compute_data(self, *args, **kwargs):
            pass

    assert registry.get("test") == TestAdapter


def test_adapters_raise_error_if_calctype_not_supported(calcspec):
    """Test that adapters raise an error if the calctype is not supported."""

    class TestAdapter(base.ProgramAdapter):
        # Both program and supported_calctypes defined
        program = "test"
        supported_calctypes = [CalcType.energy]

        def program_version(self, *args, **kwargs) -> str:
            return "v1.0.0"

        def compute_data(self, *args, **kwargs):
            pass

    gradient_input = calcspec("gradient")
    with pytest.raises(AdapterInputError):
        TestAdapter().compute(gradient_input)


def test_results_added_to_program_output_object_if_exception_contains_them(
    calcspec, mocker, results, test_adapter
):
    """Test that results are added to the Results object if the exception
    contains them."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramError(
            program="terachem", logs="some stdout", results=results.data
        )

    mocker.patch.object(
        test_adapter,
        "compute_data",
        side_effect=raise_error,
    )
    energy_input = calcspec("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)
    assert excinfo.value.results == results.data

    # If no raise_exc=False, the results are added to the Results
    prog_failure = test_adapter.compute(energy_input, raise_exc=False)
    assert isinstance(prog_failure, Results)
    assert prog_failure.data == results.data


def test_program_output_object_added_to_exception(
    calcspec, mocker, results, test_adapter
):
    """Test that exceptions contain the Results object."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramError(
            program="terachem",
            logs="some stdout",
            results=results.data,
        )

    mocker.patch.object(
        test_adapter,
        "compute_data",
        side_effect=raise_error,
    )
    energy_input = calcspec("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)

    assert isinstance(excinfo.value.program_output, Results)
    assert excinfo.value.program_output.success is False
    # NOTE: CHECK WITH BIGCHEM
    # assert isinstance(excinfo.value.args[-1], Results)


def test_stdout_collected_with_failed_execution(
    calcspec, mocker, results, test_adapter
):
    """Test that stdout is collected even if the execution fails."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramError(
            program="terachem",
            logs="some stdout",
            results=results.data,
        )

    mocker.patch.object(
        test_adapter,
        "compute_data",
        side_effect=raise_error,
    )
    energy_input = calcspec("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)

    # Added to exception
    assert excinfo.value.logs == "some stdout"
    # Added to Results
    assert excinfo.value.program_output.logs == "some stdout"
    # Added to exception
    assert excinfo.value.results == results.data


def test_collect_wfn_raises_adapter_input_error_if_not_implemented(test_adapter):
    """Test that collect_wfn raises an AdapterInputError if not implemented."""
    with pytest.raises(AdapterInputError):
        test_adapter.collect_wfn()
