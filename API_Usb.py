__version__ = "2.0.0"

#Import standard elements
import sys

# #Import communication elements for talking to other devices such as printers, the internet, a raspberry pi, etc.
import usb
import select

import API_Com.utilities

#Required Modules
##py -m pip install
	# pyusb

##Module dependancies (Install the following .exe and/or .dll files)
	#The latest Windows binary on "https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download"
		#If on 64-bit Windows, copy "MS64\dll\libusb-1.0.dll" into "C:\windows\system32"
		#If on 32-bit windows, copy "MS32\dll\libusb-1.0.dll" into "C:\windows\SysWOW64"

#User Access Variables
ethernetError = socket.error

class USB(API_Com.utilities.Utilities_Container):
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
		API_Com.utilities.Utilities_Container.__init__(self, parent)

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

	class Child(API_Com.utilities.Utilities_Child):
		"""A USB conection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			API_Com.utilities.Utilities_Child.__init__(self, parent, label)
		
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