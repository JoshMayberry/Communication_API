__version__ = "1.0.0"

#Import standard elements
import warnings
import traceback
import threading
import subprocess

#Import communication elements for talking to other devices such as printers, the internet, a raspberry pi, etc.
import usb
import bisect
import select
import socket
import serial
import netaddr
import serial.tools.list_ports

#Import barcode software for drawing and decoding barcodes
import qrcode
import barcode

#Required Modules
##py -m pip install
	# pyserial
	# netaddr
	# pyusb
	# pyBarcode
	# qrcode

##Module dependancies (Install the following .exe and/or .dll files)
	#The latest Windows binary on "https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download"
		#If on 64-bit Windows, copy "MS64\dll\libusb-1.0.dll" into "C:\windows\system32"
		#If on 32-bit windows, copy "MS32\dll\libusb-1.0.dll" into "C:\windows\SysWOW64"

#User Access Variables
ethernetError = socket.error

#Controllers
def build(*args, **kwargs):
	"""Starts the GUI making process."""

	return Communication(*args, **kwargs)

#Iterators
class Iterator(object):
	"""Used by handle objects to iterate over their nested objects."""

	def __init__(self, data, filterNone = False):
		if (not isinstance(data, (list, dict))):
			data = data[:]

		self.data = data
		if (isinstance(self.data, dict)):
			self.order = list(self.data.keys())

			if (filterNone):
				self.order = [key for key in self.data.keys() if key != None]
			else:
				self.order = [key if key != None else "" for key in self.data.keys()]

			self.order.sort()

			self.order = [key if key != "" else None for key in self.order]

	def __iter__(self):
		return self

	def __next__(self):
		if (not isinstance(self.data, dict)):
			if not self.data:
				raise StopIteration

			return self.data.pop()
		else:
			if not self.order:
				raise StopIteration

			key = self.order.pop()
			return self.data[key]

#Background Processes
class ThreadQueue():
	"""Used by passFunction() to move functions from one thread to another.
	Special thanks to Claudiu for the base code on https://stackoverflow.com/questions/18989446/execute-python-function-in-main-thread-from-call-in-dummy-thread
	"""
	def __init__(self):
		"""Internal variables."""
	
		self.callback_queue = queue.Queue()

	def from_dummy_thread(self, myFunction, myFunctionArgs = None, myFunctionKwargs = None):
		"""A function from a MyThread to be called in the main thread."""

		self.callback_queue.put([myFunction, myFunctionArgs, myFunctionKwargs])

	def from_main_thread(self, blocking = True, printEmpty = False):
		"""An non-critical function from the sub-thread will run in the main thread.

		blocking (bool) - If True: This is a non-critical function
		"""

		def setupFunction(myFunctionList, myFunctionArgsList, myFunctionKwargsList):
			nonlocal self

			#Skip empty functions
			if (myFunctionList != None):
				myFunctionList, myFunctionArgsList, myFunctionKwargsList = Utilities_Base.formatFunctionInputList(self, myFunctionList, myFunctionArgsList, myFunctionKwargsList)
				
				#Run each function
				answerList = []
				for i, myFunction in enumerate(myFunctionList):
					#Skip empty functions
					if (myFunction != None):
						myFunctionEvaluated, myFunctionArgs, myFunctionKwargs = Utilities_Base.formatFunctionInput(self, i, myFunctionList, myFunctionArgsList, myFunctionKwargsList)
						answer = runFunction(myFunctionEvaluated, myFunctionArgs, myFunctionKwargs)
						answerList.append(answer)

				#Account for just one function
				if (len(answerList) == 1):
					answerList = answerList[0]
			return answerList

		def runFunction(myFunction, myFunctionArgs, myFunctionKwargs):
			"""Runs a function."""
			nonlocal self

			#Has both args and kwargs
			if ((myFunctionKwargs != None) and (myFunctionArgs != None)):
				answer = myFunction(*myFunctionArgs, **myFunctionKwargs)

			#Has args, but not kwargs
			elif (myFunctionArgs != None):
				answer = myFunction(*myFunctionArgs)

			#Has kwargs, but not args
			elif (myFunctionKwargs != None):
				answer = myFunction(**myFunctionKwargs)

			#Has neither args nor kwargs
			else:
				answer = myFunction()

			return answer

		if (blocking):
			myFunction, myFunctionArgs, myFunctionKwargs = self.callback_queue.get() #blocks until an item is available
			answer = setupFunction(myFunction, myFunctionArgs, myFunctionKwargs)
			
		else:       
			while True:
				try:
					myFunction, myFunctionArgs, myFunctionKwargs = self.callback_queue.get(False) #doesn't block
				
				except queue.Empty: #raised when queue is empty
					if (printEmpty):
						print("--- Thread Queue Empty ---")
					answer = None
					break

				answer = setupFunction(myFunction, myFunctionArgs, myFunctionKwargs)

		return answer

