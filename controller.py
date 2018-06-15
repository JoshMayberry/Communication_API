__version__ = "1.0.0"

#Import standard elements
import warnings
import subprocess


#Import cryptodome to encrypt and decrypt files
import Cryptodome.Random
import Cryptodome.Cipher.AES
import Cryptodome.PublicKey.RSA
import Cryptodome.Cipher.PKCS1_OAEP

#Required Modules
##py -m pip install
	# pycryptodomex

#User Access Variables
ethernetError = socket.error

#Controllers
def build(*args, **kwargs):
	"""Starts the GUI making process."""

	return Communication(*args, **kwargs)

class Communication():
	"""Helps the user to communicate with other devices.

	CURRENTLY SUPPORTED METHODS
		- COM Port (RS-232)
		- Ethernet & Wi-fi
		- Barcode
		- USB

	UPCOMING SUPPORTED METHODS
		- Raspberry Pi GPIO
		- QR Code

	Example Input: Communication()
	"""

	def __init__(self):
		"""Initialized internal variables."""

		self.usbDict     = {} #A dictionary that contains all of the created USB connections
		self.comDict     = {} #A dictionary that contains all of the created COM ports
		self.socketDict  = {} #A dictionary that contains all of the created socket connections
		self.barcodeDict = {} #A dictionary that contains all of the created barcodes

	#Barcodes
	def getBarcodeTypes(self, *args, **kwargs):
		"""Convenience Function"""

		return self.Barcode.getTypes(self, *args, **kwargs)

	def makeBarcode(self, which = None):
		"""Creates a new barcode object.

		Example Input: makeBarcode()
		Example Input: makeBarcode(0)
		"""

		#Create barcode object
		barcode = self.Barcode()
		if (which in self.barcodeDict):
			warnings.warn(f"Overwriting Barcode {which}", Warning, stacklevel = 2)

		#Catalogue the barcode
		if (which != None):
			self.barcodeDict[which] = barcode
		else:
			index = 0
			while index in self.barcodeDict:
				index += 1
			self.barcodeDict[index] = barcode

		return barcode

	def getBarcode(self, which):
		"""Returns the requested barcode object.

		Example Input: getBarcode(0)
		"""

		if (which in self.barcodeDict):
			return self.barcodeDict[which]
		else:
			warnings.warn(f"There is no barcode object {which}", Warning, stacklevel = 2)
			return None

	#COM port
	def getComPortList(self):
		"""Returns a list of available ports.
		Code from Matt Williams on http://stackoverflow.com/questions/1205383/listing-serial-com-ports-on-windows.

		Example Input: getComPortList()
		"""

		ports = [item.device for item in serial.tools.list_ports.comports()]

		return ports

	def makeComPort(self, which = None):
		"""Creates a new COM Port object.

		Example Input: makeComPort()
		Example Input: makeComPort(0)
		"""

		#Create COM object
		comPort = self.ComPort()
		if (which in self.comDict):
			warnings.warn(f"Overwriting COM Port {which}", Warning, stacklevel = 2)

		#Catalogue the COM port
		if (which != None):
			self.comDict[which] = comPort
		else:
			index = 0
			while index in self.comDict:
				index += 1
			self.comDict[index] = comPort

		return comPort

	def getComPort(self, which):
		"""Returns the requested COM object.

		Example Input: getComPort(0)
		"""

		if (which in self.comDict):
			return self.comDict[which]
		else:
			warnings.warn(f"There is no COM port object {which}", Warning, stacklevel = 2)
			return None

	#Ethernet
	def makeSocket(self, which = None):
		"""Creates a new Ethernet object.

		Example Input: makeSocket()
		Example Input: makeSocket(0)
		"""

		#Create Ethernet object
		mySocket = self.Ethernet(self)
		if (which in self.socketDict):
			warnings.warn(f"Overwriting Socket {which}", Warning, stacklevel = 2)

		#Catalogue the COM port
		if (which != None):
			self.socketDict[which] = mySocket
		else:
			index = 0
			while index in self.socketDict:
				index += 1
			self.socketDict[index] = mySocket

		return mySocket

	def getSocket(self, which):
		"""Returns the requested Ethernet object.

		Example Input: getSocket(0)
		"""

		if (which in self.socketDict):
			return self.socketDict[which]
		else:
			warnings.warn(f"There is no Ethernet object {which}", Warning, stacklevel = 2)
			return None

	#COM port
	def getUSBList(self, *args, **kwargs):
		"""Returns a list of available usb ports.
		Code from Matt Williams on http://stackoverflow.com/questions/1205383/listing-serial-com-ports-on-windows.

		Example Input: getUSBList()
		"""

		ports = self.USB.getAll(self, *args, **kwargs)

		return ports

	def makeUSB(self, which = None):
		"""Creates a new USB object.

		Example Input: makeUSB()
		Example Input: makeUSB(0)
		"""

		#Create USB object
		usb = self.USB(self)
		if (which in self.usbDict):
			warnings.warn(f"Overwriting USB Port {which}", Warning, stacklevel = 2)

		#Catalogue the USB port
		if (which != None):
			self.usbDict[which] = usb
		else:
			index = 0
			while index in self.usbDict:
				index += 1
			self.usbDict[index] = usb

		return usb

	def getUSB(self, which):
		"""Returns the requested USB object.

		Example Input: getUSB(0)
		"""

		if (which in self.usbDict):
			return self.usbDict[which]
		else:
			warnings.warn(f"There is no USB object {which}", Warning, stacklevel = 2)
			return None

	class USB():
		"""A controller for a USB connection.
		
		Special thanks to KM4YRI for how to install libusb on https://github.com/pyusb/pyusb/issues/120
			- Install the latest Windows binary on "https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download"
			- If on 64-bit Windows, copy "MS64\dll\libusb-1.0.dll" into "C:\windows\system32"
			- If on 32-bit windows, copy "MS32\dll\libusb-1.0.dll" into "C:\windows\SysWOW64"
		"""

		def __init__(self, parent):
			"""Defines the internal variables needed to run."""
			
			self.parent = parent
			self.device = None
			self.catalogue = {} #Information on the current usb device

			self.current_config = None
			self.current_interface = None
			self.current_endpoint = None

		def getAll(self):
			"""Returns all connected usb objects.
			Modified Code from: https://www.orangecoat.com/how-to/use-pyusb-to-find-vendor-and-product-ids-for-usb-devices

			Example Input: getAll()
			"""

			valueList = []
			return valueList
			

			devices = usb.core.find(find_all=True)
			for config in devices:
				value = (config.idVendor, config.idProduct)#, usb.core._try_lookup(usb._lookup.device_classes, config.bDeviceClass), usb.core._try_get_string(config, config.iProduct), usb.core._try_get_string(config, config.iManufacturer))
				valueList.append(value)

			return valueList

		def open(self, vendor, product = None):
			"""Connects to a USB object.
			Modified Code from: https://github.com/walac/pyusb/blob/master/docs/tutorial.rst

			Special thanks to frva for how to allow device configurations on https://stackoverflow.com/questions/31960314/pyusb-1-0-notimplementederror-operation-not-supported-or-unimplemented-on-this
				- Install the latest version of "Zadig" on "http://zadig.akeo.ie/"
				- Connect your USB device
				- Run "Zadig.exe", select "Options" and enable "List All Devices"
				- Select your device, then select "WINUSB" and press "Reinstall Driver"
				See: https://github.com/libusb/libusb/wiki/Windows#How_to_use_libusb_on_Windows

			vendor (int) - The vendor id
				- If tuple: (vendor id (int), product id (int))
			product (int) - The product id

			Example Input: open(1529, 16900)
			Example Input: open((1529, 16900))
			"""

			if (isinstance(vendor, (list, tuple))):
				product = vendor[1]
				vendor = vendor[0]

			#Locate the device
			self.device = usb.core.find(idVendor = vendor, idProduct = product)#, find_all = True)
			if (self.device is None):
				raise ValueError(f"Device {vendor}:{product} not found in open() for {self.__repr__()}")

			#Get info on device
			self.catalogue[None] = self.device
			self.catalogue["type"] = usb.core._try_lookup(usb._lookup.device_classes, self.device.bDeviceClass)
			self.catalogue["company"] = usb.core._try_get_string(self.device, self.device.iManufacturer)
			self.catalogue["name"] = usb.core._try_get_string(self.device, self.device.iProduct)
			for i, config in enumerate(self.device):
				self.catalogue[i] = {}
				self.catalogue[i][None] = config
				self.catalogue[i]["type"] = usb.core._try_get_string(config.device, config.iConfiguration)
				# self.catalogue[i]["value"] = config.bConfigurationValue

				self.catalogue[i]["data"] = ""
				if (config.bmAttributes & (1<<6)):
					self.catalogue[i]["data"] += "Self"
				else:
					self.catalogue[i]["data"] += "Bus"
				if (config.bmAttributes & (1<<5)):
					self.catalogue[i]["data"] += ", Remote Wakeup"

				for j, interface in enumerate(config):
					self.catalogue[i][j] = {}
					self.catalogue[i][j][None] = interface
					self.catalogue[i][j]["type"] = usb.core._try_lookup(usb._lookup.interface_classes, interface.bInterfaceClass)
					self.catalogue[i][j]["name"] = usb.core._try_get_string(interface.device, interface.iInterface)

					for k, endpoint in enumerate(interface):
						self.catalogue[i][j][k] = {}
						self.catalogue[i][j][k][None] = endpoint

						if (usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN):
							self.catalogue[i][j][k]["type"] = "IN"
						else:
							self.catalogue[i][j][k]["type"] = "OUT"

						self.catalogue[i][j][k]["data"] = usb._lookup.ep_attributes[(endpoint.bmAttributes & 0x3)]

		def info(self):
			"""Returns info on the current USB object.

			Example Input: info()
			"""

			return self.catalogue

		def listen(self, config_id = 0, interface_id = 0, endpoint_id = 0):
			#Maybe Needed: https://www.ghacks.net/2017/06/03/stop-windows-from-installing-drivers-for-specific-devices/
			#https://learn.pimoroni.com/tutorial/robots/controlling-your-robot-wireless-keyboard

			#listen
			config = catalogue[config_id][None]
			config.set()

			interface = catalogue[config_id][interface_id][None]
			try:
				interface.set_altsetting()
			except usb.core.USBError:
				pass

			endpoint = catalogue[config_id][interface_id][endpoint_id][None]

			#Modified code from: https://www.orangecoat.com/how-to/read-and-decode-data-from-your-mouse-using-this-pyusb-hack
			mustClaim = False# device.is_kernel_driver_active(interface.bInterfaceNumber)
			try:
				if mustClaim is True:
					# device.detach_kernel_driver(interface.bInterfaceNumber)
					usb.util.claim_interface(device, interface.bInterfaceNumber)

				for i in range(300):
					try:
						data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout = None)
						print("@1", data)
						print("@3", ''.join([chr(x) for x in data]))
					except usb.core.USBError as error:
						print("@2")
						data = None
						if (error.__str__() == "Operation timed out"):
							continue
					time.sleep(1)
			finally:
				if mustClaim is True:
					usb.util.release_interface(device, interface.bInterfaceNumber)
					# device.attach_kernel_driver(interface.bInterfaceNumber)


	class Ethernet():
		"""A controller for a single ethernet socket.

		Note: If you create a socket in a background function, 
		do not try to read or write to your GUI until you create and open the socket.
		If you do not, the GUI will freeze up.
		"""

		def __init__(self, parent):
			"""Defines the internal variables needed to run."""

			#Create internal variables
			self.parent = parent #The GUI object

			#Background thread variables
			self.dataBlock   = [] #Used to recieve data from the socket
			self.ipScanBlock = [] #Used to store active ip addresses from an ip scan
			self.clientDict  = {} #Used to keep track of all client connections {"mySocket": connection object (socket), "data": client dataBlock (str), "stop": stop flag (bool), "listening": currently listening flag, "finished": recieved all flag}

			self.recieveStop = False #Used to stop the recieving function early
			self.ipScanStop  = False #Used to stop the ip scanning function early
			self.recieveListening = False #Used to chek if the recieve function has started listening or if it has finished listeing

			#Create the socket
			self.mySocket = None
			self.stream = None
			self.address = None
			self.port = None

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

			if (self.mySocket != None):
				warnings.warn(f"Socket already opened", Warning, stacklevel = 2)

			#Account for the socket having been closed
			# if (self.mySocket == None):
			if (stream):
				self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.stream = "SOCK_STREAM"
			else:
				self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.stream = "SOCK_DGRAM"

			if (timeout != -1):
				self.setTimeout(timeout)

			#Remove any white space
			address = re.sub("\s", "", address)

			#Make sure it exists
			if (pingCheck):
				addressExists = self.ping(address)

				if (not addressExists):
					print(f"Cannot ping address {address}")
					self.mySocket = None
					return False

			#Remember Values
			self.address = address
			self.port = port

			#Connect to the socket
			if (stream):
				if (error):
					error = self.mySocket.connect_ex((address, port))
					return error
				else:
					self.mySocket.connect((address, port))

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

			if (self.mySocket == None):
				warnings.warn(f"Socket already closed", Warning, stacklevel = 2)
				return

			if (now != None):
				if (now):
					self.restrict()

				self.mySocket.close()
			else:
				self.mySocket.detach()

			self.mySocket = None

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
				self.mySocket.sendto(data, (self.address, self.port))
			else:
				self.mySocket.sendall(data)
				# self.mySocket.send(data)

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
					if (self.recieveStop or (self.mySocket == None)):# or ((len(self.dataBlock) > 0) and (self.dataBlock[-1] == None))):
						self.recieveStop = False
						break

					#Check for data to recieve
					self.mySocket.setblocking(0)
					ready = select.select([self.mySocket], [], [], 0.5)
					if (not ready[0]):
						#Stop listening
						break

					#Retrieve the block of data
					data = self.mySocket.recv(bufferSize).decode() #The .decode is needed for python 3.4, but not for python 2.7
					# data, address = self.mySocket.recvfrom(bufferSize)#.decode() #The .decode is needed for python 3.4, but not for python 2.7

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

			if ((len(self.dataBlock) > 0) and (self.dataBlock[-1] == None)):
				warnings.warn(f"Use checkRecieve() to take out data", Warning, stacklevel = 2)
				return None

			#Listen for data on a separate thread
			self.dataBlock = []
			self.parent.backgroundRun(runFunction, [self, bufferSize])

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
					if (self.dataBlock[-1] != None):
						self.startRecieve()
				else:
					self.startRecieve()

			#The entire message has been read once the last element is None.
			finished = False
			compareBlock = self.dataBlock[:] #Account for changing mid-analysis
			self.dataBlock = []
			if (len(compareBlock) != 0):
				if (compareBlock[-1] == None):
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
				if (address == None):
					address = '0.0.0.0'

				#Remove any white space
				address = re.sub("\s", "", address)

				serverIp = (socket.gethostbyname(address), port)
				self.address = address
				self.port = port

				self.mySocket.bind(serverIp)

				#Listen for incoming connections
				self.mySocket.listen(clients)
				count = clients #How many clients still need to connect
				clientIp = None
				while True:
					# Wait for a connection
					try:
						connection, clientIp = self.mySocket.accept()
					except:
						traceback.print_exc()
						if (clientIp != None):
							count = self.closeClient(clientIp[0], count)
						else:
							break

						#Check for all clients having connected and left
						if (count <= 0):
							break

					if (clientIp != None):
						#Catalogue client
						if (clientIp not in self.clientDict):
							self.clientDict[clientIp] = {"mySocket": connection, "data": "", "stop": False, "listening": False, "finished": False}
						else:
							warnings.warn(f"Client {clientIp} recieved again", Warning, stacklevel = 2)

					time.sleep(scanDelay / 1000)

			#Error Checking
			self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			#Listen for data on a separate thread
			self.parent.backgroundRun(runFunction)

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
			client = self.clientDict[clientIp]["mySocket"]
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
				client = self.clientDict[clientIp]["mySocket"]
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
			self.parent.backgroundRun(runFunction, [self, clientIp, bufferSize])

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
				warnings.warn(f"There is no client {clientIp} for this server", Warning, stacklevel = 2)
			else:
				client = self.clientDict[clientIp]["mySocket"]
				client.close()
				del(self.clientDict[clientIp])

			if (clientsLeft != None):
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
				self.mySocket.shutdown(socket.SHUT_RDWR)

			elif (how == "r"):
				self.mySocket.shutdown(socket.SHUT_RD)

			elif (how == "w"):
				self.mySocket.shutdown(socket.SHUT_WR)

			elif (how == "b"):
				self.mySocket.setblocking(False)

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
				# self.mySocket.shutdown(socket.SHUT_RDWR)
				pass

			elif (how == "r"):
				# self.mySocket.shutdown(socket.SHUT_RD)
				pass

			elif (how == "w"):
				# self.mySocket.shutdown(socket.SHUT_WR)
				pass

			elif (how == "b"):
				self.mySocket.setblocking(True)

			else:
				warnings.warn(f"Unknown unrestiction flag {how}", Warning, stacklevel = 2)

		def getTimeout(self):
			"""Gets the tiemout for the socket.
			By default, the timeout is None.

			Example Input: getTimeout()
			"""

			timeout = self.mySocket.gettimeout()
			return timeout

		def setTimeout(self, timeout):
			"""Sets the tiemout for the socket.
			By default, the timeout is None.

			timeout (int) - How many seconds until timeout
				If None: There is no timeout

			Example Input: setTimeout(60)
			"""

			#Ensure that there is no negative value
			if (timeout != None):
				if (timeout < 0):
					warnings.warn(f"Timeout cannot be negative for setTimeout() in {self.__repr__()}", Warning, stacklevel = 2)
					return

			self.mySocket.settimeout(timeout)

		def getAddress(self, mine = False):
			"""Returns either the socket address or the remote address.

			mine (bool) - Determines which address is returned
				If True: Returns the socket's address
				If False: Returns the remote address

			Example Input: getAddress()
			"""

			if (mine):
				address = self.mySocket.getsockname()
			else:
				address = self.mySocket.getpeername()

			return address

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

		def startScanIpRange(self, start, end):
			"""Scans a range of ip addresses in the given range for online ones.
			Because this can take some time, it saves the list of ip addresses as an internal variable.
			Special thanks to lovetocode on http://stackoverflow.com/questions/4525492/python-list-of-addressable-ip-addresses

			start (str) - The ip address to start at
			end (str)  - The ip address to stop after

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

			#Listen for data on a separate thread
			self.ipScanBlock = []
			self.parent.backgroundRun(runFunction, [self, start, end])

		def checkScanIpRange(self):
			"""Checks for found active ip addresses from the scan.
			Each read portion is an element in a list.
			Returns the current block of data and whether it is finished listening or not.

			Example Input: checkScanIpRange()
			"""

			#The entire message has been read once the last element is None.
			finished = False
			if (len(self.ipScanBlock) != 0):
				if (self.ipScanBlock[-1] == None):
					finished = True
					self.ipScanBlock.pop(-1) #Remove the None from the end so the user does not get confused

			return self.ipScanBlock, finished

		def stopScanIpRange(self):
			"""Stops listening for data from the socket.
			Note: The data is still in the buffer. You can resume listening by starting startRecieve() again.
			To flush it, close the socket and then open it again.

			Example Input: stopScanIpRange()
			"""

			self.ipScanStop = True

		def isOpen(self, address = None):
			"""Returns if a socket is already open."""

			# error = self.mySocket.connect_ex((address, port))
			# if (error == 0):
			#   self.mySocket.shutdown(2)
			#   return True
			# return False

			if (self.mySocket == None):
				return True
			return False

	class ComPort():
		"""A controller for a single COM port."""

		def __init__(self):
			"""Defines the internal variables needed to run."""

			#Create needed objects
			self.serialPort = serial.Serial()

			#These are the defaults for serial.Serial.__init__()
			self.comPort         = None                #The device name
			self.comBaudRate     = 9600                #Rate at which information is transferred
			self.comByteSize     = serial.EIGHTBITS    #Number of bits per bytes
			self.comParity       = serial.PARITY_NONE  #For error detection
			self.comStopBits     = serial.STOPBITS_ONE #Signals message end
			self.comTimeoutRead  = None                #Read timeout. Makes the listener wait
			self.comTimeoutWrite = None                #Write timeout. Makes the speaker wait
			self.comFlowControl  = False               #Software flow control
			self.comRtsCts       = False               #Hardware (RTS/CTS) flow control
			self.comDsrDtr       = False               #Hardware (DSR/DTR) flow control
			self.comMessage      = None                #What is sent to the listener

		#Getters
		def getComPort(self):
			"""Returns the port.

			Example Input: getComPort()
			"""

			return self.comPort

		def getComBaudRate(self):
			"""Returns the baud rate.

			Example Input: getComBaudRate()
			"""

			return self.comBaudRate

		def getComDataBits(self):
			"""Overridden function for getComByteSize().

			Example Input: getComDataBits()
			"""

			value = self.getComByteSize()
			return value

		def getComByteSize(self):
			"""Returns the byte size.

			Example Input: getComByteSize()
			"""

			#Format the byte size
			if (self.comByteSize == serial.FIVEBITS):
				return 5

			elif (self.comByteSize == serial.SIXBITS):
				return 6

			elif (self.comByteSize == serial.SEVENBITS):
				return 7

			elif (self.comByteSize == serial.EIGHTBITS):
				return 8

			else:
				return self.comByteSize

		def getComParity(self):
			"""Returns the parity.

			Example Input: getComParity()
			"""

			if (self.comParity == serial.PARITY_NONE):
				return None

			elif (self.comParity == serial.PARITY_ODD):
				return "odd"
			
			elif (self.comParity == serial.PARITY_EVEN):
				return "even"
			
			elif (self.comParity == serial.PARITY_MARK):
				return "mark"
			
			elif (self.comParity == serial.PARITY_SPACE):
				return "space"

			else:
				return self.comParity

		def getComStopBits(self):
			"""Returns the stop bits.

			Example Input: getComStopBits()
			"""

			if (self.comStopBits == serial.STOPBITS_ONE):
				return 1

			elif (self.comStopBits == serial.STOPBITS_TWO):
				return 2

			elif (self.comStopBits == serial.STOPBITS_ONE_POINT_FIVE):
				return 1.5

			else:
				return self.comStopBits

		def getComTimeoutRead(self):
			"""Returns the read timeout.

			Example Input: getComTimeoutRead()
			"""

			return self.comTimeoutRead

		def getComTimeoutWrite(self):
			"""Returns the write timeout.

			Example Input: getComTimeoutWrite()
			"""

			return self.comTimeoutWrite

		def getComFlow(self):
			"""Returns the software flow control.

			Example Input: getComFlow()
			"""

			return self.comFlowControl

		def getComFlowS(self):
			"""Returns the hardware flow control.

			Example Input: getComFlowS(True)
			"""

			return self.comRtsCts

		def getComFlowR(self):
			"""Returns the hardware flow control.

			Example Input: getComFlowR()
			"""

			return self.comDsrDtr

		def getComMessage(self):
			"""Returns the message that will be sent.

			Example Input: getComMessage()
			"""

			return self.comMessage

		#Setters
		def setComPort(self, value):
			"""Changes the port.

			value (str) - The new port

			Example Input: setComPort("COM1")
			"""

			self.comPort = value

		def setComBaudRate(self, value):
			"""Changes the baud rate.

			value (int) - The new baud rate

			Example Input: setComBaudRate(9600)
			"""

			self.comBaudRate = value

		def setComDataBits(self, value):
			"""Overridden function for setComByteSize().

			value (int) - The new byte size. Can be 5, 6, 7, or 8

			Example Input: setComDataBits(8)
			"""

			self.setComByteSize(value)

		def setComByteSize(self, value):
			"""Changes the byte size.

			value (int) - The new byte size. Can be 5, 6, 7, or 8

			Example Input: setComByteSize(8)
			"""

			#Ensure that value is an integer
			if (type(value) != int):
				value = int(value)

			#Format the byte size
			if (value == 5):
				self.comByteSize = serial.FIVEBITS

			elif (value == 6):
				self.comByteSize = serial.SIXBITS

			elif (value == 7):
				self.comByteSize = serial.SEVENBITS

			elif (value == 8):
				self.comByteSize = serial.EIGHTBITS

		def setComParity(self, value):
			"""Changes the parity.

			value (str) - The new parity. Can be None, "odd", "even", "mark", or "space". Only the first letter is needed

			Example Input: setComParity("odd")
			"""

			if (value != None):
				#Ensure correct format
				if (type(value) == str):
					value = value.lower()

					if (value[0] == "n"):
						self.comParity = serial.PARITY_NONE
					
					elif (value[0] == "o"):
						self.comParity = serial.PARITY_ODD
					
					elif (value[0] == "e"):
						self.comParity = serial.PARITY_EVEN
					
					elif (value[0] == "m"):
						self.comParity = serial.PARITY_MARK
					
					elif (value[0] == "s"):
						self.comParity = serial.PARITY_SPACE

					else:
						warnings.warn(f"There is no parity {value}", Warning, stacklevel = 2)
						return False

				else:
					warnings.warn(f"There is no parity {value}", Warning, stacklevel = 2)
					return False

			else:
				self.comParity = serial.PARITY_NONE

			return True

		def setComStopBits(self, value):
			"""Changes the stop bits.

			value (int) - The new stop bits

			Example Input: setComStopBits(1)
			Example Input: setComStopBits(1.5)
			Example Input: setComStopBits(2)
			"""

			#Ensure that value is an integer or float
			if ((type(value) != int) and (type(value) != float)):
				value = int(value)

			#Format the stop bits
			if (value == 1):
				self.comStopBits = serial.STOPBITS_ONE

			elif (value == 2):
				self.comStopBits = serial.STOPBITS_TWO

			elif (value == 1.5):
				self.comStopBits = serial.STOPBITS_ONE_POINT_FIVE

			else:
				warnings.warn(f"There is no stop bit {value} for {self.__repr__()}", Warning, stacklevel = 2)

		def setComTimeoutRead(self, value):
			"""Changes the read timeout.

			value (int) - The new read timeout
						  None: Wait forever
						  0: Do not wait
						  Any positive int or float: How many seconds to wait

			Example Input: setComTimeoutRead(None)
			Example Input: setComTimeoutRead(1)
			Example Input: setComTimeoutRead(2)
			"""

			self.comTimeoutRead = value

		def setComTimeoutWrite(self, value):
			"""Changes the write timeout.

			value (int) - The new write timeout
						  None: Wait forever
						  0: Do not wait
						  Any positive int or float: How many seconds to wait

			Example Input: setComTimeoutWrite(None)
			Example Input: setComTimeoutWrite(1)
			Example Input: setComTimeoutWrite(2)
			"""

			self.comTimeoutWrite = value

		def setComFlow(self, value):
			"""Changes the software flow control.

			value (bool) - If True: Enables software flow control

			Example Input: setComFlow(True)
			"""

			self.comFlowControl = value

		def setComFlowS(self, value):
			"""Changes the hardware flow control.

			value (bool) - If True: Enables RTS/CTS flow control

			Example Input: setComFlowS(True)
			"""

			self.comRtsCts = value

		def setComFlowR(self, value):
			"""Changes the hardware flow control.

			value (bool) - If True: Enables DSR/DTR flow control

			Example Input: setComFlowR(True)
			"""

			self.comDsrDtr = value

		def setComMessage(self, value):
			"""Changes the message that will be sent.

			value (str) - The new message

			Example Input: setComMessage("Lorem ipsum")
			"""

			self.comMessage = value

		def openComPort(self, port = None):
			"""Gets the COM port that the zebra printer is plugged into and opens it.
			Returns True if the port sucessfully opened.
			Returns False if the port failed to open.

			### Untested ###
			port (str) - If Provided, opens this port instead of the port in memory

			Example Input: openComPort()
			Example Input: openComPort("COM2")
			"""

			#Configure port options
			if (port != None):
				self.serialPort.port     = port
			else:
				self.serialPort.port     = self.comPort
			self.serialPort.baudrate     = self.comBaudRate
			self.serialPort.bytesize     = self.comByteSize
			self.serialPort.parity       = self.comParity
			self.serialPort.stopbits     = self.comStopBits
			self.serialPort.timeout      = self.comTimeoutRead
			self.serialPort.writeTimeout = self.comTimeoutWrite
			self.serialPort.xonxoff      = self.comFlowControl
			self.serialPort.rtscts       = self.comRtsCts
			self.serialPort.dsrdtr       = self.comDsrDtr

			#Open the port
			try:
				self.serialPort.open()
			except:
				traceback.print_exc()
				warnings.warn(f"Cannot find serial port {self.serialPort.port} for {self.__repr__()}", Warning, stacklevel = 2)
				return False

			#Check port status
			if self.serialPort.isOpen():
				# print(f"Serial port {self.serialPort.port} sucessfully opened")
				return True
			else:
				warnings.warn(f"Cannot open serial port {self.serialPort.port} for {self.__repr__()}", Warning, stacklevel = 2)
				return False

		def isOpen(self):
			"""Checks whether the COM port is open or not."""

			return self.serialPort.isOpen()

		def emptyComPort(self):
			"""Empties the buffer data in the given COM port."""

			self.serialPort.flushInput() #flush input buffer, discarding all its contents
			self.serialPort.flushOutput()#flush output buffer, aborting current output and discard all that is in buffer

		def closeComPort(self, port = None):
			"""Closes the current COM Port.

			### Not Yet Implemented ###
			port (str) - If Provided, closes this port instead of the port in memory

			Example Input: closeComPort()
			"""

			self.serialPort.close()

		def comWrite(self, message = None):
			"""Sends a message to the COM device.

			message (str) - The message that will be sent to the listener
							If None: The internally stored message will be used.

			Example Input: comWrite()
			Example Input: comWrite("Lorem ipsum")
			"""

			if (message == None):
				message = self.comMessage

			if (message != None):
				if self.serialPort.isOpen():
					#Ensure the buffer is empty
					self.serialPort.flushInput() #flush input buffer, discarding all its contents
					self.serialPort.flushOutput()#flush output buffer, aborting current output and discard all that is in buffer

					if (type(message) == str):
						#Convert the string to bytes
						unicodeString = message
						unicodeString = unicodeString.encode("utf-8")
					else:
						#The user gave a unicode string already
						unicodeString = message

					#write data
					self.serialPort.write(unicodeString)
					print("Wrote:", message)
				else:
					warnings.warn(f"Serial port has not been opened yet for {self.__repr__()}\n Make sure that ports are available and then launch this application again", Warning, stacklevel = 2)
			else:
				warnings.warn(f"No message to send for comWrite() in {self.__repr__()}", Warning, stacklevel = 2)

		def comRead(self):
			"""Listens to the comport for a message.

			Example Input: comRead()
			"""

			message = self.serialPort.read()
			# message = self.serialPort.readline()
			return message

	class Barcode():
		"""Allows the user to create and read barcodes."""

		def __init__(self):
			"""Initializes internal variables."""

			self.myBarcode = None
			self.type = None

		def getType(self, formatted = False):
			"""Returns the barcode type."""

			if (formatted):
				return self.getTypes(5)[self.type]
			else:
				return self.type

		def setType(self, newType):
			"""Sets the default barcode type."""

			if (newType in self.getTypes(5)):
				self.type = newType
			elif (newType in self.getTypes(4)):
				self.type = self.getTypes(4)[newType]
			else:
				warnings.warn(f"Unknown type {newType} in setType() for {self.__repr__()}", Warning, stacklevel = 2)

		def getTypes(self):
			"""Returns the possible barcode types to the user as a list.

			Example Input: getTypes()
			"""

			typeList = sorted(barcode.PROVIDED_BARCODES)# + ["qr"])

			return typeList

		def create(self, text, codeType = None, filePath = None):
			"""Returns a PIL image of the barcode for the user or saves it somewhere as an image.

			text (str)     - What the barcode will say
			codeType (str) - What type of barcode will be made
				- If None: Will use self.type

			Example Input: create(1234567890)
			Example Input: create(1234567890, "code128")
			"""

			if (codeType == None):
				codeType = self.type
			elif (codeType not in self.getTypes()):
				warnings.warn(f"Unknown type {codeType} in create() for {self.__repr__()}", Warning, stacklevel = 2)
				return

			#Create barcode
			if (codeType == "qr"):
				#https://ourcodeworld.com/articles/read/554/how-to-create-a-qr-code-image-or-svg-in-python
				self.myBarcode = None
				pass
			else:
				thing = barcode.get(codeType, f"{text}", writer = barcode.writer.ImageWriter())
				self.myBarcode = thing.render(writer_options = None)

				if (filePath != None):
					thing.save(filePath)

			return self.myBarcode

		def show(self):
			"""Shows the barcode to the user."""

			self.myBarcode.show()

		def get(self):
			"""Returns the barcode."""

			return self.myBarcode