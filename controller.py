__version__ = "1.1.1"

#Import standard elements
import re
import os
import sys
import warnings
import traceback
import threading
import subprocess

# #Import communication elements for talking to other devices such as printers, the internet, a raspberry pi, etc.
import usb
import types
import bisect
import select
import socket
import serial
import netaddr
import serial.tools.list_ports

# #Import barcode modules for drawing and decoding barcodes
import qrcode
import barcode

# #Import email modules for sending and viewing emails
import smtplib
import xml.etree.cElementTree as xml
from email import encoders as email_encoders
from email.mime.base import MIMEBase as email_MIMEBase
from email.mime.text import MIMEText as email_MIMEText
from email.mime.image import MIMEImage as email_MIMEImage
from email.mime.multipart import MIMEMultipart as email_MIMEMultipart

import io
import wx
import glob
import PIL
import base64
import zipfile
import collections

import API_Database as Database
import MyUtilities.common

#Required Modules
##py -m pip install
	# pyusb
	# qrcode
	# netaddr
	# pyserial
	# pyBarcode

##Module dependancies (Install the following .exe and/or .dll files)
	#The latest Windows binary on "https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download"
		#If on 64-bit Windows, copy "MS64\dll\libusb-1.0.dll" into "C:\windows\system32"
		#If on 32-bit windows, copy "MS32\dll\libusb-1.0.dll" into "C:\windows\SysWOW64"

#User Access Variables
ethernetError = socket.error

#Utility Classes
class Utilities_Base(MyUtilities.common.Container, MyUtilities.common.EtcFunctions):
	def __init__(self, *args, **kwargs):
		"""Utility functions that everyone gets."""

		MyUtilities.common.Container.__init__(self, *args, **kwargs)

class Utilities_Container(Utilities_Base):
	def __init__(self, parent):
		"""Utility functions that only container classes get."""

		#Internal Variables
		if (not hasattr(self, "parent")): self.parent = parent
		if (not hasattr(self, "root")): self.root = self.parent
		
		#Initialize Inherited Modules
		Utilities_Base.__init__(self)

	def __str__(self):
		"""Gives diagnostic information on this when it is printed out."""

		output = Utilities_Base.__str__(self)
		if (len(self) > 0):
			output += f"-- Children: {len(self)}\n"
		return output

	def add(self, label = None):
		"""Adds a new child.
		If a child with the given label already exists, it will simply return the child instead of making a new one.

		Example Input: add()
		"""

		if (label in self):
			return self[label]
		return self.Child(self, label)

	def remove(self, child = None):
		"""Removes a child.

		child (str) - Which child to remove. Can be a children_class handle
			- If None: Will select the current child

		Example Input: remove()
		Example Input: remove(0)
		"""

		if (child is None):
			child = self.current
		elif (not isinstance(child, self.Child)):
			child = self[child]
		
		child.remove()

	def select(self, child = None):
		"""Selects a particular child.

		child (str) - Which child to select. Can be a children_class handle
			- If None: Will select the default child

		Example Input: select()
		Example Input: select(0)
		"""

		if (child is None):
			child = list(self)[0]
		elif (not isinstance(child, self.Child)):
			child = self[child]
		
		self.current = child

class Utilities_Child(Utilities_Base):
	def __init__(self, parent, label):
		"""Utility functions that only child classes get."""

		#Internal Variables
		if (not hasattr(self, "label")): self.label = label
		if (not hasattr(self, "parent")): self.parent = parent
		if (not hasattr(self, "root")): self.root = self.parent.root

		#Nest in parent
		if (self.label is None):
			self.label = 0
			while True:
				if (self.label not in self.parent):
					break
				self.label += 1
		self.parent[self.label] = self

		#Initialize Inherited Modules
		Utilities_Base.__init__(self)

	def __str__(self):
		"""Gives diagnostic information on this when it is printed out."""

		output = Utilities_Base.__str__(self)
		return output

	def rename(self, value):
		"""Renames this child to the new label.

		value (str) - The new label for this child

		Example Input: rename("Guest")
		"""

		del self.parent[self.label]
		
		self.label = value
		self.parent[value] = self

	def remove(self):
		"""Removes the rows in the database corresponding to this child.

		Example Input: remove()
		"""

		#Remove Child
		del self.parent[self.label]

		#Account for current selection
		if (self.parent.current == self):
			self.parent.select()

	def select(self):
		"""Selects this child.

		Example Input: select()
		"""

		self.parent.select(self)

#API Library
class USB(Utilities_Container):
	"""A controller for a USB connection.
	
	Special thanks to KM4YRI for how to install libusb on https://github.com/pyusb/pyusb/issues/120
		- Install the latest Windows binary on "https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download"
		- If on 64-bit Windows, copy "MS64\dll\libusb-1.0.dll" into "C:\windows\system32"
		- If on 32-bit windows, copy "MS32\dll\libusb-1.0.dll" into "C:\windows\SysWOW64"
	
	______________________ EXAMPLE USE ______________________
	
	com = API_Com.build()
	usb = com.usb[0]
	usb.open(1529, 16900)
	data = usb.listen()
	_________________________________________________________
	"""

	def __init__(self, parent):
		"""Defines the internal variables needed to run."""

		#Initialize Inherited Modules
		Utilities_Container.__init__(self, parent)

	def getAll(self):
		"""Returns all connected usb.
		Modified Code from: https://www.orangecoat.com/how-to/use-pyusb-to-find-vendor-and-product-ids-for-usb-devices

		Example Input: getAll()
		"""

		#See: https://github.com/pyusb/pyusb/issues/203
		raise NotImplementedError()

		valueList = []
		devices = usb.core.find(find_all=True)
		for config in devices:
			value = (config.idVendor, config.idProduct)#, usb.core._try_lookup(usb._lookup.device_classes, config.bDeviceClass), usb.core._try_get_string(config, config.iProduct), usb.core._try_get_string(config, config.iManufacturer))
			valueList.append(value)

		return valueList

	class Child(Utilities_Child):
		"""A USB conection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self.device = None

			self.current_config = None
			self.current_interface = None
			self.current_endpoint = None

		def open(self, vendor, product = None):
			"""Connects to a USB.
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
			"""Returns info on the current USB.

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

class Ethernet(Utilities_Container):
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
		Utilities_Container.__init__(self, parent)
		
		#Internal Variables
		self.ipScanBlock = [] #Used to store active ip addresses from an ip scan
		self.ipScanStop  = False #Used to stop the ip scanning function early

	def getAll(self):
		"""Returns all local area connections.

		Example Input: getAll()
		"""

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

	def startScanIpRange(self, start = None, end = None):
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
			raise FutureWarning("Add code here for getting the current ip Address")
			currentIp = "169.254.231.24"
			start = currentIp[:-2] + "0"
			end = currentIp[:-2] + "255"

		#Listen for data on a separate thread
		self.ipScanBlock = []
		self.backgroundRun(runFunction, [self, start, end])

	def checkScanIpRange(self):
		"""Checks for found active ip addresses from the scan.
		Each read portion is an element in a list.
		Returns the current block of data and whether it is finished listening or not.

		Example Input: checkScanIpRange()
		"""

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

		self.ipScanStop = True

	class Child(Utilities_Child):
		"""An Ethernet connection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)

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

			return Utilities_Container.__exit__(self, exc_type, exc_value, traceback)

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

