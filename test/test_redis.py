#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/29 11:09
import txredisapi as redis
from twisted.internet import defer
from twisted.internet import reactor

@defer.inlineCallbacks
def main():
    rc = yield redis.Connection()
    ss=yield rc.zadd('foo3',1,'abc')

    zz=yield rc.zrange('foo3',0,100,True)

    pp=set(range(5))
    print zz, type(zz), zz+map(lambda k: {'roomid':k}, list(pp))

    return

    txn = yield rc.multi()
    txn.zrange('foo',0,100,True)
    txn.scard("foo")
    print '---'
    z=yield txn.commit()


    print '---',z
    yield rc.disconnect()

if __name__ == "__main__":
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()