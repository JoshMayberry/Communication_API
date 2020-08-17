__version__ = "2.0.0"

#Import standard elements
import re
import os
import sys
import datetime

import io
import wx
import glob
import zipfile
import contextlib
import collections

#Import email modules for sending and viewing emails
import ssl
import imaplib
import smtplib
import xml.etree.cElementTree as xml

import email
from email.mime.base import MIMEBase as email_MIMEBase
from email.mime.text import MIMEText as email_MIMEText
from email.mime.image import MIMEImage as email_MIMEImage
from email.mime.multipart import MIMEMultipart as email_MIMEMultipart

import MyUtilities.wxPython
# import API_Database as Database

class ConnectionAlreadyOpenError(Exception):
	pass

class SearchError(Exception):
	pass

class EmailServer():
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

	def __init__(self):
		self.current_address = None

	@contextlib.contextmanager
	def openRead(self, address, password, host, port = None, encrypt = True, **kwargs):
		"""Opens a connection to an email for reading

		address (str) - A valid email address to send from
		password (str) - The password for 'address'

		host (str) - What email server is being used
			- If None: Will use gmail
		port (int) - What port to use
			- If None: 587 for sending, and 143 for recieving

		Example Input: openRead("lorem.ipsum@example.com", "LoremIpsum")
		"""

		if (self.current_address is not None):
			raise ConnectionAlreadyOpenError()

		self.current_address = address
		self.current_readMode = True

		with imaplib.IMAP4(host = host or "imap4.gmail.com", port = int(port or 143)) as serverHandle:
			if (encrypt):
				serverHandle.starttls()

			serverHandle.login(address, password)
			serverHandle.select("Inbox")

			yield serverHandle

		self.current_address = None
		self.current_sendMode = None

	@contextlib.contextmanager
	def openWrite(self, address, password, host, port = None, encrypt = True, **kwargs):
		"""Opens a connection to an email for writing.

		address (str) - A valid email address to send from
		password (str) - The password for 'address'

		host (str) - What email server is being used
			- If None: Will use gmail
		port (int) - What port to use
			- If None: 587 for sending, and 143 for recieving

		Example Input: openWrite("lorem.ipsum@example.com", "LoremIpsum")
		"""

		if (self.current_address is not None):
			raise ConnectionAlreadyOpenError()

		self.current_address = address
		self.current_readMode = False

		try:
			with smtplib.SMTP(host = host or "smtp.gmail.com", port = int(port or 587)) as serverHandle:
				if (encrypt):
					serverHandle.starttls()

				serverHandle.login(address, password)

				yield serverHandle

		#Use: https://www.alibabacloud.com/help/doc-detail/29453.htm
		except smtplib.SMTPConnectError as error:
			print('Mail delivery fails, the connection fails:', error.smtp_code, error.smtp_error)
			raise error

		except smtplib.SMTPAuthenticationError as error:
			print('Mail delivery failure, certification error:', error.smtp_code, error.smtp_error)
			raise error

		except smtplib.SMTPSenderRefused as error:
			print('Send mail failed, the sender is rejected:', error.smtp_code, error.smtp_error)
			raise error

		except smtplib.SMTPRecipientsRefused as error:
			print('Send mail failed, the recipient was rejected:', error.smtp_code, error.smtp_error)
			raise error

		except smtplib.SMTPDataError as error:
			print('Send mail failed, data reception to refuse:', error.smtp_code, error.smtp_error)
			raise error

		except smtplib.SMTPException as error:
			print('Send mail failed, ', error.message)
			raise error

		except Exception as error:
			print('Send mail abnormal, ', str(error))
			raise error

		self.current_address = None
		self.current_sendMode = None

	def email_toDict(self, emailHandle, include_plainBody = True, include_htmlBody = False, include_csv = False, include_attachment = False):
		"""Converts an email into a dictionary.
		Uses include_* variables to control what is returned in the catalogue.

		Example Input: email_toDict(emailHandle)
		Example Input: email_toDict(emailHandle, include_plainBody = False, include_csv = True)
		"""

		catalogue_contentType = {
			"text/plain": (include_plainBody, "plain_body"),
			"text/html": (include_htmlBody, "html_body"),
			"text/csv": (include_csv, "csv"),
		}

		catalogue = collections.defaultdict(list)
		catalogue["subject"] = emailHandle["subject"]
		catalogue["from"] = emailHandle["from"]
		catalogue["date"] = datetime.datetime.strptime(emailHandle["date"], "%a, %d %b %Y %H:%M:%S %z (%Z)")

		for part in emailHandle.walk():
			content_type = part.get_content_type()

			if (content_type in catalogue_contentType):
				include, key = catalogue_contentType[content_type]
				if (not include):
					continue
				catalogue[key].append(part.get_payload())

			elif(content_type.startswith("multipart")):
				continue

			else:
				raise UnknownContentTypeError(content_type)

			if (not include_attachment):
				continue

			fileName = part.get_filename()
			if (fileName):
				raise NotImplementedError()
				# filePath = os.path.join("/Users/sanketdoshi/python/", fileName)
				# if not os.path.isfile(filePath) :
				# 	fp = open(filePath, "wb")
				# 	fp.write(part.get_payload(decode=True))
				# 	fp.close()
				# catalogue["attachment"].append(filePath)

		return dict(catalogue)

	def search(self, serverHandle, keyword = None, folderName = None, fromFilter = None, **kwargs):
		"""Searches the email server for teh given keyword.

		keyword (str) - What to search for
			~ If None: returns all contents of *folderName*

		folderName (str) - Which folder to search in
			~ If None: Searches in the current folder

		Example Input: search(serverHandle)
		Example Input: search(serverHandle, "Lorem")
		"""

		if (folderName):
			serverHandle.select(folderName)

		status_search, id_list = serverHandle.search(keyword, "ALL")
		if (status_search != "OK"):
			raise SearchError(status_search)

		#Look at each mail by id
		for mail_id in id_list[0].split():
			status_fetch, data = serverHandle.fetch(mail_id, "(RFC822)" )
			if (status_fetch != "OK"):
				raise SearchError(status_search)

			#Format Email
			raw_email = data[0][1]
			raw_email_string = raw_email.decode("utf-8")
			emailHandle = email.message_from_string(raw_email_string)

			#Apply Filter
			if (fromFilter and (emailHandle["from"] not in fromFilter)):
				continue

			yield emailHandle

	@contextlib.contextmanager
	def sendEmail(self, serverHandle, address, subject = None, *, testing_doNotSend = False, testing_printEmail = False, **kwargs):
		messageHandle = self.EmailMessage(self)

		yield messageHandle

		message = messageHandle.build(address = address, subject = subject)

		if (testing_doNotSend):
			print(f"An email would have been sent to {address} from {message['From']}")
		else:
			serverHandle.sendmail(message["From"], address, message.as_string())

		if (testing_printEmail):
			print(message.as_string())

	def test_search(self):
		with self.openRead(address = "omnitraks@decaturmold.com", password = "Fu3lu$@g3", host = "194.2.1.1") as serverHandle:
			for emailHandle in self.search(serverHandle):
				print(self.email_toDict(emailHandle))
				break

	def test_send(self):
		with self.openWrite(address = "omnitraks@decaturmold.com", password = "Fu3lu$@g3", host = "194.2.1.1") as serverHandle:
		# with self.openWrite(address = "dmtebi@decaturmold.com", password = "N0tchJ0hn$0n", host = "194.2.1.1") as serverHandle:
			with self.sendEmail(serverHandle, address = "josh.mayberry@decaturmold.com") as messageHandle:
				messageHandle.body.append("Test")
				messageHandle.body.append("123")
				messageHandle.body.append("Testing")

	class EmailMessage():
		def __init__(self, parent):
			self.parent = parent

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

		def build(self, address, subject = None):
			"""Finishes building the emailand links it to the provided address.

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
						email.encoders.encode_base64(section)
						section.add_header('Content-Disposition', 'attachment',  filename = f"{zip_label}.zip")
						yield section

			########################################

			message = email_MIMEMultipart()
			message["From"] = self.parent.current_address
			message["To"] = address

			if (subject):
				message["Subject"] = subject

			for item in self.body.yieldMime():
				message.attach(item)

			for item in yieldAttachments():
				message.attach(item)

			for item in yieldZip():
				message.attach(item)

			return message

		class Body():
			"""Holds the body of the email to send."""

			def __init__(self, parent):
				self.parent = parent

				self.plainText = ""
				self.attachBody = True
				self.message_root = xml.Element("html")
				self.message_head = xml.SubElement(self.message_root, "head")
				self.message_body = xml.SubElement(self.message_root, "body")

			def addStyle(self):
				"""Adds a css styling section to the html.

				Example Input: addStyle()
				"""

				return self.Style(self)

			def appendXml(self, tag, text = None, attributes = None, prePlainText = None, postPlainText = None, returnWrapper = True, *, xmlHandle = None):
				"""Appends the given xml information to the email.

				Example Input: appendXml("p", "Lorem Ipsum")
				Example Input: appendXml("a", "dolor", attributes = {"href": "www.example.com"})
				Example Input: appendXml("h2", header, prePlainText = "**", postPlainText = "**")
				"""

				if (xmlHandle is None):
					xmlHandle = self.message_body

				element = xml.SubElement(xmlHandle, tag, attrib = attributes or {})
				
				if (text):
					element.text = text
					self.plainText += f"{prePlainText or ''}{text}{postPlainText or ''}\n"

				if (returnWrapper):
					return self.Element(self, element)

				return element

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
					self.appendXml("h2", header, prePlainText = "\t**", postPlainText = "**", returnWrapper = False)

				self.appendXml("p", text, returnWrapper = False)

				if (link):
					appendXml("a", link[1], attributes = {"href": link[0]}, postPlainText = f": {link[0]}", returnWrapper = False)

			def plain(self):
				"""Returns the body of the message as plain text.

				Example Input: plain()
				"""

				return self.plainText

			def html(self):
				"""Returns the MIME handle to attach to the email.

				Example Input: html()
				"""

				return xml.tostring(self.message_root, method = "html").decode()

			def yieldMime(self, html = True):
				"""Returns the MIME handle to attach to the email.

				Example Input: yieldMime()
				"""

				if (html):
					yield email_MIMEText(self.html(), "html")
				else:
					yield email_MIMEText(self.plain(), "plain")

			class Element():
				"""An element that is attached to the email body."""

				def __init__(self, body, xmlHandle):
					self.body = body
					self.xmlHandle = xmlHandle

				def __enter__(self):
					return self

				def __exit__(self, exc_type, exc_value, traceback):
					if (traceback is not None):
						return False

				def appendXml(self, *args, **kwargs):
					return self.body.appendXml(*args, **{**kwargs, "xmlHandle": self.xmlHandle})

				def appendRawText(self, text):
					self.xmlHandle.text += f"{text}"

			class Style(Element):
				"""A style section for css styling."""

				def __init__(self, body):
					EmailServer.EmailMessage.Body.Element.__init__(self, body, xml.SubElement(body.message_head, "style"))
					
					self.xmlHandle.text = ""

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

				if (isinstance(source, (io.StringIO, io.TextIOWrapper))):
					self.fileLike_routine(source, *args, **kwargs)
					return

				# if (isinstance(source, Database.Base)):
				# 	if (isinstance(source, Database.Configuration)):
				# 		self.database_routine(source, *args, override_readOnly = True, **kwargs)
				# 		return

				# 	if (isinstance(source, Database.Config_Base)):
				# 		self.database_routine(source, *args, ifDirty = False, removeDirty = False, applyOverride = False, **kwargs)
				# 		return

				# 	if (isinstance(source, Database.Database)):
				# 		_defaultName = re.split("\.", os.path.basename(source.baseFileName))[0]
				# 		self.database_routine(source, *args, _defaultName = f"{_defaultName}.sql", **kwargs)
				# 		return

				raise NotImplementedError(type(source))

			def file_routine(self, source, name = None):
				"""Sets up the attachment to add a file.

				source (str) - Where the file to attach is located on disk

				Example Use: attach("example.txt")
				Example Use: attach("example.*")
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
						email.encoders.encode_base64(section)
						
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

				Example Use: attach(bitmap)
				Example Use: attach(bitmap, imageType = "png")
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

			def fileLike_routine(self, source, name = None, fileType = "txt"):
				"""Sets up the attachment for a file-like object.
				See: https://stackoverflow.com/questions/30043215/attach-file-like-object-to-email-python-3/30043343#30043343

				Example Use: attach(fileHandle)
				"""

				def _baseRoutine():
					nonlocal self, payload, name, fileType

					yield payload, f"{name or 'file'}.{fileType}"

				def _mimeRoutine():
					nonlocal self, fileType

					for _payload, _name in _baseRoutine():
						section = email_MIMEBase("application", "octet-stream")
						section.set_payload(_payload)
						email.encoders.encode_base64(section)
						
						section.add_header("Content-Disposition", f"attachment; filename = {_name}")
						yield section

				#################################################

				payload = source.getvalue()

				self.yieldPayload = _baseRoutine
				self.yieldMime = _mimeRoutine

			def database_routine(self, source, name = None, *, _defaultName = None, **kwargs):
				"""Sets up the attachment to add a json, yaml, configuration, or sql database handle.

				Example Input: database_routine()
				"""

				raise NotImplementedError("Things have changed in the database module sense this was last set up")

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

@contextlib.contextmanager
def sendEmail(address_from, address_to, *, emailServer = None, **kwargs):
	"""Shortcut for sending an email.

	Example Input: sendEmail(address_from = "lorem.ipsum@example.com", address_to = "dolor.sit@example.com", password = "LoremIpsum")
	"""

	if (emailServer is None):
		emailServer = EmailServer()

	with emailServer.openWrite(address = address_from, **kwargs) as serverHandle:
		with emailServer.sendEmail(serverHandle, address = address_to, **kwargs) as messageHandle:
			yield messageHandle

if (__name__ == "__main__"):
	controller = EmailServer()
	controller.test_send()