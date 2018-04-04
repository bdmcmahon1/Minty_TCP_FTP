#This test client will make a conecction with a server

#using python basic TCP tutorial from python.org

import socket
import select

saddr = ('localhost',10000)

buf_size = 1024

message = 'this sucks butt'

print "etablishing client"
client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print "connecting to server"
client.connect(saddr)

#use select to know what to do 
#create lists for select to usereadSock = [clientSocket]
#for reading msgs from server
readSock = [client]
# empty list since we arent writing to sockets(used in queue
writeSock = [client]
# empty list - not interested in errors from select
errorSock = [client]
# time out variable since select has timeout built in
timeout = 1


while(1):
	readRdy,writeRdy,errorRdy = select.select(readSock,writeSock,errorSock)
		
	for socket in readRdy:
		client.send(message)
	for socket in writeRdy:
		response = client.recv(buf_size)
		print 'Message recieved: ' ,response
		print 'Closing Client'
		break
	for socket in errorRdy:
		#so some error shit
		print 'Error: closing client'
		break
				

client.close()
