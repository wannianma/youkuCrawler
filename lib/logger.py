#!/usr/bin/env python
#coding=utf-8

import config
import logging
from logging.handlers import TimedRotatingFileHandler

loggerName = config.LOG_NAME
basic_log_path = config.BASIC_LOG_PATH
filename = config.LOG_FILENAME
logfile = '%s/%s' % (basic_log_path, filename)

formatter = logging.Formatter(
    '%(asctime)s # %(filename)s # %(levelname)s - %(message)s')
# 写入日志文件
fileTimeHandler = TimedRotatingFileHandler(logfile, "H", 1)
fileTimeHandler.suffix = "%Y%m%d-%H.log"
fileTimeHandler.setFormatter(formatter)
fileTimeHandler.setLevel(logging.INFO)

# 创建一个handler，输出到控制台
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(loggerName)
logger.addHandler(fileTimeHandler)
logger.addHandler(ch)
logger.propagate = False
