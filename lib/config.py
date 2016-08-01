#!/usr/bin/python
#coding = utf-8

# Email config
EMAIL_FROM = '###'
EMAIL_PASSWORD = '###'
EMAIL_TO = '###'
EMAIL_SMTP_SERVER = 'smtp.163.com'
EMAIL_CHARSET = 'utf-8'
EMAIL_PORT = 25

#logger config
LOG_NAME = 'video_youku'
BASIC_LOG_PATH = '/data/crawler/log/'
LOG_FILENAME = 'video_youku_crawler.log'

#mysql config
DB_HOST = ''
DB_USER = ''
DB_PASSWD = ''
DB_CHARSET = 'utf8'
DB_NAME = 'shenyou'
DB_TABLE = 'sy_zhibo'
DB_TABLE_TOUTIAO = 'sy_news'
DB_TABLE_TOUTIAO_DATA = 'sy_news_data'
DB_TABLE_VIDEO_DATA = 'sy_video_data'
DB_TABLE_VIDEO = 'sy_video'
DB_TABLE_PICTURE_DATA = 'sy_picture_data'
DB_TABLE_PICTURE = 'sy_picture'
DB_TABLE_ANCHOR = 'sy_anchor'

#gevent and requests config
GPOOLSIZE = 10
TIMEOUT = 5
HEADERS = {'Referer':'http://i.youku.com/i/UNTU1Mzg3Mzk2'}
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
CONNECT_TIME = 1

# Youku video
YOUKU_UPDATE_PERIOD = 3600*12
YOUKU_CLIENT_ID = '5af6a7d8274a36e8'

#worker config
INTERVAL = 1

#proxy config
PROXY_EXPIRETIME = 10

IGNORE_SUFFIXES = set(['.jpg', '.jpeg', '.png', '.gif', '.pdf'])
