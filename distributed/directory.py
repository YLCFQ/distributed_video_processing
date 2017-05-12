import socket
from packet import PacketType, Packet, RegisterPacket, LoadPacket, Header
import threading
import time
import os
import multiprocessing
from collections import deque
import datetime 
import math
import subprocess
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from shutil import copyfile

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
	#def onConnect(self, request):
	#	print "A client has connected!"
	#def onClose(self, wasClean, code, reason):
	#	1
	def dataReceived(self,data):
		1
	def makeConnection(self, transport):
		1
		print "A client has connected!"
	def connectionLost(self, reason):
		1
	#def onMessage(self, payload, isBinary):
		#Receive 0 then look for 0.mp4 to process
	#	print payload
	#	try:
	#		process(id)
	#	except Exception as e:
	#		print "Error occurred when receiving a message from client " + str(e)

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
				ffmpeg_out = './processing/' + str(request.id) + '/' + str(request.index) + '/' + "%d.bmp"
				split_directory = './processing/' + str(request.id) + '/' + str(request.index) + '/'
				#1-24.png

				offset = request.offset #-ss flag for ffmpeg
				duration = request.duration #-t flag for ffmpeg
				#DO FFMPEG SPLIT


				outstream = open(os.devnull, 'w')
				ffmpegBreak = subprocess.Popen(["ffmpeg", "-ss", offset] + ["-t", duration] + ["-i", movie_file, ffmpeg_out], stdout=outstream, stderr=subprocess.STDOUT)
				ffmpegBreak.wait()

				print (request.index)
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
			
			packet_semaphore.release()
			print "Packet has been added to packet queue"
def determine_split(path):
	#Given a path determine how many splits are there. For example 0:30 with 1 second split is 30 splits
	#Ffprobe

	duration = subprocess.check_output(['ffprobe', '-i', path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])

	return int(float(duration)) + 1
def process(id):
	global process_queue, process_semaphore
	print "Processing " + str(id) + ".mp4"
	#Move /uploading/0.mp4 to /processing/0/0.mp4
	if not os.path.exists('./processing/' + str(id)):
		os.mkdir('./processing/' + str(id))
	if not os.path.exists('./processing/' + str(id) + '/completed'):
		os.mkdir('./processing/' + str(id) + '/completed') #Making the completed directory. Movies will come back here SCP'd in directly.
	movie_file = './processing/' + str(id) + '/movie.mp4'
	print './uploading/' + str(id) + '.mp4'
	#os.rename('./uploading/' + str(id) + '.mp4', movie_file)
	copyfile('./uploading/' + str(id) + '.mp4', movie_file)

	start_time = "00:00:00"
	duration = "00:00:00"
	duration_count = 5;
	start = datetime.datetime.now()

	total_time = determine_split(movie_file)
	default_time = datetime.datetime.strptime("00:00:00", '%H:%M:%S')
	convert_time =  default_time + datetime.timedelta(0,total_time/duration_count)
	duration = convert_time.strftime('%H:%M:%S')
	print ("total_time is : " + str(total_time))
	print("duration is : " + str(duration))

	print ('\t\t' + " processing start");
	for x in range(0, total_time/duration_count):
		os.mkdir('./processing/' + str(id) + '/' + str(x))
		process_queue.append(ProcessRequest(start_time, duration, x, id))
		process_semaphore.release() #Means starting at offset x to 1
		temp_time = datetime.datetime.strptime(start_time, '%H:%M:%S')
		temp_time = temp_time + datetime.timedelta(0, total_time/duration_count)
		start_time = temp_time.strftime('%H:%M:%S')

		#Need to format 00:01 from x so if x is 61 then it is 1:01
		#Make folders from 0-4 if determine_split is given from it
	
	while (not os.path.exists('./processing/' + str(id) + '/' + str(23) + '/1.bmp')):
		end = datetime.datetime.now()
	print ('\t\t' + " splitting finished at: " + str(end - start))

def send_available(id, index, path):
	global peer_count, peer_servers, peer_paramiko
	#Given a path like ./processing/0/0/
	#Send all files in that path to a server
	if len(peer_servers) == 0:
		return None
	peer_count = peer_count + 1

	if peer_count >= len(peer_servers):
		peer_count = 0

	#paramiko
	#send all files in path
	print "Walking path " + path
	if not os.path.exists('./received_images/' + str(id)):
		os.mkdir('./received_images/' + str(id))
	if not os.path.exists('./received_images/' + str(id) + '/' + str(index)):
		os.mkdir('./received_images/' + str(id) + '/' + str(index))
	for root, directories, filenames in os.walk(path):
		for filename in filenames:
			#debugging purposes
			#14949494940920_0_1.bmp
			#print("A: " + './processing/' + str(id) + '/' + str(index) + '/' + filename)
			#print("B: " + './received_images/' + str(index) +'/' + filename)
			os.rename('./processing/' + str(id) + '/' + str(index) + '/' + filename, './received_images/' + str(id) + '/' + str(index) + '/' +filename)
	loadHeader = Header()
	loadHeader.type = PacketType.Load

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
for x in range(0, 1):
	ProcessThread(x).start()

time.sleep(20)
process("1494544527034")

#factory = WebSocketServerFactory()
#factory.protocol = MyServerProtocol

#reactor.listenTCP(6654, factory)
#reactor.run()
