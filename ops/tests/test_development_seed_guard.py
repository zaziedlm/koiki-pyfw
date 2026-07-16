import pytest

from ops.scripts.setup_security import ensure_development_seed_environment


def test_development_seed_allows_only_isolated_environments():
    ensure_development_seed_environment("development")
    ensure_development_seed_environment("testing")

    with pytest.raises(RuntimeError, match="Development/E2E users"):
        ensure_development_seed_environment("production")
