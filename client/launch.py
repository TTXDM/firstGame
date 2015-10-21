#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/14 13:59  

import logging,sys,getopt
from functools import partial
from twisted.internet import reactor
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.protocol import Protocol, ClientCreator

def usage():
    '''
    :return:
    '''
    print 'usage:'
    print '-h, --help: print help message.'
    print '-u, --loginname: input login user name of Majiang game account.'
    print '-p, --password:  input login password of Majiang game account.'
    print '-r, --register:  register new game account if not exist.'



if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # from consts import HOST, PORT
    # HOST='localhost'
    import consts
    # consts.HOST='120.26.129.8'
    consts.PORT=6988
    login_name='admin'
    login_password='111'

    opts, args = getopt.getopt(sys.argv[1:], "hu:p:r:")
    for op, value in opts:
        if op == "-u":
            login_name = value
        elif op == "-p":
            login_password = value
        elif op == "-r":
            reg = True
        elif op == "-h":
            usage()
            sys.exit()
    # try:
    #     open("./server.pid", "w").write("%s\n" % os.getpid())
    # except Exception as e:
    #     sys.exit(repr(e))

    print u"*********************************"
    print u"*    南昌麻将测试客户端 v1.0.0              *"
    print u"*********************************"
    print u"\n正在初始化..."

    import logging, logConfig, packet, admin
    print u"\n正在连接服务器..."
    from admin import create_GM
    a=create_GM(login_name, login_password)
    logging.getLogger('boot').info(u'game start.')
    reactor.run()
