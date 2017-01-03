#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import subprocess
import time
import datetime
import sys

sys.path.append('..')
from lib.logger import logger
from lib import req_sy


class BaseExtractor(object):
    def __init__(self, zhubo):
        if zhubo:
            self._zhubo = zhubo
        self._logger = logger

    def get_html(self, url):
        return req_sy.get_html(url)

    def get_json(self, url):
        return req_sy.get_html(url, is_json=True)

    # 执行phantomjs获取网页内容
    def get_html_by_phantomjs(self, url):
        cmd = 'phantomjs phantomjs/pro_youku.js "%s"' % url
        try:
            print 'cmd:', cmd
            stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            # print 'err:', stderr
        except Exception, e:
            self._logger.error(stderr)
        return stdout

    # 工具函数：将字符串2016-03-19 09:10:25转化为Unix时间戳
    def _str_to_timestamp(self, timestr):
        if timestr is None:
            return int(time.time())
        timearr = time.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        return int(time.mktime(timearr))

    # 根据优酷的视频url地址，解析该视频的vid
    def _extract_vid_from_url(self, url):
        pass

    # 获取前几天对应的日期
    # 2013-02-16
    def _get_pre_n_day(self, n):
        format = "%Y-%m-%d"
        t = time.localtime(int(time.time()) - n * 24 * 3600)
        return time.strftime(format, t)

    # 将视频发布时间进行转换为Unix时间戳
    # 1分钟前,1小时前,昨天 14.26,前天 18:13,
    def _convert_publish_time(self, str):
        # 当前时间
        current_time = int(time.time())
        today = datetime.date.today()
        # 56分钟前,1小时前,8小时前,3天前
        if str.find('前') > 0:
            if str.find('分钟') > 0:
                num = int(str[0:str.find('分钟')])
                return current_time - num * 60
            if str.find('小时') > 0:
                num = int(str[0:str.find('小时')])
                return current_time - num * 60 * 60
            if str.find('天') > 0:
                num = int(str[0:str.find('天')])
                return current_time - num * 60 * 60 * 24
            return current_time
        else:
            time_str = None;
            if str.find('昨天'):
                time_str = self._get_pre_n_day(1)
                m = re.search(r'\d+:\d+', str)
                if m:
                    time_str = '{0} {1}:00'.format(time_str, m.group())
            if str.find('前天'):
                time_str = self._get_pre_n_day(1)
                m = re.search(r'\d+:\d+', str)
                if m:
                    time_str = '{0} {1}:00'.format(time_str, m.group())
            if re.match(r'\d+-\d+-\d+$', str):
                time_str = '{0} 00:00:01'.format(str)
            match_obj = re.match(r'(\d+)-\d+\s\d+:\d+:\d+$', str)
            if match_obj:
	        t_month = int(match_obj.group(1))
                time_str = '{0}-{1}'.format(t_month > today.month and today.year-1 or today.year, str)
            match_obj = re.match(r'(\d+)-\d+\s\d+:\d+$', str)
            if match_obj:
		t_month = int(match_obj.group(1))
                time_str = '{0}-{1}:00'.format(t_month>today.month and today.year-1 or today.year, str)
            if re.match(r'\d+-\d+-\d+\s\d+:\d+:\d+$', str):
                time_str = str
            return self._str_to_timestamp(time_str)

    # 将视频时长转换为数字形式
    # 20:35 => 1235.00
    def _convert_video_time(self, str):
        arr = str.split(':')
        totle_time = 0
        for t in arr:
            totle_time = totle_time * 60 + int(t)
        return totle_time

    # 将视频观看数转换为数字形式
    # from 5,343 => 5343
    # from 2.4万 => 24000
    # 特殊情况 1,012万
    def _convert_video_num(self, str):
        if str.find(',') > 0 and str.find('万') > 0:
            pre_num = str[0:str.find('万')]
            pre_num = int(''.join(str.split(',')))
            return pre_num * 10000
        if str.find(',') > 0:
            return int(''.join(str.split(',')))
        if str.find('万') > 0:
            return int(float(str[0:str.find('万')]) * 10000);
        return int(str);



