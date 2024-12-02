# read version from installed package
from importlib.metadata import version
__version__ = version("m203mylibrary")

#from .m203mylibrary import test_function