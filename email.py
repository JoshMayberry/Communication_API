__version__ = "2.0.0"

#Import standard elements
import re
import os
import sys

import io
import wx
import glob
import zipfile
import collections

#Import email modules for sending and viewing emails
import smtplib
import xml.etree.cElementTree as xml
from email import encoders as email_encoders
from email.mime.base import MIMEBase as email_MIMEBase
from email.mime.text import MIMEText as email_MIMEText
from email.mime.image import MIMEImage as email_MIMEImage
from email.mime.multipart import MIMEMultipart as email_MIMEMultipart


import API_Com.utilities
import API_Database as Database

#Required Modules
##py -m pip install
	# wxPython

class Email(API_Com.utilities.Utilities_Container):
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
		API_Com.utilities.Utilities_Container.__init__(self, parent)

	class Child(API_Com.utilities.Utilities_Child):
		"""An email conection."""

		def __init__(self, parent, label):
			"""Defines the internal variables needed to run."""

			#Initialize Inherited Modules
			API_Com.utilities.Utilities_Child.__init__(self, parent, label)
		
			#Internal Variables
			self._from = None
			self._password = None

			self.current_config = None

		def test(self):
			self.open("dmtebi@decaturmold.com", "N0tchJ0hn$0n", "194.2.1.1", 587)

			self.body.appendHtml("<p>Test <b>123</b> Testing </p>")
			self.send("josh.mayberry@decaturmold.com")

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