#!/usr/bin/env python
#coding=utf-8

from collections import deque


class Queue(object):

    def __init__(self):
        self.q = deque()

    def push(self, jsonjob):
        self.q.appendleft(jsonjob)
        return True

    def rpush(self, jsonjob):
        self.q.append(jsonjob)
        return True

    def lpush(self, jsonjob):
        self.q.appendleft(jsonjob)
        return True

    def rpushmany(self, *jsonjob):
        self.q.append(jsonjob)
        return True

    def lpushmany(self, *jsonjob):
        self.q.appendleft(*jsonjob)
        return True

    def rpop(self):
        try:
            return self.q.pop()
        except IndexError:
            return None

    def lpop(self):
        try:
            return self.q.pop()
        except IndexError:
            return None

    def getjobs(self, limit=None):
        jobs = [self.rpop() for i in xrange(limit)]
        return filter(None, jobs)

    def get(self, index):
        try:
            job = self.q[index]
        except IndexError:
            job = None
        return job

    def pack(self, url, **kw):
        job = {'url': url}.update(kw)
        return job

    def size(self):
        return len(self.q)


if __name__ == '__main__':
    q = Queue()
    for i in xrange(1, 100):
        q.lpush('{"url": "%s"}' % i)
    print q.getjobs(10)
    print q.get(0)
    print q.size()
