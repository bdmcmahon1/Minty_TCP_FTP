#This test client will make a conecction with a server

#using python basic TCP tutorial from python.org

import socket

sAddr = ('localhost',50000)

buf_size = 1024


print "etablishing client"
client=socket.socket(socket.AT_INET,socket.SOCK_STREAM)
print "connecting to server"
client.connect(saddr)
print "sending Data(hello world)"
client.send('hello world')
print "waiting for response"
response = s.recv(buf_size)

s.close()
print "response: " response
