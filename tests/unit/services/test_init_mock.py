"""Minimal test to verify test infrastructure works"""

import pytest


@pytest.mark.unit
def test_imports():
    """Test that basic imports work"""
    assert True


@pytest.mark.unit
def test_fixtures_available(sample_product, sample_session_id):
    """Test that fixtures are available"""
    assert sample_product is not None
    assert sample_session_id is not None
    assert "id" in sample_product
