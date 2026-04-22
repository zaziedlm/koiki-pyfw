import os
import sys


LIBKOIKI_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

if LIBKOIKI_SRC not in sys.path:
    sys.path.insert(0, LIBKOIKI_SRC)
