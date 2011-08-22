#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

DEBUG = True
MODE_STREAM = 0
MODE_VIDEOS = 1

class AbstractAPI:
	
	MODE = MODE_STREAM
	iProvider = "free"
	iName = "example"
	NEXT_API = None 
	NUMBER_PASS = False
	
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.SID = False
		self.packet_expire = None
	
	def start(self):
		pass
	
	def trace(self, msg):
		if DEBUG:
			print "[KartinaTV] %s: %s" % (self.iName, msg)
