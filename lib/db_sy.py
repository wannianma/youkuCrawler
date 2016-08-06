#-*-coding:utf-8-*-
#!/usr/bin/python

#
# DB module 
#

'DB'

import MySQLdb
import config
from logger import logger
import time
import gevent
from gevent.pool import Pool
import os

gpool = Pool(config.GPOOLSIZE)

def getConnection():
    dbconn = MySQLdb.connect(host=config.DB_HOST,user=config.DB_USER,passwd=config.DB_PASSWD,charset=config.DB_CHARSET)
    dbconn.select_db(config.DB_NAME)
    return dbconn 

def db_insert(dbconn, insert_data, tb_type='onlive'):
    # 通过eval动态使用字符串调用函数
    callback_func = eval('_insert_'+tb_type+'_data')
    cursor = dbconn.cursor()
    print "length:%d" % len(insert_data)
    for kw in insert_data:
        gpool.spawn(callback_func, cursor, kw)
    gpool.join()
    cursor.close()
    # 提交修改
    dbconn.commit()

def db_update(dbconn, update_data, tb_type='onlive'):
    # 更新之前，先将历史数据的is_live字段置为0
    callback_func = eval('_update_'+tb_type+'_data')
    cursor = dbconn.cursor()
    for kw in update_data:
        gpool.spawn(callback_func, cursor, kw)
    gpool.join()
    cursor.close()
    # 提交修改
    dbconn.commit()

def db_select(dbconn, tb_type, where, fields = [],limit = None):
    try:
        cursor = dbconn.cursor()
        if len(fields) == 0:
            str_fields = '*'
        else:
            str_fields = ','.join(fields)
        sql = "SELECT %s FROM `%s` WHERE %s" % (str_fields, 'sy_' + tb_type, where)
        if not limit is None:
            sql = sql + " limit %s" % limit
        # print sql
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
    except Exception as e:
        logger.error("%s | %s" % ('DB Select Error', e))
        raise
    return result

def _update_onlive_data(cursor, kw, is_get_livedata = True):
    try:
        cursor.execute("SELECT * FROM "+config.DB_TABLE+" WHERE `zbid` = %s AND `source` = %s", (kw['zbid'], kw['source']))
        data = cursor.fetchone()
        if data:
            if not is_get_livedata:
                # 主要针对斗鱼平台
                cursor.execute("UPDATE " +config.DB_TABLE+" SET `zbname`=%s, `title`=%s, `views`=%s, `isOnlive`=1, `updatetime`=%s, `livedata`=%s, `thumb`= %s, `category`=%s WHERE `zbid` = %s AND `source` = %s", (kw['zbname'], kw['title'], kw['views'], kw['inputtime'], kw['livedata'], kw['thumb'], kw['category'], kw['zbid'], kw['source']))
            else:
                cursor.execute("UPDATE " +config.DB_TABLE+" SET `zbname`=%s, `title`=%s, `views`=%s, `isOnlive`=1, `updatetime`=%s, `avatar`=%s, `thumb`= %s, `category`=%s, `livedata` = %s WHERE `zbid` = %s AND `source` = %s", (kw['zbname'], kw['title'], kw['views'], kw['inputtime'], kw['zb_thumb'], kw['thumb'], kw['category'], kw['livedata'], kw['zbid'], kw['source']))
        else:
            _insert_onlive_data(cursor, kw)
    except Exception as e:
        logger.error("%s | %s" % ('DB Update Error', e))
        raise

def _update_anchor_data(cursor, kw):
    try:
        cursor.execute("UPDATE " +config.DB_TABLE_ANCHOR+ " SET `v_updatetime` = %s, `v_num` = %s, `v_next_updatetime`=%s WHERE `id` = %s", (kw['v_updatetime'], kw['v_num'], kw['v_next_updatetime'],kw['id']))
    except Exception as e:
        logger.error("%s | %s" % ("DB anchor Update Error", e))
        raise

def _before_update_data(dbconn, source):
    cursor = dbconn.cursor()
    try:
        cursor.execute("UPDATE " +config.DB_TABLE+" SET `isOnlive`= 0 WHERE `source` = %s", source)
    except Exception as e:
        logger.error("%s | %s" % ('DB Before Update Error', e))
        raise
    cursor.close()
    dbconn.commit()

def _insert_video_data(cursor,kw):
    try:
        #####
        inputtime = str(int(time.time()))
        #将爬取到的视频，存入其他(14)分类，并设置状态为1级审核
        cursor.execute("INSERT INTO " +config.DB_TABLE_VIDEO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`,`vision`,`video_category`,`anchor`) VALUES (%s, '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s,'1','1',%s)",(kw['catid'], kw['title'], kw['thumb'], kw['keywords'], kw['keywords'], kw['publishtime'], 0,kw['anchor']))
        insert_id = cursor.lastrowid
        # 更新搜索表
        seg_data = "{0} {1}".format(kw['title'], kw['keywords'].replace(',', ' '))
        cursor.execute("INSERT INTO sy_search (`typeid`, `id`, `adddate`, `data`, `siteid`) VALUES (57, %s, %s, %s, 1)", (insert_id, int(time.time()), seg_data))
        #更新hits表
        cursor.execute("INSERT INTO sy_hits (`hitsid`, `catid`) VALUES ('c-11-%s', %s)",(insert_id, kw['catid']))
        #将vid写入data附表
        cursor.execute("INSERT INTO "+config.DB_TABLE_VIDEO_DATA+" (`id`, `content`, `readpoint`, `groupids_view`, `paginationtype`, `maxcharperpage`, `template`, `paytype`, `allow_comment`, `relation`, `video`, `from`, `vid`, `videoTime`) VALUES (%s, %s, 0, '', 0, 10000, '', 0, '1', %s, '1', %s, %s, %s)", (str(insert_id), kw['description'] ,kw['mark'], kw['platform'], kw['vid'], kw['v_time']))
        # #将vid与from写入vdata目录的json中
        dir_name = str(insert_id % 100)
        path = "/data/wwwroot/ShenYou/vdata/"+dir_name
        if(os.path.exists(path)!=True):
            os.mkdir(path)
        json_str = '{"from":"youku","vid":"{0}"}'.format(kw['vid'])
        f=file(path+"/"+str(insert_id)+".json","w+")
        f.write(str(json_str))
        f.close()

    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise

def _insert_onlive_data(cursor, kw):
    try:
        cursor.execute("INSERT INTO " +config.DB_TABLE+" (`zbid`, `zbname`, `source`, `title`, `views`, `category`, `isOnlive`, `inputtime`, `avatar`, `thumb`, `livedata`, `catid`, `typeid`, `status`) VALUES (%s, %s, %s, %s, %s, %s, '1', %s, %s, %s, %s, 9, 8, 99)",(kw['zbid'],kw['zbname'],kw['source'],kw['title'],kw['views'],kw['category'],kw['inputtime'],kw['zb_thumb'],kw['thumb'],kw['livedata']))
    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise

def _insert_feixiong_data(cursor, kw):
    try:
        remark = str(kw['video_num']) + '_' + str(kw['order_num']) + '_' + str(kw['read_num'])
        # 将content插入到data附表
        cursor.execute("INSERT INTO `zhubo` "+" (`name`, `channel_url`, `avatar_url`, `description`, `cat_name`, `remark`) VALUES (%s, %s, %s, %s, %s, %s)",(kw['name'],'http:',kw['img_url'],kw['description'],kw['cat_name'],remark))
        insert_id = cursor.lastrowid
        print "insert_id :" + str(insert_id)
    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise

def run():
    pass

if __name__ == "__main__":
    run()
