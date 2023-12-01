# Anonymous Web Get - ss.py/stepping-stone
# CS457 - Computer Networks and the Internet
# Colorado State University - Dept. of Computer Science
# Author: Axel Wahlstrom
# Lang: Python3

import sys, socket, pickle, time, struct, os, threading, random
from urllib.request import urlopen

DEFAULT_PORT = 33333

def main():
	port = getCmdLineArgs()
	hostname = socket.gethostname()
	IP = socket.gethostbyname(hostname)
	print("ss <" + str(IP) + ", " + str(port) + ">:")

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((IP, port))
	sock.listen()

	while True:
		conn, addr = sock.accept()
		recData = conn.recv(4096)
		goodData = pickle.loads(recData)
		if len(goodData) == 2:
			# get the web page - final hop
			fileCount = int(goodData.pop())
			URL = goodData.pop()
			file = requestAndSendFile(URL, conn, fileCount)
		else:
			# initiate a client to continue the hops
			fileCount = int(goodData.pop())
			URL = goodData.pop()
			addresses = goodData
			thread = threading.Thread(target=client, args=(addresses, URL, conn, fileCount))
			thread.start()
			thread.join()

def client(addresses, URL, returnSocket, fileCount):

	nextFileCount = fileCount + 1

	print("Request: " + str(URL))
	print("chainlist is")
	for address in addresses:
		print("<" + str(address[0]) + ", " + str(address[1]) + ">")
	randIndex = random.randint(0, len(addresses) - 1)
	nextAddress = addresses.pop(randIndex)
	print("next SS is <" + str(nextAddress[0]) + ", " + str(nextAddress[1]) + ">")

	addresses.append(str(URL))
	addresses.append(nextFileCount)
	data = pickle.dumps(addresses)

	nextIP = nextAddress[0]

	newSocket = None

	try:
		nextPort = int(nextAddress[1])
		newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		newSocket.connect((nextIP, nextPort))
		newSocket.send(data)
	except:
		error("could not connect to (ip:" + nextIP + ", port:" + str(nextPort) + ").")

	print("waiting for file...")

	URL, fileName, extension = filterURL(URL)

	newFileName = "file" + str(fileCount) + extension

	data = recv_msg(newSocket)

	file = open(newFileName, "wb")
	file.write(data)
	file.close()

	print("Relaying file...")

	sendFile = open(newFileName, "rb")
	contents = sendFile.read()
	sendMessage(returnSocket, contents)
	sendFile.close()
	newSocket.close()
	try:
		os.remove(newFileName)
	except:
		print("stepping-stone error: could not delete file " + str(newFileName))

	print("Goodbye!")

def requestAndSendFile(URL, sock, fileCount):

	print("Request: " + str(URL))
	print("chainlist is empty")

	urlAttempts = 0
	urlMaxAttempts = 80

	if URL.rfind('/') == len(URL) - 1:
		URL += "index.html"

	if URL.find('/') == -1:
		URL = URL + "/index.html"
	fileName = URL[URL.rfind('/') + 1:len(URL)]

	URL, fileName, extension = filterURL(URL)

	print("issuing wget for file " + str(fileName))

	# print(URL)
	# print(fileName)
	# print(extension)

	webContent = None

	try:
		with urlopen(URL) as file:
			webContent = file.read()
	except:
		webContent = b"Could not download file from URL"

	newFileName = "file" + str(fileCount) + extension

	newFile = open(newFileName, "wb")
	newFile.write(webContent)
	newFile.close()

	print("File received")
	print("Relaying file...")

	f = open(newFileName, "rb")
	contents = f.read()
	sendMessage(sock, contents)
	f.close()
	sock.close()
	try:
		os.remove(newFileName)
	except:
		print("stepping-stone error: could not delete file " + str(newFileName))

	print("Goodbye!")

def sendMessage(sock, msg):
	msg = struct.pack(">I", len(msg)) + msg
	sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    length = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, length)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def filterURL(URL):
	http = False
	https = False
	fileName = ""

	# apply string filters to the URL
	if URL.find("https://") != -1:
		https = True
		URL = URL[8:len(URL)]
	if URL.find("http://") != -1:
		http = True
		URL = URL[7:len(URL)]
	if URL.rfind('/') == -1:
		URL = URL + "/index.html"
		fileName = "index.html"
	else:
		fileName = URL[URL.rfind('/') + 1:len(URL)]

	if http:
		URL = "http://" + URL
	if https:
		URL = "https://" + URL
	if not http and not https:
		URL = "https://" + URL

	extension = fileName[fileName.rfind("."):len(fileName)]

	return URL, fileName, extension

def getCmdLineArgs():
	optionalPort = -1
	length = len(sys.argv)
	if length == 1:
		optionalPort = DEFAULT_PORT
	if length == 2:
		error("usage")
	if length == 3:
		if sys.argv[2] == "-p":
			error("usage")
		if sys.argv[1] == "-p":
			try:
				optionalPort = int(sys.argv[2])
			except:
				error("usage")
		else:
			error("usage")
	if length > 3:
		error("usage")
	if optionalPort < 1024 or optionalPort > 65353:
		error("port number must be a valid port number between the values (1024 and 65353).")
	return optionalPort

def error(msg):
	if msg == "usage":
		error("usage - ss [-p port]")
	EXIT_MESSAGE = "stepping-stone error:"
	print(EXIT_MESSAGE + " " + msg)
	exit()

main()