class ComPort(Utilities_Container):
	"""A controller for a ComPort connection.
	Use: https://pyserial.readthedocs.io/en/latest/pyserial_api.html#module-serial.threaded
	
	______________________ EXAMPLE USE ______________________
	
	com = API_Com.build()
	comPort = com.comPort[0]

	comPort.setPort("COM12")
	comPort.setBaudRate(115200)
	comPort.setParity(None)
	comPort.setDataBits(8)
	comPort.setStopBits(1)
	comPort.openComPort()

	comPort.open()
	data = comPort.read()
	comPort.close()
	_________________________________________________________

	com = API_Com.build()
	comPort = com.comPort[0]

	with comPort:
		comPort.setPort("COM1")
		comPort.open()
		data = comPort.read()

	with comPort.open("COM2"):
		data = comPort.read()
	_________________________________________________________
	"""

	def __init__(self, parent):
		"""Defines the internal variables needed to run."""

		#Initialize Inherited Modules
		Utilities_Container.__init__(self, parent)

	def getAll(self, include = [], exclude = [], portOnly = False):
		"""Returns all connected com ports.
		Modified code from Matt Williams on http://stackoverflow.com/questions/1205383/listing-serial-com-ports-on-windows.

		Example Input: getAll()
		Example Input: getAll(portOnly = True)
		Example Input: getAll(include = ["vendorId", "productId"])
		Example Input: getAll(exclude = ["serial", "description"])
		"""

		if (include is None):
			include = []
		elif (not isinstance(include, (list, tuple, types.GeneratorType))):
			include = [include]

		if (exclude is None):
			exclude = []
		elif (not isinstance(exclude, (list, tuple, types.GeneratorType))):
			exclude = [exclude]

		valueList = []
		catalogue = {"port": "device", "name": "name", "description": "description", "hwid": "hwid", 
			"vendorId": "vid", "productId": "pid", "serial": "serial_number", "location": "location", 
			"manufacturer": "manufacturer", "product": "product", "interface": "interface"}

		for item in serial.tools.list_ports.comports():
			if (portOnly):
				valueList.append(item.device)
			else:
				info = {}
				for key, variable in catalogue.items():
					if (((len(include) == 0) or (key in include)) and ((len(exclude) == 0) or (key not in exclude))):
						info[key] = getattr(item, variable)
				valueList.append(info)

		return valueList

	class Child(Utilities_Child):
		"""A COM Port connection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self.device = serial.Serial()

			#These are the defaults for serial.Serial.__init__()
			self.port         = None                #The device name or (vendor id (int), product id (int))
			self.baudRate     = 9600                #Rate at which information is transferred
			self.byteSize     = serial.EIGHTBITS    #Number of bits per bytes
			self.parity       = serial.PARITY_NONE  #For error detection
			self.stopBits     = serial.STOPBITS_ONE #Signals message end
			self.timeoutRead  = None                #Read timeout. Makes the listener wait
			self.timeoutWrite = None                #Write timeout. Makes the speaker wait
			self.flowControl  = False               #Software flow control
			self.rtsCts       = False               #Hardware (RTS/CTS) flow control
			self.dsrDtr       = False               #Hardware (DSR/DTR) flow control
			self.message      = None                #What is sent to the listener
			self.vendorId     = None
			self.productId    = None

		def __exit__(self, exc_type, exc_value, traceback):
			"""Allows the user to use a with statement to make sure the socket connection gets closed after use."""

			self.close()

			return Utilities_Container.__exit__(self, exc_type, exc_value, traceback)

		def getPort(self):
			"""Returns the port.

			Example Input: getPort()
			"""

			return self.port

		def getBaudRate(self):
			"""Returns the baud rate.

			Example Input: getBaudRate()
			"""

			return self.baudRate

		def getDataBits(self):
			"""Overridden function for getByteSize().

			Example Input: getDataBits()
			"""

			value = self.getByteSize()
			return value

		def getByteSize(self):
			"""Returns the byte size.

			Example Input: getByteSize()
			"""

			#Format the byte size
			if (self.byteSize == serial.FIVEBITS):
				return 5

			elif (self.byteSize == serial.SIXBITS):
				return 6

			elif (self.byteSize == serial.SEVENBITS):
				return 7

			elif (self.byteSize == serial.EIGHTBITS):
				return 8

			else:
				return self.byteSize

		def getParity(self):
			"""Returns the parity.

			Example Input: getParity()
			"""

			if (self.parity == serial.PARITY_NONE):
				return None

			elif (self.parity == serial.PARITY_ODD):
				return "odd"
			
			elif (self.parity == serial.PARITY_EVEN):
				return "even"
			
			elif (self.parity == serial.PARITY_MARK):
				return "mark"
			
			elif (self.parity == serial.PARITY_SPACE):
				return "space"

			else:
				return self.parity

		def getStopBits(self):
			"""Returns the stop bits.

			Example Input: getStopBits()
			"""

			if (self.stopBits == serial.STOPBITS_ONE):
				return 1

			elif (self.stopBits == serial.STOPBITS_TWO):
				return 2

			elif (self.stopBits == serial.STOPBITS_ONE_POINT_FIVE):
				return 1.5

			else:
				return self.stopBits

		def getTimeoutRead(self):
			"""Returns the read timeout.

			Example Input: getTimeoutRead()
			"""

			return self.timeoutRead

		def getTimeoutWrite(self):
			"""Returns the write timeout.

			Example Input: getTimeoutWrite()
			"""

			return self.timeoutWrite

		def getFlow(self):
			"""Returns the software flow control.

			Example Input: getFlow()
			"""

			return self.flowControl

		def getFlowS(self):
			"""Returns the hardware flow control.

			Example Input: getFlowS(True)
			"""

			return self.rtsCts

		def getFlowR(self):
			"""Returns the hardware flow control.

			Example Input: getFlowR()
			"""

			return self.dsrDtr

		def getMessage(self):
			"""Returns the message that will be sent.

			Example Input: getMessage()
			"""

			return self.message

		def getId(self):
			"""Returns the product id and vendor id of the device connected to the COM Port.

			Example Input: getId()
			"""

			return (self.vendorId, self.productId)

		#Setters
		def setPort(self, value):
			"""Changes the port.

			value (str) - The new port

			Example Input: setPort("COM1")
			"""

			self.port = value

		def setBaudRate(self, value):
			"""Changes the baud rate.

			value (int) - The new baud rate

			Example Input: setBaudRate(9600)
			"""

			self.baudRate = value

		def setDataBits(self, value):
			"""Overridden function for setByteSize().

			value (int) - The new byte size. Can be 5, 6, 7, or 8

			Example Input: setDataBits(8)
			"""

			self.setByteSize(value)

		def setByteSize(self, value):
			"""Changes the byte size.

			value (int) - The new byte size. Can be 5, 6, 7, or 8

			Example Input: setByteSize(8)
			"""

			#Ensure that value is an integer
			if (type(value) != int):
				value = int(value)

			#Format the byte size
			if (value == 5):
				self.byteSize = serial.FIVEBITS

			elif (value == 6):
				self.byteSize = serial.SIXBITS

			elif (value == 7):
				self.byteSize = serial.SEVENBITS

			elif (value == 8):
				self.byteSize = serial.EIGHTBITS

		def setParity(self, value):
			"""Changes the parity.

			value (str) - The new parity. Can be None, "odd", "even", "mark", or "space". Only the first letter is needed

			Example Input: setParity("odd")
			"""

			if (value is not None):
				#Ensure correct format
				if (type(value) == str):
					value = value.lower()

					if (value[0] == "n"):
						self.parity = serial.PARITY_NONE
					
					elif (value[0] == "o"):
						self.parity = serial.PARITY_ODD
					
					elif (value[0] == "e"):
						self.parity = serial.PARITY_EVEN
					
					elif (value[0] == "m"):
						self.parity = serial.PARITY_MARK
					
					elif (value[0] == "s"):
						self.parity = serial.PARITY_SPACE

					else:
						errorMessage = f"There is no parity {value}"
						raise KeyError(errorMessage)
						# return False

				else:
					errorMessage = f"There is no parity {value}"
					raise KeyError(errorMessage)
					# return False

			else:
				self.parity = serial.PARITY_NONE

			return True

		def setStopBits(self, value):
			"""Changes the stop bits.

			value (int) - The new stop bits

			Example Input: setStopBits(1)
			Example Input: setStopBits(1.5)
			Example Input: setStopBits(2)
			"""

			#Ensure that value is an integer or float
			if ((type(value) != int) and (type(value) != float)):
				value = int(value)

			#Format the stop bits
			if (value == 1):
				self.stopBits = serial.STOPBITS_ONE

			elif (value == 2):
				self.stopBits = serial.STOPBITS_TWO

			elif (value == 1.5):
				self.stopBits = serial.STOPBITS_ONE_POINT_FIVE

			else:
				errorMessage = f"There is no stop bit {value}"
				raise KeyError(errorMessage)

		def setTimeout(self, value = None):
			"""Runs setTimeoutRead and setTimeoutWrite().

			Example Input: setTimeout()
			Example Input: setTimeout(1000)
			"""

			self.setTimeoutRead(value)
			self.setTimeoutWrite(value)

		def setTimeoutRead(self, value = None):
			"""Changes the read timeout.

			value (int) - How many milli-seconds to wait for read()
				- If None: Wait forever
				- If 0: Do not wait

			Example Input: setTimeoutRead()
			Example Input: setTimeoutRead(1000)
			"""

			self.timeoutRead = value

		def setTimeoutWrite(self, value = None):
			"""Changes the write timeout.

			value (int) - How many milli-seconds to wait for write()
				- If None: Wait forever
				- If 0: Do not wait

			Example Input: setTimeoutWrite()
			Example Input: setTimeoutWrite(1000)
			"""

			self.timeoutWrite = value

		def setFlow(self, value):
			"""Changes the software flow control.

			value (bool) - If True: Enables software flow control

			Example Input: setFlow(True)
			"""

			self.flowControl = value

		def setFlowS(self, value):
			"""Changes the hardware flow control.

			value (bool) - If True: Enables RTS/CTS flow control

			Example Input: setFlowS(True)
			"""

			self.rtsCts = value

		def setFlowR(self, value):
			"""Changes the hardware flow control.

			value (bool) - If True: Enables DSR/DTR flow control

			Example Input: setFlowR(True)
			"""

			self.dsrDtr = value

		def setMessage(self, value):
			"""Changes the message that will be sent.

			value (str) - The new message

			Example Input: setMessage("Lorem ipsum")
			"""

			self.message = value

		def open(self, port = None, autoEmpty = True):
			"""Gets the COM port that the zebra printer is plugged into and opens it.
			Returns True if the port sucessfully opened.
			Returns False if the port failed to open.
			Special thanks to Mike Molt for how tos earch by vendor id and product id on https://stackoverflow.com/questions/38661797/is-it-possible-to-refer-to-a-serial-device-by-vendor-and-device-id-in-pyserial

			port (str) - If Provided, opens this port instead of the port in memory
				- If tuple: (vendorId (int or hex), productId (int or hex))
			autoEmpty (bool) - Determines if the comPort is automatically flushed after opening

			Example Input: open()
			Example Input: open("COM2")
			Example Input: open(autoEmpty = False)
			Example Input: open((1529, 16900))
			Example Input: open((0x05F9, 0x4204))
			"""

			if (port is None):
				port = self.port
				if (port is None):
					errorMessage = f"'port' cannot be None for open() in {self.__repr__()}"
					raise ValueError(errorMessage)

			if (isinstance(port, (tuple, list, range, types.GeneratorType))):
				if (len(port) != 2):
					errorMessage = f"'port' should have a length of 2, not {len(port)} for open() in {self.__repr__()}"
					raise ValueError(errorMessage)

				self.vendorId = port[0]
				self.productId = port[1]
				port = None
			else:
				self.vendorId = None
				self.productId = None
				
			if (isinstance(self.vendorId, str)):
				try:
					self.vendorId = hex(int(self.vendorId, 16))
				except ValueError:
					self.vendorId = int(self.vendorId)
			if (isinstance(self.productId, str)):
				try:
					self.productId = hex(int(self.productId, 16))
				except ValueError:
					self.productId = int(self.productId)

			for item in serial.tools.list_ports.comports():
				if (port is None):
					if ((item.vid == self.vendorId) and (item.pid == self.productId)):
						port = item.device
						break
				else:
					if (item.device == port):
						self.vendorId = item.vid
						self.productId = item.pid
						break
			else:
				if (port is None):
					errorMessage = f"Cannot find COM Port with a device whose vendor id is {self.vendorId} and product id is {self.productId} for open() in {self.__repr__()}"
				else:
					errorMessage = f"Cannot find COM Port on port {port} for open() in {self.__repr__()}"
				raise ValueError(errorMessage)
			self.port = port

			#Configure port options
			self.device.port         = self.port
			self.device.baudrate     = self.baudRate
			self.device.bytesize     = self.byteSize
			self.device.parity       = self.parity
			self.device.stopbits     = self.stopBits
			self.device.xonxoff      = self.flowControl
			self.device.rtscts       = self.rtsCts
			self.device.dsrdtr       = self.dsrDtr

			if (self.timeoutRead is None):
				self.device.timeout = None
			else:
				self.device.timeout = self.timeoutRead / 1000

			if (self.timeoutWrite is None):
				self.device.writeTimeout = None
			else:
				self.device.writeTimeout = self.timeoutWrite / 1000

			if (self.isOpen()):
				self.close()

			#Open the port
			try:
				self.device.open()
			except socket.error as error:
				return error

			#Check port status
			if (not self.isOpen()):
				error = ValueError(f"Cannot open serial port {self.device.port} for {self.__repr__()}")
				return error

			if (autoEmpty):
				self.empty()

		def isOpen(self):
			"""Checks whether the COM port is open or not."""

			return self.device.isOpen()

		def empty(self):
			"""Empties the buffer data in the given COM port."""

			if (not self.isOpen()):
				warnings.warn(f"Serial port has not been opened yet for {self.__repr__()}\n Make sure that ports are available and then launch this application again", Warning, stacklevel = 2)
				
			self.device.flushInput() #flush input buffer, discarding all its contents
			self.device.flushOutput()#flush output buffer, aborting current output and discard all that is in buffer

		def close(self, port = None):
			"""Closes the current COM Port.

			### Not Yet Implemented ###
			port (str) - If Provided, closes this port instead of the port in memory

			Example Input: close()
			"""

			if (not self.isOpen()):
				warnings.warn(f"Serial port has not been opened yet for {self.__repr__()}\n Make sure that ports are available and then launch this application again", Warning, stacklevel = 2)
				return

			self.device.close()

		def send(self, message = None, autoEmpty = True):
			"""Sends a message to the COM device.
			Returns if the send was sucessful or not.

			message (str) - The message that will be sent to the listener
							If None: The internally stored message will be used.

			Example Input: send()
			Example Input: send("Lorem ipsum")
			"""

			if (message is None):
				message = self.message

			if (message is None):
				warnings.warn(f"No message to send for send() in {self.__repr__()}", Warning, stacklevel = 2)
				return
			
			if (not self.isOpen()):
				warnings.warn(f"Serial port has not been opened yet for {self.__repr__()}\n Make sure that ports are available and then launch this application again", Warning, stacklevel = 2)
				return

			if (autoEmpty):
				self.empty()

			if (not isinstance(message, bytes)):
				message = message.encode("utf-8")

			#write data
			try:
				self.device.write(message)
			except:
				return False
			return True

		def read(self, length = None, end = None, decode = True, lines = 1, reply = None, 
			reply_retryAttempts = 0, reply_retryDelay = 0, reply_retryPrintError = False):
			"""Listens to the comport for a message.

			length (int) - How long the string is expected to be

			end (str) - What to listen for as an end of message
				- If None: Will return the first character in the buffer

			decode (bool) - Determines if the sring should be automatically decoded
				- If True: Will decode the string
				- If False: Will not decode the string

			lines (int) - How many lines to read that end with 'end'
				- Does not apply if 'end' is None

			reply (str) - What to send back after recieving the full message

			Example Input: read()
			Example Input: read(10000)
			Example Input: read(end = "\n")
			"""

			if (not self.isOpen()):
				warnings.warn(f"Serial port has not been opened yet for {self.__repr__()}\n Make sure that ports are available and then launch this application again", Warning, stacklevel = 2)
				return

			if (reply is not None):
				if (not isinstance(reply, bytes)):
					reply = reply.encode("utf-8")

			if (end is None):
				if (length is None):
					length = 1
				message = self.device.read(length)
			elif (end == "\n"):
				if (lines <= 1):
					if (length is None):
						length = -1
					message = self.device.readline(length)
				else:
					message = self.device.readlines(lines)
			else:
				message = b""

				if (not isinstance(end, bytes)):
					end = end.encode("utf-8")
				if (length is None):
					length = 1

				linesRead = 0
				while True:
					while True:
						if (not self.isOpen()):
							return

						value = self.device.read(length)
						message += value
						if (end in value):
							linesRead += 1
							break
					
					if (linesRead >= lines):
						break

			if (reply is not None):
				try:
					self.device.write(reply)
				except Exception as error_1:
					if (reply_retryPrintError):
						traceback.print_exception(type(error_1), error_1, error_1.__traceback__)
					attempts = 0
					while (attempts > reply_retryAttempts):
						try: 
							self.device.write(reply)
							break
						except Exception as error_2:
							if (reply_retryPrintError):
								traceback.print_exception(type(error_2), error_2, error_2.__traceback__)
							time.sleep(reply_retryDelay / 1000)
					else:
						return False

			if (decode):
				message = message.decode("utf-8")

			return message

		def checkId(self, vendor = None, product = None):
			"""Returns if the connected COM Port has the given vendor id and/or product id.

			Example Input: checkId(vendor = 1529)
			Example Input: checkId(product = 16900)
			Example Input: checkId(vendor = 1529, product = 16900)
			Example Input: checkId(product = [16900, 16901, 16902])
			"""

			if ((vendor is None) and (product is None)):
				errorMessage = f"Must provide arguments 'vendor' and/or 'product' for checkId() in {self.__repr__()}"
				raise ValueError(errorMessage)
			if (not isinstance(vendor, (list, tuple, range, types.GeneratorType, type(None)))):
				vendor = [vendor]
			if (not isinstance(product, (list, tuple, range, types.GeneratorType, type(None)))):
				product = [product]

			if ((self.vendorId is None) or (self.productId is None)):
				for item in serial.tools.list_ports.comports():
					if (item.device == port):
						vendorId = item.vid
						productId = item.pid
						break
				else:
					return
			else:
				vendorId = self.vendorId
				productId = self.productId

			return (((vendor is None) or ((vendor is not None) and (vendorId in vendor))) and
					((product is None) or ((product is not None) and (productId in product))))

class Barcode(Utilities_Container):
	"""A controller for a Barcode.
	
	______________________ EXAMPLE USE ______________________
	
	com = API_Com.build()
	barcode = com.barcode[0]
	barcode.create("Lorem Ipsum")
	barcode.show()
	_________________________________________________________
	"""

	def __init__(self, parent):
		"""Defines the internal variables needed to run."""

		#Initialize Inherited Modules
		Utilities_Container.__init__(self, parent)

	def getAll(self):
		"""Returns all barcoder formats.

		Example Input: getAll()
		"""

		valueList = sorted(barcode.PROVIDED_BARCODES + ["qr"])

		return valueList

	class Child(Utilities_Child):
		"""A COM Port connection."""

		def __init__(self, parent, label, size = None, pixelSize = None, borderSize = None, 
			correction = None, color_foreground = None, color_background = None):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self.device = None
			self.image = None
			self.type = "code123"
			self.text = None

			#Barcode Attributes
			self.size = size
			self.pixelSize = pixelSize
			self.borderSize = borderSize
			self.correction = correction
			self.color_foreground = color_foreground
			self.color_background = color_background
			self.qrcode_correctionCatalogue = {
			7: qrcode.constants.ERROR_CORRECT_L, 15: qrcode.constants.ERROR_CORRECT_M, 25: 
			qrcode.constants.ERROR_CORRECT_Q, 30: qrcode.constants.ERROR_CORRECT_H, 
			"L": qrcode.constants.ERROR_CORRECT_L, "M": qrcode.constants.ERROR_CORRECT_M, 
			"Q": qrcode.constants.ERROR_CORRECT_Q, "H": qrcode.constants.ERROR_CORRECT_H, 
			"l": qrcode.constants.ERROR_CORRECT_L, "m": qrcode.constants.ERROR_CORRECT_M, 
			"q": qrcode.constants.ERROR_CORRECT_Q, "h": qrcode.constants.ERROR_CORRECT_H}

		def getType(self, formatted = False):
			"""Returns the barcode type."""

			return self.type

		def getText(self):
			"""Returns what the barcode should say when decoded."""

			return self.text

		def setType(self, newType):
			"""Sets the default barcode type."""

			if (newType in self.parent.getAll()):
				self.type = newType
			else:
				warnings.warn(f"Unknown type {newType} in setType() for {self.__repr__()}", Warning, stacklevel = 2)

		def setCorrection(self, percent = 15):
			"""Sets the max amount that can be error correctted.

			percent (int) - How much can be correctted as a percentage
				~ 7, 15, 25, 30

			Example Input: setCorrection()
			Example Input: setCorrection(30)
			"""

			if (percent not in self.qrcode_correctionCatalogue):
				if (isinstance(percent, (int, float))):
					percent = self.getClosest((7, 15, 25, 30), percent)
				else:
					percent = 15
			self.correction = self.qrcode_correctionCatalogue[percent]

		def setSize(self, number = None):
			"""Must be between 1 and 40.

			Example Input: setSize()
			Example Input: setSize(5)
			"""

			if ((number is not None) and (number not in range(1, 40))):
				number = self.getClosest(range(1, 40), number)

			self.size = number

		def setPixelSize(self, number = None):
			"""How large the boxes in the QR code are.

			Example Input: setPixelSize()
			Example Input: setPixelSize(5)
			"""

			if (number is None):
				number = 10

			self.pixelSize = number

		def setBorderSize(self, number = None):
			"""How wide the border is.

			Example Input: setBorderSize()
			Example Input: setBorderSize(5)
			"""

			if (number is None):
				number = 4

			self.borderSize = number

		def setColor(self, foreground = None, background = None):
			"""What color the barcode will be.

			foreground (str) - Color of the foreground
			background (str) - Color of the background

			Example Input: setColor()
			Example Input: setColor("red", "blue")
			"""

			if (foreground is None):
				foreground = "black"
			if (background is None):
				background = "white"

			self.color_foreground = foreground
			self.color_background = background

		def create(self, text, codeType = None, filePath = None, size = None, pixelSize = None, borderSize = None, 
			correction = None, color_foreground = None, color_background = None, logo = None, logoSize = None):
			"""Returns a PIL image of the barcode for the user or saves it somewhere as an image.
			Use: https://ourcodeworld.com/articles/read/554/how-to-create-a-qr-code-image-or-svg-in-python

			text (str)     - What the barcode will say
			codeType (str) - What type of barcode will be made
				- If None: Will use self.type

			Example Input: create(1234567890)
			Example Input: create(1234567890, "code128")
			"""

			self.text = text
			if (codeType not in [None, self.type]):
				self.setType(codeType)

			#Create barcode
			if (self.type == "qr"):
				if (correction is not None):
					self.correction = correction
				elif (self.correction is None):
					self.correction = qrcode.constants.ERROR_CORRECT_M

				if (pixelSize is not None):
					self.pixelSize = pixelSize
				elif (self.pixelSize is None):
					self.pixelSize = 10

				if (borderSize is not None):
					self.borderSize = borderSize
				elif (self.borderSize is None):
					self.borderSize = 4

				if (logoSize is not None):
					self.logoSize = logoSize
				elif (self.logoSize is None):
					self.logoSize = 10

				if (color_foreground is not None):
					self.color_foreground = color_foreground
				elif (self.color_foreground is None):
					self.color_foreground = "black"

				if (color_background is not None):
					self.color_background = color_background
				elif (self.color_background is None):
					self.color_background = "white"

				if (size is not None):
					self.size = size

				self.device = qrcode.QRCode(version = self.size,
					error_correction = self.correction,
					box_size = self.pixelSize, 
					border = self.borderSize,
					image_factory = None,
					mask_pattern = None)

				self.device.add_data(f"{text}")
				self.device.make(fit = True)
				self.image = self.device.make_image(fill_color = self.color_foreground, back_color = self.color_background)

				if (logo is not None):
					#See: https://docs.eyesopen.com/toolkits/cookbook/python/image-manipulation/addlogo.html#solution
					image_logo = PIL.Image.open(logo)
					if (self.logoSize > 0):
						newSize = self.logoSize / 100
						image_logo = image_logo.resize((int(self.image.size[0] * newSize), int(self.image.size[1] * newSize)))
					self.image.paste(image_logo, (int(self.image.size[0] / 2 - image_logo.size[0] / 2), int(self.image.size[1] / 2 - image_logo.size[1] / 2)))

			else:
				self.device = barcode.get(self.type, f"{text}", writer = barcode.writer.ImageWriter())
				self.image = self.device.render(writer_options = None)

				if (filePath is not None):
					self.device.save(filePath)

			return self.image

		def show(self):
			"""Shows the barcode to the user."""

			self.image.show()

		def get(self):
			"""Returns the barcode."""

			return self.image

		def save(self, filePath):
			"""Saves the barcode as an image."""

			self.image.save(filePath)

		def getBestSize(self, text):
			"""Returns what qr code version would be applied to keep the barcode small.

			text (str) - What the barcode would say

			Example Input: getBestSize(1234567890)
			"""
			if (self.correction is None):
				self.correction = qrcode.constants.ERROR_CORRECT_M

			device = qrcode.QRCode(error_correction = self.correction)
			device.add_data(f"{text}")
			return device.best_fit()

class Email(Utilities_Container):
	"""A controller for a Email connection.
	Note: If you use gmail, make sure you allow less secure apps: https://myaccount.google.com/lesssecureapps?pli=1

	Special thanks to Nael Shiab for how to send emails with attachments on http://naelshiab.com/tutorial-send-email-python/
	Use: https://www.blog.pythonlibrary.org/2008/08/16/wxpymail-creating-an-application-to-send-emails/
	
	______________________ EXAMPLE USE ______________________
	
	com = API_Com.build()
	email = com.email[0]
	email.open("lorem.ipsum@example.com", "LoremIpsum")
	email.append("Lorem ipsum dolor sit amet")
	email.attach("example.txt")
	email.send("dolor.sit@example.com")
	_________________________________________________________
	"""

	def __init__(self, parent):
		"""Defines the internal variables needed to run."""

		#Initialize Inherited Modules
		Utilities_Container.__init__(self, parent)

	class Child(Utilities_Child):
		"""A USB conection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self._from = None
			self._password = None

			self.current_config = None

		def open(self, address, password, server = None, port = None):
			"""Opens a connection to an email to send from.

			address (str) - A valid email address to send from
			password (str) - The password for 'address'

			server (str) - What email server is being used
				- If None: Will use gmail
			port (int) - What port to use
				- If None: 587

			Example Input: open("lorem.ipsum@example.com", "LoremIpsum")
			Example Input: open("lorem.ipsum@example.com", "LoremIpsum", server = "194.2.1.1", port = 587)
			"""

			self._from = address
			self._password = password

			self.server = server or "smtp.gmail.com"
			self.port = port or 587

			self.attachments = []
			self.zipCatalogue = collections.defaultdict(list)
			self.body = self.Body(self)

		def append(self, *args, **kwargs):
			"""Appends the given text to the email.

			Example Input: append("Lorem ipsum dolor sit amet")
			"""

			return self.body.append(*args, **kwargs)

		def attach(self, *args, **kwargs):
			"""Attaches the given object to the email.

			Example Input: attach("example.txt")
			"""

			return self.Attachment(self, *args, **kwargs)

		def send(self, address, subject = None, server = None, port = None):
			"""Sends an email to the provided address.

			address (str) - A valid email address to send to
			subject (str) - The subject of the email

			Example Input: send("dolor.sit@example.com")
			Example Input: send("dolor.sit@example.com", subject = "Example")
			"""

			def yieldAttachments():
				for attachmentHandle in self.attachments:
					for item in attachmentHandle.yieldMime():
						yield item

			def yieldZip():
				for zip_label, attachments in self.zipCatalogue.items():
					with io.BytesIO() as stream:
						with zipfile.ZipFile(stream, mode = "w") as zipHandle:
							for attachmentHandle in attachments:
								for payload, name in attachmentHandle.yieldPayload():
									zipHandle.writestr(name, payload)

						section = email_MIMEBase('application', 'zip')
						section.set_payload(stream.getvalue())
						email_encoders.encode_base64(section)
						section.add_header('Content-Disposition', 'attachment',  filename = f"{zip_label}.zip")
						yield section

			########################################

			assert self._from is not None

			message = email_MIMEMultipart()
			message["From"] = self._from
			message["To"] = address

			if (subject):
				message["Subject"] = subject

			for item in self.body.yieldMime():
				message.attach(item)

			for item in yieldAttachments():
				message.attach(item)

			for item in yieldZip():
				message.attach(item)

			with smtplib.SMTP(server or self.server, int(port or self.port)) as serverHandle:
				serverHandle.starttls()
				serverHandle.login(message["From"], self._password)
				serverHandle.sendmail(message["From"], address, message.as_string())

		class Body():
			"""Holds the body of the email to send."""

			def __init__(self, parent):
				self.parent = parent

				self.plainText = ""
				self.attachBody = True
				self.message_root = xml.Element("html")
				self.message_body = xml.SubElement(self.message_root, "body")

			def append(self, text, header = None, link = None):
				"""Appends the given text to the email.
				Use: https://stackoverflow.com/questions/882712/sending-html-email-using-python
				Use: https://www.blog.pythonlibrary.org/2013/04/30/python-101-intro-to-xml-parsing-with-elementtree/

				text (str) - What to append to the end of the email

				Example Input: append("Lorem ipsum dolor sit amet")
				Example Input: append("Lorem ipsum dolor sit amet", header = "Lorem Ipsum")
				Example Input: append("Lorem ipsum dolor sit amet", link = ("https://www.lipsum.com/", "click here"))
				"""

				if (header):
					paragraph = xml.SubElement(self.message_body, "h2")
					paragraph.text = header

					self.plainText += f"\t**{header}**\n"

				paragraph = xml.SubElement(self.message_body, "p")

				paragraph.text = text
				self.plainText += f"{text}\n"

				if (link):
					paragraph = xml.SubElement(self.message_body, "a", attrib = {"href": link[0]})
					paragraph.text = link[1]

					self.plainText += f"{link[1]}: {link[0]}\n"

			def plain(self):
				"""Returns the body of the message as plain text.

				Example Input: plain()
				"""

				return self.plainText

			def html(self):
				"""Returns the MIME handle to attach to the email.

				Example Input: html()
				"""

				text = xml.tostring(self.message_root, method = "html").decode()
				return text.replace("\n", "<br>")

			def yieldMime(self, html = True):
				"""Returns the MIME handle to attach to the email.

				Example Input: yieldMime()
				"""

				if (html):
					yield email_MIMEText(self.html(), "html")
				else:
					yield email_MIMEText(self.plain(), "plain")

		class Attachment():
			"""An attachment to put on the email."""

			def __init__(self, parent, source, *args, zip_label = None, **kwargs):
				"""Auto-detects how to attach 'source'.

				source (any) - What to attach
				zip_label (str) - What zip folder to put this attachment in
					- If None: Will not zip this attachment

				Example Input: attach("example.txt")
				Example Input: attach(bitmap, name = "screenshot")
				"""

				self.parent = parent
				self.yieldPayload = NotImplementedError #Yields (payload, name)
				self.yieldMime = NotImplementedError #Yields MIME handles

				if (zip_label):
					self.parent.zipCatalogue[zip_label].append(self)
				else:
					self.parent.attachments.append(self)

				if (isinstance(source, str)):
					self.file_routine(source, *args, **kwargs)
					return

				if (isinstance(source, wx.Bitmap)):
					self.wxBitmap_routine(source, *args, **kwargs)
					return

				if (isinstance(source, Database.Base)):
					if (isinstance(source, Database.Configuration)):
						self.database_routine(source, *args, override_readOnly = True, **kwargs)
						return

					if (isinstance(source, Database.Config_Base)):
						self.database_routine(source, *args, ifDirty = False, removeDirty = False, applyOverride = False, **kwargs)
						return

					if (isinstance(source, Database.Database)):
						_defaultName = re.split("\.", os.path.basename(source.baseFileName))[0]
						self.database_routine(source, *args, _defaultName = f"{_defaultName}.sql", **kwargs)
						return

				raise NotImplementedError(type(source))

			def file_routine(self, source, name = None):
				"""Sets up the attachment to add a file.

				source (str) - Where the file to attach is located on disk

				Example Input: attach("example.txt")
				Example Input: attach("example.*")
				"""

				def yieldWalk():
					for dirName, subdirList, fileList in os.walk(source):
						for item in fileList:
							yield os.path.join(dirName, item)

				def yieldFilePaths(location):
					if (os.path.isdir(location)):
						pathList = yieldWalk()
					else:
						pathList = glob.iglob(location)

					for filePath in pathList:
						if (os.path.isdir(filePath)):
							for item in yieldFilePaths(filePath):
								yield item
							continue

						yield filePath

				def _baseRoutine():
					nonlocal self, pathList, name

					for filePath in pathList:
						with open(filePath, "rb") as fileHandle:
							yield fileHandle.read(), name or os.path.basename(filePath)

				def _mimeRoutine():
					nonlocal self

					for _payload, _name in _baseRoutine():

						section = email_MIMEBase("application", "octet-stream")
						section.set_payload(_payload)
						email_encoders.encode_base64(section)
						
						section.add_header("Content-Disposition", f"attachment; filename = {_name}")
						yield section

				#################################################

				pathList = tuple(yieldFilePaths(source))

				self.yieldPayload = _baseRoutine
				self.yieldMime = _mimeRoutine

			def wxBitmap_routine(self, source, name = None, *, imageType = "bmp"):
				"""Sets up the attachment to add a wxBitmap.
				Special thanks to the following for how to attach a wxBitmap object:
					Kolmar on: https://stackoverflow.com/questions/27931079/base-64-encode-bitmap-from-wx-python/27931710#27931710
					woss-2 on: http://wxpython-users.1045709.n5.nabble.com/Python-3-6-wx-4-0-0-RichtextCtrl-Export-and-import-text-in-xml-format-td5726961.html

				source (wxBitmap) - A bitmap in memory to attach

				Example Input: attach(bitmap)
				Example Input: attach(bitmap, imageType = "png")
				"""

				def _baseRoutine():
					nonlocal self, payload, name, imageType

					yield payload, f"{name or 'bitmap'}.{imageType}"

				def _mimeRoutine():
					nonlocal self, imageType

					for _payload, _name in _baseRoutine():
						yield email_MIMEImage(_payload, name = _name, _subtype = imageType)

				#################################################

				with io.BytesIO() as stream:
					MyUtilities.wxPython.saveBitmap(source, stream, imageType = imageType)
					payload = stream.getvalue()

				self.yieldPayload = _baseRoutine
				self.yieldMime = _mimeRoutine

			def database_routine(self, source, name = None, *, _defaultName = None, **kwargs):
				"""Sets up the attachment to add a json, yaml, configuration, or sql database handle.

				Example Input: database_routine()
				"""

				def _baseRoutine():
					nonlocal self, payload, name

					yield payload, name or _defaultName or os.path.basename(source.default_filePath) or f"settings.{source.defaultFileExtension}"

				def _mimeRoutine():
					nonlocal self

					for _payload, _name in _baseRoutine():
						section = email_MIMEText(_payload)
						section.add_header("Content-Disposition", "attachment", filename = _name)
						yield section

				#################################################

				with io.StringIO() as stream:
					source.save(stream, closeIO = False, **kwargs)
					payload = stream.getvalue()

				self.yieldPayload = _baseRoutine
				self.yieldMime = _mimeRoutine

