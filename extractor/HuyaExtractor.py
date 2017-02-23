#!/usr/bin/env python
# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from BaseExtractor import BaseExtractor
import re

class HuyaExtractor(BaseExtractor):
    def __init__(self, zhubo):
        super(HuyaExtractor, self).__init__(zhubo)

    # 虎牙列表单页面处理
    def get_single_list(self, channel_url, is_all=False):
        self._logger.info('url:{0}'.format(channel_url))
        v_list = None
        # 下一页地址
        next_page_url = None
        html = self.get_html(channel_url)
        if html.strip() != '':
            soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
	    # 获取下一页地址
            next_page = soup.find(class_='uiPaging-next')
            if not next_page is None and not next_page.a is None:
                next_page_url = next_page.a['href']
            # 判断页面所用模板
            if not soup.find(class_='video-list fltL') is None:
                items_list = soup.find(class_='video-list fltL').find_all('li')
                v_list = self._extract_videos_by_4_col(items_list)
        	# 对v_list数据进行组装
        	for video in v_list:
            	    try:
                	video['vid'] = self._extract_vid_from_url(video['link'])
                	video['time'] = self._convert_video_time(video['time'])
                	video['publish_time'] = self._convert_publish_time(video['publish_time'])
                	video['num'] = self._convert_video_num(video['num'])
                	# TODO 提取视频标题中关键词
                	video['keyword'] = ''
            	    except Exception, e:
                	self._logger.error(e)
                	continue
        return v_list, next_page_url

    def _extract_videos_by_4_col(self, items_list):
        v_list = []
        for item in items_list:
            info = {}
            try:
                v_link = item.a
                # 提取视频地址
                info['link'] = v_link['href']
                # 提取视频title
                info['title'] = v_link['title']
                # 提取视频封面
                info['avatar'] = v_link.img['src']
                # 提取视频时长
                info['time'] = item.find(class_='video-duration').string.strip()
                # 提取视频发布时间
                info['publish_time'] = item.find(class_='fltR').string.strip()
                # 提取视频观看量
                info['num'] = item.find(class_='video-meta-pnum').text.strip()
                self._logger.info('{0}:{1}'.format(info['publish_time'], self._convert_publish_time(info['publish_time'])))
            except Exception, e:
                # 去除class为yk-col4但不包含视频信息的节点
                self._logger.error(e)
                continue
            v_list.append(info)
        return v_list

    # 根据虎牙的视频url地址，解析该视频的vid
    # from: http://v.huya.com/play/173868.html
    # to: 173868
    def _extract_vid_from_url(self, url):
        res = None
        if not url or url == '':
            return res
        matchObj = re.search(r'\/([0-9\-]+)\.html', url)
        if matchObj:
            res = matchObj.group(1)
        return res


if __name__ == '__main__':
    zhubo = [{'url':'http://v.huya.com/u/171423073/video.html'},{'url':'http://v.huya.com/u/5452110/video.html'}]
    youku = HuyaExtractor(zhubo)
    for zb in zhubo:
        arr = youku.get_single_list(zb['url'])
