# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
from importlib import metadata

from .main import compute, compute_args  # noqa: F401
from .utils import get_adapter  # noqa: F401

__version__ = metadata.version(__name__)