class MyThread(threading.Thread):
	"""Used to run functions in the background.
	More information on threads can be found at: https://docs.python.org/3.4/library/threading.html
	_________________________________________________________________________

	CREATE AND RUN A NEW THREAD
	#Create new threads
	thread1 = myThread(1, "Thread-1", 1)
	thread2 = myThread(2, "Thread-2", 2)

	#Start new threads
	thread1.start()
	thread2.start()
	_________________________________________________________________________

	RUNNING A FUNCTION ON A THREAD
	After the thread has been created and started, you can run functions on it like you do on the main thread.
	The following code shows how to run functions on the new thread:

	runFunction(longFunction, [1, 2], {label: "Lorem"}, self, False)
	_________________________________________________________________________

	If you exit the main thread, the other threads will still run.

	EXAMPLE CREATING A THREAD THAT EXITS WHEN THE MAIN THREAD EXITS
	If you want the created thread to exit when the main thread exits, make it a daemon thread.
		thread1 = myThread(1, "Thread-1", 1, daemon = True)

	You can also make it a daemon using the function:
		thread1.setDaemon(True)
	_________________________________________________________________________

	CLOSING A THREAD
	If any thread is open, the program will not end. To close a thread use return on the function that is running in the thread.
	The thread will then close itself automatically.
	"""

	def __init__(self, threadID = None, name = None, counter = None, daemon = None):
		"""Setup the thread.

		threadID (int) -
		name (str)     - The thread name. By default, a unique name is constructed of the form "Thread-N" where N is a small decimal number.
		counter (int)  - 
		daemon (bool)  - Sets whether the thread is daemonic. If None (the default), the daemonic property is inherited from the current thread.
		
		Example Input: MyThread()
		Example Input: MyThread(1, "Thread-1", 1)
		Example Input: MyThread(daemon = True)
		"""

		#Initialize the thread
		threading.Thread.__init__(self, name = name, daemon = daemon)
		# self.setDaemon(daemon)

		#Setup thread properties
		if (threadID != None):
			self.threadID = threadID

		self.stopEvent = threading.Event() #Used to stop the thread

		#Initialize internal variables
		self.shown = None
		self.window = None
		self.myFunction = None
		self.myFunctionArgs = None
		self.myFunctionKwargs = None

	def runFunction(self, myFunction, myFunctionArgs, myFunctionKwargs, window, shown):
		"""Sets the function to run in the thread object.

		myFunction (str)        - What function will be ran. Can a function object
		myFunctionArgs (list)   - The arguments for 'myFunction'
		myFunctionKwargs (dict) - The keyword arguments for 'myFunction'
		window (wxFrame)        - The window that called this function
		shown (bool)            - If True: The function will only run if the window is being shown. It will wait for the window to first be shown to run.
								  If False: The function will run regardless of whether the window is being shown or not
								  #### THIS IS NOT WORKING YET ####

		Example Input: runFunction(longFunction, [1, 2], {label: "Lorem"}, 5, False)
		"""

		#Record given values
		self.shown = shown
		self.window = window
		self.myFunction = myFunction
		self.myFunctionArgs = myFunctionArgs
		self.myFunctionKwargs = myFunctionKwargs
		self.start()

	def run(self):
		"""Runs the thread and then closes it."""

		if (self.shown):
			#Wait until the window is shown to start
			while True:
				#Check if the thread should still run
				if (self.stopEvent.is_set()):
					return

				#Check if the window is shown yet
				if (self.window.showWindowCheck()):
					break

				#Reduce lag
				time.sleep(0.01)

		#Has both args and kwargs
		if ((self.myFunctionKwargs != None) and (self.myFunctionArgs != None)):
			self.myFunction(*self.myFunctionArgs, **self.myFunctionKwargs)

		#Has args, but not kwargs
		elif (self.myFunctionArgs != None):
			self.myFunction(*self.myFunctionArgs)

		#Has kwargs, but not args
		elif (self.myFunctionKwargs != None):
			self.myFunction(**self.myFunctionKwargs)

		#Has neither args nor kwargs
		else:
			self.myFunction()

	def stop(self):
		"""Stops the running thread."""

		self.stopEvent.set()

