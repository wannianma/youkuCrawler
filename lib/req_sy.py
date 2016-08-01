#-*-coding:utf-8-*-
#!/usr/bin/python

#
# Send Email with Content Log
#

'GET HTML CONTENT'

import gevent
from gevent import monkey
monkey.patch_all()

import urllib2
import config
import requests
from logger import logger
import logging
import random

# disable Requests log messages
logging.getLogger("requests").setLevel(logging.WARNING)

def get_html(url, is_json = False, connect_time = 0):
    html = ''
    res_code = 200
    try:
        res_code, html = _fetch_html_by_requests(url, is_json)
        if res_code == 200:
           return html
    except Exception, e:
        print Exception, e
        logger.error("%s | %s" % (e, url))

    return html

def get_html_2(url, is_json = False, allow_redirects=False, connect_time = 0):
    html = ''
    res_code = 200
    try:
        res_code, html = _fetch_html_by_requests(url, is_json, allow_redirects)
        return res_code, html
    except Exception, e:
        logger.error("%s | %s" % (e, url))
        reconnect_time = config.CONNECT_TIME
        if(connect_time < reconnect_time):
            # 暂停五秒
            logger.error('stop '+str(reconnect_time)+' seconds, reconnect! ' + url)
            gevent.sleep(reconnect_time)
            connect_time = connect_time + 1
            get_html(url, is_json, connect_time)
        else:
            logger.error(u'连接次数:'+str(reconnect_time)+u',退出! ' + url)
            return ''

    return res_code, html
def _fetch_html_by_proxy(url, is_json=False, timeout=None, headers={}, user_agent=None):
    timeout = timeout or config.TIMEOUT
    headers = headers or config.HEADERS
    headers["user-agent"] = user_agent or config.USER_AGENT
    http_proxies = config.HTTP_PROXIES
    proxy = random.choice(http_proxies)
    proxies = {"http":"http://" + proxy}
    s = requests.Session()
    with gevent.Timeout(config.TIMEOUT, Exception):
        r = s.get(url, timeout=timeout, headers=headers, proxies=proxies)
    if is_json:
        return r.status_code, r.json()
    
    return r.status_code, r.content
# 通过urllib2获取HTML页面
# def _fetch_html_by_urllib(url, timeout=None):
#     timeout = timeout or config.TIMEOUT
#     page = urllib2.urlopen(url, timeout=timeout)
#     if page != '':
#         return 200, page.read()
#     else:
#         return 404, page.read()

# 通过requests包获取HTML页面
def _fetch_html_by_requests(url, is_json=False, allow_redirects=True, timeout=None, headers={}, cookies={}, proxy={}, 
        stream=False, verify=False, user_agent=None, **kw):
    r = None
    status_code = 404
    return_content = ''
    timeout = timeout or config.TIMEOUT
    headers = headers or config.HEADERS
    headers["user-agent"] = user_agent or config.USER_AGENT

    try:
        r = requests.get(url, headers = headers)
        if r and r.status_code == 200:
            status_code = r.status_code
            if is_json:
                return_content = r.json()
            else:
                return_content = r.content
            return status_code, return_content
    except Exception, e:
        print Exception, e
        logger.error("%s | %s" % (e, r))
    return status_code, return_content
    

def run(url):
    print(get_html(url))

if __name__ == "__main__":
    run('http://www.douyutv.com/directory/isgame')
