from socket import *
import select
import os.path

# Versions:
# 1.2 - TCP Server with select - multiple clients - GET

# Globals
client_messages = {} # Dictionary to hold (client_addresses, message buffer)

# Class for processing readable sockets
class ProcessReads:
    def __init__(self, sock):
        self.sock = sock
        print 'Processing readable socket...'
        # Confirm this is our TCP socket
        if sock is tcpSock: # This is a new client connection request
            print 'A TCP Socket is ready for connection...'
            connection, clientAddress = sock.accept()
            #clientAddress = sock.getpeername()
            print 'Connected new client...'
            connection.setblocking(0)
            # Append to our readable sockets
            readSocks.append(connection)
        else:   # This is a message received from an already connected client
            clientData = sock.recv(1024)    # 1KB only
            clientAddress = sock.getpeername()
            if clientData:
                print 'Processing data from readable client socket...'
                print 'Data is: ' + clientData
                # Need to add to dictionary with (client_address, buffer for message)
                # Then can read until received GET or PUT
                if clientData[:3] == "GET":
                    print 'GET request received, parsing filename...'
                    strParseFile = clientData[3:]
                    strFileName = strParseFile.strip('@')
                    print 'Filename is: ' + strFileName + ', searching for file...'
                    # Check if file exists
                    if os.path.isfile(strFileName):
                        print 'File found, preparing to send file size...'
                        fileSize = os.path.getsize(strFileName)
                        sock.send(str(fileSize)+'@')
                        print 'File size sent, preparing to send file...'
                        myFile = open(strFileName,'rb')   # Open as binary file
                        fileBuffer = myFile.read(1024)   # Read and send only 1KB at a time
                        while (fileBuffer):
                           sock.send(fileBuffer)
                           print('Sent data: ',repr(fileBuffer))
                           fileBuffer = myFile.read(1024)    # Read next 1KB
                        myFile.close()
                    
                        print 'File transfer complete'
                    else:
                        print 'File not found, notifying client and closing connection...'
                        sock.send('ERR@File not found@')
                        sock.close()
                        readSocks.remove(sock)
                elif clientData[:3] == "PUT":
                    print 'PUT request received, parsing filename...'
                else:
                    print 'not a GET or PUT request'
            else:   # Empty buffer from connected readable client socket means closed connection
                print 'Reading empty buffer from client, closing connection...'
                # Remove the socket from our expected readable sockets
                readSocks.remove(sock)
                sock.close()

serverPort = 10000
serverHost = ''

# Create a TCP socket and bind it to server port
tcpSock = socket(AF_INET, SOCK_STREAM)
#Set blocking must be false or it will fail right away
tcpSock.setblocking(0)
tcpSock.bind((serverHost, serverPort))
print 'TCP Echo Server starting up on port 10000...'

# Set the TCP socket to listen for incoming connections
# Max 1 simultaneous
tcpSock.listen(1)

# Sockets which we expect to read from
readSocks = [ tcpSock ]

# Sockets which we expect to write to
writeSocks = [ ]

while readSocks:
    #select drives everything
    readableSocks, writableSocks, errorSocks = select.select(readSocks, writeSocks, readSocks)
    # Process the readable sockets
    for sock in readableSocks:
        ProcessReads(sock)
    for sock in writableSocks:
        print 'Processing writeable sockets...'
    for sock in errorSocks:
        print 'Processing error sockets...'