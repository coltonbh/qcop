import pytest

from tests.conftest import skipif_program_not_available


@pytest.mark.integration
@skipif_program_not_available("psi4")
def test_integration_with_psi4():
    # your test code here...
    assert False
