#!/usr/bin/env python
# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from BaseExtractor import BaseExtractor
import re,json

class QqExtractor(BaseExtractor):
    def __init__(self, zhubo):
        super(QqExtractor, self).__init__(zhubo)
        # orderflag=0 最新排序
        # orderflag=1 最热排序
        self.list_api = 'http://c.v.qq.com/vchannelinfo?otype=json&uin={vuin}&qm=1&pagenum={page_num}&num=24&sorttype=0&orderflag=0&low_login=1'
        self.page_num = 1
        self.vuin = None
        if zhubo.get('platform_id', False):
            # QQ视频上主播对应的id
            self.vuin = zhubo['platform_id']

    # 重写get_json方法
    # qq视频列表API返回样式为：QZOutputJson={...};,非正常json数据
    def get_json(self, url):
        html = self.get_html(url)
        return html[html.find('=')+1:-1]

    # QQ列表单页面处理
    def get_single_list(self, channel_url, is_all=False):
        self._logger.info('url:{0}'.format(channel_url))
        v_list = []
        vuin = ''
        # 下一页地址
        next_page_url = None
        # 如果是视频起始页，首先获取该列表页对应的api请求页面
        if self.page_num == 1:
            if self.vuin is None:
                # 获取主播在腾讯平台上对应的vuin
                html = self.get_html(channel_url)
                if html.strip() != '':
                    try:
                        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                        self.vuin = soup.find(class_='ico_collect')['data-vuin']
                    except Exception, e:
                        self._logger.error(e)
                        return v_list, ''
            channel_url = self.list_api.format(vuin=self.vuin, page_num=self.page_num)
        v_json = json.loads(self.get_json(channel_url))
        if v_json.get('videolst', False):
            for video in v_json['videolst']:
                info = {}
                try:
                    info['link'] = video['url']
                    info['title'] = video['title']
                    info['vid'] = video['vid']
                    info['avatar'] = video['pic']
                    info['time'] = self._convert_video_time(video['duration'])
                    info['num'] = self._convert_video_num(video['play_count'])
                    info['publish_time'] = self._convert_publish_time(video['uploadtime'])
                except Exception, e:
                    self._logger.error(e)
                    continue
                v_list.append(info)
            # 当前page+1
            self.page_num += 1
            next_page_url = self.list_api.format(vuin=self.vuin, page_num=self.page_num)
            return v_list, next_page_url
        else:
            return v_list, next_page_url


    # 根据虎牙的视频url地址，解析该视频的vid
    # from: http://v.huya.com/play/173868.html
    # to: 173868
    def _extract_vid_from_url(self, url):
        res = None
        if not url or url == '':
            return res
        matchObj = re.search(r'\/([0-9a-zA-Z]+)\.html', url)
        if matchObj:
            res = matchObj.group(1)
        return res


if __name__ == '__main__':
    zhubo = [{'url':'http://v.qq.com/vplus/qiangpao/videos'},{'url':'http://v.qq.com/vplus/caomei/videos'}]
    for zb in zhubo:
        qq = QqExtractor(zb)
        arr = qq.get_single_list(zb['url'])
