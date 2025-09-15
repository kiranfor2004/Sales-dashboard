"""Legacy helper file kept to avoid recreation side-effects.

Converted into a skipped pytest module so it no longer interferes with test collection
or triggers import file mismatch errors. Original Flask demo app content removed.
"""

import pytest

pytestmark = pytest.mark.skip("Legacy demo file not part of test suite")

def test_legacy_placeholder():
    assert True