#Utility Classes
class Utilities_Base():
	def __init__(self):
		"""Utility functions that everyone gets."""

		pass

	def __repr__(self):
		representation = f"{type(self).__name__}(id = {id(self)})"
		return representation

	def __str__(self):
		output = f"{type(self).__name__}()\n-- id: {id(self)}\n"
		if (hasattr(self, "parent") and (self.parent != None)):
			output += f"-- Parent: {self.parent.__repr__()}\n"
		if (hasattr(self, "root") and (self.root != None)):
			output += f"-- Root: {self.root.__repr__()}\n"
		return output

	def __len__(self):
		return len(self[:])

	def __contains__(self, key):
		return self._get(key, returnExists = True)

	def __iter__(self):
		return Iterator(self.childCatalogue)

	def __getitem__(self, key):
		return self._get(key)

	def __setitem__(self, key, value):
		self.childCatalogue[key] = value

	def __delitem__(self, key):
		del self.childCatalogue[key]

	def __enter__(self):			
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if (traceback != None):
			print(exc_type, exc_value)
			return False

	def _get(self, itemLabel = None, returnExists = False, addNew = True):
		"""Searches the label catalogue for the requested object.

		itemLabel (any) - What the object is labled as in the catalogue
			- If slice: objects will be returned from between the given spots 
			- If None: Will return all that would be in an unbound slice
		addNew (bool)   - Determines what happens if the requested child does not exists
			- If True: Creates a new child
			- If False: Throws an error

		Example Input: _get()
		Example Input: _get(0)
		Example Input: _get(slice(None, None, None))
		Example Input: _get(slice(2, 7, None))
		"""

		#Account for retrieving all nested
		if (itemLabel == None):
			itemLabel = slice(None, None, None)

		#Account for indexing
		if (isinstance(itemLabel, slice)):
			if (itemLabel.step != None):
				raise FutureWarning(f"Add slice steps to _get() for indexing {self.__repr__()}")
			
			elif ((itemLabel.start != None) and (itemLabel.start not in self.childCatalogue)):
				errorMessage = f"There is no item labled {itemLabel.start} in the row catalogue for {self.__repr__()}"
				raise KeyError(errorMessage)
			
			elif ((itemLabel.stop != None) and (itemLabel.stop not in self.childCatalogue)):
				errorMessage = f"There is no item labled {itemLabel.stop} in the row catalogue for {self.__repr__()}"
				raise KeyError(errorMessage)

			handleList = []
			begin = False
			for item in sorted(self.childCatalogue.keys()):
				#Allow for slicing with non-integers
				if ((not begin) and ((itemLabel.start == None) or (self.childCatalogue[item].label == itemLabel.start))):
					begin = True
				elif ((itemLabel.stop != None) and (self.childCatalogue[item].label == itemLabel.stop)):
					break

				#Slice catalogue via creation date
				if (begin):
					handleList.append(self.childCatalogue[item])
			answer = handleList

		elif (itemLabel not in self.childCatalogue):
			answer = None
		else:
			answer = self.childCatalogue[itemLabel]

		if (returnExists):
			return answer != None

		if (answer != None):
			if (isinstance(answer, (list, tuple, range))):
				if (len(answer) == 1):
					answer = answer[0]
			return answer

		if (addNew):
			return self.add(itemLabel)
		else:
			errorMessage = f"There is no item labled {itemLabel} in the data catalogue for {self.__repr__()}"
			raise KeyError(errorMessage)

	#Background Processes
	def passFunction(self, myFunction, myFunctionArgs = None, myFunctionKwargs = None, thread = None):
		"""Passes a function from one thread to another. Used to pass the function
		If a thread object is not given it will pass from the current thread to the main thread.
		"""

		#Get current thread
		myThread = threading.current_thread()
		mainThread = threading.main_thread()

		#How this function will be passed
		if (thread != None):
			pass

		else:
			if (myThread != mainThread):
				self.controller.threadQueue.from_dummy_thread(myFunction, myFunctionArgs, myFunctionKwargs)

			else:
				warnings.warn(f"Cannot pass from the main thread to the main thread for {self.__repr__()}", Warning, stacklevel = 2)

	def recieveFunction(self, blocking = True, printEmpty = False):
		"""Passes a function from one thread to another. Used to recieve the function.
		If a thread object is not given it will pass from the current thread to the main thread.
		"""

		self.controller.threadQueue.from_main_thread(blocking = blocking, printEmpty = printEmpty)

	def backgroundRun(self, myFunction, myFunctionArgs = None, myFunctionKwargs = None, shown = False, makeThread = True):
		"""Runs a function in the background in a way that it does not lock up the GUI.
		Meant for functions that take a long time to run.
		If makeThread is true, the new thread object will be returned to the user.

		myFunction (str)       - The function that will be ran when the event occurs
		myFunctionArgs (any)   - Any input arguments for myFunction. A list of multiple functions can be given
		myFunctionKwargs (any) - Any input keyword arguments for myFunction. A list of variables for each function can be given. The index of the variables must be the same as the index for the functions
		shown (bool)           - Determines when to run the function
			- If True: The function will only run if the window is being shown. If the window is not shown, it will terminate the function. It will wait for the window to first be shown to run
			- If False: The function will run regardless of whether the window is being shown or not
		makeThread (bool)      - Determines if this function runs on a different thread
			- If True: A new thread will be created to run the function
			- If False: The function will only run while the GUI is idle. Note: This can cause lag. Use this for operations that must be in the main thread.

		Example Input: backgroundRun(self.startupFunction)
		Example Input: backgroundRun(self.startupFunction, shown = True)
		"""

		#Skip empty functions
		if (myFunction != None):
			myFunctionList, myFunctionArgsList, myFunctionKwargsList = self.formatFunctionInputList(myFunction, myFunctionArgs, myFunctionKwargs)

			#Run each function
			for i, myFunction in enumerate(myFunctionList):

				#Skip empty functions
				if (myFunction != None):
					myFunctionEvaluated, myFunctionArgs, myFunctionKwargs = self.formatFunctionInput(i, myFunctionList, myFunctionArgsList, myFunctionKwargsList)

					#Determine how to run the function
					if (makeThread):
						#Create parallel thread
						thread = MyThread(daemon = True)
						thread.runFunction(myFunctionEvaluated, myFunctionArgs, myFunctionKwargs, self, shown)
						return thread
					else:
						#Add to the idling queue
						if (self.idleQueue != None):
							self.idleQueue.append([myFunctionEvaluated, myFunctionArgs, myFunctionKwargs, shown])
						else:
							warnings.warn(f"The window {self} was given it's own idle function by the user for {self.__repr__()}", Warning, stacklevel = 2)
				else:
					warnings.warn(f"function {i} in myFunctionList == None for backgroundRun() for {self.__repr__()}", Warning, stacklevel = 2)
		else:
			warnings.warn(f"myFunction == None for backgroundRun() for {self.__repr__()}", Warning, stacklevel = 2)

		return None

	def formatFunctionInputList(self, myFunctionList, myFunctionArgsList, myFunctionKwargsList):
		"""Formats the args and kwargs for various internal functions."""

		#Ensure that multiple function capability is given
		##Functions
		if (myFunctionList != None):
			#Compensate for the user not making it a list
			if (type(myFunctionList) != list):
				if (type(myFunctionList) == tuple):
					myFunctionList = list(myFunctionList)
				else:
					myFunctionList = [myFunctionList]

			#Fix list order so it is more intuitive
			if (len(myFunctionList) > 1):
				myFunctionList.reverse()

		##args
		if (myFunctionArgsList != None):
			#Compensate for the user not making it a list
			if (type(myFunctionArgsList) != list):
				if (type(myFunctionArgsList) == tuple):
					myFunctionArgsList = list(myFunctionArgsList)
				else:
					myFunctionArgsList = [myFunctionArgsList]

			#Fix list order so it is more intuitive
			if (len(myFunctionList) > 1):
				myFunctionArgsList.reverse()

			if (len(myFunctionList) == 1):
				myFunctionArgsList = [myFunctionArgsList]

		##kwargs
		if (myFunctionKwargsList != None):
			#Compensate for the user not making it a list
			if (type(myFunctionKwargsList) != list):
				if (type(myFunctionKwargsList) == tuple):
					myFunctionKwargsList = list(myFunctionKwargsList)
				else:
					myFunctionKwargsList = [myFunctionKwargsList]

			#Fix list order so it is more intuitive
			if (len(myFunctionList) > 1):
				myFunctionKwargsList.reverse()

		return myFunctionList, myFunctionArgsList, myFunctionKwargsList

	def formatFunctionInput(self, i, myFunctionList, myFunctionArgsList, myFunctionKwargsList):
		"""Formats the args and kwargs for various internal functions."""

		myFunction = myFunctionList[i]

		#Skip empty functions
		if (myFunction != None):
			#Use the correct args and kwargs
			if (myFunctionArgsList != None):
				myFunctionArgs = myFunctionArgsList[i]
			else:
				myFunctionArgs = myFunctionArgsList

			if (myFunctionKwargsList != None):
				myFunctionKwargs = myFunctionKwargsList[i]
				
			else:
				myFunctionKwargs = myFunctionKwargsList

			#Check for User-defined function
			if (type(myFunction) != str):
				#The address is already given
				myFunctionEvaluated = myFunction
			else:
				#Get the address of myFunction
				myFunctionEvaluated = eval(myFunction, {'__builtins__': None}, {})

			#Ensure the *args and **kwargs are formatted correctly 
			if (myFunctionArgs != None):
				#Check for single argument cases
				if ((type(myFunctionArgs) != list)):
					#The user passed one argument that was not a list
					myFunctionArgs = [myFunctionArgs]
				# else:
				#   if (len(myFunctionArgs) == 1):
				#       #The user passed one argument that is a list
				#       myFunctionArgs = [myFunctionArgs]

			#Check for user error
			if ((type(myFunctionKwargs) != dict) and (myFunctionKwargs != None)):
				errorMessage = f"myFunctionKwargs must be a dictionary for function {myFunctionEvaluated.__repr__()}"
				raise ValueError(errorMessage)

		return myFunctionEvaluated, myFunctionArgs, myFunctionKwargs

	def getClosest(myList, number, returnLower = True, autoSort = False):
		"""Returns the closest number in 'myList' to 'number'
		Assumes myList is sorted.
		Modified Code from: Lauritz V. Thaulow on https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value

		myList (list) - The list to look through
		number (int)  - The number to search with
		returnLower (bool) - Determines what happens if 'number' is equadistant from the left and right bound.
			- If True: Returns the left bound
			- If False: Returns the right bound
		autoSort (bool) - Determines if the list should be sorted before checking
			- If True: Ensures the list is sorted
			- If False: Assumes the list is sorted already

		Example Input: getClosest([7, 15, 25, 30], 20))
		"""

		if (autoSort):
			myList = sorted(myList)

		position = bisect.bisect_left(myList, number)
		if (position == 0):
			answer = myList[0]

		elif (position == len(myList)):
			answer = myList[-1]

		else:
			before = myList[position - 1]
			after = myList[position]

			if (after - number < number - before):
				answer = after
			elif (returnLower):
				answer = before
			else:
				answer = after

		return answer

