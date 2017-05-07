import sys          # For argument handling
import datetime
import time
from datetime import datetime
import os, inspect  # For path handling, file deletion
import dlib         # For facial recognition (neural network)
import glob         # For file path handling
import subprocess   # For running FFMPEG
import cv2          # image input/output
import numpy as np  # For array handling, line scaling
#import scipy.misc

'''
TO HOOK INTO THE DATABASE (POSTGRES)
1. filename -> meta-data + frames
   meta-data -> face datapoints (for each frame)
2. video ID -> meta data -> eye datapoints (for each frame)
3. video ID -> meta data -> Delauney tri images (w/o overwrite)
'''

'''
To-Do:
Parallel Processing
Head Pos: Yaw, Pitch, Roll
write eye tracking coords to db
'''
lazy_output_file = None
global_script_start = datetime.now() 
URI_Handling = False
image_ratio = 0.5
#Prints the CLI help menu
def displayHelp():
    print(" Available Arguments\t\t\tDefault Arguments")
    print(" -h\tAccess the help menu (--help)")
    print(" -uri\thandle URI images (thanks Kevin/Pei)")
    print(" -l\tlose original frames(overwrite)\tFalse")
    print(" -r\trealtime (don't track pupils)\tFalse")
    print(" -p\tPath of the Dlib predictor\t" + run_dir + "/shape_predictor_68_face_landmarks.dat")
    print(" -f\tProcess only a single frame\tFalse")
    print(" -ss\tStart time of input file\t00:00.00")
    print(" -t\tDuration of final video\t\t00:01.00")
    print(" -i\tInput file path\t\t\t" + input_path)
    print(" -o\tOutput file path\t\tInput file path + \"_final.mp4\"")
    print(" -v\tVerbose\t\t\t\tFalse")
    print(" -w\tWait before mutating frame\tFalse")
    print(" Sample shell input:\t\t\tpython Faceline.py -l -ss 00:30 -t 00:01 -i /home/hew/Desktop/F/Fash.divx")

#Returns boolean representing whether point 1 or point two is within the points of rectangle r
def in_rect(r, p):
    return p[0] > r[0] and p[1] > r[1] and p[0] < r[2] and p[1] < r[3] 

