## imports

# standard
import importlib.metadata

# local
from .refresh import *
from .volumes import *
from .configuration import *


## constants

try:
    __version__ = importlib.metadata.version("modal-utilities")
except:
    __version__ = "unknown"
