#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/7/23 18:04  

import json,os
import logging.config

def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
            logging.config.dictConfig(config)
            print 'ok'
    else:
        logging.basicConfig(level=default_level)
        print '..'

setup_logging()


import logging
logger = logging.getLogger(__name__)

logger.info('log config successed!')