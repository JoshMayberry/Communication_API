__version__ = "2.0.0"

#Import standard elements
import sys
import warnings

#Import barcode modules for drawing and decoding barcodes
import qrcode
import barcode
import PIL

import API_Com.utilities

#Required Modules
##py -m pip install
	# qrcode
	# pyBarcode
	# pillow

class Barcode(API_Com.utilities.Utilities_Container):
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
		API_Com.utilities.Utilities_Container.__init__(self, parent)

	def getAll(self):
		"""Returns all barcoder formats.

		Example Input: getAll()
		"""

		valueList = sorted(barcode.PROVIDED_BARCODES + ["qr"])

		return valueList

	class Child(API_Com.utilities.Utilities_Child):
		"""A COM Port connection."""

		def __init__(self, parent, label, size = None, pixelSize = None, borderSize = None, 
			correction = None, color_foreground = None, color_background = None):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			API_Com.utilities.Utilities_Child.__init__(self, parent, label)
		
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