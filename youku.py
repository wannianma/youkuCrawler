#-*-coding:utf-8-*-
#!/usr/bin/python

from lib import config, req_sy, db_sy, encoding
from lib import email_sy as email
from lib.logger import logger
from bs4 import BeautifulSoup
import subprocess
import time,datetime
import re,sys,os
import json
import gevent.monkey


gevent.monkey.patch_socket()
import gevent
from gevent.pool import Pool

gpool = Pool(config.GPOOLSIZE)
# 全局数据库连接
dbconn = db_sy.getConnection()
# 优酷视频的定期更新间隔
update_period = config.YOUKU_UPDATE_PERIOD

# 修复插入数据库乱码问题
reload(sys)
sys.setdefaultencoding('utf-8')

# 游戏类别对应的PHPCMS中的catid
game_type = {'lol':'6','Dota2':'7','dota2':'7','starcraft':'8','wow':'13','cf':'20','diablo':'21','hearthstone':'22','minecraft':'60','overwatch':'61','pvp':'62','WorldOfTanks':'63','CS_GO':'64','cos':'65','dota':'66','warcraft':'67','zhanzheng':'68','sheji':'69','CR':'70','yuanchuang':'71','zixun':'72','other':'14'}


def _pro_video_by_show_api(vid):
	title, avatar, v_time, link, description, uid, tags, publishtime, mark = [None] * 9
	OPEN_API = 'https://openapi.youku.com/v2/videos/show.json?client_id={0}&video_id={1}'
	url = OPEN_API.format(config.YOUKU_CLIENT_ID, vid)
	#response = req_sy.get_html(url, is_json=True)
	#print "response[id] :" + response['id']
	response = None
	if response and response.get('id', 0) == vid:
		title = response['title']
		avatar = response['bigThumbnail']
		v_time = response['duration']
		link = response['link']
		description = response['description']
		uid = response['user']['id']
		tags = response['tags']
		publishtime= response['published']
		# 将视频发布时间转化为Unix时间戳
		publishtime = _str_to_timestamp(publishtime)
		mark = str(response['view_count']) + '#' + str(response['comment_count']) + "#" + str(response['up_count'])
	return title, avatar, v_time, link, description, uid, tags, publishtime, mark, vid

# 异步获取视频信息，并更新主播信息
def _get_video_info_asynchronous(zhubo, vids):
	threads = []
	for vid in vids:
		threads.append(gpool.spawn(_pro_video_by_show_api, vid))
	gpool.join()

	res = []
	uid = zhubo['uid']
	anchor_id = zhubo['id']
	catid = zhubo['game_type']
	# 视频的上次更新时间
	old_updatetime = zhubo['v_updatetime']
	updatetime = zhubo['v_updatetime']
	# 遍历threads, 判断是否成功
	for thread in threads:
		# 加入筛选条件title不能为空
		if thread.successful() and thread.value[0] and thread.value[7] > old_updatetime:
			temp_kw = {}
			temp_kw['title'] = thread.value[0]
			temp_kw['thumb'] = thread.value[1]
			temp_kw['v_time'] = thread.value[2]
			temp_kw['link'] = thread.value[3]
			temp_kw['description'] = thread.value[4]
			if uid is None or uid == '':
				uid = thread.value[5]
			temp_kw['anchor'] = anchor_id
			temp_kw['catid'] = catid
			temp_kw['keywords'] = thread.value[6]
			temp_kw['publishtime'] = thread.value[7]
			if updatetime < temp_kw['publishtime']:
				updatetime = temp_kw['publishtime']
			temp_kw['mark'] = thread.value[8]
			temp_kw['vid'] = thread.value[9]
			res.append(temp_kw)
	# 更新主播uid信息和最新视频更新时间
	zhubo['uid'] = uid
	zhubo['v_updatetime'] = updatetime
	# 更新主播下次视频更新时间
	zhubo['v_next_updatetime'] = get_zhubo_next_updatetime(updatetime)

	# 若执行过程出错，发送邮件
	# if is_error:
	# 	email.send_email(u'douyu直播爬取error', str(reason))
	return zhubo, res

