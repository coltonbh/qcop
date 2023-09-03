import pytest
from qcio import CalcType, ProgramFailure

from qcop.adapters import base, registry
from qcop.exceptions import AdapterInputError, ExternalProgramExecutionError


def test_adapter_subclasses_must_define_program():
    """Test that subclasses of QCOPProgramAdapter must define a nonempty
    program list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # supported_calctypes defined but program not defined
            supported_calctypes = [CalcType.energy]

            def compute_results(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_supported_calctypes():
    """Test that subclasses of QCOPSinglePointAdapter must define a nonempty
    supported_calctypes list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # program defined but supported_calctypes not defined
            program = "test"

            def compute_results(self, *args, **kwargs):
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

        def compute_results(self, *args, **kwargs):
            pass

    assert registry.get("test") == TestAdapter


def test_adapters_raise_error_if_calctype_not_supported(prog_inp):
    """Test that adapters raise an error if the calctype is not supported."""

    class TestAdapter(base.ProgramAdapter):
        # Both program and supported_calctypes defined
        program = "test"
        supported_calctypes = [CalcType.energy]

        def program_version(self, *args, **kwargs) -> str:
            return "v1.0.0"

        def compute_results(self, *args, **kwargs):
            pass

    gradient_input = prog_inp("gradient")
    with pytest.raises(AdapterInputError):
        TestAdapter().compute(gradient_input)


def test_results_added_to_program_failure_object_if_exception_contains_them(
    prog_inp, mocker, sp_output, test_adapter
):
    """Test that results are added to the ProgramFailure object if the exception
    contains them."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramExecutionError(
            1,
            "terachem tc.in",
            stdout="some stdout",
            results=sp_output.results,
        )

    mocker.patch.object(
        test_adapter,
        "compute_results",
        side_effect=raise_error,
    )
    energy_input = prog_inp("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramExecutionError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)
    assert excinfo.value.results == sp_output.results

    # If no raise_exc=False, the results are added to the ProgramFailure
    prog_failure = test_adapter.compute(energy_input)
    assert isinstance(prog_failure, ProgramFailure)
    assert prog_failure.results == sp_output.results


def test_program_failure_object_added_to_exception(
    prog_inp, mocker, sp_output, test_adapter
):
    """Test that exceptions contain the ProgramFailure object."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramExecutionError(
            1,
            "terachem tc.in",
            stdout="some stdout",
            results=sp_output.results,
        )

    mocker.patch.object(
        test_adapter,
        "compute_results",
        side_effect=raise_error,
    )
    energy_input = prog_inp("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramExecutionError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)

    assert isinstance(excinfo.value.program_failure, ProgramFailure)


def test_stdout_collected_with_failed_execution(
    prog_inp, mocker, sp_output, test_adapter
):
    """Test that stdout is collected even if the execution fails."""
    test_adapter = registry["test"]()

    def raise_error(*args, **kwargs):
        raise ExternalProgramExecutionError(
            1,
            "terachem tc.in",
            stdout="some stdout",
            results=sp_output.results,
        )

    mocker.patch.object(
        test_adapter,
        "compute_results",
        side_effect=raise_error,
    )
    energy_input = prog_inp("energy")

    # Check that the exception object contains the results
    with pytest.raises(ExternalProgramExecutionError) as excinfo:
        test_adapter.compute(energy_input, raise_exc=True)

    # Added to exception
    assert excinfo.value.stdout == "some stdout"
    # Added to ProgramFailure
    assert excinfo.value.program_failure.stdout == "some stdout"
