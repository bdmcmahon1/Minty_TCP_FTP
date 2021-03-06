#This client will either GET a file from a server or put one on the Server
#
#Instructions:
#	Example of client creation 	
#		client_1 = client(saddr,'client_1','declaration.txt',"PUT")
#	saddr 				- server address
#	'client_1' 			- name of client, named numerically for ease of 
#							debugging
#	'declaration.txt' 	- name of file you wish to GET or PUT
#	"PUT" 				- operation you wish to preform 
#							GET - Pull file from server
#							PUT - sotre local file on computer
#
#	Add Client:
#		-To add a client copay and paste the example code in the Build 
#		Clident section below and rename the object assignment to a unique 
#		identifier. Fill in arguments as you see fi
#
#		-Add your client object name to the 'Client List' as well
#			client_list = [client_1,client_2,client_3......]
#	
#	Remove Client:
#		To remove simply delete the line of text creating the client 
#		object and remove it from the Client List
#_______________________________________________________________________

#Define libraries and global variables__________________________________
import socket
import select
import sys
import os
from pprint import pprint

saddr = ('localhost',10000)
client_list = []
#_______________________________________________________________________

#Define Client Class____________________________________________________COMMENTS ON CODE OPERATION__________________________________
class client:
	global client_list
	
	def __init__(self,saddr,client_name,filename,action):
		self.state = 1													#list of state meanings in main program loop
		self.name = client_name
		print "Binding %s to Socket" % self.name
		self.sock = sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		sock.setblocking(0)
		sock.connect_ex(saddr)
		self.filename = filename
		self.readData=""
		self.action = action											#so we know if client is getting or putting
		self.saddr = saddr
		self.filesize = 0
		self.fileInfo = ""
		if self.action == "PUT":										#if putting a file, open it and store contents to send later
			fp=open(self.filename,"r")
			self.fileData = fp.read()
			fp.close()
		else:
			self.fileData = ""											#if getting a file empty string to be poopulated later
		self.send_win_low = 0											#variables used when sending windows of 1024 bytes for putting a file
		self.send_win_high = 1											#use is clear in the send_data() function of the client class
			
	def send_req(self):
		if (self.action == "GET"):
			message = "GET@%s@" % self.filename
			print '%s sending request "%s"' % (self.name,message)
			self.sock.send(message)
			self.state = 2
		if (self.action == "PUT"):
			self.filesize = os.stat(self.filename).st_size
			message = "PUT@%s@%s@" % (self.filename,self.filesize)
			print '%s sending request "%s"' % (self.name,message)
			self.sock.send(message)
			self.state = 4
			
	def recieve_fileinfo(self):											#fileInfo is meta information about the file itsself, not what is in it
		self.fileInfo = self.fileInfo + self.sock.recv(1024)
		if self.action == "GET":										#if getting a file the client will get back FNF(file not found)
			if '@' in self.fileInfo:									#or the size of the file so it knows when the transfer is complete
				atIndex = self.fileInfo.find('@')
				data = self.fileInfo[:atIndex]
				if data == 'FNF':
					print '%s: File Not Found' % self.name
					self.state = 0
				else:													#if file present store file size and save any data that may have been
					self.filesize = self.fileInfo[:atIndex]				#sent so you dont lose it
					client.readData = client.readData + self.fileInfo[(atIndex+1):]
					self.state = 3
		if self.action == "PUT":										#if putting a file ideally the server will send an ACK back when the 
			atIndex = self.fileInfo.find('@',4)							#entire file transfer is complete
			if atIndex>0:
				fileACK = self.fileInfo[4:atIndex]
				if fileACK == self.filename:
					print '%s: Server recieved file' % self.name
					self.state = 0		
					
	def recieve_data(self):
		currentRead = self.sock.recv(1024)
		print '%s: Data Recieved (%s)' % (self.name,currentRead)
		self.readData = self.readData + currentRead
		if str(len(self.readData)) == self.filesize:					#once the end of file has been reached store data into a file
			print '%s: EOF reached - Writing data to file' % self.name
			fileout = self.name + 'OUT.txt'
			fp=open(fileout,"w+")
			fp.write(self.readData)
			fp.close
			self.state = 0
			
	def close_client(self):
		print '%s finished. Closing Connection.' % self.name
		#send ack to server that I got the entire file
		#if self.action == "GET":										#Send ACK to server that entire file was recieved
		#	self.sock.send('ACK@%s') % self.filename
		self.sock.close()												#close the client and remove it from all lists so nothing calls on
		client_list.remove(self)										#a dead client again
		sockets_for_reading.remove(self.sock)
		sockets_for_writing.remove(self.sock)
		sockets_for_error.remove(self.sock)
		
	def send_data(self):
		message = self.fileData[1024*self.send_win_low:1024*self.send_win_high]
																		#here is where win_high/low happen. Each pass through this state only
		if len(message):												#send 1024 bytes out at a time. This allows us to make sure the buffer
			self.sock.send(message)										#has room and have all clients operate rather than waiting for 
			self.send_win_low = self.send_win_low + 1					#one to finish before moving to next client
			self.send_win_high = self.send_win_high + 1
			print '%s: Sent Data (%s)' % (self.name,message)
			return
		else:
			print '%s: Entire Message Sent - Ready to close' % self.name
			self.state = 0
		
		
	
#_______________________________________________________________________	
		
#Client Creation________________________________________________________
client_1 = client(saddr,'client_1','declaration.txt',"PUT")
client_2 = client(saddr,'client_2','declaration.txt',"GET")
client_3 = client(saddr,'client_3','declaration.txt',"PUT")
client_list = [client_1,client_2,client_3]
#_______________________________________________________________________

#Prepare lists for select function______________________________________
sockets_for_reading = []
sockets_for_writing = []
sockets_for_error = []

for client in client_list:
	sockets_for_reading.append(client.sock)
	sockets_for_writing.append(client.sock)
	sockets_for_error.append(client.sock)
#_______________________________________________________________________	

#Print client information for debugging_________________________________	
	print '%s Created. Here are some properties' % client.name
	pprint(vars(client))
#_______________________________________________________________________

#SETUP COMPLETE - Execute program_______________________________________

while len(client_list):	
	print 'calling select'
	sockets_ready_reading,sockets_ready_writing,sockets_with_error = select.select(sockets_for_reading,sockets_for_writing,sockets_for_error)
	
	for client in client_list:
		print '%s: processing state %s' % (client.name,client.state)
		
		#state 0 - All actions complete - close client
		if client.state == 0:
			client.close_client()
		
		#state 1 - send requests
		if client.state == 1:
			if client.sock in sockets_ready_writing:
				client.send_req()

		#state 2 - recieve file information
		if client.state == 2:
			if client.sock in sockets_ready_reading:
				client.recieve_fileinfo()
		
		#state 3 - recieve data (GET)
		if client.state == 3:
			if client.sock in sockets_ready_reading:
				client.recieve_data()
		
		#state 4 - send Data (PUT)
		if client.state == 4:
			if client.sock in sockets_ready_writing:
				client.send_data()
				
#_______________________________________________________________________


print 'All clients complete - program closing'

#open all the files and print them later?