# 工具函数：将字符串2016-03-19 09:10:25转化为Unix时间戳
def _str_to_timestamp(timestr):
	if timestr is None:
		return int(time.time())
	timearr = time.strptime(timestr, '%Y-%m-%d %H:%M:%S')
	return int(time.mktime(timearr))

# 根据优酷的视频url地址，解析该视频的vid
def _extract_vid_from_url(url):
	res = None
	if not url or url == '':
		return res
	matchObj = re.search(r'id_(.*)\.html', url)
	if matchObj:
		res = matchObj.group(1)
	return res

# 获取前几天对应的日期
# 2013-02-16
def _get_pre_n_day(n):
	format = "%Y-%m-%d"
	t = time.localtime(int(time.time())-n*24*3600)
	return time.strftime(format, t)

# 将视频发布时间进行转换为Unix时间戳
# 1分钟前,1小时前,昨天 14.26,前天 18:13,
def _convert_publish_time(str):
	# 当前时间
	current_time = int(time.time())
	today = datetime.date.today()
	# 56分钟前,1小时前,8小时前,3天前
	if str.find('前') > 0:
		if str.find('分钟') > 0:
			num = int(str[0:str.find('分钟')])
			return current_time - num*60
		if str.find('小时') > 0:
			num = int(str[0:str.find('小时')])
			return current_time - num*60*60
		if str.find('天') > 0:
			num = int(str[0:str.find('天')])
			return current_time - num*60*60*24
		return current_time
	else:
		time_str = None;
		if str.find('昨天'):
			time_str = _get_pre_n_day(1)
			m = re.search(r'\d+:\d+',str)
			if m:
				time_str = '{0} {1}:00'.format(time_str, m.group())
		if str.find('前天'):
			time_str = _get_pre_n_day(1)
			m = re.search(r'\d+:\d+', str)
			if m:
				time_str = '{0} {1}:00'.format(time_str, m.group())
		if re.match(r'\d+-\d+-\d+$', str):
			time_str = '{0} 00:00:01'.format(str)
		if re.match(r'\d+-\d+\s\d+:\d+:\d+', str):
			time_str = '{0}-{1}'.format(today.year, str)
		return _str_to_timestamp(time_str)

# 将视频时长转换为数字形式
# 20:35 => 1235.00
def _convert_video_time(str):
	arr = str.split(':')
	totle_time = 0
	for t in arr:
		totle_time = totle_time * 60 + int(t)
	return totle_time

# 将视频观看数转换为数字形式
# from 5,343 => 5343
# from 2.4万 => 24000
def _convert_video_num(str):
	if str.find(',') > 0:
		return int(''.join(str.split(',')))
	if str.find('万') > 0:
		return int(float(str[0:str.find('万')]) * 10000);
	return int(str);

# 执行phantomjs获取网页内容
def get_ajax_html_by_phantomjs(url):
	cmd = 'phantomjs D:/Code/phantomjs/examples/pro_youku.js "%s"'%url
	print 'cmd:', cmd
	stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	print 'err:', stderr
	return stdout

# 对组装video和主播信息
def get_videos_info(zhubo, videos):
	uid = None
	vids = []
	res_arr = []
	anchor_id = zhubo['id']
	catid = zhubo['game_type']
	# 视频的上次更新时间
	old_updatetime = zhubo['v_updatetime']
	updatetime = zhubo['v_updatetime']
	# 遍历threads, 判断是否成功
	for video in videos:
		# 加入筛选条件title不能为空
		if video['title'] and video['publish_time'] > old_updatetime:
			temp_kw = {}
			temp_kw['title'] = video['title']
			temp_kw['thumb'] = video['avatar']
			temp_kw['v_time'] = video['time']
			temp_kw['link'] = video['link']
			# description当然方法无法获取，置空
			temp_kw['description'] = ''
			temp_kw['anchor'] = anchor_id
			temp_kw['catid'] = catid
			temp_kw['keywords'] = zhubo['name']
			temp_kw['publishtime'] = video['publish_time']
			if updatetime < temp_kw['publishtime']:
				updatetime = temp_kw['publishtime']
			temp_kw['mark'] = video['num']
			temp_kw['vid'] = video['vid']
			res_arr.append(temp_kw)
	# 更新主播uid信息和最新视频更新时间
	zhubo['uid'] = uid
	zhubo['v_updatetime'] = updatetime
	# 更新主播下次视频更新时间
	zhubo['v_next_updatetime'] = get_zhubo_next_updatetime(updatetime)

	return zhubo, res_arr

