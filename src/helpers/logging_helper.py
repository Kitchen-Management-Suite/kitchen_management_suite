"""
File: logging_helper.py
File-Path: src/helpers/logging_helper.py
Author: Thomas Bruce
Date-Created: 11-04-2025

Description:
    simple logging helper for application events

Inputs:
    log messages and context

Outputs:
    formatted log entries to stdout
"""

import logging
import sys
from flask import request

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def setup_logger(name: str = 'app', level: int = logging.INFO) -> logging.Logger:
    """sets up a basic logger"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    
    return logger


logger = setup_logger('auth')


def get_client_ip() -> str:
    """gets client ip from request"""
    if request:
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.remote_addr:
            return request.remote_addr
    return 'unknown'


def log_auth(message: str, level: str = 'info'):
    """
    logs auth-related events
    
    Args:
        message: message to log
        level: log level ('info', 'warning', 'error')
    """
    ip = get_client_ip()
    msg = f"{message} | IP: {ip}"
    
    if level == 'error':
        logger.error(msg)
    elif level == 'warning':
        logger.warning(msg)
    else:
        logger.info(msg)

