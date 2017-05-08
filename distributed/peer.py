import socket
import threading
import os
import time
from collections import deque
from packet import Packet, PacketType, Header, RegisterPacket, LoadPacket

import glob
import datetime
import dlib
import cv2


packet_queue = deque()
process_queue = deque()
packet_semaphore = threading.Semaphore(0)
process_semaphore = threading.Semaphore(0)
alive = True

#dlib library
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('./shape_predictor_68_face_landmarks.dat') #directory for shape_predictor_68_face_landmarks.dat

#resize the image 
image_ratio = 0.8

def ScanFrames (input_path, output_path):
	g = glob.glob(input_path[:input_path.rfind(".")] + "*.png")
	for i, fn in enumerate(g):
		print ("Handling frame " + str(i) + ":")
		tstart = datetime.now()
		HandleFrame(fn, output_path)
		tend = datetime.now()
		print("Finished handling frame " + str(tend - tstart))
	ffmpegBuild = subprocess.Popen(["ffmpeg", "-i", output_path, output_path+"final.mp4"], stdout=outstream, stderr=subprocess.STDOUT)# Run FFMPEG to rebake the video
	ffmpegBuild.wait()
	cleanUpImages(input_path, output_path)

def HandleFrame(input_path, output_path):
	img = cv2.imread(input_path, 1)

	ptsList, breadthList = detectFrame(img)
	markFrame(img, ptsList, breadthList)
	pupilData = getPupilData(input_path) #IPC to get pupil data
	markPupil(img, pupilData, breadthList)

	cv2.imwrite(output_path, img)



def detectFrame(img):
	global detector, predictor, image_ratio

	image = cv2.resize(img, (0,0), fx=image_ratio, fy=image_ratio)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	detections = detector(gray, 1)# type(detections) == dlib.rectangles

	ptsList = []
	breadthList = []

	for i, d in enumerate(detections):# type(d) == dlib.rectangle
		print("\t\tBeginning prediction (detection " + str(i) + ")")
		tstart = datetime.now()
		shape = predictor(gray, d)# type(shape) == dlib.full_object_detection

		pts = []
		for p in shape.parts():
			if p.x > 0 and p.y >0:
                #pts.append((p.x, p.y))
				pts.append((p.x/image_ratio, p.y/image_ratio))
		ptsList.append(pts)
	
	breadthList.append(np.sqrt(d.width() ** 2 + d.height() ** 2)) #this is a list of magnitudes of the hypotenuse (so called breadth) of the face detection
	tend = datetime.now()
	print("\t\t" + str(tend - tstart))

	return ptsList, breadthList

def markFrame(img, ptsList, breadthList):
	if raw_input("Overwrite " + fn + " Y/N?") == "Y":
		print("\t\tBeginning Delauney drawing algorithm")
		tstart = datetime.now()
	
		
		i = 0
		for pts in ptsList:
			bounds = (0, 0, img.shape[1], img.shape[0])
			subdiv = cv2.Subdiv2D(bounds)
			for p in pts:
				subdiv.insert(p)
			tris = subdiv.getTriangleList();
			for t in tris:
				pt1 = (t[0], t[1])
				pt2 = (t[2], t[3])
				pt3 = (t[4], t[5])

				if in_rect(bounds, pt1) and in_rect(bounds, pt2) and in_rect(bounds, pt3):
					cv2.line(img, pt1, pt2, (0, 255, 0), int(breadthList[i] * 1/100), 8, 0) #tried using cv2.CV_AA
					cv2.line(img, pt2, pt3, (0, 255, 0), int(breadthList[i] * 1/100), 8, 0)
					cv2.line(img, pt3, pt1, (0, 255, 0), int(breadthList[i] * 1/100), 8, 0)
			i+=1 #something weird may happen
		tend = datetime.now()
		print("\t\t" + str(tend - tstart))
	else:
		print("Permission denied. (mark Frame)")

