import logging


logger = logging.getLogger("wechat_django")


getLogger = logger.getChild
debug = logger.debug
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception
