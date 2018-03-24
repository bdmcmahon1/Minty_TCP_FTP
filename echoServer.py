import sys
import traceback
from select import *
from socket import *

import re
import params

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False) # boolean (set if present)
    )

paramMap = params.parseParams(switchesVarDefaults)
listenPort, usage, debug = paramMap["listenPort"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()

try:
    listenPort = int(listenPort)
except:
    print "Can't parse listen port from %s" % listenPort
    sys.exit(1)

sockNames = {}               # from socket to name - global list of socket names
nextConnectionNumber = 0     # each connection is assigned a unique id

class Fwd:
	#Tries to read from in sock and write to out sock
	#Buffer capacity is 1000
    def __init__(self, conn, inSock, outSock, bufCap = 1000):
        self.conn, self.inSock, self.outSock, self.bufCap = conn, inSock, outSock, bufCap
        self.inClosed, self.buf = 0, ""
    def checkRead(self):
		#Don't want to read if buffer is full
        if len(self.buf) < self.bufCap and not self.inClosed:
            return self.inSock
        else:
            return None
    def checkWrite(self):
		#No reason to write if nothing to write
        if len(self.buf) > 0:
            return self.outSock
        else:
            return None	#This is special reserved value in Python
    def doRecv(self):
		#Received bytes from socket and put in buffer
        b = ""
        try:
            b = self.inSock.recv(self.bufCap - len(self.buf))
        except:
            self.conn.die()
		#If forwarder tried to read for socket
		#and select only tells when ready
		#and this function returns 0
		#then connection should be closed b/c we know we're done
        if len(b):
            self.buf += b
        else:
            self.inClosed = 1
        self.checkDone()
    def doSend(self):
		#Send everything in buffer
        try:
            n = self.outSock.send(self.buf)
            self.buf = self.buf[n:]
        except:	#If nothing to send, and select called, then close connection
            self.conn.die()
        self.checkDone()
    def checkDone(self):
		#checks if forward is done
        if len(self.buf) == 0 and self.inClosed:
            try:	#If done, connection is shut down
                self.outSock.shutdown(SHUT_WR)
            except:
                pass
            self.conn.fwdDone(self)
            
    
connections = set()		#our set of connections, used in the core while loop

class Conn:	
	#For every client we have a connection
	#Every client has socket and address
	#So Server knows where each client is coming from (address)
    def __init__(self, csock, caddr):
		#Numbers all connections with global, increment by 1
		#because every connection has only 1 connection
        global nextConnectionNumber
        self.csock = csock      # to client
        self.caddr = caddr
        self.connIndex = connIndex = nextConnectionNumber
        nextConnectionNumber += 1
		#Every connection has one set of forwarders
        self.forwarders = forwarders = set()
        print "New connection #%d from %s" % (connIndex, repr(caddr))
        sockNames[csock] = "C%d:ToClient" % connIndex	#Dictionary that maps sockets to names; this is global set of connections
		forwarders.add(Fwd(self, csock, csock)) #Make a forwarder, and add it to the set of forwarders
        connections.add(self)
    def fwdDone(self, forwarder):
		# If forward is done:
		# Close socket and remove from list of names
        forwarders = self.forwarders
        forwarders.remove(forwarder)
        print "forwarder %s ==> %s from connection %d shutting down" % (sockNames[forwarder.inSock], sockNames[forwarder.outSock], self.connIndex)
        if len(forwarders) == 0:
            self.die()
    def die(self):	# Closes socket and removes from list of names
        print "connection %d shutting down" % self.connIndex
        for s in [self.csock]:
            del sockNames[s]
            try:
                s.close()
            except:
                pass 
        connections.remove(self)
    def doErr(self):	#If ever get connection with error, close connection
        print "forwarder from client %s failing due to error" % repr(self.caddr)
        die()
                
class Listener:	#Listens for incoming connections then bind
	#A listener socket is a factory for manufacturing the new connection
    def __init__(self, bindaddr, addrFamily=AF_INET, socktype=SOCK_STREAM): #AF_INET is IPv4
        self.bindaddr = bindaddr
        self.addrFamily, self.socktype = addrFamily, socktype
        self.lsock = lsock = socket(addrFamily, socktype)
        sockNames[lsock] = "listener"
        lsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        lsock.bind(bindaddr)	#Bind connection
		#Set blocking must be false or it will fail right away
        lsock.setblocking(False)
        lsock.listen(2)	#Will only allow two clients to try to simultaneously connect
    def doRecv(self):
		#If listener socket is ready for reading, then create connection
        try:
            csock, caddr = self.lsock.accept() # socket connected to client
            conn = Conn(csock, caddr)
        except:
            print "weird.  listener readable but can't accept!"
            traceback.print_exc(file=sys.stdout)
    def doErr(self):
        print "listener socket failed!!!!!"
        sys.exit(2)

    def checkRead(self):	#Always want a new connection
        return self.lsock
    def checkWrite(self):	#Never want to write to listener socket
        return None
    def checkErr(self):
        return self.lsock
        
#Creates listener on any address "this machine - 0.0.0.0"
l = Listener(("0.0.0.0", listenPort))

def lookupSocknames(socks):	#Pass in array of sockets 
    return [ sockName(s) for s in socks ]	#returns array of socket names

while 1:	#Forever
	#Create dictionaries for read, write, error sockets
    rmap,wmap,xmap = {},{},{}   # socket:object mappings for select
    xmap[l.checkErr()] = l	#Always read from listener and check for errors
    rmap[l.checkRead()] = l	#Always read from listener and check for read
    for conn in connections:	#all connections
        for sock in [conn.csock]:	#all sockets
            xmap[sock] = conn
            for fwd in conn.forwarders:
                sock = fwd.checkRead()	#If socket available for reading, tell forwarder about it
                if (sock): rmap[sock] = fwd
                sock = fwd.checkWrite()	#If socket available for writing, tell forwarder
                if (sock): wmap[sock] = fwd
	#select will call forwarder 'FWD' everytime
	#select drives everything
    rset, wset, xset = select(rmap.keys(), wmap.keys(), xmap.keys(),60)
    #print "select r=%s, w=%s, x=%s" %
    if debug: print [ repr([ sockNames[s] for s in sset]) for sset in [rset,wset,xset] ]
    for sock in rset:
        rmap[sock].doRecv()	#for sockets ready to read, then doRecv
    for sock in wset:
        wmap[sock].doSend()	#for sockets ready to write, then doSend
    for sock in xset:
        xmap[sock].doErr()	#for sockets that have errors, then doErr

    

