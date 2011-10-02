#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from abstract_api import MODE_STREAM, AbstractAPI
import cookielib, urllib, urllib2 #TODO: optimize imports
from xml.etree.cElementTree import fromstring
import datetime
from Plugins.Extensions.KartinaTV.utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, unescapeEntities

#TODO: GLOBAL: add private! Get values by properties.

global Timezone
import time
Timezone = -time.timezone / 3600
print "[KartinaTV] dreambox timezone is GMT", Timezone
			

class KartinaAPI(AbstractAPI):
	
	iProvider = "kartinatv"
	NUMBER_PASS = True
		
	site = "http://iptv.kartina.tv"
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5')]
	
	def start(self):
		self.authorize()
		self.setTimezone()
		
	def authorize(self):
		self.trace("Authorization started")
		#self.trace("username = %s" % self.username)
		self.cookiejar.clear()
		params = urllib.urlencode({"login" : self.username,
								  "pass" : self.password})
		reply = self.opener.open(self.site+'/api/xml/login?', params).read()
		
		#checking cookies
		cookies = list(self.cookiejar)
		cookiesdict = {}
		hasSSID = False
		deleted = False
		
		reply = fromstring(reply)
		if reply.find("error"):
			raise Exception(reply.find('error').findtext('message'))
		
		for cookie in cookies:
			cookiesdict[cookie.name] = cookie.value
			if (cookie.name.find('SSID') != -1):
				hasSSID = True
			if (cookie.value.find('deleted') != -1):
				deleted = True
		if (not hasSSID):
			raise Exception(self.username+": Authorization of user failed!")
		if (deleted):
			raise Exception(self.username+": Wrong authorization request")
		self.packet_expire = datetime.datetime.fromtimestamp(int(reply.find('account').findtext('packet_expire')))
		self.trace("Authorization returned: %s" % urllib.urlencode(cookiesdict))
		self.trace("Packet expire: %s" % self.packet_expire)
		self.SID = True	
	
	def setTimezone(self):
		params = {"act": "x_set_timezone",
				  "m": "clients",
				  "tzn": Timezone }
		self.getData("/?"+urllib.urlencode(params), "(setting) timezone (old api) GMT %s" % Timezone)
		params = {"var" : "timezone",
				  "val" : Timezone}
		#not necessary because we use timestamp 
		#self.getData("/api/xml/settings_set?"+urllib.urlencode(params), "time zone new api %s" % Timezone) 

		
	def getData(self, url, name):
		self.SID = False
		url = self.site + url
		
		self.trace("Getting %s" % (name))
		#self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
			#print reply
		except:
			reply = ""

		if ((reply.find("code_login") != -1)and(reply.find("code_pass") != -1)or(reply.find("<error>") != -1)):
			self.trace("Authorization missed or lost")
			self.authorize()
			self.trace("Second try to get %s (%s)" % (name, url))
			reply = self.opener.open(url).read()
			if ((reply.find("code_login") != -1)and(reply.find("code_pass") != -1)):
				raise Exception("Failed to get %s:\n%s" % (name, reply))
		
		try:
			root = fromstring(reply)
		except:
			raise Exception("Failed to parse xml response")
		if root.find('error'):
			err = root.find('error')
			raise Exception(err.find('code').text.encode('utf-8')+" "+err.find('message').text.encode('utf-8'))
		
		self.SID = True
		return root

