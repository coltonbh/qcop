import pytest
from qcio.models.single_point import SPCalcType

from qcop.adapters import base, registry
from qcop.exceptions import UnsupportedCalcTypeError


def test_adapter_subclasses_must_define_program():
    """Test that subclasses of QCOPProgramAdapter must define a nonempty
    program list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.QCOPProgramAdapter):
            # supported_calc_types defined but program not defined
            supported_calc_types = [SPCalcType.energy]

            def _compute(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_supported_calc_types():
    """Test that subclasses of QCOPSinglePointAdapter must define a nonempty
    supported_calc_types list."""
    with pytest.raises(NotImplementedError):

        class TestAdapter(base.QCOPSinglePointAdapter):
            # program defined but supported_calc_types not defined
            program = "test"

            def _compute(self, *args, **kwargs):
                pass


def test_adapter_subclasses_must_define_compute_method():
    """Test that subclasses of QCOPProgramAdapter defining a nonempty program
    list and supported_calc_types list can be instantiated."""

    class TestAdapter(base.QCOPProgramAdapter):
        # Both program and supported_calc_types defined
        program = "test"
        supported_calc_types = [SPCalcType.energy]

    with pytest.raises(TypeError):
        TestAdapter()


def test_adapter_subclasses_defining_program_and_supported_calc_types():
    """Test that subclasses of QCOPProgramAdapter defining a nonempty program
    list and supported_calc_types list can be instantiated."""

    class TestAdapter(base.QCOPProgramAdapter):
        # Both program and supported_calc_types defined
        program = "test"
        supported_calc_types = [SPCalcType.energy]

        def _compute(self, *args, **kwargs):
            pass

    assert registry.get("test") == TestAdapter


def test_single_point_subclasses_raise_error_if_calc_type_not_supported(sp_input):
    """Test that subclasses of QCOPSinglePointAdapter raise an error if the
    calc_type is not supported."""

    class TestAdapter(base.QCOPSinglePointAdapter):
        # Both program and supported_calc_types defined
        program = "test"
        supported_calc_types = [SPCalcType.energy]

        def program_version(self, *args, **kwargs) -> str:
            return "v1.0.0"

        def _compute(self, *args, **kwargs):
            pass

    gradient_input = sp_input("gradient")
    with pytest.raises(UnsupportedCalcTypeError):
        TestAdapter().compute(gradient_input, None, None)
