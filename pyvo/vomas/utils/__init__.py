import sys, os
from pyvo.vomas.utils.logger_setup import LoggerSetup

logger = LoggerSetup.get_logger()
LoggerSetup.set_debug_level()

logger.info("utils package initialized")
