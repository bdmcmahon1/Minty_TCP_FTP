from socket import *
import select

# Versions:
# 1.1 - Simple TCP Echo Server with select

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
        print 'Processing readable sockets...'
        # Confirm this is our TCP socket
        if sock is tcpSock: # This is a new client connection request
            print 'A TCP Socket is ready for connection...'
            connection, clientAddress = sock.accept()
            print 'Connected new client...'
            connection.setblocking(0)
            # Append to our readable sockets
            readSocks.append(connection)
        else:   # This is a message received from an already connected client
            clientData = sock.recv(1024)    # 1KB only
            if clientData:
                print 'Processing data from readable client socket...'
                print 'Data is: ' + clientData
                print 'Echoing data back to client...'
                sock.send('echo data: ' + clientData)
            else:   # Empty buffer from connected readable client socket means closed connection
                print 'Reading empty buffer from client, closing connection...'
                # Remove the socket from our expected readable sockets
                readSocks.remove(sock)
                sock.close()