#-*-coding:utf-8-*-
#!/usr/bin/python

#
# Send Email with Content Log
#

'Send Log By Email'

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import config
import queue
from datetime import datetime
import json
import time

email_queue = queue.Queue()

def send_email(subject, content):
    # 判断邮件发送队列是否超过最大发送数目
    if email_queue.size() <= config.EMAIL_MAX_SIZE:
        # 获取当前时间 
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S');
        email_queue.lpush('{"time":"%s", "subject":"%s", "content":"%s"}' % (current_time, subject, content))
        return True
    else:
        return False


def _format_addr(s, charset):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, charset).encode(), \
        addr.encode(charset) if isinstance(addr, unicode) else addr))

def _send_email(subject, content):
    from_addr = config.EMAIL_FROM
    password = config.EMAIL_PASSWORD
    to_addr = config.EMAIL_TO
    smtp_server = config.EMAIL_SMTP_SERVER

    msg = MIMEText(content, 'plain', config.EMAIL_CHARSET)
    msg['From'] = _format_addr(u'Shenyou.TV<%s>' % from_addr, config.EMAIL_CHARSET)
    msg['To'] = _format_addr(u'管理员<%s>' % to_addr, config.EMAIL_CHARSET)
    msg['subject'] = Header(subject, config.EMAIL_CHARSET).encode()

    server = smtplib.SMTP(smtp_server, config.EMAIL_PORT)
    server.set_debuglevel(0)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()

def send_emails():
    # 每次发送15封邮件,如果邮件列表只包含一封邮件，不发送
    emails = email_queue.getjobs(15)
    while emails and len(emails) > 3:
        email_content = ""
        email_suject = u"爬取日志"
        for em in emails:
            obj = json.loads(em)
            current_time = obj['time']
            subject = obj['subject']
            content = obj['content']
            email_content = email_content + current_time + "," + subject + " : " + content + "\r\n"
        _send_email(email_suject, email_content)
        # 防止不间断发送邮件遭拒收
        time.sleep(2)
        emails = email_queue.getjobs(15)

def run():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S');
    send_email(u'测试发送邮件模块', u'当前时间' + current_time)


if __name__ == "__main__":
    run()
