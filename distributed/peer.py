import socket
import threading
import os
import time
from collections import deque
from packet import Packet, PacketType, Header, CompletePacket, RegisterPacket, LoadPacket


packet_queue = deque()
packet_semaphore = threading.Semaphore(0)
alive = True

class PacketThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		while alive:
			packet_semaphore.acquire()
			if packet_queue:
				packet = packet_queue.popleft()
				#Public infomraiton
				if type(packet) is RegisterPacket:
					1
				elif type(packet) is LoadPacket:
					1
				elif type(packet) is ProgressPacket:
					1
				elif type(packet) is CompletePacket:
					1	


class ReceiveThread(threading.Thread):
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
	def run(self):
		headerBytes = self.socket.recv(8)
		header = Header().unpack(headerBytes)
		
		packetBytes = self.socket.recv(header.size)
		if header.type == PacketType.Register:
			packet_queue.append(RegisterPacket().unpack(packetBytes))
		elif header.type == PacketType.Load:
			packet_queue.append(LoadPacket().unpack(packetBytes))
		elif header.type == PacketType.Complete:
			packet_queue.append(CompletePacket().unpack(packetBytes))
		elif header.type == PacketType.Progress:
			packet_queue.append(ProgressPacket().unpack(packetBytes))
		print "Packet has been added to packet queue"

peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer_socket.connect(('0.0.0.0', 27015))
ReceiveThread(peer_socket).start()