def extract_videos_by_4_col(url, items_list, is_all= False):
	v_list = []
	if is_all:
		# 由于4列视频列表是动态加载，需要通过phantomjs重新抓取全部页面内容
		html = get_ajax_html_by_phantomjs(url)
		if html.strip() != '':
			soup = BeautifulSoup(html, 'html.parser', from_encoding = 'utf-8')
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
			logger.info('{0}:{1}'.format(info['publish_time'], _convert_publish_time(info['publish_time'])))
		except Exception, e:
			# 去除class为yk-col4但不包含视频信息的节点
			logger.error(e)
			continue
		v_list.append(info)
	print "4 col list size :" + str(len(v_list))
	return v_list

def extract_videos_by_5_col(url,items_list):
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
			logger.info('{0}:{1}'.format(info['publish_time'], _convert_publish_time(info['publish_time'])))
		except Exception, e:
			# 去除class为yk-col4但不包含视频信息的节点
			logger.error(e)
			continue
		v_list.append(info)
	return v_list

# 优酷列表单页面处理
def get_single_list(channel_url):
	print 'channel_url : ' + channel_url + '\r\n'
	v_list = None
	# 下一页地址
	next_page_url = None
	html = req_sy.get_html(channel_url)
	if html.strip() != '':
		soup = BeautifulSoup(html, 'html.parser', from_encoding = 'utf-8')
		# 获取下一页地址
		next_page = soup.find(class_='next')
		if not next_page is None and not next_page.a is None:
			next_page_url = 'http://i.youku.com' + next_page.a['href']
		# 判断页面所用模板
		if not soup.find(class_='yk-col4') is None:
			items_list = soup.find_all(class_='yk-col4')
			v_list = extract_videos_by_4_col(channel_url, items_list)
		else:
			items_list = soup.find_all(class_='v va')
			v_list = extract_videos_by_5_col(channel_url, items_list)
	# 对v_list数据进行组装
	for video in v_list:
		video['vid'] = _extract_vid_from_url(video['link'])
		video['time'] = _convert_video_time(video['time'])
		video['publish_time'] = _convert_publish_time(video['publish_time'])
		video['num'] = _convert_video_num(video['num'])
		# TODO 提取视频标题中关键词
		video['keyword'] = ''
	return v_list, next_page_url

# 通过Youku API调取列表信息
def get_single_list_by_api(zhubo):
	videos_api = 'https://openapi.youku.com/v2/videos/by_user.json?client_id={0}&user_id={1}&page=1&count=50'.format(config.YOUKU_CLIENT_ID, zhubo['uid'])
	response = req_sy.get_html(videos_api, is_json=True)
	v_list = []
	#print "response[id] :" + response['id']
	if response and response.get('count', 0) == 50:
		videos = response['videos']
		print 'videos length : {0}'.format(len(videos))
		for video_item in videos:
			info = {}
			new_updatetime = _str_to_timestamp(video_item['published'])
			if new_updatetime < zhubo['v_updatetime']:
				continue
			info['link'] = video_item['link']
			v_list.append(info)
	return v_list, videos_api

# 对优酷所有列表页进行处理
def get_all_list(channel_url):
	v_all_list = []
	next_page_url = channel_url
	start_page = 0
	# 加入限制条件,只爬取前250页数据
	while not next_page_url is None and start_page < 250:
		v_list = []
		v_list, next_page_url = get_single_list(next_page_url)
		if v_list is None:
			continue
		v_all_list.extend(v_list)
		start_page += 1
	print 'v_all_list size :' + str(len(v_all_list)) + '\r\n'
	return v_all_list