def getPupilData(input_path):
	print("\t\tsubprocessing pupil data")
	tstart = datetime.now()
	eyeLine = subprocess.Popen(["./eyeLine", "-d", input_path], stdout=subprocess.PIPE, shell=True)
	eyeLine.wait()
	eyeLineStdout = eyeLine.communicate()[0]

	spaceIndexing = eyeLineStdout.split(" ")
	pupilData = []

	if len(spaceIndexing) % 5 == 0:				#it parsed appropriately
		spaceIndexing = spaceIndexing[:len(spaceIndexing)-1] 	#remove newlines elements from parsing, NOT FINISHED, ONLY HANDLES ONE SET ATM... LAZINESS
		for i, sp in enumerate(spaceIndexing):
			if i & 1 == 0: #every other one (think c: step+=2)
				pupilData.append((int(sp), int(spaceIndexing[i+1])))
	else:
		pupilData.append((-1, -1)) #dummy data necessary for drawing appropriate scaled pupils later
    
	tend = datetime.now()
	print("\t\t" + str(tend - tstart))
	return pupilData


def markPupil(img, pupilData, breadthList):
	print("\t\tDrawing pupils to image.")
	if raw_input("Overwrite " + fn + " Y/N?") == "Y":
		tstart = datetime.now()
		i = 0
		for pupil in pupilData:
			if pupil != (-1, -1):
				pupilArray = np.array(pupil, np.int32).reshape((-1, 1, 2))
				cv2.polylines(img, pupilArray, True, (0, 0, 255/(i+1)), int(breadthList[i/2] * 3/100))
				cv2.polylines(img, pupilArray, True, (255/(i+1), 0, 0), int(breadthList[i/2] * 1/100))
			i += 1
		tend = datetime.now()
		print("\t\t" + str(tend - tstart))
	else:
		print("Permission denied. (mark Pupil")

def cleanUpImages(input_path, output_path):
	for f in glob.glob(input_path[:input_path.rfind(".")] + "*.png"):
		os.remove(f)
	for f in glob.glob(output_path[:output_path.rfind(".")] + "*.png"):
		os.remove(f)



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
					print "Added load packet to process queue with id " + str(packet.id) + " index: " + str(packet.index)
					process_queue.append(ProcessRequest(packet.id, packet.index))



class ProcessThread(threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		print "Thread #" + str(threadID) + " has started!"
	def run(self):
		while alive:
			process_semaphore.acquire()
			if process_queue:
				request = process_queue.popleft()
				input_path = '../received/' + str(request.id) + "_" + str(packet.index)
				output_path = '../completed/' + str(request.id)
				if not os.path.exists(output_path):
					os.makedirs(output_path)
				ScanFrames(input_path, output_path)


class ProcessRequest:
	def __init__(self, index, id):
		self.index = index #0-29
		self.id = id #12394e982348923


class ReceiveThread(threading.Thread):
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
	def run(self):
		while alive:
			headerBytes = self.socket.recv(8)
			header = Header()
			header.unpack(headerBytes)
			
			packetBytes = self.socket.recv(header.size)
			if header.type == PacketType.Register:
				packet = RegisterPacket()
				packet.unpack(packetBytes)
				packet_queue.append(packet)
			elif header.type == PacketType.Load:
				packet = LoadPacket()
				packet.unpack(packetBytes)
				packet_queue.append(packet)

			packet_semaphore.release()


peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	peer_socket.connect(('0.0.0.0', 27015))
	initialHeader = Header()
	initialHeader.type = PacketType.Register

	registerPacket = RegisterPacket()
	registerPacket.id = 0

	initialHeader.size = len(str(registerPacket.pack()))
	peer_socket.sendall(initialHeader.pack())
	peer_socket.sendall(registerPacket.pack())

except Exception as e:
	print "Error occurred while connecting " + str(e)
	exit(0)
ReceiveThread(peer_socket).start()
PacketThread().start()
