#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from abstract_api import MODE_STREAM, AbstractAPI, AbstractStream
import cookielib, urllib, urllib2 #TODO: optimize imports
from xml.etree.cElementTree import fromstring
from datetime import datetime
from . import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, unescapeEntities, Timezone, APIException, SettEntry
from kartina_api import Ktv as Kartina

#TODO: GLOBAL: add private! Get values by properties.

class Ktv(Kartina):
	
	iProvider = "sovoktv"
	iName = "SovokTV"
	iTitle = "SovokTV"
	NEXT_API = None 
	MODE = MODE_STREAM
	NUMBER_PASS = False

	site = "http://sovok.tv"
	
	HAS_PIN = True
	locked_cids = [163, 171, 172, 119]
	
	def authorize(self):
		self.trace("Authorization started")
		self.trace("username = %s" % self.username)
		self.cookiejar.clear()
		params = urllib.urlencode({"login" : self.username,
								  "pass" : self.password,
								  "settings" : "all"})
		reply = self.opener.open(self.site+'/api/xml/login?', params).read()
		
		#checking cookies
		cookies = list(self.cookiejar)
		cookiesdict = {}
		hasSSID = False
		deleted = False
		
		reply = fromstring(reply)
		if reply.find("error"):
			raise APIException(reply.find('error').findtext('message'))
		
		for cookie in cookies:
			cookiesdict[cookie.name] = cookie.value
			if (cookie.name.find('SSID') != -1):
				hasSSID = True
			if (cookie.value.find('deleted') != -1):
				deleted = True
		if (not hasSSID):
			raise APIException(self.username+": Authorization of user failed!")
		if (deleted):
			raise APIException(self.username+": Wrong authorization request")

                try:
                        self.packet_expire = datetime.fromtimestamp(int(reply.find('account').findtext('packet_expire')))
                except:
                        self.trace("Could not read packet_expire from reply: %s" % reply)
                        self.packet_expire = 'Unknown'

		self.trace("Authorization returned: %s" % urllib.urlencode(cookiesdict))
		self.trace("Packet expire: %s" % self.packet_expire)
		self.SID = True
	
	def setTimeShift(self, timeShift):
		pass
