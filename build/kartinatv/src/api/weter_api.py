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

#TODO: GLOBAL: add private! Get values by properties.

			

class WeterAPI(AbstractAPI):
	
	iProvider = "wetertv"
	NUMBER_PASS = True
	
	site = "http://weter.team-dobrogea.ru"
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)

#		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener()
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-2.0')]
	
	def start(self):
		self.authorize()
		
	def authorize(self):
		self.trace("Authorization started")
		self.trace("username = %s" % self.username)

		params = urllib.urlencode({"login" : self.username,
								  "pass" : self.password,
								  "settings" : "all"})
		reply = self.opener.open(self.site+'/api/xml/login?'+params).read()
		print reply
		
		reply = fromstring(reply)
		if reply.find("error"):
			raise APIException(reply.find('error').findtext('message'))
	
		self.sidval = urllib.urlencode({"sid_name": reply.findtext('sid_name'),
		                                "sid": reply.findtext('sid') })
		
		self.packet_expire = datetime.fromtimestamp(int(reply.find('account').findtext('packet_expire')))
		
		#Load settings here, because kartina api is't friendly
		self.settings = []
		sett = reply.find("settings")
		
		self.trace(self.sidval)
		self.trace("Packet expire: %s" % self.packet_expire)
		self.SID = True	
	
	def getData(self, url, name):
		self.SID = False
		
		url = self.site + url
		#if url.endswith('?'):
			#url += self.sidval
		#else:
		url += "&" + self.sidval
		
		#self.trace("Getting %s" % (name))
		self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
		except:
			reply = ""
		print reply
		
		try:
			root = fromstring(reply.replace('&','&amp;') )
		except:
			raise APIException("Failed to parse xml response")
		if root.find('error'):
			err = root.find('error')
			raise APIException(err.find('code').text.encode('utf-8')+" "+err.find('message').text.encode('utf-8'))
		
		self.SID = True
		return root

class Ktv(WeterAPI, AbstractStream):
	
	iName = "WeterTV"
	MODE = MODE_STREAM
	NEXT_API = "KartinaMovies"
	
	locked_cids = [155, 159, 161, 257, 311]
	HAS_PIN = True
	
	def __init__(self, username, password):
		WeterAPI.__init__(self, username, password)
		AbstractStream.__init__(self)
	
	def setChannelsList(self):
	  	root = self.getData("/api/xml/channel_list?", "channels list")
		lst = []
		t_str = root.findtext("servertime").encode("utf-8")
		t_cur = datetime.fromtimestamp(int(t_str))
		setSyncTime(t_cur)
		num = -1
		for group in root.find("groups"):
			title = group.findtext("name").encode("utf-8")
			gnum = int(group.findtext("id"))
			for channel in group.find("channels"):
				num += 1
				name = channel.findtext("name").encode("utf-8")
				id = int(channel.findtext("id").encode("utf-8"))
				archive = channel.findtext("have_archive") or 0
				self.channels[id] = Channel(name, title, num, gnum, archive)
				if channel.findtext("epg_progname") and channel.findtext("epg_end"):
					prog = channel.findtext("epg_progname").encode("utf-8")
					t_str = channel.findtext("epg_start").encode("utf-8")
					t_start = datetime.fromtimestamp(int(t_str))
					t_str = channel.findtext("epg_end").encode("utf-8")
					t_end = datetime.fromtimestamp(int(t_str))
					#print "[KartinaTV] updating epg for cid = ", id
					self.channels[id].epg = EpgEntry(prog, t_start, t_end)
				else:
					#print "[KartinaTV] there is no epg for id=%d on ktv-server" % id
					pass


	def getStreamUrl(self, cid, pin, time = None):
		params = {"cid" : cid}
		if time:
			params["gmt"] = time.strftime("%s")
		params["protect_code"] = pin
		root = self.getData("/api/xml/get_url?"+urllib.urlencode(params), "URL of stream %s" % cid)
		url = root.findtext("url").encode("utf-8").split(' ')[0].replace('http/ts://', 'http://')
		if url == "protected": return self.ACCESS_DENIED
		return url
	
	def getChannelsEpg(self, cids):
		params = {"cids" : ",".join(map(str, cids))}
		root = self.getData("/api/xml/epg_current?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
		for channel in root.find('epg'):
			cid = int(channel.findtext("cid").encode("utf-8"))
			e = channel.find("epg")
			t = int(e.findtext('epg_start').encode("utf-8"))
			t_start = datetime.fromtimestamp(t)
			t = int(e.findtext('epg_end').encode("utf-8"))
			t_end = datetime.fromtimestamp(t)
			prog = e.findtext('epg_progname').encode('utf-8')
			self.channels[cid].pushEpg( EpgEntry(prog, t_start, t_end) )
	
	def getGmtEpg(self, cid, time):
		self.getDayEpg(cid, time)
		self.getDayEpg(cid, time-secTd(24*60*60))

	def getNextGmtEpg(self, cid, time):
		return self.getDayEpg(cid, time)
	
	def getDayEpg(self, cid, date):
		params = {"day" : date.strftime("%d%m%y"),
		          "cid" : cid}
		root = self.getData("/api/xml/epg?"+urllib.urlencode(params), "day EPG for channel %s" % cid)
		epglist = []
		for program in root.find('epg'):
			t = int(program.findtext("ut_start").encode("utf-8"))
			time = datetime.fromtimestamp(t)
			progname = unescapeEntities(program.findtext("progname")).encode("utf-8")
			epglist += [EpgEntry(progname, time, None)]
		self.channels[cid].pushEpgSorted(epglist)

	def getCurrentEpg(self, cid):
		return self.getNextEpg(cid)

	def getNextEpg(self, cid):
		params = {"cid": cid}
		root = self.getData("/api/xml/epg_next?"+urllib.urlencode(params), "EPG next for channel %s" % cid)
		lst = []
		for epg in root.find('epg'):
			t = int(epg.findtext('ts').encode("utf-8"))
			tstart = datetime.fromtimestamp(t)
			title = epg.findtext('progname').encode('utf-8')
			lst += [EpgEntry(title, tstart, None)]
		self.channels[cid].pushEpgSorted(lst)

	def getSettings(self):
		return self.settings
	
	def pushSettings(self, sett):
		for x in sett:
			params = {"var" : x[0],
			          "val" : x[1]}
			self.getData("/api/xml/settings_set?"+urllib.urlencode(params), "setting %s" % x[0])
