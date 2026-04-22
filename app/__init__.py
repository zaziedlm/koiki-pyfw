from pathlib import Path
from pkgutil import extend_path
import sys

__path__ = extend_path(__path__, __name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
KOIKI_REF_APP_SRC = REPO_ROOT / "components" / "koiki_ref_app" / "src"
KOIKI_REF_APP_PACKAGE = KOIKI_REF_APP_SRC / "koiki_ref_app"
LIBKOIKI_SRC = REPO_ROOT / "components" / "libkoiki" / "src"

for path in (KOIKI_REF_APP_SRC, LIBKOIKI_SRC):
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)

if KOIKI_REF_APP_PACKAGE.exists():
    __path__.append(str(KOIKI_REF_APP_PACKAGE))

