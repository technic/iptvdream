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
	NEXT_API = None 
	MODE = MODE_STREAM
	NUMBER_PASS = False

	site = "http://sovok.tv"
	
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
		self.packet_expire = datetime.fromtimestamp(int(reply.find('account').findtext('packet_expire')))	
		
		self.trace("Authorization returned: %s" % urllib.urlencode(cookiesdict))
		self.trace("Packet expire: %s" % self.packet_expire)
		self.SID = True	
	
	#locked_cids = [155, 159, 161, 257, 311]
	#HAS_PIN = True
	#epg_day_edge = (20, 00)
	
	#def getChannelsEpg(self, cids):
		#params = {"cids" : ",".join(map(str, cids))}
		#root = self.getData("/api/xml/epg_current?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
		#for channel in root.find('epg'):
			#cid = int(channel.findtext("cid").encode("utf-8"))
			#e = channel.find("epg")
			#t = int(e.findtext('epg_start').encode("utf-8"))
			#t_start = datetime.fromtimestamp(t)
			#t = int(e.findtext('epg_end').encode("utf-8"))
			#t_end = datetime.fromtimestamp(t)
			#prog = e.findtext('epg_progname').encode('utf-8')
			#self.channels[cid].pushEpg( EpgEntry(prog, t_start, t_end) )