class Utilities_Container(Utilities_Base):
	def __init__(self, parent):
		"""Utility functions that only container classes get."""

		#Internal Variables
		if (not hasattr(self, "parent")): self.parent = parent
		if (not hasattr(self, "root")): self.root = self.parent
		
		self.childCatalogue = {}

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

		Example Input: add()
		"""

		child = self.Child(self, label)
		return child

	def remove(self, child = None):
		"""Removes a child.

		child (str) - Which child to remove. Can be a children_class handle
			- If None: Will select the current child

		Example Input: remove()
		Example Input: remove(0)
		"""

		if (child == None):
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

		if (child == None):
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
		if (self.label == None):
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

		if ((start == None) or (end == None)):
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

			if (self.device != None):
				warnings.warn(f"Socket already opened", Warning, stacklevel = 2)

			#Account for the socket having been closed
			# if (self.device == None):
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

			if (self.device == None):
				warnings.warn(f"Socket already closed", Warning, stacklevel = 2)
				return

			if (now != None):
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
					if (self.recieveStop or (self.device == None)):# or ((len(self.dataBlock) > 0) and (self.dataBlock[-1] == None))):
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

			if ((len(self.dataBlock) > 0) and (self.dataBlock[-1] == None)):
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
				warnings.warn(f"There is no client {clientIp} for this server", Warning, stacklevel = 2)
			else:
				client = self.clientDict[clientIp]["device"]
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
			if (timeout != None):
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

			if (self.device == None):
				return True
			return False

class ComPort(Utilities_Container):
	"""A controller for a ComPort connection.
	
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

	def getAll(self):
		"""Returns all connected com ports.
		Modified code from Matt Williams on http://stackoverflow.com/questions/1205383/listing-serial-com-ports-on-windows.

		Example Input: getAll()
		"""

		valueList = [item.device for item in serial.tools.list_ports.comports()]

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
			self.port         = None                #The device name
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

			if (value != None):
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
						warnings.warn(f"There is no parity {value}", Warning, stacklevel = 2)
						return False

				else:
					warnings.warn(f"There is no parity {value}", Warning, stacklevel = 2)
					return False

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
				warnings.warn(f"There is no stop bit {value} for {self.__repr__()}", Warning, stacklevel = 2)

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

			port (str) - If Provided, opens this port instead of the port in memory
			autoEmpty (bool) - Determines if the comPort is automatically flushed after opening

			Example Input: open()
			Example Input: open("COM2")
			Example Input: open(autoEmpty = False)
			"""

			#Configure port options
			if (port != None):
				self.device.port     = port
			else:
				self.device.port     = self.port

			self.device.baudrate     = self.baudRate
			self.device.bytesize     = self.byteSize
			self.device.parity       = self.parity
			self.device.stopbits     = self.stopBits
			self.device.xonxoff      = self.flowControl
			self.device.rtscts       = self.rtsCts
			self.device.dsrdtr       = self.dsrDtr

			if (self.timeoutRead == None):
				self.device.timeout = None
			else:
				self.device.timeout = self.timeoutRead / 1000

			if (self.timeoutWrite == None):
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

			message (str) - The message that will be sent to the listener
							If None: The internally stored message will be used.

			Example Input: send()
			Example Input: send("Lorem ipsum")
			"""

			if (message == None):
				message = self.message

			if (message == None):
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
			self.device.write(message)

		def read(self, length = None, end = None, decode = True, lines = 1, reply = None):
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

			if (reply != None):
				if (not isinstance(reply, bytes)):
					reply = reply.encode("utf-8")

			if (end == None):
				if (length == None):
					length = 1
				message = self.device.read(length)
			elif (end == "\n"):
				if (lines <= 1):
					if (length == None):
						length = -1
					message = self.device.readline(length)
				else:
					message = self.device.readlines(lines)
			else:
				message = b""

				if (not isinstance(end, bytes)):
					end = end.encode("utf-8")
				if (length == None):
					length = 1

				linesRead = 0
				while True:
					while True:
						if (not self.isOpen()):
							return

						value = self.device.read(length)
						message += value
						print("@1", message)
						if (end in value):
							linesRead += 1
							break
					
					if (linesRead >= lines):
						break

			if (reply != None):
				self.device.write(reply)

			if (decode):
				message = message.decode("utf-8")

			return message

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

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self.device = None
			self.image = None
			self.type = "code123"

			#Barcode Attributes
			self.size = None
			self.pixelSize = None
			self.borderSize = None
			self.correction = None
			self.color_foreground = None
			self.color_background = None
			self.qrcode_correctionCatalogue = {7: qrcode.constants.ERROR_CORRECT_L, 15: qrcode.constants.ERROR_CORRECT_M, 25: qrcode.constants.ERROR_CORRECT_Q, 30: qrcode.constants.ERROR_CORRECT_H}

		def getType(self, formatted = False):
			"""Returns the barcode type."""

			return self.type

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

			if (percent not in [7, 15, 25, 30]):
				percent = self.getClosest([7, 15, 25, 30], percent)

			self.correction = self.qrcode_correctionCatalogue[percent]

		def setSize(self, number = None):
			"""Must be between 1 and 40.

			Example Input: setSize()
			Example Input: setSize(5)
			"""

			if (number not in [None, range(1, 40)]):
				number = self.getClosest(range(1, 40), number)

			self.size = number

		def setPixelSize(self, number = None):
			"""How large the boxes in the QR code are.

			Example Input: setPixelSize()
			Example Input: setPixelSize(5)
			"""

			if (number == None):
				number = 10

			self.pixelSize = number

		def setBorderSize(self, number = None):
			"""How wide the border is.

			Example Input: setBorderSize()
			Example Input: setBorderSize(5)
			"""

			if (number == None):
				number = 4

			self.borderSize = number

		def setColor(self, foreground = None, background = None):
			"""What color the barcode will be.

			foreground (str) - Color of the foreground
			background (str) - Color of the background

			Example Input: setColor()
			Example Input: setColor("red", "blue")
			"""

			if (foreground == None):
				foreground = "black"
			if (background == None):
				background = "white"

			self.color_foreground = foreground
			self.color_background = background

		def create(self, text, codeType = None, filePath = None):
			"""Returns a PIL image of the barcode for the user or saves it somewhere as an image.
			Use: https://ourcodeworld.com/articles/read/554/how-to-create-a-qr-code-image-or-svg-in-python

			text (str)     - What the barcode will say
			codeType (str) - What type of barcode will be made
				- If None: Will use self.type

			Example Input: create(1234567890)
			Example Input: create(1234567890, "code128")
			"""

			if (codeType not in [None, self.type]):
				self.setType(codeType)

			#Create barcode
			if (self.type == "qr"):
				if (self.correction == None):
					self.correction = qrcode.constants.ERROR_CORRECT_M
				if (self.pixelSize == None):
					self.pixelSize = 10
				if (self.borderSize == None):
					self.borderSize = 4
				if (self.color_foreground == None):
					self.color_foreground = "black"
				if (self.color_background == None):
					self.color_background = "white"

				self.device = qrcode.QRCode(version = self.size,
					error_correction = self.correction,
					box_size = self.pixelSize, 
					border = self.borderSize,
					image_factory = None,
					mask_pattern = None)

				self.device.add_data(f"{text}")
				self.device.make(fit = True)
				self.image = self.device.make_image(fill_color = self.color_foreground, back_color = self.color_background)

			else:
				self.device = barcode.get(self.type, f"{text}", writer = barcode.writer.ImageWriter())
				self.image = self.device.render(writer_options = None)

				if (filePath != None):
					self.device.save(filePath)

			return self.image

		def show(self):
			"""Shows the barcode to the user."""

			self.image.show()

		def get(self):
			"""Returns the barcode."""

			return self.image

class Communication():
	"""Helps the user to communicate with other devices.

	CURRENTLY SUPPORTED METHODS
		- COM Port
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

		self.ethernet = Ethernet(self)
		self.barcode = Barcode(self)
		self.comPort = ComPort(self)
		self.usb = USB(self)

	def __str__(self):
		"""Gives diagnostic information on the GUI when it is printed out."""

		output = f"Communication()\n-- id: {id(self)}\n"

		output += f"-- Ethernets: {len(self.ethernet)}\n"
		output += f"-- COM Ports: {len(self.comPort)}\n"
		output += f"-- USB Ports: {len(self.usb)}\n"
		output += f"-- Barcodes: {len(self.barcode)}\n"

		return output

	def __repr__(self):
		representation = f"Communication(id = {id(self)})"
		return representation

	def getAll(self):
		"""Returns all available communication types.

		Example Input: getAll()
		"""

		return [self.ethernet, self.comPort, self.usb, self.barcode]

if __name__ == '__main__':
	com = build()
