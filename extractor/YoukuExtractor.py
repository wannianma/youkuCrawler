#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bs4 import BeautifulSoup
from BaseExtractor import BaseExtractor
import re

class YoukuExtractor(BaseExtractor):
    def __init__(self, zhubo):
        super(YoukuExtractor, self).__init__(zhubo)
        self.host_url = 'http://i.youku.com'
        self.api_client_id = '5af6a7d8274a36e8'

    # 根据优酷的视频url地址，解析该视频的vid
    # From :
    def _extract_vid_from_url(self, url):
        res = None
        if not url or url == '':
            return res
        matchObj = re.search(r'id_(.*)\.html', url)
        if matchObj:
            res = matchObj.group(1)
        return res

    def _extract_videos_by_4_col(self, url, items_list, is_all=False):
        v_list = []
        if is_all:
            # 由于4列视频列表是动态加载，需要通过phantomjs重新抓取全部页面内容
            html = self.get_html_by_phantomjs(url)
            if html.strip() != '':
                soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                items_list = soup.find_all(class_='yk-col4')
        for item in items_list:
            info = {}
            try:
                # 提取视频封面
                info['avatar'] = item.find(class_='v-thumb').img['src']
                v_link = item.find(class_='v-link').a
                # 提取视频地址
                info['link'] = v_link['href']
                # 提取视频title
                info['title'] = v_link['title']
                # 提取视频时长
                info['time'] = item.find(class_='v-time').string
                # 提取视频发布时间
                info['publish_time'] = item['c_time']
                # 提取视频观看量
                info['num'] = item.find(class_='v-num').string
                self._logger.info('{0}:{1}'.format(info['publish_time'], self._convert_publish_time(info['publish_time'])))
            except Exception, e:
                # 去除class为yk-col4但不包含视频信息的节点
                self._logger.error(e)
                continue
            v_list.append(info)
        print "4 col list size :" + str(len(v_list))
        return v_list

    def _extract_videos_by_5_col(self, url, items_list):
        v_list = []
        for item in items_list:
            info = {}
            try:
                # 提取视频封面
                info['avatar'] = item.find(class_='v-thumb').img['src']
                v_link = item.find(class_='v-link').a
                # 提取视频地址
                info['link'] = v_link['href']
                # 提取视频title
                info['title'] = v_link['title']
                # 提取视频时长
                info['time'] = item.find(class_='v-time').string
                # 提取视频发布时间
                info['publish_time'] = item.find(class_='v-publishtime').string
                # 提取视频观看量
                info['num'] = item.find(class_='v-num').string
                self._logger.info('{0}:{1}'.format(info['publish_time'], self._convert_publish_time(info['publish_time'])))
            except Exception, e:
                # 去除class为yk-col4但不包含视频信息的节点
                self._logger.error(e)
                continue
            v_list.append(info)
        return v_list

    # 优酷列表单页面处理
    def get_single_list(self, channel_url, is_all=False):
        self._logger.info('url:{0}'.format(channel_url))
        v_list = None
        # 下一页地址
        next_page_url = None
        html = self.get_html(channel_url)
        if html.strip() != '':
            soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
            # 获取下一页地址
            next_page = soup.find(class_='next')
            if not next_page is None and not next_page.a is None:
                next_page_url = self.host_url + next_page.a['href']
            # 判断页面所用模板
            if not soup.find(class_='yk-col4 new') is None:
                items_list = soup.find_all(class_='yk-col4')
                v_list = self._extract_videos_by_4_col(channel_url, items_list, is_all)
            else:
                items_list = soup.find_all(class_='v va')
                v_list = self._extract_videos_by_5_col(channel_url, items_list)
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

    def _pro_video_by_show_api(self, vid):
        title, avatar, v_time, link, description, uid, tags, publishtime, mark = [None] * 9
        OPEN_API = 'https://openapi.youku.com/v2/videos/show.json?client_id={0}&video_id={1}'
        url = OPEN_API.format(self.api_client_id, vid)
        response = self.get_json(url)
        if response and response.get('id', 0) == vid:
            title = response['title']
            avatar = response['bigThumbnail']
            v_time = response['duration']
            link = response['link']
            description = response['description']
            uid = response['user']['id']
            tags = response['tags']
            publishtime = response['published']
            # 将视频发布时间转化为Unix时间戳
            publishtime = self._str_to_timestamp(publishtime)
            mark = str(response['view_count']) + '#' + str(response['comment_count']) + "#" + str(response['up_count'])
        return title, avatar, v_time, link, description, uid, tags, publishtime, mark, vid

    # 获取视频详情页面信息
    def get_single_page(self, vid):
        pass

    # 通过Youku API调取列表信息
    def get_single_list_by_api(self, zhubo):
        videos_api = 'https://openapi.youku.com/v2/videos/by_user.json?client_id={0}&user_id={1}&page=1&count=50'.format(
            self.api_client_id, zhubo['uid'])
        response = self.get_json(videos_api)
        v_list = []
        # print "response[id] :" + response['id']
        if response and response.get('count', 0) == 50:
            videos = response['videos']
            print 'videos length : {0}'.format(len(videos))
            for video_item in videos:
                info = {}
                new_updatetime = self._str_to_timestamp(video_item['published'])
                if new_updatetime < zhubo['v_updatetime']:
                    continue
                info['link'] = video_item['link']
                v_list.append(info)
        return v_list, videos_api


if __name__ == '__main__':
    pass
