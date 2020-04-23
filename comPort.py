__version__ = "2.0.0"

#Import standard elements
import sys
import warnings
import traceback

#Import communication elements for talking to other devices such as printers, the internet, a raspberry pi, etc.
import types
import socket
import serial
import serial.tools.list_ports

import API_Com.utilities

#Required Modules
##py -m pip install
	# pyserial

class ComPort(API_Com.utilities.Utilities_Container):
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
		API_Com.utilities.Utilities_Container.__init__(self, parent)

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

	class Child(API_Com.utilities.Utilities_Child):
		"""A COM Port connection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			API_Com.utilities.Utilities_Child.__init__(self, parent, label)
		
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

			return API_Com.utilities.Utilities_Container.__exit__(self, exc_type, exc_value, traceback)

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