import socket
import threading
import sys

mutex = threading.Lock()

clients = [] 
user_names_set = set([])

def start_server():
	try:
		custom_port = 49152 #ports from 49152-65535 can be used for custom purposes
		bad_port = True
		chatroom = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket with the address family AF_INET and socket type SOCK_STREAM
		
		hostname = socket.gethostbyname(socket.gethostname()) #The current machine becomes the server

		while(bad_port and custom_port < 65536): #Bind the socket to a port number that is not already taken
			try: #try binding with the given port number
				chatroom.bind((hostname, custom_port))
			except socket.error: #if it is already taken, 
				custom_port += 1 #increment the port number by 1
			else:
				bad_port = False
				print "Using host", "'" + hostname + "'", "and port", custom_port
		
		if custom_port == 65536:
			sys.exit("Error: Unable to find a port that is not already taken. Something has gone wrong...")

		chatroom.listen(1) #begin listening for incoming requests.

		while True: #Always accept new connections
			conn, address = chatroom.accept() #conn is the socket, address is a tuple of (host, port)
			if len(clients) < 10:
				user_name_exists = True
				while(user_name_exists):
					chosen_user_name = conn.recv(4096) #the first message from the client is the name
					if chosen_user_name not in user_names_set:
						user_name_exists = False
						
						conn.sendall("True") #Communicate to the client that the name is not taken
						client = {}
						client['user_name'] = chosen_user_name
						client['connection'] = conn
						
						mutex.acquire()
						clients.append(client)
						for client in clients:
							if client['user_name'] != chosen_user_name:
								client['connection'].sendall(chosen_user_name + " has joined the chatroom.\n")
						user_names_set.add(chosen_user_name)#add the unique name to the list
						mutex.release()
						
						msg_thread = threading.Thread(target=listen_for_msgs, args=(client,chatroom))
						msg_thread.start() #Begin a new thread that listens for messages from this client
					else:
						conn.sendall("False") #Communicate to the client that the name is taken
						print chosen_user_name, "already taken."
			else:
				print "Too many clients are attempting to connect"
				conn.sendall("/too_many")
	except KeyboardInterrupt:
		print "Server has initiated shutdown"
		warn_and_close(chatroom)




def listen_for_msgs(connection, chatroom):
	user_has_left = False #if the user sends /exit, /quit, or /part, this will be set to true
	server_closing = False

	while(user_has_left == False and server_closing == False):
		msg = connection['connection'].recv(4096)

		if msg == '/connection_closed': #A client will send /connection_closed to acknowledge the server shutdown.s
			mutex.acquire()
			clients.remove(connection)
			user_names_set.remove(connection['user_name'])
			mutex.release()
			
			if len(clients) == 0: #If all clients have acknowledged the shutdown and themselves closed, the chatroom can close
				chatroom.close()
				sys.exit("Chatroom closed.")
			
			server_closing = True

		if msg == '/exit' or msg == "/quit" or msg == "/part":
			mutex.acquire()
			clients.remove(connection)
			user_names_set.remove(connection['user_name'])
			mutex.release()

			connection['connection'].sendall("/bye") #Tell the client that it is no longer listening to it
			
			user_has_left = True
		
		if msg == '/connection_closed/': #used so the user doesn't inadvertantly send an admin command
			msg = '/connection_closed'

		if (user_has_left == False):
			msg = connection['user_name'] + ": " + msg
		elif (user_has_left == True):
			msg = connection['user_name'] + " has left the chatroom."

		if (server_closing == False):
			mutex.acquire()
			for client in clients:
				if client['user_name'] != connection['user_name']:
					client['connection'].sendall(msg)
			mutex.release()


def warn_and_close(connection):
	for client in clients:
		client['connection'].sendall("/shutdown")

start_server()














