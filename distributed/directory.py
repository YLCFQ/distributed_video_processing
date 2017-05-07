import socket
from packet import PacketType, Packet, RegisterPacket, LoadPacket, Header
import threading
import time
import os
import multiprocessing
from collections import deque
#from twisted.python import log
#from twisted.internet import reactor
#from autobahn.twisted.websocket import WebSocketServerProtocol
#from autobahn.twisted.websocket import WebSocketServerFactory

alive = False
process_queue = deque()
process_semaphore = threading.Semaphore(0)
peer_servers = []
peer_paramiko = []
#These are parallel arrays
packet_queue = deque()
packet_semaphore = threading.Semaphore(0)
peer_count = -1

#Websocket server
#WebSocketServerProtocol)
class MyServerProtocol():
	def onConnect(self, request):
		print "A client has connected!"
	def onClose(self, wasClean, code, reason):
		1
	def onMessage(self, payload, isBinary):
		#Receive 0 then look for 0.mp4 to process
		print payload
		try:
			process(id)
		except Exception as e:
			print "Error occurred when receiving a message from client " + str(e)

class ProcessRequest:
	def __init__(self, offset, duration, index, id):
		self.offset = offset #-ss 00:25
		self.duration = duration #-t 00:01
		self.index = index #0-29
		self.id = id #12394e982348923

class ProcessThread(threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		print "Thread #" + str(threadID) + " has started!"
	def run(self):
		global alive
		while alive:
			process_semaphore.acquire()
			if process_queue:
				request = process_queue.popleft()
				movie_file = './processing/' + str(request.id) + '/movie.mp4'
				split_directory = './processing/' + str(request.id) + '/' + str(request.index) '/'
				midPath = split_directory[:split_directory.rfind(".")] + "%d.png"
				#1-24.png

				



				offset = request.offset #-ss flag for ffmpeg
				duration = request.duration #-t flag for ffmpeg
				#DO FFMPEG SPLIT

				ffmpegBreak = subprocess.Popen(["ffmpeg", "-ss", offset] + ["-t", duration] + ["-i", movie_file, midPath], stdout=outstream, stderr=subprocess.STDOUT)
				ffmpegBreak.wait()

				#Once done splitting here

				send_available(request.id, request.index, split_directory)
		
class PacketThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		global alive, packet_queue, packet_semaphore
		while alive:
			packet_semaphore.acquire()
			if packet_queue:
				packet = packet_queue.popleft()

				if type(packet) is RegisterPacket:
					#Handle register pqacket here
					print "Handling register packet"
				elif type(packet) is LoadPacket:
					1




def add_file(path):
	1
	#Remove and move somewhere else
	#Then add to the fucking queue

class AcceptThread(threading.Thread):
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
	def run(self):
		global alive, peer_servers
		print "Server is ready to accept peer connections."
		while alive:
			(new_socket, address) = self.socket.accept()
			peer_servers.append(new_socket)
			print "Peer server has connected!"
			ReceiveThread(new_socket).start()


class ReceiveThread(threading.Thread):
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
	def run(self):
		global alive, packet_queue, packet_semaphore
		while alive:
			headerBytes = self.socket.recv(8)
			header = Header()
			header.unpack(headerBytes)
			print "Received a packet!"

			packetBytes = self.socket.recv(header.size)

			if header.type == PacketType.Register:
				print "Found a register packet!"
				packet = RegisterPacket()
				packet.unpack(packetBytes)
				packet_queue.append(packet)
			
			elif header.type == PacketType.Load:
				packet = LoadPacket()
				packet.unpack(packetBytes)
				packet_queue.append(packet)
			
			else:
				packet = Packet()
				packet.unpack(packetBytes)
				packet_queue.append(packet)
			
			packet_semaphore.release()
			print "Packet has been added to packet queue"
def determine_split(path):
	#Given a path determine how many splits are there. For example 0:30 with 1 second split is 30 splits
	#Ffprobe
	return 30
def process(id):
	global process_queue
	print "Processing " + str(id) + ".mp4"
	#Move /uploading/0.mp4 to /processing/0/0.mp4
	os.mkdir('./processing/' + str(id))
	os.mkdir('./processing/' + str(id) + '/completed') #Making the completed directory. Movies will come back here SCP'd in directly.
	movie_file = './processing/' + str(id) + '/movie.mp4'
	os.rename('./uploading/' + str(id) + '.mp4', movie_file)

	for x in range(0, len(determine_split(movie_file))):
		os.mkdir('./processing/' + str(id) + '/' + str(x))
		process_queue.append(ProcessRequest(x, 1, x, id)) #Means starting at offset x to 1
		#Need to format 00:01 from x so if x is 61 then it is 1:01
		#Make folders from 0-4 if determine_split is given from it

def send_available(id, index, path):
	global peer_count, peer_servers, peer_paramiko
	#Given a path like ./processing/0/0/
	#Send all files in that path to a server
	peer_count = peer_count + 1

	if peer_count >= len(peer_servers):
		peer_count = 0

	#paramiko
	#send all files in path
	for root, directories, filenames in os.walk(path):
		for filename in filenames:
			1 #include SCP here
	loadHeader = Header()
	loadHeader.type = PacketType.LoadPacket

	loadPacket = LoadPacket()
	loadPacket.id = id
	loadPacket.index = index

	loadHeader.size = len(loadPacket.pack())

	print "Sending Load Packet to Peer Server #" + str(peer_count) + " with id " + str(id) + " and index: " + str(index)
	peer_servers[peer_count].sendall(loadHeader.pack())
	peer_servers[peer_count].sendall(loadPacket.pack())




alive = True
master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
master_socket.bind(('0.0.0.0', 27015))
master_socket.listen(0)

AcceptThread(master_socket).start()
PacketThread().start()

pu_count = multiprocessing.cpu_count()
#Leave one out for server and other shit
print "Starting Process Threads..."
for x in range(0, pu_count - 1):
	ProcessThread(x).start()

#factory = WebSocketServerFactory()
#factory.protocol = MyServerProtocol

#reactor.listenTCP(6654, factory)
#reactor.run()