#Takes URI of data location and converts it to a cv2 image.
def data_uri_to_cv2_img(uri):
    encoded_data = uri.split(',')[1]
    nparr = np.fromstring(encoded_data.decode('base64'), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

# Takes in an image, list of points,
# breadthList which is a list of all of the hypotenuses, and a frame to wait at,
# Draws Delaunay triangles across points within the
# Bounded area. Achieved by subdividing and then drawing lines for each tri
# using OpenCV Delaunay triangle algorithm succeeded by cv2 line drawing.
def markFrame(img, ptsList, breadthList, wait_at_frame):
    if(not wait_at_frame) or raw_input("Overwrite " + fn + " Y/N?") == "Y":
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
	    i+=1
        tend = datetime.now()
	print("\t\t" + str(tend - tstart))
    else:
        print("Permission denied. (mark Frame)")

#Draws Lines related to pupils on an input image,
#at points pupil data across hypotenuses in breadthList, waits a given frame.
def markPupil(img, pupilData, breadthList, wait_at_frame):
    print("\t\tDrawing pupils to image.")
    if (not wait_at_frame) or raw_input("Overwrite " + fn + " Y/N?") == "Y":
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

#Takes an image, detector and predictor and returns a list of lists of points and a list of hypotenuses
def detectFrame(img, detector, predictor):
    print("\t\tBeginning detection")
    tstart = datetime.now()
    global image_ratio
    image = cv2.resize(img, (0,0), fx=image_ratio, fy=image_ratio)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detections = detector(gray, 1)# type(detections) == dlib.rectangles
    tend = datetime.now()
    print("\t\t" + str(tend - tstart))
    
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

#Magic function that takes an input path and uses FFprobe to check for metadata including
#width, height, average frame rate and number of frames for a video and returns it in a list.
def getMetadata(input_path):
    ffprobe = subprocess.Popen(["ffprobe", "-show_streams", input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    ffprobe.wait()
    metadata = ffprobe.communicate()[0]

    metaWidth = metadata[metadata.find("width="):metadata.find("\n", metadata.find("width="))]
    metaHeight = metadata[metadata.find("height="):metadata.find("\n", metadata.find("height="))]
    metaAvgRate = metadata[metadata.find("avg_frame_rate="):metadata.find("\n", metadata.find("avg_frame_rate="))]
    metaFrameNumb = metadata[metadata.find("nb_frames="):metadata.find("\n", metadata.find("nb_frames="))]
    
    return [metaWidth, metaHeight, metaAvgRate, metaFrameNumb]	

#Returns a list of pupil data acquired using eyeLine, a modified version of Tristan Hume's eyeLike
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

#Does frame processing such as calling mark frame and mark pupil
def handleFrame(input_path, detector, predictor, wait_at_frame):
    global lazy_output_file, global_script_start
    print("\tBase encoding time")
    tstart = datetime.now()

    if URI_Handling:
        content_file = open(fn, 'r')
        img = data_uri_to_cv2_img(content_file.read())
        content_file.close()
    else:
	img = cv2.imread(input_path, 1)
    tend = datetime.now()
    print("\t" + str(tend - tstart))

    ptsList, breadthList = detectFrame(img, detector, predictor)
    markFrame(img, ptsList, breadthList, wait_at_frame)
    #write ptsList to JSON to DB

    if not realTime:
        pupilData = getPupilData(input_path) #IPC to get pupil data
        markPupil(img, pupilData, breadthList, wait_at_frame)
        #write pupil data to DB
	
    cv2.imwrite((lazy_output_file if newCopy else input_path), img) 
    tend = datetime.now()
    print("\ttime to write since encoding")
    print("\t" + str(tend - tstart)) 
    return img #for the sake of the single frame option (needed metadata)

if __name__ == "__main__":
    global_script_start = datetime.now()

    if len(sys.argv) < 2:
        print("Error: Too few arguments supplied.")
        exit()

    elif len(sys.argv) > 14:
        print("Error: Too many arguments supplied.")
        exit()

    run_dir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
    predictor_path = run_dir + "/shape_predictor_68_face_landmarks.dat"
    newCopy = True
    realTime = False
    single_frame = False
    start_time = "00:00"
    duration = "00:10"
    input_path = ""
    output_path = "/Users/chenyulong/Documents/DPP/result/final.mp4"
    verbose = False
    wait_at_frame = False

    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        displayHelp()
        exit()

    for index, arg in enumerate(sys.argv):
        if arg == "-uri":
	    URI_Handling = True 
	elif arg == "-l":
            newCopy = False
	elif arg == "-r":
	    realTime = True
        elif arg == "-p":
            predictor_path = sys.argv[index+1]
        elif arg == "-f":
            single_frame = True
        elif arg == "-ss":
            start_time = sys.argv[index+1]
        elif arg == "-t":
            duration = sys.argv[index+1]
        elif arg == "-i":
            input_path = sys.argv[index+1]
            if output_path == "":
                output_path = input_path[:input_path.rfind(".")] + "_final.mp4"
        elif arg == "-o":
            output_path = sys.argv[index+1]
	    lazy_output_file = output_path
	    print("Output path is now" + lazy_output_file)
        elif arg == "-v":
            verbose = True
        elif arg == "-w":
            wait_at_frame = True

    if input_path == "":
        print("Please enter an input file")
        exit()

    print("Calling DLib")
    start = datetime.now()
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    end = datetime.now()
    print("Finished calling at " + str(start - end)) #WTF

    outstream = (None if verbose else open(os.devnull, 'w')) #for redirecting output to nothing as desired

    if single_frame:
	print("Handling a frame")
	tstart = datetime.now()
	img = handleFrame(input_path, detector, predictor, wait_at_frame)
        print("Image " + input_path + ": Width - " + str(img.shape[0]) + ", Height - " + str(img.shape[1])) #write to DB?
	tend = datetime.now()
	print("Finished handling frame at" + str(tend - tstart))


    else:
	("Gathering metadata")
	tstart = datetime.now()
	
	metadata = getMetadata(input_path)
	for d in metadata:
	    print(d)
	#write metadata to DB

	tend = datetime.now()
	print("Finished gathering at " + str(tend - tstart))

        midPath = input_path[:input_path.rfind(".")] + "%d.png"
	print("Breaking into frames")
	tstart = datetime.now()
        ffmpegBreak = subprocess.Popen(["ffmpeg", "-ss", start_time] + ["-t", duration] + ["-i", input_path, midPath], stdout=outstream, stderr=subprocess.STDOUT) # Run FFMPEG, using pngs
	ffmpegBreak.wait()
	tend = datetime.now()
    total_spliting_time = tend - tstart
    print("Finished breaking at " + str(tend - tstart))
    g = glob.glob(input_path[:input_path.rfind(".")] + "*.png")

    start = datetime.now()
    for i, fn in enumerate(g):
        print("Handling frame " + str(i) + ":")
        tstart = datetime.now()
        handleFrame(fn, detector, predictor, wait_at_frame)
        tend = datetime.now()
        print("Finished handling frame " + str(tend - tstart))
    if newCopy:
        midPath = midPath[:midPath.rfind(".")] + "_final.png"
    end = datetime.now()
    total = end - start    
    print("Rebuilding video")
    tstart = datetime.now()
    print(midPath)
    print(output_path)
    ffmpegBuild = subprocess.Popen(["ffmpeg", "-i", midPath, output_path], stdout=outstream, stderr=subprocess.STDOUT)# Run FFMPEG to rebake the video
    ffmpegBuild.wait()
    tend = datetime.now()
    print("Finished rebuilding at " + str(tend - tstart))
    if newCopy:
        for f in glob.glob(input_path[:input_path.rfind(".")] + "*_final.png"):
            os.remove(f)
    else:
        for f in glob.glob(input_path[:input_path.rfind(".")] + "*.png"):
            os.remove(f)
    end = datetime.now()
    print("Execution Complete at " + str(end - global_script_start))
    print("Total spliting time is: " + str(total_spliting_time))
    print("Total handling time is: " + str(total))