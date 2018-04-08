Readme for TCP Protocol Project
	Charlie Sullivan
	Brian McMahon
	Networking
	
NOTE - 

1) PROJECT NOT COMPLETED____________________________________________
2) Not fully tested through Stammering Proxy

The project is not currently completed. Here is a summary of what we 
have completed and our plan going forward.

Completed:
	Charlie:
		Client:
			GET and PUT both working exclusively
			Server currently unable to proces both requests so no testing
			has been succesful. 
		Server:
			none
		
	Brian:
		Server:
			Handles multiple clients.
			GET and PUT working, when clients send either GET or PUT requests (not both) simultaneously.
				Server unable to process simultaneous client requests where both GET and PUT requests are being sent.
		Client:
			None.

Plan moving forward:
	Charlie:
		Client:
			Complete
		Server:
			I have a test next wednesday. I will work Sunday a bit to 
			bring up my own versoin of a server. If I cannot complete it 
			I will resume work on it wednesday night.
			
			The client has provided me a good framework for the server
			and I think I can have something up and running soon.
	Brian:
		Client:
			Incomplete
		Server:
			Needs functionality for simultaneous GET and PUT requests. All other functionality present.
			Needs further testing with stammering proxy.
	

________________________________________________________________________	
	
Operation:

Current working files (as long as clients PUt or GET exclusively):
	Client:
		CharlieTCPclientV1.3.py
	Server:
		Brainserver_v1.3.py
	
How to test code:
	Server:
		The server only needs to be started, at which point our TCP FTP service will run on port 10000.
	
	Client:
		To do different things changes must be made to the client code as of
		now. Simple instructions reside in the file on how to operate the 
		client. Otherwise just runnning the client will provide output that 
		can offer infor on what is happening.
		
		Note: Simply running the client will work 
			python clientcode.py
			
Protocol:
	A couple of decisions were made when communicating at first to 
	establish what the client wanted and some relevant information. 
	
	Getting a file from server:
		To get a file from the server the client would make a request. 
		
		Client Request: GET@filename@
		
		the server would then look for the file. if it found the file it
		would respond back with the file size the start sending the file
		
		Server Response (file available): filesize@-----file data ------
		
		However, if the file was not there the server woud respond that
		the file was not found
		
		Server Response (file not present): FNF@
		
		The client would either close if not found or start storing the
		end of the file based on the filesize
		
	Putting a file on the server:
		
		Client Reqeust: PUT@filename@filesize@
		
		Once the request was set the client would start sending data 
		from the file. The server could then figure out when the file 
		was done based on the file size in the request.
		
		Server:
		
		The server will add the client address as a prefix to the filename when saving it on the server.
			E.g. 56879filename.txt
		
	
		
