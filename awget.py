# Anonymous Web Get - awget.py/reader
# CS457 - Computer Networks and the Internet
# Colorado State University - Dept. of Computer Science
# Author: Axel Wahlstrom
# Lang: Python3

import sys, random, socket, pickle, struct

# main entry point to interface
def main():
	URL, chainFile = getCmdLineArgs()
	numLines, addresses = readFileContents(chainFile)

	fileCount = 0

	print("awget:")
	print("Request: " + str(URL))
	print("chainlist is")
	for addr in addresses:
		print("<" + addr[0] + ", " + addr[1] + ">")

	randomIndex = random.randint(0, len(addresses) - 1)
	nextSteppingStone = addresses.pop(randomIndex) # TODO: change the 0 in pop() to randomIndex for randomness

	addresses.append(URL)
	addresses.append(fileCount)
	nextStoneIP = nextSteppingStone[0]
	nextStonePort = nextSteppingStone[1]
	print("next ss is: <" + nextStoneIP + ", " + nextStonePort + ">")

	data = pickle.dumps(addresses)

	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((nextStoneIP, int(nextStonePort)))
		sock.send(data)
	except:
		error("could not connect to (ip:" + nextStoneIP + ", port:" + str(nextStonePort) + ").")

	print("waiting for file...")

	if URL.rfind('/') == len(URL) - 1:
		URL += "index.html"

	if URL.find('/') == -1:
		URL = URL + "/index.html"
	fileName = URL[URL.rfind('/') + 1:len(URL)]

	data = recv_msg(sock)
	file = open(fileName, "wb")
	file.write(data)
	file.close()

	print("Received file " + str(fileName))
	print("Goodbye!")

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

# reads contents of the file
# returns number of lines in the file
# returns list of tuples holding the addresses (IP, PORT)
def readFileContents(fileToRead):

	numLines = 0 # number of ip addresses in file
	addresses = [] # list of tuples of ip addresses from file (IP, PORT)

	try:
		file = open(fileToRead, "r")
		numLines = int(file.readline())
		for i in range(0, numLines):
			currLine = file.readline().split(' ')
			if currLine[1][len(currLine[1]) - 1] == '\n':
				currLine[1] = currLine[1][:len(currLine[1]) - 1]
			addresses.append(currLine)
	except:
		if fileToRead == "chaingang.txt":
			error("chaingang.txt configuration file could not be found.\nEnsure a configuration file named chaingang.txt is\nin the same directory as awget.py\nOtherwise, you may specifiy your own configuration file by using the -c flag.")
		else:
			error("file " + fileToRead + " could not be read or does not exist.")
	return numLines, addresses
	

def getCmdLineArgs():
	length = len(sys.argv)
	URL = ""
	chainFile = ""

	if length == 1:
		print("not enough command line arguments.")
		error("usage")
	if length == 2:
		if sys.argv[1] == "-c":
			error("usage")
		URL = sys.argv[1]
		chainFile = "chaingang.txt"
	if length == 3:
		error("usage")
	if length == 4:
		if sys.argv[1] == '-c':
			chainFile = sys.argv[2]
			URL = sys.argv[3]
		if sys.argv[2] == '-c':
			chainFile = sys.argv[3]
			URL = sys.argv[1]
		if sys.argv[3] == '-c':
			error("usage")
	if length > 4:
		error("usage")

	return URL, chainFile

def error(msg):
	if msg == "usage":
		error("usage - awget URL [-c chainfile]")
	EXIT_MESSAGE = "awget error:"
	print(EXIT_MESSAGE + " " + msg)
	exit()

main()