class CommunicationManager():
	"""Helps the user to communicate with other devices.

	CURRENTLY SUPPORTED METHODS
		- COM Port
		- Ethernet & Wi-fi
		- Barcode
		- QR Code
		- USB
		- Email

	UPCOMING SUPPORTED METHODS
		- Raspberry Pi GPIO

	Example Input: Communication()
	"""

	def __init__(self):
		"""Initialized internal variables."""

		self.ethernet = Ethernet(self)
		self.barcode = Barcode(self)
		self.comPort = ComPort(self)
		self.email = Email(self)
		self.usb = USB(self)

	def __str__(self):
		"""Gives diagnostic information on the GUI when it is printed out."""

		output = f"Communication()\n-- id: {id(self)}\n"

		output += f"-- Ethernets: {len(self.ethernet)}\n"
		output += f"-- COM Ports: {len(self.comPort)}\n"
		output += f"-- USB Ports: {len(self.usb)}\n"
		output += f"-- Barcodes: {len(self.barcode)}\n"
		output += f"-- Email Accounts: {len(self.email)}\n"

		return output

	def __repr__(self):
		representation = f"Communication(id = {id(self)})"
		return representation

	def getAll(self):
		"""Returns all available communication types.

		Example Input: getAll()
		"""

		return [self.ethernet, self.comPort, self.usb, self.barcode, self.email]

