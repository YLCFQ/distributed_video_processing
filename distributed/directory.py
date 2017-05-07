import socket
from packet import PacketType, Packet, RegisterPacket, LoadPacket, Header
import threading
import time
import os
from collections import deque

alive = False
process_queue = deque()
process_semaphore = threading.Semaphore(0)
peer_servers = []
packet_queue = deque()
packet_semaphore = threading.Semaphore(0)

class ProcessThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		global alive
		while alive:
			process_semaphore.acquire()
			if process_queue:
				f = process_queue.popleft()
				process_file(f)
		
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
				elif type(packet) is ProgressPacket:
					1
				elif type(packet) is CompletePacket:
					1

def process_file(path):
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
		global alive, packet_queue
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
			
			print "Packet has been added to packet queue"

	
alive = True
master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
master_socket.bind(('0.0.0.0', 27015))
master_socket.listen(0)

AcceptThread(master_socket).start()
PacketThread().start()

while alive:	
	time.sleep(1)
