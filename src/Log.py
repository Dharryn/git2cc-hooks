#!/usr/bin/env python

"""
@summary: This module provides logging methods.

"""

import logging
import logging.handlers

LOG_FILENAME = "/tmp/Git2CC.log"

LOG_FORMATTER = '%(asctime)s %(levelname)-8s %(message)s'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# define a Handler which writes INFO messages or higher to the sys.stderr
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMATTER)
handler.setFormatter(formatter)
logger.addHandler(handler)

# create error file handler and set level to error

handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOG_FORMATTER)
handler.setFormatter(formatter)
logger.addHandler(handler)

def debug (comment):
    """
    Logs a debug trace.

    """
    logger.debug(comment)


def error (comment):
    """
    Logs a debug trace.

    """
    logger.error(comment)

def info (comment):
    """
    Logs a debug trace.

    """
    logger.info(comment)

def warning (comment):
    """
    Logs a debug trace.

    """
    logger.warning(comment)

def critical (comment):
    """
    Logs a debug trace.

    """
    logger.critical(comment)


    