rootManager = CommunicationManager()

def getEthernet(label = None, *, comManager = None):
	"""Returns an ethernet handle with the given label. If it does not exist, it will make one.

	label (str) - What ethernet to get
		- If None: Will make a new ethernet port

	Example Input: getEthernet()
	Example Input: getEthernet(1)
	"""
	global rootManager
	
	comManager = MyUtilities.common.ensure_default(comManager, default = rootManager)
	return comManager.ethernet.add(label = label)

def getCom(label = None, *, comManager = None):
	"""Returns a com port handle with the given label. If it does not exist, it will make one.

	label (str) - What com port to get
		- If None: Will make a new com port

	Example Input: getCom()
	Example Input: getCom(1)
	"""
	global rootManager
	
	comManager = MyUtilities.common.ensure_default(comManager, default = rootManager)
	return comManager.comPort.add(label = label)

def getUsb(label = None, *, comManager = None):
	"""Returns a usb handle with the given label. If it does not exist, it will make one.

	label (str) - What usb to get
		- If None: Will make a new usb port

	Example Input: getusb()
	Example Input: getusb(1)
	"""
	global rootManager
	
	comManager = MyUtilities.common.ensure_default(comManager, default = rootManager)
	return comManager.usb.add(label = label)

def getBarcode(label = None, *, comManager = None):
	"""Returns a barcode handle with the given label. If it does not exist, it will make one.

	label (str) - What barcode to get
		- If None: Will make a new barcode port

	Example Input: getBarcode()
	Example Input: getBarcode(1)
	"""
	global rootManager
	
	comManager = MyUtilities.common.ensure_default(comManager, default = rootManager)
	return comManager.barcode.add(label = label)

def getEmail(label = None, *, comManager = None):
	"""Returns an email handle with the given label. If it does not exist, it will make one.

	label (str) - What email to get
		- If None: Will make a new email port

	Example Input: getEmail()
	Example Input: getEmail(1)
	"""
	global rootManager
	
	comManager = MyUtilities.common.ensure_default(comManager, default = rootManager)
	return comManager.email.add(label = label)

# def runFile():


if __name__ == '__main__':
	# print(getEthernet())
	# for item in rootManager.comPort.getAll():
	# 	print(item["vendorId"], item["productId"])


	import time
	import subprocess
	subprocess.Popen(["py", "maintenance.py"]) #https://docs.python.org/2/library/os.html#os.startfile
	print("@1.2")
	time.sleep(1)
	print("@1.3")
	sys.exit()

