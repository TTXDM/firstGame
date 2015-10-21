#coding:utf-8
# Author:  Eric.Slver 
# Created: 2011/9/27
########################################################
#
########################################################
import os, sys, struct, time

EnumIOCP = ['nt']
EnumEPOLL = ['posix', 'mac', 'os2', 'ce', 'java', 'riscos']
if not 'twisted.internet.reactor' in sys.modules:
    if os.name in EnumIOCP:
        from twisted.internet import iocpreactor
        iocpreactor.reactor.install()
    elif os.name in EnumEPOLL:
        from twisted.internet import epollreactor
        epollreactor.install()

from twisted.application.service import Service
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.defer import inlineCallbacks
from twisted.python import log

########################################################
#                          安全沙箱                     #
########################################################
class PolicyProtocol(Protocol, TimeoutMixin):
    def connectionMade(self):
        #reactor.callLater(5, lambda : self.transport.loseConnection("timeout"))
        self.setTimeout(5)

    def dataReceived(self, data):
        # print u"\n->policy-file-request.from: ", self.transport.clientAddr.host, self.transport.clientAddr.port, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        if data == "<policy-file-request/>\0":
            self.transport.write(self.factory.Policy)
        else:
            self.transport.write("unknow protocols.")
        self.transport.loseConnection()

class PolicyFactory(Factory):
    def __init__(self):
        self.protocol = PolicyProtocol;
        self.Policy = """<?xml version="1.0"?>
                        <!DOCTYPE cross-domain-policy SYSTEM "/xml/dtds/cross-domain-policy.dtd">
                        <cross-domain-policy>
                            <site-control permitted-cross-domain-policies="master-only"/>
                            <allow-access-from domain="*" to-ports="*" />
                        </cross-domain-policy>\0"""

class PolicyService(Service):
    def __init__(self, poetry_file):
        self.poetry_file = poetry_file

    def startService(self):
        Service.startService(self)

'''
   TAC服务
'''
if os.name in EnumEPOLL:
    from twisted.application import TCPServer
    from twisted.application.service import Service, MultiService, Application
    log.msg('tac init.')
    top_service = MultiService()
    policy_service=PolicyService()
    policy_service.setServiceParent(top_service)
    application = Application("flash_policy_service")
    tcp_service = TCPServer(843, PolicyFactory(policy_service))
    tcp_service.setServiceParent(top_service)
    top_service.setServiceParent(application)

elif __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print u"*********************************"
    print u"*    Flash安全沙箱843 v1.1.0      *"
    print u"*********************************"
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),u"\n正在初始化..."
    try:
        from twisted.internet import iocpreactor
        iocpreactor.reactor.install()
    except:
        pass

    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),"\n[policy] server start...[843]"
    from twisted.internet import reactor
    reactor.listenTCP(843, PolicyFactory())
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),"\n[policy] server start successed.[843]"
    reactor.run()
