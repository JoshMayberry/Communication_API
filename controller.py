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
import MyUtilities.threadManager

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


	# import time
	# import subprocess
	# subprocess.Popen(["py", "maintenance.py"]) #https://docs.python.org/2/library/os.html#os.startfile
	# print("@1.2")
	# time.sleep(1)
	# print("@1.3")
	# sys.exit()

	print("Starting")
	getEmail().test()