def pro_video_list(zhubo):
	is_init = zhubo['is_init']
	channel_url = zhubo['url']
	res_list  = []
	# 判断当前主播是否为初始爬取，是则爬取所有分页，否则只爬取第一页
	if is_init:
		res_list = get_all_list(channel_url)
		# 过滤操作
		print "#####IN Videos Filter#####\r\n"
		zhubo, videos = get_videos_info(zhubo, res_list)
		print "#####End Videos Filter\r\n"
		# 获取主播视频数量
		zhubo['v_num'] = len(videos)
		# 入库
		# 更新video表数据
		#db_sy.db_insert(dbconn, videos, 'video')
		# 更新anchor表数据
		# 组装主播数据
		#zhubo_list = []
		#zhubo_list.append(zhubo)
		#db_sy.db_update(dbconn, zhubo_list, 'anchor')
	else:
		next_updatetime = zhubo['v_next_updatetime']
		# 判断当前主播是否更新
		if (next_updatetime == 0 or is_update_zhubo(next_updatetime)):
			res_list, url = get_single_list(channel_url)
		# 过滤操作
		print "#####IN Videos Filter,size:{0}#####\r\n".format(len(res_list))
		zhubo, videos = get_videos_info(zhubo, res_list)
		print "#####End Videos Filter,size:{0}#####\r\n".format(len(videos))
		if len(videos) != 0:
			# 更新主播视频数量
			zhubo['v_num'] = zhubo['v_num'] + len(videos)
			# 入库
			# 更新anchor表数据,更新v_num,v_updatetime
			db_sy.db_insert(dbconn, videos, 'video')
			# 更新video表数据
			zhubo_list = []
			zhubo_list.append(zhubo)
			db_sy.db_update(dbconn, zhubo_list, 'anchor')
	print zhubo['id'] + ', size: ' + str(len(videos)) + '\r\n'

# 判断主播当前时间是否进行更新操作
# 根据更新单位和下次更新时间判断当前是否需要更新该主播
# 更新单位 24h, 12h, 6h, 1h
def is_update_zhubo(next_updatetime):
	current_time = int(time.time())
	return True if abs(current_time - next_updatetime) < update_period else False;

# 获取主播下次更新时间
def get_zhubo_next_updatetime(new_updatetime):
	current_time = int(time.time())
	if new_updatetime > current_time:
		raise Exception('获取的视频更新时间一长，请检查！')
	# 根据最新的视频更新时间，决定下次的更新时间
	return abs(current_time - new_updatetime) + current_time
	

# 获取优酷主播频道信息
def get_zhubo_from_db():
	res = []
	is_init = False
	# To_do 添加主播视频最近更新时间
	fields = ['id', 'title', 'game_type', 'platform_url', 'v_updatetime', 'v_next_updatetime', 'v_num', 'platform_id']
	res_zhubo = db_sy.db_select(dbconn, 'anchor', "`thumb` like '%anchor%' ", fields, 50)
	for zhubo in res_zhubo:
		info = {}
		info['id'] = str(zhubo[0])
		info['name'] = zhubo[1]
		info['game_type'] = game_type[zhubo[2]]
		info['url'] = zhubo[3]
		info['v_updatetime'] = zhubo[4]
		info['v_next_updatetime'] = zhubo[5]
		info['v_num'] = zhubo[6]
		info['uid'] = zhubo[7]
		info['is_init'] = is_init
		res.append(info)
	return res


if __name__ == "__main__":
	# 读取主播自频道信息
	#zipindao_info = [{'name':u'粉鱼pink__fish', 'url':'http://i.youku.com/u/UMTI4Nzg5OTUwNA==/videos', 'is_init':True}]
	zipindao_info = get_zhubo_from_db()

	now =  time.time()

	for zhubo in zipindao_info:
		pro_video_list(zhubo)
	# 执行时间
	print "time cost : " + str(int((time.time() - now))) + " seconds"
	# 关闭数据库连接
	dbconn.close()
	# 将最新视频更新时间更新到对应主播记录中
