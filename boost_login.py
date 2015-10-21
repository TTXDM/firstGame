#coding:utf-8
# Author:  Eric.Slver 
# Created: 2011/9/27
########################################################
#
########################################################
import os
import sys

if not 'twisted.internet.reactor' in sys.modules:
    EnumIOCP = ['nt']
    EnumEPOLL = ['posix', 'mac', 'os2', 'ce', 'java', 'riscos']
    if os.name in EnumIOCP:
        from twisted.internet import iocpreactor
        iocpreactor.reactor.install()
    elif os.name in EnumEPOLL:
        from twisted.internet import epollreactor
        epollreactor.install()


import txredisapi as redis
from twisted.internet import defer

@defer.inlineCallbacks
def config_server(maxRoomNum):
    print u"config_server..."
    rc = yield redis.Connection()
    print u"redis connected."
    yield rc.select("0")
    for i in range(1,maxRoomNum):
        yield rc.sadd("room_empty", i)
    yield rc.disconnect()

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # try:
    #     open("./server.pid", "w").write("%s\n" % os.getpid())
    # except Exception as e:
    #     sys.exit(repr(e))

    print u"*********************************"
    print u"*    南昌麻将 v1.0.0              *"
    print u"*********************************"
    print u"\n正在初始化..."

    import logging, logConfig
    from twisted.internet import reactor
    from core.socket_server import AppFactory
    from core.packet import request_handler
    import login.user_manager
    config_server(maxRoomNum=100)
    print "\n[game] server start...[6988]"
    reactor.listenTCP(6988, AppFactory(request_handler))
    print u"\n初始化完成."
    print '----------------------------'
    logging.getLogger('boot').info(u'game start.')
    reactor.run()