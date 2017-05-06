import packet
from abc import ABCMeta, abstractmethod
from enum import Enum

class PacketType(Enum):
	Packet = 0
	Register = 1
	Load = 2
	Progress = 3
	Complete = 4
	
#4 bytes for packet type
#4 bytes for packet size
class Header:
	def __init__(self):
		1
	def unpack(self, bytes):
		#Take them all out
		1
	def pack(self):
		1

		

class Packet:
	__metaclass__ = ABCMeta

	@abstractmethod
	def unpack(self,bytes):
		pass
	def pack(self,):
		pass

class RegisterPacket(Packet):
	__metaclass = ABCMeta
	def __init__(self):
		1
	def unpack(self, bytes):
		1
	def pack(self):
		1

#From directory to peer
def LoadPacket(Packet):
	def pack(self):
		1
	def unpack(self,bytes):
		1

class ProgressPacket(Packet):
	def unpack(self,bytes):
		1
	def pack(self):
		1
#From peer to directory
def CompletePacket(Packet):
	def __init__(self):
		1
	def unpack(self, bytes):
		1
	def pack(self):
		1		
