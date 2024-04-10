"""Must import all adapters here for them to be found by the AdapterRegistry."""

from .base import *  # noqa: F403
from .file import FileAdapter  # noqa: F401
from .geometric import GeometricAdapter  # noqa: F401
from .qcengine import QCEngineAdapter  # noqa: F401
from .terachem import TeraChemAdapter  # noqa: F401
from .xtb import XTBAdapter  # noqa: F401
