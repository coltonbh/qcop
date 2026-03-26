from importlib import metadata as _metadata

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:
    # Source tree / build hook / CI checkout
    __version__ = "0.0.0+local"

from .main import compute, compute_args  # noqa: F401
from .utils import get_adapter  # noqa: F401
