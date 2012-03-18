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
from m3u_playlist import M3UReader
from Plugins.Extensions.KartinaTV.utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, APIException
from Plugins.Extensions.KartinaTV.jtvreader import read as jtv_read, current as jtv_current
import os

EPG_ZIP = '/tmp/jtv.zip'
EPG_DIR = EPG_ZIP[:-4]+'/'
urlnew = "http://www.teleguide.info/download/new3/jtv.zip"
urlold = "http://www.teleguide.info/download/old/jtv.zip"

class Ktv(M3UReader, AbstractAPI, AbstractStream):
	
	iName = "dobrogeatv"
	iProvider = "dobrogea"		
	locked_cids = []
	iTitle = "Team-dobrogea"
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		AbstractStream.__init__(self)
		self.groups = {}
		
		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5')]
		
		self.readlines = '';
		self.act_url = urlnew
		self.lastload = syncTime()
		
	def start(self):
		self.authorize()
		self.load_epg()
		pass
	
	def authorize(self):
		print "authorizing"
		params = urllib.urlencode({"login" : self.username,
								   "pass" : self.password})
		try:
			reply = self.opener.open(urllib2.Request('http://tv.team-dobrogea.ru/plugin.php?playlist', params)).readlines()
		except Exception as e:
			raise APIException(e[1])
		self.readlines = reply
					
	def setTimezone(self):
		pass
	
	def getPiconName(self, cid):
		return "%s_%s" % (self.iName, self.channels[cid].name)
	
	def setChannelsList(self):
		lines = self.readlines
		BOM = u'\ufeff'.encode('utf-8')
		if lines[0].find(BOM) > -1:
			print 'remove BOM'
			lines[0] = lines[0][3:]
		self.parse_m3u(lines, self.iTitle)
	
	def getChannelsEpg(self, cids):
		for cid in cids:
			self.getCurrentEpg(cid)
	
	def getCurrentEpg(self, cid):
		f = self.channels[cid].name
		f = f.encode('CP866').replace(' ', '_')
		fname = EPG_DIR + f
		try:
			jtv = jtv_current(fname)
		except IOError as e:
			if e[0] == 2:
				self.trace('epg fail for %s (possible encoding problem)' % self.channels[cid].name)
				return -1
			else:
				raise(e)
		lepg = [EpgEntry(x[1].encode('utf-8'), datetime.utcfromtimestamp(x[0]), None) for x in jtv]
		print jtv
		if datetime.utcfromtimestamp(jtv[0][0]) > syncTime():
			self.act_url = urlold
			self.load_epg()
		self.channels[cid].pushEpgSorted(lepg)
	
	def check_epgdir(self):
		if not os.path.isdir(EPG_DIR):
			self.load_epg()
	
	def load_epg(self):
		try:
			os.mkdir(EPG_DIR)
		except OSError as e:
			if e[0] != 17:
				raise(e)
		self.trace("Loading epg %s" % self.act_url)
		try:
			urllib.urlretrieve(self.act_url, EPG_ZIP)
			self.lastload = syncTime()
		except:
			raise APIException("epg download failed")
		cmd = "unzip -q -o %s -d %s" % (EPG_ZIP, EPG_DIR)
		self.trace(cmd)
		os.system(cmd)
		
	def getDayEpg(self, cid, date):
		f = self.channels[cid].name
		f = f.encode('CP866').replace(' ', '_')
		fname = EPG_DIR + f
		self.trace("epg for cid %s" % cid)
		try:
			jtv = jtv_read(fname)
		except:
			return -1
		lepg = [EpgEntry(x[1].encode('utf-8'), datetime.utcfromtimestamp(x[0]), None) for x in jtv]
		self.channels[cid].pushEpgSorted(lepg)

if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	ktv.start()
	ktv.setChannelsList()
	print ktv.getStreamUrl(0)
	ktv.getChannelsEpg(ktv.channels.keys())
	for x in ktv.channels.keys():
		y = ktv.channels[x]
		print x, y.name, y.group, y.num, y.gid
