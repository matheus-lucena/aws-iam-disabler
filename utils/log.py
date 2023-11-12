import sys
import logging


class Log:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(module)s:%(message)s')
        logging.StreamHandler(sys.stdout)

    def get_logger(self, name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        return logger
