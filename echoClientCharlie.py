import random
import sys
import traceback
from select import *
from socket import *

import re
import params

#input parameter default values
#-default server address
#-default num of clients is 4 unless specified by system arguments
switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50000"),
    (('-n', '--numClients'), 'numClients', "4"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False) # boolean (set if present)
    )

#you can just parse stuff into a dictionary apparently?
#-what library is this!!!
paramMap = params.parseParams(switchesVarDefaults)
server, usage, debug = paramMap["server"], paramMap["usage"], paramMap["debug"]
numClients = int(paramMap["numClients"])


if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print "Can't parse server:port from '%s'" % server
    sys.exit(1)


sockNames = {}               # from socket to name
nextClientNumber = 0     # each client is assigned a unique id

            
    
liveClients, deadClients = set(), set()

class Client:
    def __init__(self, af, socktype, saddr):							#af=AF_INET - (host ip, port integer) for your server address requirements
																		#socktype = SOCK_STREAM - 
																		#saddr =server address - give by (servHost, ServPort)
        global nextClientNumber
        global liveClients, deadClients
        self.saddr = saddr # addresses
																		#initialize all of the properties of the new client object
        self.numSent, self.numRecv = 0,0
        self.allSent = 0
        self.error = 0
        self.isDone = 0
        self.clientIndex = clientIndex = nextClientNumber				#Once this client built, increment so next iteration builds the next client
        nextClientNumber += 1
        self.ssock = ssock = socket(af, socktype)						#client socket definition and assignment 
																		#(talking to same server) - returns object of type socket
        print "New client #%d to %s" % (clientIndex, repr(saddr))		#display cleient creation and shich server it talks to
        sockNames[ssock] = "C%d:ToServer" % clientIndex					#assign each client to sockNames dictionary by socket definition
        ssock.setblocking(False)										#
        ssock.connect_ex(saddr)											#same as connect with special error handling built in
        liveClients.add(self)											#add newly created client to list of active clients
    def doSend(self):
        try:
            self.numSent += self.ssock.send("a"*(random.randrange(1,2048)))
        except Exception as e:
            self.errorAbort("can't send: %s" % e)
            return
        if random.randrange(0,200) == 0:
            self.allSent = 1
            self.ssock.shutdown(SHUT_WR)
    def doRecv(self):
        try:
            n = len(self.ssock.recv(1024))
        except Exception as e:
            print "doRecv on dead socket"
            print e
            self.done()
            return
        self.numRecv += n
        if self.numRecv > self.numSent: 
            self.errorAbort("sent=%d < recd=%d" %  (self.numSent, self.numRecv))
        if n != 0:
            return
        if debug: print "client %d: zero length read" % self.clientIndex
        # zero length read (done)
        if self.numRecv == self.numSent:
            self.done()
        else:
            self.errorAbort("sent=%d but recd=%d" %  (self.numSent, self.numRecv))
    def doErr(self, msg=""):
        error("socket error")
    def checkWrite(self):												#WHAT ARE WE ACTUALLY CHECKING HERE??????	
        if self.allSent: 
            return None            
        else:			
            return self.ssock
    def checkRead(self):
        if self.isDone: #if the client is done return nothing
            return None
        else:
            return self.ssock #if not done return the socket it was assigned
    def done(self):
        self.isDone = 1
        self.allSent =1
        if self.numSent != self.numRecv: self.error = 1
        try:
            self.ssock(close)
        except:
            pass
        print "client %d done (error=%d)" % (self.clientIndex, self.error)
        deadClients.add(self)
        try: liveClients.remove(self)
        except: pass
            
    def errorAbort(self, msg):
        self.allSent =1
        self.error = 1
        print "FAILURE client %d: %s" % (self.clientIndex, msg)
        self.done()
        
                  
def lookupSocknames(socks):
    return [ sockName(s) for s in socks ]
#creat instances of each client using the client clas
#add each instancs to the live clients list
for i in range(numClients):												#for every client in the numClients, establish a client
    liveClients.add(Client(AF_INET, SOCK_STREAM, (serverHost, serverPort)))


while len(liveClients):													#if clients are present and active continue operating client program
    rmap,wmap,xmap = {},{},{}   										# socket:object mappings for select
    for client in liveClients: 											#for each client that is still present and active
		sock = client.checkRead()										#       READING
		if (sock): rmap[sock] = client									#       check if there are any sockets to read (socket client was assigned)
																		#       if something is to be read - add the client to the list of read for select
		sock = client.checkWrite()										#       WRITING
		if (sock): wmap[sock] = client									#       check the sockets to be written to if they are empty (able to be written to         
																		# Not really sure what is happining here--------
        xmap[client.ssock] = client										#		Writing
																		#		check sockets with errors
																		#THIS SECTION OS FOR DEBUGGING
    if debug: print "select params (r,w,x):", [ repr([ sockNames[s] for s in sset] ) for sset in [rmap.keys(), wmap.keys(), xmap.keys()] ]
    rset, wset, xset = select(rmap.keys(), wmap.keys(), xmap.keys(),60)	
    #print "select r=%s, w=%s, x=%s" %
    if debug: print "select returned (r,w,x):", [ repr([ sockNames[s] for s in sset] ) for sset in [rset,wset,xset] ]
																		#handling everything after checking the sockets
    for sock in xset:													#handle error sockets
        xmap[sock].doErr()
    for sock in rset:													#handle read sockets
        rmap[sock].doRecv()
    for sock in wset:
        wmap[sock].doSend()
    

numFailed = 0
for client in deadClients:
    err = client.error
    print "Client %d Succeeded=%s, Bytes sent=%d, rec'd=%d" % (client.clientIndex, not err, client.numSent, client.numRecv)
    if err:
        numFailed += 1
print "%d Clients failed." % numFailed

