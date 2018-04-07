#This test client will make a conecction with a server

#using python basic TCP tutorial from python.org

import socket
import select
import sys
import os
from pprint import pprint

saddr = ('localhost',10000)
filename = ''
state = 0
#State values and meanings
#0=program start or program end
#1=recieve data (get)
#2=send data (put)
client_list = []
buf_size = 1024
message = 'this sucks butt'

class client:
	global client_list
	
	def __init__(self,saddr,client_name,filename,action):
		self.state = 1
		self.name = client_name
		print "Binding %s to Socket" % self.name
		self.sock = sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		sock.setblocking(0)
		sock.connect_ex(saddr)
		self.filename = filename
		self.readData=""
		self.action = action
		self.saddr = saddr
		self.filesize = 0
		self.fileInfo = ""
		
	def send_req(self):
		if (self.action == "GET"):
			message = "GET@%s@" % self.filename
			print '%s sending request "%s"' % (self.name,message)
			self.sock.send(message)
		if (self.action == "PUT"):
			self.filesize = os.stat(filename).st_size
			message = "PUT@%s@%s:" % (self.filename,self.filesize)
			print '%s sending request "%s"' % (self.name,message)
			self.sock.send(message)
		self.state = 2
	def recieve_fileinfo(self):			
		#self.fileInfo.append(self.sock.recv(buf_size))
		self.fileInfo = self.fileInfo + self.sock.recv(buf_size)
		if '@' in self.fileInfo:
			atIndex = self.fileInfo.find('@')
			data = self.fileInfo[:atIndex]
			if data == 'FNF':
				print '%s: File Not found - closing client' % self.name
				self.state = 0
				#sockets_for_reading.remove(self.sock)
			else:
				self.filesize = self.fileInfo[:atIndex]
				#add anythin extra as start of read data
				#client.readData.append(fileInfo[(atindex+1):])
				client.readData = client.readData + self.fileInfo[(atIndex+1):]
				self.state = 3
	def recieve_data(self):
		currentRead = self.sock.recv(1024)
		print '%s: Data Recieved (%s)' % (self.name,currentRead)
		#self.readData.append(currentRead)
		self.readData = self.readData + currentRead
		if str(len(self.readData)) == self.filesize:
			print '%s: EOF reached - Writing data to file' % self.name
			fileout = 'C:\\' + self.name + 'OUT.txt'
			fp=open(fileout,"w+")
			fp.write(self.readData)
			fp.close
			self.state = 0
	def close_client(self):
		print '%s finished. Closing Connection.' % self.name
		self.sock.close()
		client_list.remove(self)
		sockets_for_reading.remove(self.sock)
		sockets_for_writing.remove(self.sock)
		sockets_for_error.remove(self.sock)
#create multiple clients
client_1 = client(saddr,'client_1','C:\\filename.txt',"GET")
client_2 = client(saddr,'client_2','C:\\filename.txt',"GET")
client_3 = client(saddr,'client_3','C:\\filename.txt',"GET")

client_list = [client_1,client_2,client_3]

sockets_for_reading = []
sockets_for_writing = []
sockets_for_error = []


for client in client_list:
	sockets_for_reading.append(client.sock)
	sockets_for_writing.append(client.sock)
	sockets_for_error.append(client.sock)
	
	#print out the client state to make sure they have been created properly
	print '%s Created. Here are some properties' % client.name
	pprint(vars(client))

#SETUP COMPLETE - RUNNING CODE BELOW____________________________________

while len(client_list):
	#if state variable calls for it run inputs	
	print 'calling select'
	sockets_ready_reading,sockets_ready_writing,sockets_with_error = select.select(sockets_for_reading,sockets_for_writing,sockets_for_error)
	
	for client in client_list:
		print '%s: processing state %s' % (client.name,client.state)
		#state 0 - ready fto close the client, all actions complete
		if client.state == 0:
			client.close_client()
		
		#state 1 - send requests
		if client.state == 1:
			if client.sock in sockets_ready_writing:
				client.send_req()

		#state 2 - recieve file size
		if client.state == 2:
			if client.sock in sockets_ready_reading:
				client.recieve_fileinfo()
		
		#state 3 - recieve data
		if client.state == 3:
			if client.sock in sockets_ready_reading:
				client.recieve_data()
				

print 'All clients complete - program closing'

#open all the files and print them later?


