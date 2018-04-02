import sys
import traceback
from select import *
from socket import *

import re
import params



#this will just return everything sent to it back to the place it came from

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

sockNames = {}               # from socket to name
nextConnectionNumber = 0     # each connection is assigned a unique id
#
#
#
#
#
#
#self referes to the 'this' instance of the class

#every method has a extra parameter spelled 'self'
#if i call x.checkWrite() - x becomes self in this code

class Fwd:
    def __init__(self, conn, inSock, outSock, bufCap = 1000):
        self.conn, self.inSock, self.outSock, self.bufCap = conn, inSock, outSock, bufCap
        self.inClosed, self.buf = 0, ""
    def checkRead(self):
        if len(self.buf) < self.bufCap and not self.inClosed: #read if something there to read (returns sock you want to read from or 'none'
            return self.inSock
        else:
            return None
    def checkWrite(self): #dont write if nothing to write (return sock you want to write to or None)
        if len(self.buf) > 0:
            return self.outSock
        else:
            return None
    def doRecv(self):
        b = "" #array of bytes that arrive
        try:
            b = self.inSock.recv(self.bufCap - len(self.buf))
        except:
            self.conn.die()
        if len(b): #if something present
            self.buf += b #append new data to end of buffer
        else: #if nothing present the importer is closed and we dont want to read it again (case covered in one note - this means end of file)
            self.inClosed = 1
        self.checkDone()
    def doSend(self): #n bytes from buffer then deledt them from buffer
        try:
            n = self.outSock.send(self.buf) #OS will take all bytes it can - so you may not be able to send whole buffer
            self.buf = self.buf[n:]
        except:
            self.conn.die()
        self.checkDone()
    def checkDone(self): #checks if the forward is done
        if len(self.buf) == 0 and self.inClosed: #if buffer is 0 and the input is closed nothing left to do
            try:
                self.outSock.shutdown(SHUT_WR)
            except:
                pass
            self.conn.fwdDone(self)
            
    
connections = set()
#for every client you have a connection
#for every client accepted make a new connection with a client address and which sockets to use
class Conn:
    def __init__(self, csock, caddr):
        global nextConnectionNumber
        self.csock = csock      # to client
        self.caddr = caddr	#client addressed
        self.connIndex = connIndex = nextConnectionNumber
        nextConnectionNumber += 1 #increment connection number to keep track of how many connections server has
        self.forwarders = forwarders = set() #set of forwarders
        print "New connection #%d from %s" % (connIndex, repr(caddr))
        sockNames[csock] = "C%d:ToClient" % connIndex #map connections to readable names
        forwarders.add(Fwd(self, csock, csock))  #make a forwarder connection client sock to itself | one connection contains one forwarder
        connections.add(self) #add this client and forwarder to the lest of connections (global sedt of connections
    def fwdDone(self, forwarder): #when done remove the forwarder and call die
        forwarders = self.forwarders
        forwarders.remove(forwarder)
        print "forwarder %s ==> %s from connection %d shutting down" % (sockNames[forwarder.inSock], sockNames[forwarder.outSock], self.connIndex)
        if len(forwarders) == 0:
            self.die()
    def die(self): #kill connection
        print "connection %d shutting down" % self.connIndex
        for s in [self.csock]:
            del sockNames[s]
            try:
                s.close()
            except:
                pass 
        connections.remove(self)
    def doErr(self): #causes it to die unexpectedly
        print "forwarder from client %s failing due to error" % repr(self.caddr)
        die()
          
          
#socekts and attached to clients and then there are listener sockets
#listen for connection then push it off somewhere
#if listener socket available for reading there is a new connection desired      
class Listener:
    def __init__(self, bindaddr, addrFamily=AF_INET, socktype=SOCK_STREAM): #(where to listen to (bind), ipv4, stream sock)
        self.bindaddr = bindaddr
        self.addrFamily, self.socktype = addrFamily, socktype
        self.lsock = lsock = socket(addrFamily, socktype) #make listener socket
        sockNames[lsock] = "listener"
        lsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        lsock.bind(bindaddr)
        lsock.setblocking(False) #bind non blocking - if you read and nothing there doesnt block just fails
        lsock.listen(2) #listen - 2 means up to 2 clients can be waiting before you call listen
    def doRecv(self): #if listener socket ready for reading
        try:
            csock, caddr = self.lsock.accept() # socket connected to client - accept connection
            conn = Conn(csock, caddr)
        except:
            print "weird.  listener readable but can't accept!"
            traceback.print_exc(file=sys.stdout)
    def doErr(self):
        print "listener socket failed!!!!!"
        sys.exit(2) #go away give up you have real issues

    def checkRead(self):
        return self.lsock
    def checkWrite(self):
        return None
    def checkErr(self):
        return self.lsock
        

l = Listener(("0.0.0.0", listenPort))

def lookupSocknames(socks):
    return [ sockName(s) for s in socks ]

while 1:
    rmap,wmap,xmap = {},{},{}   # socket:object mappings for select
    xmap[l.checkErr()] = l
    rmap[l.checkRead()] = l
    for conn in connections:
        for sock in [conn.csock]:
            xmap[sock] = conn
            for fwd in conn.forwarders:
                sock = fwd.checkRead()
                if (sock): rmap[sock] = fwd #if sock available for reading tell forwarder
                sock = fwd.checkWrite()
                if (sock): wmap[sock] = fwd #if available for writing " " 
    rset, wset, xset = select(rmap.keys(), wmap.keys(), xmap.keys(),60)
    #print "select r=%s, w=%s, x=%s" %
    if debug: print [ repr([ sockNames[s] for s in sset]) for sset in [rset,wset,xset] ]
    for sock in rset:
        rmap[sock].doRecv()
    for sock in wset:
        wmap[sock].doSend()
    for sock in xset:
        xmap[sock].doErr()
#ask every forwarder who wants to read and who wants to write
    