class Ktv(KartinaAPI):
	
	iName = "KartinaTV"
	MODE = MODE_STREAM
	NEXT_API = "KartinaMovies"
	
	locked_cids = [155, 159, 161, 257]
	
	def __init__(self, username, password):
		KartinaAPI.__init__(self, username, password)
		self.channels = {}
		self.aTime = 0
	
	def setChannelsList(self):
		root = self.getChannelsList()
		lst = []
		t_str = root.findtext("servertime").encode("utf-8")
		t_cur = datetime.datetime.fromtimestamp(int(t_str))
		setSyncTime(t_cur)
		num = -1
		for group in root.find("groups"):
			title = group.findtext("name").encode("utf-8")
			gid = int(group.findtext("id"))
			for channel in group.find("channels"):
				num += 1
				name = channel.findtext("name").encode("utf-8")
				id = int(channel.findtext("id").encode("utf-8"))
				archive = channel.findtext("have_archive") or 0
				self.channels[id] = Channel(name, title, num, gid, archive)
				if channel.findtext("epg_progname") and channel.findtext("epg_end"):
					prog = channel.findtext("epg_progname").encode("utf-8")
					t_str = channel.findtext("epg_start").encode("utf-8")
					t_start = datetime.datetime.fromtimestamp(int(t_str))
					t_str = channel.findtext("epg_end").encode("utf-8")
					t_end = datetime.datetime.fromtimestamp(int(t_str))
					#print "[KartinaTV] updating epg for cid = ", id
					self.channels[id].epg = EpgEntry(prog, t_start, t_end)
				else:
					#print "[KartinaTV] there is no epg for id=%d on ktv-server" % id
					pass
	
	def setTimeShift(self, timeShift):
		params = {"act" : "x_set_timeshift",
				  "m" : "clients",
				  "ts" : timeShift}
		self.getData("/?"+urllib.urlencode(params), "(setting) time shift %s" % timeShift)
		params = {"var" : "timeshift",
				  "val" : timeShift}
		self.getData("/api/xml/settings_set?"+urllib.urlencode(params), "time shift new api %s" % timeShift) 

	def getChannelsList(self):
		params = { }
		xmlstream = self.getData("/api/xml/channel_list?"+urllib.urlencode(params), "channels list") 
		return xmlstream
	
	def getStreamUrl(self, id):
		params = {"m" : "channels",
				  "act" : "get_stream_url",
				  "cid" : id}
		if self.aTime:
			params["gmt"] = (syncTime() + secTd(self.aTime)).strftime("%s")
		params["protect_code"] = self.password
		root = self.getData("/?"+urllib.urlencode(params), "URL of stream %s" % id)
		if self.aTime:
			prog = unescapeEntities(root.attrib.get("programm"))
			if prog:
				prog = prog.encode("utf-8")
				tstart = datetime.datetime.fromtimestamp( int(root.attrib.get("start").encode("utf-8")) ) #unix
				tend = datetime.datetime.fromtimestamp( int(root.attrib.get("next").encode("utf-8")) )
				self.channels[id].aepg = EpgEntry(prog, tstart, tend)
		return root.attrib.get("url").encode("utf-8").split(' ')[0].replace('http/ts://', 'http://')
	
	def getChannelsEpg(self, cids):
		if len(cids) == 1:
			return self.epgNext(cids[0])
		params = {"cids" : ",".join(map(str, cids))}
		root = self.getData("/api/xml/epg_current?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
		for channel in root.find('epg'):
			id = int(channel.findtext("cid").encode("utf-8"))
			e = channel.find("epg")
			t = int(e.findtext('epg_start').encode("utf-8"))
			t_start = datetime.datetime.fromtimestamp(t)
			t = int(e.findtext('epg_end').encode("utf-8"))
			t_end = datetime.datetime.fromtimestamp(t)
			prog = e.findtext('epg_progname').encode('utf-8')
			self.channels[id].epg = EpgEntry(prog, t_start, t_end)
	
	def getGmtEpg(self, id):
		params = {"m" : "channels",
				  "act" : "get_stream_url",
				  "cid" : id,
				  "gmt": (syncTime() + secTd(self.aTime)).strftime("%s"),
				  "just_info" : 1 }
		root = self.getData("/?"+urllib.urlencode(params), "get GmtEpg of stream %s" % id)
		prog = unescapeEntities(root.attrib.get("programm")).encode("utf-8")
		tstart = datetime.datetime.fromtimestamp( int(root.attrib.get("start").encode("utf-8")) ) #unix
		tend = datetime.datetime.fromtimestamp( int(root.attrib.get("next").encode("utf-8")) )
		self.channels[id].aepg = EpgEntry(prog, tstart,  tend)
		
	
	def getDayEpg(self, cid, date = None):
		if not date:
			date = syncTime()
		params = {"m" : "epg",
				  "act" : "show_day_xml",
				  "day" : date.strftime("%d%m%y"),
				  "cid" : cid}
		root = self.getData("/?"+urllib.urlencode(params), "EPG for channel %s" % cid)
		epglist = []
		archive = int(root.attrib.get("have_archive").encode("utf-8"))
		self.channels[cid].archive = archive
		for program in root:
			t = int(program.attrib.get("t_start").encode("utf-8"))
			time = datetime.datetime.fromtimestamp(t)
			progname = unescapeEntities(program.attrib.get("progname")).encode("utf-8")
			pdescr =  unescapeEntities(program.attrib.get("pdescr")).encode("utf-8")
			epglist += [(time, progname, pdescr)]
		return epglist
	
	def epgNext(self, cid):
		params = {"cid": cid}
		root = self.getData("/api/xml/epg_next?"+urllib.urlencode(params), "EPG next for channel %s" % cid)
		lst = root.find('epg')
		def parseepg(epg):
			t = int(epg.findtext('ts').encode("utf-8"))
			tstart = datetime.datetime.fromtimestamp(t)
			title = epg.findtext('progname').encode('utf-8')
			return (tstart, title)
		if len(lst)>1:
			#print parseepg(lst[0])[0]
			self.channels[cid].epg = EpgEntry(parseepg(lst[0])[1], parseepg(lst[0])[0], parseepg(lst[1])[0])	
		if len(lst)>2:
			self.channels[cid].nepg = EpgEntry(parseepg(lst[1])[1], parseepg(lst[1])[0], parseepg(lst[2])[0])	

	

if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	ktv.start()
	#ktv.setTimeShift(0)
	#ktv.setChannelsList()
	print ktv.getStreamUrl(39)
	ktv.setChannelsList()
	ktv.getChannelsEpg(ktv.channels.keys())
