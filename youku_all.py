#-*-coding:utf-8-*-
#!/usr/bin/python

from lib import config, req_sy, db_sy, encoding
from lib import email_sy as email
from lib.logger import logger
import time,datetime
import re,sys,os
import json
from pprint import pprint
from extractor import *

# linux定时任务更改当前路径
os.chdir('/data/crawler/')

# 全局数据库连接
dbconn = db_sy.getConnection()
# 优酷视频的定期更新间隔
update_period = config.VIDEO_UPDATE_PERIOD

# 修复插入数据库乱码问题
reload(sys)
sys.setdefaultencoding('utf-8')

# 游戏类别对应的PHPCMS中的catid
game_type = {'lol':'6','Dota2':'7','dota2':'7','starcraft':'8','wow':'13','cf':'20','diablo':'21','hearthstone':'22','minecraft':'60','overwatch':'61','pvp':'62','WorldOfTanks':'63','CS_GO':'64','cos':'65','dota':'66','warcraft':'67','zhanzheng':'68','sheji':'69','CR':'70','yuanchuang':'71','zixun':'72','other':'14'}

# 检查vid是否已存在，即视频已插入数据库
# 获取优酷主播频道信息
def check_vid_from_db(vid):
	# To_do 添加主播视频最近更新时间
	fields = ['id']
	res = db_sy.db_select(dbconn, 'video_data', "`vid` = '{0}' ".format(vid), fields)
	if res:
		return True
	else:
		return False

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
			temp_kw['platform'] = zhubo['platform']
			# 查询当前vid是否存在
			if check_vid_from_db(video['vid']):
				continue
			res_arr.append(temp_kw)
	# 更新主播uid信息和最新视频更新时间
	# zhubo['uid'] = uid
	zhubo['v_updatetime'] = updatetime
	# 更新主播下次视频更新时间
	zhubo['v_next_updatetime'] = get_zhubo_next_updatetime(updatetime)

	return zhubo, res_arr

def pro_video_list(zhubo, obj_extractor):
	# 对优酷所有列表页进行处理
	def get_all_list(channel_url):
		v_all_list = []
		next_page_url = channel_url
		start_page = 0
		# 加入限制条件,只爬取前250页数据
		while not next_page_url is None and start_page < 250:
			v_list = []
			v_list, next_page_url = obj_extractor.get_single_list(next_page_url, is_all=True)
			if v_list is None:
				continue
			v_all_list.extend(v_list)
			start_page += 1
		print 'v_all_list size :' + str(len(v_all_list)) + '\r\n'
		return v_all_list
	is_init = zhubo['is_init']
	channel_url = zhubo['url']
	res_list  = []
	# 判断当前主播是否为初始爬取，是则爬取所有分页，否则只爬取第一页
	if is_init:
		res_list = get_all_list(channel_url)
		# 过滤操作
		print "#####IN Videos Filter,size:{0}#####\r\n".format(len(res_list))
		zhubo, videos = get_videos_info(zhubo, res_list)
		print "#####End Videos Filter,size:{0}#####\r\n".format(len(videos))
		# 获取主播视频数量
		zhubo['v_num'] = len(videos)
		# 入库
		# 更新video表数据
		db_sy.db_insert(dbconn, videos, 'video')
		# 更新anchor表数据
		# 组装主播数据
		zhubo_list = []
		zhubo_list.append(zhubo)
		db_sy.db_update(dbconn, zhubo_list, 'anchor')
	else:
		next_updatetime = zhubo['v_next_updatetime']
		# 判断当前主播是否更新
		if (next_updatetime == 0 or is_update_zhubo(next_updatetime)):
			res_list, url = obj_extractor.get_single_list(channel_url)
		# 过滤操作
		print "#####IN Videos Filter,size:{0}#####\r\n".format(len(res_list))
		zhubo, videos = get_videos_info(zhubo, res_list)
		print "#####End Videos Filter,size:{0}#####\r\n".format(len(videos))
		if len(videos) != 0:
			# 更新主播视频数量
			zhubo['v_num'] = zhubo['v_num'] + len(videos)
			# 入库
			# 更新video表数据
			db_sy.db_insert(dbconn, videos, 'video')
		# 更新anchor表数据,更新v_num,v_updatetime
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
	# 如果视频时间差大于一周
	if abs(current_time - new_updatetime) > 14*update_period:
		return abs(current_time - new_updatetime) + current_time
	else:
		return current_time + update_period
	

# 获取优酷主播频道信息
def get_zhubo_from_db(ids):
	res = []
	is_init = True
	str_ids = ','.join(ids)
	# To_do 添加主播视频最近更新时间
	fields = ['id', 'title', 'game_type', 'platform_url', 'v_updatetime', 'v_next_updatetime', 'v_num', 'platform_id', 'platform']
	res_zhubo = db_sy.db_select(dbconn, 'anchor', "`id` in ({0}) ".format(str_ids), fields)
	for zhubo in res_zhubo:
		info = {}
		info['id'] = str(zhubo[0])
		info['name'] = zhubo[1]
		info['game_type'] = game_type[zhubo[2]]
		info['url'] = zhubo[3].strip()
		info['v_updatetime'] = zhubo[4]
		info['v_next_updatetime'] = zhubo[5]
		info['v_num'] = zhubo[6]
		info['uid'] = zhubo[7]
		info['platform'] = zhubo[8]
		info['is_init'] = is_init
		res.append(info)
	return res


if __name__ == "__main__":
	# 读取命令行主播信息
	if len(sys.argv) < 2:
		print "请提供带爬取主播id"
		sys.exit(0)

	zhubo_ids = sys.argv[1:]
	# 读取主播自频道信息
	zipindao_info = get_zhubo_from_db(zhubo_ids)

	now =  time.time()
	for zhubo in zipindao_info:
		#动态加载页面抓取对象
		str_extractor = zhubo['platform'].capitalize() + 'Extractor'
		module = globals()[str_extractor]
		obj_extractor = getattr(module, str_extractor)(zhubo)
		pro_video_list(zhubo, obj_extractor)
	# 执行时间
	print "time cost : " + str(int((time.time() - now))) + " seconds"
	# 关闭数据库连接
	dbconn.close()
	# t = '2016-07-02 22:19:19'
	# print str(_convert_publish_time(t))
