#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from datetime import datetime
import urllib
from . import tdSec, secTd, setSyncTime, syncTime, EpgEntry, Channel, APIException, jtvreader
import os

EPG_ZIP = '/tmp/jtv.zip'
EPG_DIR = EPG_ZIP[:-4]+'/'
urlnew = "http://www.teleguide.info/download/new3/jtv.zip"
urlold = "http://www.teleguide.info/download/old/jtv.zip"

deltat = 4*60*60 #Moscow time
class JTVEpg:
	
	def __init__(self):
		self.act_url = urlnew
		self.lastload = syncTime()
	
	def getPiconName(self, cid):
		return "%s_%s" % (self.iName, self.channels[cid].name)
	
	def getFname(self, cid):
		f = self.channels[cid].epg_name
		try:
			if isinstance(f, unicode):
				f = f.decode('utf-8')
			f = f.encode('CP866')
			f = EPG_DIR + f
		except (UnicodeDecodeError, UnicodeEncodeError):
			pass
		return f

	
	def getChannelsEpg(self, cids):
		map(self.getCurrentEpg, cids)
	
	def getCurrentEpg(self, cid):
		fname = self.getFname(cid)
		try:
			jtv = jtvreader.current(fname, deltat)
		except IOError as e:
			if e[0] == 2:
#				self.trace('epg fail for %s (possible encoding problem)' % self.channels[cid].epg_name)
				return -1
			else:
				raise(e)
		lepg = [EpgEntry(x[1].encode('utf-8'), datetime.fromtimestamp(x[0]-deltat), None) for x in jtv]
#		print jtv
		if datetime.fromtimestamp(jtv[0][0]-deltat) > syncTime() and self.act_url == urlnew:
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
		fname = self.getFname(cid)
		self.trace("epg for cid %s" % cid)
		try:
			jtv = jtvreader.read(fname)
		except IOError as e:
			if e[0] == 2:
#				self.trace('epg fail for %s (possible encoding problem)' % self.channels[cid].epg_name)
				return -1
			else:
				raise(e)
		lepg = [EpgEntry(x[1].encode('utf-8'), datetime.fromtimestamp(x[0]-deltat), None) for x in jtv]
		self.channels[cid].pushEpgSorted(lepg)
