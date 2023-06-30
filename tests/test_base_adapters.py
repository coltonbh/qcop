import pytest
from qcio import CalcType

from qcop.adapters import base, registry
from qcop.exceptions import UnsupportedCalcTypeError


def test_adapter_subclasses_must_define_program():
    """Test that subclasses of QCOPProgramAdapter must define a nonempty
    program list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # supported_calctypes defined but program not defined
            supported_calctypes = [CalcType.energy]

            def _compute(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_supported_calctypes():
    """Test that subclasses of QCOPSinglePointAdapter must define a nonempty
    supported_calctypes list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.ProgramAdapter):
            # program defined but supported_calctypes not defined
            program = "test"

            def _compute(self, *args, **kwargs):
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

        def _compute(self, *args, **kwargs):
            pass

    assert registry.get("test") == TestAdapter


def test_single_point_subclasses_raise_error_if_calctype_not_supported(sp_input):
    """Test that subclasses of QCOPSinglePointAdapter raise an error if the
    calctype is not supported."""

    class TestAdapter(base.ProgramAdapter):
        # Both program and supported_calctypes defined
        program = "test"
        supported_calctypes = [CalcType.energy]

        def program_version(self, *args, **kwargs) -> str:
            return "v1.0.0"

        def _compute(self, *args, **kwargs):
            pass

    gradient_input = sp_input("gradient")
    with pytest.raises(UnsupportedCalcTypeError):
        TestAdapter().compute(gradient_input, None, None)
