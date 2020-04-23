__version__ = "2.0.0"

#Import standard elements
import re
import sys
import warnings
import traceback
import subprocess

#Import communication elements for talking to other devices such as printers, the internet, a raspberry pi, etc.
import select
import socket
import netaddr

import MyUtilities.common
import MyUtilities.threadManager

#Required Modules
##py -m pip install
	# netaddr

#User Access Variables
ethernetError = socket.error

class Ethernet(API_Com.utilities.Utilities_Container, MyUtilities.threadManager.CommonFunctions):
	"""A controller for a Ethernet connection.
	
	Note: If you create a socket in a background function, 
	do not try to read or write to your GUI until you create and open the socket.
	If you do not, the GUI will freeze up.
	
	______________________ EXAMPLE USE ______________________
	
	com = API_Com.build()
	ethernet = com.ethernet[0]
	ethernet.open("192.168.0.21")
	ethernet.send("Lorem Ipsum")
	ethernet.close()
	_________________________________________________________

	com = API_Com.build()
	ethernet = com.ethernet[0]
	with ethernet.open("192.168.0.21"):
		ethernet.send("Lorem Ipsum")
	_________________________________________________________
	"""

	def __init__(self, parent):
		"""Defines the internal variables needed to run."""

		#Initialize Inherited Modules
		API_Com.utilities.Utilities_Container.__init__(self, parent)
		MyUtilities.threadManager.CommonFunctions.__init__(self)
	
		#Internal Variables
		self.ipScanBlock = [] #Used to store active ip addresses from an ip scan
		self.ipScanStop  = False #Used to stop the ip scanning function early

		self._listener_scan = None

	@MyUtilities.common.makeProperty()
	class listener_scan():
		"""Used to scan for ip addresses."""

		def getter(self):
			raise FutureWarning("Get this working")
			if (self._listener_scan is None):
				self.self._listener_scan = self.threadManager.listen(self.listenStatusText, label = "API_COM.statusText", canReplace = True, allowMultiple = True, delay = statusText_delay, errorFunction = self.listenStatusText_handleError, autoStart = False)
			return self._listener_scan

		def setter(self, value):
			raise FutureWarning("Get this working")
			self._listener_scan = value

		def remover(self):
			raise FutureWarning("Get this working")
			del self._listener_scan

	def getAll(self, *, asBackground = False):
		"""Returns all local area connections.

		Example Input: getAll()
		"""

		if (not asBackground):
			return self.startScanIpRange(asBackground = asBackground)

		self.startScanIpRange()

		finished = False
		while (not finished):
			valueList, finished = self.checkScanIpRange()
			time.sleep(100 / 1000)

		return valueList

	def ping(self, address):
		"""Returns True if the given ip address is online. Otherwise, it returns False.
		Code modified from http://www.opentechguides.com/how-to/article/python/57/python-ping-subnet.html

		address (str) - The ip address to ping

		Example Input: ping("169.254.231.0")
		"""

		#Configure subprocess to hide the console window
		info = subprocess.STARTUPINFO()
		info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		info.wShowWindow = subprocess.SW_HIDE

		#Remove Whitespace
		address = re.sub("\s", "", address)

		#Ping the address
		output = subprocess.Popen(['ping', '-n', '1', '-w', '500', address], stdout=subprocess.PIPE, startupinfo=info).communicate()[0]
		output = output.decode("utf-8")

		#Interpret Ping Results
		if ("Destination host unreachable" in output):
			return False #Offline

		elif ("Request timed out" in output):
			return False #Offline

		elif ("could not find host" in output):
			return False #Offline

		else:
			return True #Online

	def startScanIpRange(self, start = None, end = None, *, asBackground = True):
		"""Scans a range of ip addresses in the given range for online ones.
		Because this can take some time, it saves the list of ip addresses as an internal variable.
		Special thanks to lovetocode on http://stackoverflow.com/questions/4525492/python-list-of-addressable-ip-addresses

		start (str) - The ip address to start at
			- If None: Will use the current ip address group and start at 0
		end (str)  - The ip address to stop after
			- If None: Will use the current ip address group and end at 255

		Example Input: startScanIpRange()
		Example Input: startScanIpRange("169.254.231.0", "169.254.231.24")
		"""

		def runFunction(self, start, end):
			"""Needed to scan on a separate thread so the GUI is not tied up."""

			#Remove Whitespace
			start = re.sub("\s", "", start)
			end = re.sub("\s", "", end)

			#Get ip scan range
			networkAddressSet = list(netaddr.IPRange(start, end))

			#For each IP address in the subnet, run the ping command with the subprocess.popen interface
			for i in range(len(networkAddressSet)):
				if (self.ipScanStop):
					self.ipScanStop = False
					break

				address = str(networkAddressSet[i])
				online = self.ping(address)

				#Determine if the address is desired by the user
				if (online):
					self.ipScanBlock.append(address)

			#Mark end of message
			self.ipScanBlock.append(None)

		if ((start is None) or (end is None)):
			# raise FutureWarning("Add code here for getting the current ip Address")
			currentIp = socket.gethostbyname(socket.gethostname())
			start = currentIp[:-2] + "0"
			end = currentIp[:-2] + "255"

		#Listen for data on a separate thread
		self.ipScanBlock = []

		if (asBackground):
			raise FutureWarning("Get this working again")
			self.backgroundRun(runFunction, [self, start, end])
		else:
			runFunction(self, start, end)
			return self.ipScanBlock

	def checkScanIpRange(self):
		"""Checks for found active ip addresses from the scan.
		Each read portion is an element in a list.
		Returns the current block of data and whether it is finished listening or not.

		Example Input: checkScanIpRange()
		"""

		raise FutureWarning("Get this working again")
		#The entire message has been read once the last element is None.
		finished = False
		if (len(self.ipScanBlock) != 0):
			if (self.ipScanBlock[-1] is None):
				finished = True
				self.ipScanBlock.pop(-1) #Remove the None from the end so the user does not get confused

		return self.ipScanBlock, finished

	def stopScanIpRange(self):
		"""Stops listening for data from the socket.
		Note: The data is still in the buffer. You can resume listening by starting startRecieve() again.
		To flush it, close the socket and then open it again.

		Example Input: stopScanIpRange()
		"""

		raise FutureWarning("Get this working again")
		self.ipScanStop = True

	class Child(API_Com.utilities.Utilities_Child):
		"""An Ethernet connection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			API_Com.utilities.Utilities_Child.__init__(self, parent, label)

			#Background thread variables
			self.dataBlock   = [] #Used to recieve data from the socket
			self.clientDict  = {} #Used to keep track of all client connections {"device": connection object (socket), "data": client dataBlock (str), "stop": stop flag (bool), "listening": currently listening flag, "finished": recieved all flag}

			self.recieveStop = False #Used to stop the recieving function early
			self.recieveListening = False #Used to chek if the recieve function has started listening or if it has finished listeing

			#Create the socket
			self.device = None
			self.stream = None
			self.address = None
			self.port = None

		def __exit__(self, exc_type, exc_value, traceback):
			"""Allows the user to use a with statement to make sure the socket connection gets closed after use."""

			self.close()

			return API_Com.utilities.Utilities_Container.__exit__(self, exc_type, exc_value, traceback)

		def open(self, address, port = 9100, error = False, pingCheck = False, 
			timeout = -1, stream = True):
			"""Opens the socket connection.

			address (str) - The ip address/website you are connecting to
			port (int)    - The socket port that is being used
			error (bool)  - Determines what happens if an error occurs
				If True: If there is an error, returns an error indicator. Otherwise, returns a 0
				If False: Raises an error exception
			pingCheck (bool) - Determines if it will ping an ip address before connecting to it to confirm it exists

			Example Input: open("www.example.com")
			"""

			if (self.device is not None):
				warnings.warn(f"Socket already opened", Warning, stacklevel = 2)

			#Account for the socket having been closed
			# if (self.device is None):
			if (stream):
				self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.stream = "SOCK_STREAM"
			else:
				self.device = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.stream = "SOCK_DGRAM"

			if (timeout != -1):
				self.setTimeout(timeout)

			#Remove any white space
			address = re.sub("\s", "", address)

			#Make sure it exists
			if (pingCheck):
				addressExists = self.parent.ping(address)

				if (not addressExists):
					print(f"Cannot ping address {address}")
					self.device = None
					return False

			#Remember Values
			self.address = address
			self.port = port

			#Connect to the socket
			if (stream):
				if (error):
					error = self.device.connect_ex((address, port))
					return error
				else:
					self.device.connect((address, port))

			#Finish
			if (pingCheck):
				return True

		def close(self, now = False):
			"""Closes the socket connection.

			now (bool) - Determines how the socket is closed
				If True: Releases the resource associated with a connection 
					and closes the connection immediately
				 If False: Releases the resource associated with a connection 
					but does not necessarily close the connection immediately
				 If None: Closes the socket without closing the underlying file descriptor

			Example Input: close()
			Example Input: close(True)
			Example Input: close(None)
			"""

			if (self.device is None):
				warnings.warn(f"Socket already closed", Warning, stacklevel = 2)
				return

			if (now is not None):
				if (now):
					self.restrict()

				self.device.close()
			else:
				self.device.detach()

			self.device = None

		def send(self, data):
			"""Sends data across the socket connection.

			data (str) - What will be sent

			Example Input: send("lorem")
			Example Input: send(1234)
			"""

			#Account for numbers, lists, etc.
			if ((type(data) != str) and (type(data) != bytes)):
				data = str(data)

			#Make sure that the data is a byte string
			if (type(data) != bytes):
				data = data.encode() #The .encode() is needed for python 3.4, but not for python 2.7

			#Send the data
			if (self.stream == "SOCK_DGRAM"):
				self.device.sendto(data, (self.address, self.port))
			else:
				self.device.sendall(data)
				# self.device.send(data)

		def startRecieve(self, bufferSize = 256, scanDelay = 500):
			"""Retrieves data from the socket connection.
			Because this can take some time, it saves the list of ip addresses as an internal variable.
			Special thanks to A. Polino and david.gaarenstroom on http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/

			bufferSize (int) - The size of the recieveing buffer. Should be a power of 2

			Example Input: startRecieve()
			Example Input: startRecieve(512)
			Example Input: startRecieve(4096)
			"""

			def runFunction(self, bufferSize):
				"""Needed to listen on a separate thread so the GUI is not tied up."""

				self.recieveListening = True

				#Listen
				while True:
					#Check for stop command
					if (self.recieveStop or (self.device is None)):# or ((len(self.dataBlock) > 0) and (self.dataBlock[-1] is None))):
						self.recieveStop = False
						break

					#Check for data to recieve
					self.device.setblocking(0)
					ready = select.select([self.device], [], [], 0.5)
					if (not ready[0]):
						#Stop listening
						break

					#Retrieve the block of data
					data = self.device.recv(bufferSize).decode() #The .decode is needed for python 3.4, but not for python 2.7
					# data, address = self.device.recvfrom(bufferSize)#.decode() #The .decode is needed for python 3.4, but not for python 2.7

					#Check for end of data stream
					if (len(data) < 1):
						#Stop listening
						break

					#Save the data
					self.dataBlock.append(data)

					time.sleep(scanDelay / 1000)

				#Mark end of message
				self.dataBlock.append(None)
				self.recieveListening = False

			#Checks buffer size
			if (not (((bufferSize & (bufferSize - 1)) == 0) and (bufferSize > 0))):
				warnings.warn(f"Buffer size must be a power of 2, not {bufferSize}", Warning, stacklevel = 2)
				return None

			if (self.recieveListening):
				warnings.warn(f"Already listening to socket", Warning, stacklevel = 2)
				return None

			if ((len(self.dataBlock) > 0) and (self.dataBlock[-1] is None)):
				warnings.warn(f"Use checkRecieve() to take out data", Warning, stacklevel = 2)
				return None

			#Listen for data on a separate thread
			self.dataBlock = []
			raise FutureWarning("Get this working again")
			self.backgroundRun(runFunction, [self, bufferSize])

		def checkRecieve(self, removeNone = True):
			"""Checks what the recieveing data looks like.
			Each read portion is an element in a list.
			Returns the current block of data and whether it is finished listening or not.

			Example Input: checkRecieve()
			"""

			if (self.recieveStop):
				print("WARNING: Recieveing has stopped")
				return [], False

			if (not self.recieveListening):
				if (len(self.dataBlock) > 0):
					if (self.dataBlock[-1] is not None):
						self.startRecieve()
				else:
					self.startRecieve()

			#The entire message has been read once the last element is None.
			finished = False
			compareBlock = self.dataBlock[:] #Account for changing mid-analysis
			self.dataBlock = []
			if (len(compareBlock) != 0):
				if (compareBlock[-1] is None):
					finished = True

					if (removeNone):
						compareBlock.pop(-1) #Remove the None from the end so the user does not get confused

			data = compareBlock[:]

			return data, finished

		def stopRecieve(self):
			"""Stops listening for data from the socket.
			Note: The data is still in the buffer. You can resume listening by starting startRecieve() again.
			To flush it, close the socket and then open it again.

			Example Input: stopRecieve()
			"""

			self.recieveStop = True

		#Server Side
		def startServer(self, address = None, port = 10000, clients = 1, scanDelay = 500):
			"""Starts a server that connects to clients.
			Modified code from Doug Hellmann on: https://pymotw.com/2/socket/tcp.html

			port (int)      - The port number to listen on
			clients (int)   - The number of clients to listen for
			scanDelay (int) - How long in milliseconds between scans for clients

			Example Input: startServer()
			Example Input: startServer(port = 80)
			Example Input: startServer(clients = 5)
			"""

			def runFunction():
				"""Needed to listen on a separate thread so the GUI is not tied up."""
				nonlocal self, address, port, clients, scanDelay

				#Bind the socket to the port
				if (address is None):
					address = '0.0.0.0'

				#Remove any white space
				address = re.sub("\s", "", address)

				serverIp = (socket.gethostbyname(address), port)
				self.address = address
				self.port = port

				self.device.bind(serverIp)

				#Listen for incoming connections
				self.device.listen(clients)
				count = clients #How many clients still need to connect
				clientIp = None
				while True:
					# Wait for a connection
					try:
						connection, clientIp = self.device.accept()
					except:
						traceback.print_exc()
						if (clientIp is not None):
							count = self.closeClient(clientIp[0], count)
						else:
							break

						#Check for all clients having connected and left
						if (count <= 0):
							break

					if (clientIp is not None):
						#Catalogue client
						if (clientIp not in self.clientDict):
							self.clientDict[clientIp] = {"device": connection, "data": "", "stop": False, "listening": False, "finished": False}
						else:
							warnings.warn(f"Client {clientIp} recieved again", Warning, stacklevel = 2)

					time.sleep(scanDelay / 1000)

			#Error Checking
			self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			#Listen for data on a separate thread
			raise FutureWarning("Get this working again")
			self.backgroundRun(runFunction)

		def clientSend(self, clientIp, data, logoff = False):
			"""Sends data across the socket connection to a client.

			clientIp (str) - The IP address of the client
			data (str)     - What will be sent

			Example Input: clientSend("169.254.231.0", "lorem")
			Example Input: clientSend("169.254.231.0", 1234)
			"""

			#Account for numbers, lists, etc.
			if ((type(data) != str) and (type(data) != bytes)):
				data = str(data)

			#Make sure that the data is a byte string
			if (type(data) != bytes):
				data = data.encode() #The .encode() is needed for python 3.4, but not for python 2.7

			#Send the data
			client = self.clientDict[clientIp]["device"]
			client.sendall(data)

			# if (logoff):
			# 	client.shutdown(socket.SHUT_WR)

		def clientStartRecieve(self, clientIp, bufferSize = 256):
			"""Retrieves data from the socket connection.
			Because this can take some time, it saves the list of ip addresses as an internal variable.
			Special thanks to A. Polino and david.gaarenstroom on http://code.activestate.com/recipes/577514-chek-if-a-number-is-a-power-of-two/

			clientIp (str)   - The IP address of the client
			bufferSize (int) - The size of the recieveing buffer. Should be a power of 2

			Example Input: clientStartRecieve("169.254.231.0")
			Example Input: clientStartRecieve("169.254.231.0", 512)
			"""

			def runFunction(self, clientIp, bufferSize):
				"""Needed to listen on a separate thread so the GUI is not tied up."""

				#Reset client dataBlock
				self.clientDict[clientIp]["data"] = ""
				self.clientDict[clientIp]["finished"] = False
				self.clientDict[clientIp]["listening"] = True

				#Listen
				client = self.clientDict[clientIp]["device"]
				while True:
					#Check for stop command
					if (self.clientDict[clientIp]["stop"]):
						self.clientDict[clientIp]["stop"] = False
						break

					#Retrieve the block of data
					data = client.recv(bufferSize).decode() #The .decode is needed for python 3.4, but not for python 2.7

					#Save the data
					self.clientDict[clientIp]["data"] += data

					#Check for end of data stream
					if (len(data) < bufferSize):
						#Stop listening
						break

				#Mark end of message
				self.clientDict[clientIp]["finished"] = True
				self.clientDict[clientIp]["listening"] = False

			#Checks buffer size
			if (not (((bufferSize & (bufferSize - 1)) == 0) and (bufferSize > 0))):
				warnings.warn(f"Buffer size must be a power of 2, not {bufferSize}", Warning, stacklevel = 2)
				return None

			#Listen for data on a separate thread
			self.dataBlock = []
			raise FutureWarning("Get this working again")
			self.backgroundRun(runFunction, [self, clientIp, bufferSize])

		def clientCheckRecieve(self, clientIp):
			"""Checks what the recieveing data looks like.
			Each read portion is an element in a list.
			Returns the current block of data and whether it is finished listening or not.

			clientIp (str)   - The IP address of the client

			Example Input: clientCheckRecieve("169.254.231.0")
			"""

			if (self.clientDict[clientIp]["stop"]):
				print("WARNING: Recieveing has stopped")
				return [], False

			if (not self.clientDict[clientIp]["listening"]):
				if (len(self.clientDict[clientIp]["data"]) > 0):
					if (self.clientDict[clientIp]["finished"] != True):
						self.clientStartRecieve(clientIp)
				else:
					self.clientStartRecieve(clientIp)

			#Account for changing mid-analysis
			finished = self.clientDict[clientIp]["finished"]
			data = self.clientDict[clientIp]["data"][:]
			self.clientDict[clientIp]["data"] = ""

			# if (len(compareBlock) == 0):
			# 	finished = False

			return data, finished

		def clientStopRecieve(self, clientIp):
			"""Stops listening for data from the client.
			Note: The data is still in the buffer. You can resume listening by starting clientStartRecieve() again.
			To flush it, close the client and then open it again.

			clientIp (str)   - The IP address of the client

			Example Input: clientStopRecieve("169.254.231.0")
			"""

			self.clientDict[clientIp]["stop"] = True

		def getClients(self):
			"""Returns a list of all current client IP addresses.

			Example Input: getClients()
			"""

			clients = list(self.clientDict.keys())
			return clients

		def closeClient(self, clientIp, clientsLeft = None):
			"""Cleans up the connection with a server client.

			clientIp (str)    - The IP number of the client.
			clientsLeft (int) - How many clients still need to connect

			Example Input: closeClient("169.254.231.0")
			"""

			if (clientIp not in self.clientDict):
				errorMessage = f"There is no client {clientIp} for this server"
				raise ValueError(errorMessage)
			else:
				client = self.clientDict[clientIp]["device"]
				client.close()
				del(self.clientDict[clientIp])

			if (clientsLeft is not None):
				return clientsLeft - 1

		def restrict(self, how = "rw"):
			"""Restricts the data flow between the ends of the socket.

			how (str) - What will be shut down
				"r"  - Will not allow data to be recieved
				"w"  - Will not allow data to be sent
				"rw" - Will not allow data to be recieved or sent
				"b"  - Will block the data

			Example Input: restrict()
			Example Input: restrict("r")
			"""

			if (how == "rw"):
				self.device.shutdown(socket.SHUT_RDWR)

			elif (how == "r"):
				self.device.shutdown(socket.SHUT_RD)

			elif (how == "w"):
				self.device.shutdown(socket.SHUT_WR)

			elif (how == "b"):
				self.device.setblocking(False)

			else:
				warnings.warn(f"Unknown restiction flag {how}", Warning, stacklevel = 2)

		def unrestrict(self, how = "rw"):
			"""Un-Restricts the data flow between the ends of the socket.

			how (str) - What will be shut down
				"r"  - Will allow data to be recieved
				"w"  - Will allow data to be sent
				"rw" - Will allow data to be recieved and sent
				"b"  - Will not block the data. Note: Sets the timeout to None

			Example Input: unrestrict()
			Example Input: unrestrict("r")
			"""

			if (how == "rw"):
				# self.device.shutdown(socket.SHUT_RDWR)
				pass

			elif (how == "r"):
				# self.device.shutdown(socket.SHUT_RD)
				pass

			elif (how == "w"):
				# self.device.shutdown(socket.SHUT_WR)
				pass

			elif (how == "b"):
				self.device.setblocking(True)

			else:
				warnings.warn(f"Unknown unrestiction flag {how}", Warning, stacklevel = 2)

		def getTimeout(self):
			"""Gets the tiemout for the socket.
			By default, the timeout is None.

			Example Input: getTimeout()
			"""

			timeout = self.device.gettimeout()
			return timeout

		def setTimeout(self, timeout):
			"""Sets the tiemout for the socket.
			By default, the timeout is None.

			timeout (int) - How many seconds until timeout
				If None: There is no timeout

			Example Input: setTimeout(60)
			"""

			#Ensure that there is no negative value
			if (timeout is not None):
				if (timeout < 0):
					warnings.warn(f"Timeout cannot be negative for setTimeout() in {self.__repr__()}", Warning, stacklevel = 2)
					return

			self.device.settimeout(timeout)

		def getAddress(self, mine = False):
			"""Returns either the socket address or the remote address.

			mine (bool) - Determines which address is returned
				If True: Returns the socket's address
				If False: Returns the remote address

			Example Input: getAddress()
			"""

			if (mine):
				address = self.device.getsockname()
			else:
				address = self.device.getpeername()

			return address

		def isOpen(self, address = None):
			"""Returns if a socket is already open."""

			# error = self.device.connect_ex((address, port))
			# if (error == 0):
			#   self.device.shutdown(2)
			#   return True
			# return False

			if (self.device is None):
				return True
			return False