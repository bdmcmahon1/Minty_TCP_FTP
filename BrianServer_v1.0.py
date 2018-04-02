from socket import *

# Versions:
# 1.0 - Simple TCP Echo Server without select

serverPort = 10000
serverHost = ''

# Create a TCP socket and bind it to server port
tcpSock = socket(AF_INET, SOCK_STREAM)
tcpSock.bind((serverHost, serverPort))

# Set the TCP socket to listen for incoming connections
# v1.0 - Max 1 simultaneous
tcpSock.listen(1)
print 'Server listening on port 10000...'
while 1:
    # Create new connection/socket for client
    clientConn, clientAddr = tcpSock.accept()
    print 'Accepted new connection from client: ' + clientAddr
    while 1:
        clientData = clientConn.recv(1024) # Only get up to 1 KB
        print 'Received data: ' + clientData
        if clientData:
            print 'Echoing data back to client...'
            clientConn.send('echo data: ' + clientData)
        else:
            break
    clientConn.close()
    print 'Closing connection to client: ' + clientAddr