#coding:utf-8
# Author:  Eric.Slver 
# Created: 2012/10/10
'''
struct 类型表
Format	C Type	        Python type	Standard size	Notes
x	    pad byte	    no value
c	    char	        string of length 1	1
b	    signed char	    integer	1	(3)
B	    unsigned char	integer	1	(3)
?	    _Bool	        bool	1	(1)
h	    short	        integer	2	(3)
H	    unsigned short	integer	2	(3)
i	    int	            integer	4	(3)
I	    unsigned int	integer	4	(3)
l	    long	        integer	4	(3)
L	    unsigned long	integer	4	(3)
q	    long long	    integer	8	(2), (3)
Q	    unsigned 8long 	integer	8	(2), (3)
f	    float	        float	4	(4)
d	    double	        float	8	(4)
s	    char[]	        string	1
p	    char[]	        string
P	    void *	        integer	 	(5), (3)
'''
import struct
import StringIO

class Parser():
    def __init__(self, data):
        self.buf=StringIO.StringIO(data)

    def read_bool(self):
        return struct.unpack('>c',self.buf.read(1))[0]

    def read_char(self):
        return struct.unpack('>b',self.buf.read(1))[0]

    def read_ubyte(self):
        return struct.unpack('>B',self.buf.read(1))[0]

    def read_short(self):
        return struct.unpack('>h',self.buf.read(2))[0]

    def read_ushort(self):
        return struct.unpack('>H',self.buf.read(2))[0]

    def read_long(self):
        return struct.unpack('>i',self.buf.read(4))[0]

    def read_ulong(self):
        return struct.unpack('>I',self.buf.read(4))[0]

    def read_string(self):
        str_size=int(struct.unpack('>H',self.buf.read(2))[0])
        str_bin=struct.unpack(">%ds" % str_size, self.buf.read(str_size))[0]
        return str_bin.decode()

class Buffer():
    def __init__(self):
        self.buf=StringIO.StringIO('')

    def getValue(self):
        return self.buf.getvalue()

    def write_bool(self, s):
        self.buf.write(struct.pack('>c',s))

    def write_byte(self, s):
        self.buf.write(struct.pack('>B',s))

    def write_short(self, s):
        self.buf.write(struct.pack('>h',s))

    def write_ushort(self, s):
        self.buf.write(struct.pack('>H',s))

    def write_long(self, s):
        self.buf.write(struct.pack('>i',s))

    def write_ulong(self, s):
        self.buf.write(struct.pack('>I',s))

    def write_string(self, s):
        if type(s)==str:
            self.buf.write(struct.pack(">H%ds" % len(s), len(s), s))
        elif type(s)==unicode:
            s1=s.encode('utf-8')
            self.buf.write(struct.pack(">H%ds" % len(s1), len(s1), s1))

sys_message={}
def registe_msg_handler(who,event_type):
    def msg_handler(func):
        # print u'注册msg_handler:', event_type, func, who
        handlers=sys_message.get(str(id(who))+'_'+str(event_type),[])
        handlers.append(func)
        sys_message[str(id(who))+'_'+str(event_type)]=handlers
        return func
    return msg_handler

def unregiste_msg_handler(who,event_type):
    # print u'un注册msg_handler:', event_type, func, who
    if sys_message.has_key(str(id(who))+'_'+str(event_type)):
        del sys_message[str(id(who))+'_'+str(event_type)]

from twisted.internet import defer
@defer.inlineCallbacks
def msg_notify(who,event_type,*args,**kwargs):
    print u'msg_notify', event_type, args, kwargs
    handlers=sys_message.get(str(id(who))+'_'+str(event_type),[])
    for func in reversed(handlers):
        yield func(*args,**kwargs)

