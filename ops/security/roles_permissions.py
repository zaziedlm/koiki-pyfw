"""Compatibility exports for reference role and permission definitions.

The definitions are owned by ``koiki_ref_app.bootstrap.reference_seed``.
Fixed-password development users are intentionally not exported here; they live
in ``ops.security.dev_users``.
"""

from koiki_ref_app.bootstrap.reference_seed import (
    REFERENCE_PERMISSIONS as BASIC_PERMISSIONS,
)
from koiki_ref_app.bootstrap.reference_seed import REFERENCE_ROLES as BASIC_ROLES

__all__ = ["BASIC_PERMISSIONS", "BASIC_ROLES"]
