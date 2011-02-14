#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

import cookielib, urllib, urllib2 #TODO: optimize imports
from xml.etree.cElementTree import fromstring
try: 
	from json import loads as jdecode
except:
	print "[KartinaTV] using cjson"
	from cjson import decode as jdecode
import datetime
from utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, BouquetManager, EpgEntry, Channel

site = "http://iptv.kartina.tv"

#TODO: GLOBAL: add private! Get values by properties.

global Timezone
import time
Timezone = -time.timezone / 3600
print "[KartinaTV] dreambox timezone is GMT", Timezone
				
class Ktv():

	locked_cids = [155, 159, 161, 257]
	
	def __init__(self, username, password, traces = True):
		self.username = username
		self.password = password
		self.traces = traces

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5')]
		self.channels = {}
		self.aTime = 0
		self.__videomode = False
		self.SID = False
	
	def setVideomode(self, mode):
		self.__videomode = mode
	
	def getVideomode(self):
		return self.__videomode
	
	videomode = property(getVideomode, setVideomode)
	
	def start(self):
		self.authorize()
		self.setTimezone()

	def sortByName(self):
		x = [(val.name, key) for (key, val) in self.channels.items()]
		x.sort()
		services = Bouquet(Bouquet.TYPE_MENU, 'all')
		for item in x:
			ch = self.channels[item[1]]
			services.append(Bouquet(Bouquet.TYPE_SERVICE, item[1], ch.name, ch.num )) #two sort args [channel_name, number]
		return services
	
	def sortByGroup(self):
		x = [(val.group, key) for (key, val) in self.channels.items()]
		x.sort()
		groups = Bouquet(Bouquet.TYPE_MENU, 'By group')
		groupname = x[0][0]
		ch = self.channels[x[0][1]]
		group = Bouquet(Bouquet.TYPE_MENU, groupname, ch.group, ch.gid) #two sort args [group_name, number]
		for item in x:
			ch = self.channels[item[1]]
			if item[0] == groupname:
				group.append(Bouquet(Bouquet.TYPE_SERVICE, item[1], ch.name, ch.num))
			else:
				groups.append(group)
				groupname = item[0]
				ch = self.channels[item[1]]
				group = Bouquet(Bouquet.TYPE_MENU, groupname, ch.group, ch.gid) #two sort args [group_name, number]
				group.append(Bouquet(Bouquet.TYPE_SERVICE, item[1], ch.name, ch.num))
		groups.append(group)
		return groups
	
	def setChannelsList(self):
		root = fromstring(self.getChannelsList())
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
		self.getData(site+"/?"+urllib.urlencode(params), "(setting) time shift %s" % timeShift)
		params = {"var" : "timeshift",
				  "val" : timeShift}
		self.getData(site+"/api/xml/settings_set?"+urllib.urlencode(params), "time shift new api %s" % timeShift) 

	def getChannelsList(self):
		params = { }
		xmlstream = self.getData(site+"/api/xml/channel_list?"+urllib.urlencode(params), "channels list") 
		return xmlstream
	
	def getStreamUrl(self, id):
		params = {"m" : "channels",
				  "act" : "get_stream_url",
				  "cid" : id}
		if self.aTime:
			params["gmt"] = (syncTime() + secTd(self.aTime)).strftime("%s")
		params["protect_code"] = self.password
		xmlstream = self.getData(site+"/?"+urllib.urlencode(params), "URL of stream %s" % id)
		root = fromstring(xmlstream)
		if self.aTime:
			prog = root.attrib.get("programm")
			if prog:
				prog = prog.encode("utf-8")
				tstart = datetime.datetime.fromtimestamp( int(root.attrib.get("start").encode("utf-8")) ) #unix
				tend = datetime.datetime.fromtimestamp( int(root.attrib.get("next").encode("utf-8")) )
				self.channels[id].aepg = EpgEntry(prog, tstart, tend)
		return root.attrib.get("url").encode("utf-8").split(' ')[0].replace('http/ts://', 'http://')
	
	def getChannelsEpg(self, cids):
		if len(cids) == 1:
			return self.epgNext(cids[0])
		params = {"m" : "channels",
				  "act" : "get_info_xml",
				  "cids" : str(cids).replace(" ","")[1:-1]}
		xmlstream = self.getData(site+"/?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
		root = fromstring(xmlstream)
		for channel in root:
			id = int(channel.attrib.get("id").encode("utf-8"))
			prog = channel.attrib.get("programm")
			if prog:
				prog = prog.encode("utf-8").replace("&quot;", "\"")
				t_str = channel.attrib.get("sprog").encode("utf-8")
				t_start = datetime.datetime.strptime(t_str, "%b %d, %Y %H:%M:%S")
				t_str = channel.attrib.get("eprog") and channel.attrib.get("eprog").encode("utf-8")
				t_end = datetime.datetime.strptime(t_str, "%b %d, %Y %H:%M:%S")
				self.channels[id].epg = EpgEntry(prog, t_start, t_end)
			else:
				#print "[KartinaTV] INFO there is no epg for id=%d on ktv-server" % id
				self.channels[id].lastUpdateFailed = True
				pass 
	
	def getGmtEpg(self, id):
		params = {"m" : "channels",
				  "act" : "get_stream_url",
				  "cid" : id,
				  "gmt": (syncTime() + secTd(self.aTime)).strftime("%s"),
				  "just_info" : 1 }
		xmlstream = self.getData(site+"/?"+urllib.urlencode(params), "URL of stream %s" % id)
		root = fromstring(xmlstream)
		prog = root.attrib.get("programm").encode("utf-8").replace("&quot;", "\"")
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
		xmlstream = self.getData(site+"/?"+urllib.urlencode(params), "EPG for channel %s" % cid)
		root = fromstring(xmlstream)
		epglist = []
		archive = int(root.attrib.get("have_archive").encode("utf-8"))
		self.channels[cid].archive = archive
		for program in root:
			t = int(program.attrib.get("t_start").encode("utf-8"))
			time = datetime.datetime.fromtimestamp(t)
			progname = program.attrib.get("progname").encode("utf-8").replace("&quot;", "\"")
			pdescr =  program.attrib.get("pdescr").encode("utf-8").replace("&quot;", "\"")
			epglist += [(time, progname, pdescr)]
		return epglist
	
	def epgNext(self, cid):
		params = {"cid": cid}
		xmlstream = self.getData(site+"/api/xml/epg_next?"+urllib.urlencode(params), "EPG next for channel %s" % cid)
		root = fromstring(xmlstream)		
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
	
	def authorize(self):
		self.trace("Authorization started")
		self.trace("username = %s" % self.username)
		self.cookiejar.clear()
		params = urllib.urlencode({"login" : self.username,
								  "pass" : self.password})
		reply = self.opener.open(site+'/api/xml/login?', params).read()
		
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
		self.getData(site+"/?"+urllib.urlencode(params), "(setting) timezone GMT %s" % Timezone)
		params = {"var" : "timezone",
				  "val" : Timezone}
		#not necessary because of timestamp 
		#self.getData(site+"/api/xml/settings_set?"+urllib.urlencode(params), "time zone new api %s" % Timezone) 
	
	def getVideos(self, stype='last', nums_onpage=15, page=1, genre=[]):
		params = {"type" : stype,
				  "nums" : nums_onpage,
				  "page" : page,
				  "genre" : "|".join(genre) }
		d = self.getData(site+"/api/json/vod_list?"+urllib.urlencode(params), "getting video list by type %s" % stype)
		root = jdecode(d)
		root['total'] =  int(root[u'total'].encode('utf-8'))
		for x in root['rows']:
			x['id'] = int(x[u'id'])
		#self.videos = jdecode(d)["rows"]
		return root
	
	def getVideoInfo(self, vid):
		params = {"id": vid}
		d = self.getData(site+"/api/json/vod_info?"+urllib.urlencode(params), "getting video info %s" % vid)
		root = jdecode(d)
		#self.videos = jdecode(d)["rows"]
		return root
	
	def getVideoUrl(self, vid):
		params = {"fileid" : vid}
		d = self.getData(site+"/api/xml/vod_geturl?"+urllib.urlencode(params), "getting video url %s" % vid)
		root = fromstring(d)
		#self.videos = jdecode(d)["rows"]
		#if root.has_key('url'):
		return root.find('url').text.encode('utf-8').split(' ')[0]
		#else: 
		#	raise Exception(root['error']['message'])	
	
		
	def getData(self, url, name):
		self.SID = False
		
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
		self.SID = True
		return reply

	def trace(self, msg):
		if self.traces:
			print "[KartinaTV] api: %s" % (msg)

if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	ktv.start()
	ktv.setTimeShift(0)
	ktv.setChannelsList()
	print ktv.getStreamUrl(39)
#	x = 51
#	print x, ktv.channels[x].name, ktv.channels[x].epg.tstart, ktv.channels[x].epg.tend,  ktv.channels[x].epg.name
#	ktv.getChannelsEpg([x])
#	print x, ktv.channels[x].name, ktv.channels[x].epg.tstart, ktv.channels[x].epg.tend,  ktv.channels[x].epg.name
	#l = ktv.getVideos()
	#print int(l[u'rows'][1][u'id'])
	#print  ktv.getVideoUrl(121)
