import lazyLoad
lazyLoad.load(
	"usb", 
	"email", 
	"socket", 
	"serial", 

	"qrcode", 
	"barcode", 

	"xml", 
	"bisect", 
	"select", 
	"netaddr", 
	"smtplib", 
) 

#Import the controller module as this namespace
from .controller import *
del controller