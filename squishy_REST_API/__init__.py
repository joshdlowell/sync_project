__version__ = "1.0.0"
from .configuration import config, logger
from .app_factory import RESTAPIFactory

__all__ = ['config', 'logger', 'RESTAPIFactory']