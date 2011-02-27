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
import datetime
from md5 import md5
from utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, BouquetManager, EpgEntry, Channel

site = "http://file-teleport.com/iptv/api/xml"

global Timezone
Timezone = int(round(tdSec(datetime.datetime.now()-datetime.datetime.utcnow()) / 3600.0)*60)
print "[KartinaTV] dreambox timezone is", Timezone, "min"
	
class Ktv():
	
	locked_cids = [155, 156, 157, 158, 159]
	
	def __init__(self, username, password, traces = True):
		self.username = username
		self.password = password
		self.traces = traces
		
		self.time_shift = 0
		self.protect_code = ''

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
		self.channels = {}
		self.aTime = 0
		self.__videomode = False
		self.SID = False
	
	def setVideomode(self, mode):
		#RodnoeTV has no  video collection!!!
		return
	
	def getVideomode(self):
		return self.__videomode
	
	videomode = property(getVideomode, setVideomode)		
	
	def start(self):
		if self.authorize():
			params = {'var': 'time_zone time_shift',
					  'val':  '%s %s' % (60, self.time_shift*60) } #FIXME: API BUG!!
			root = self.getData(site+"/set?"+urllib.urlencode(params), "setting time zone %s and time shift %s" % (Timezone, self.time_shift) )	

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
		root = self.getChannelsList()
		t = int(root.findtext('servertime'))
		self.trace('server time %s' % datetime.datetime.fromtimestamp(t))
		setSyncTime(datetime.datetime.fromtimestamp(t))
		
		groups = root.find('groups')
		for group in groups.findall('item'):
			gid = int(group.findtext('id').encode('utf-8'))
			groupname = group.findtext('name').encode('utf-8')
			channels = group.find('channels')
			for channel in channels.findall('item'): 
				id = int(channel.findtext('id').encode('utf-8'))
				name = channel.findtext('name').encode('utf-8')
				num = int(channel.findtext('number').encode('utf-8')) 
				archive = int(channel.findtext('has_archive').encode('utf-8'))
				self.channels[id] = Channel(name, groupname, num, gid, archive)
				self.channels[id].is_protected = int(channel.findtext('protected'))
				if channel.findtext('epg_current_title') and channel.findtext('epg_current_start'):
					prog = channel.findtext('epg_current_title').encode('utf-8') + '\n'
					prog += channel.findtext('epg_current_info').encode('utf-8')
					t_start = datetime.datetime.fromtimestamp(int(channel.findtext('epg_current_start')))
					t_end = datetime.datetime.fromtimestamp(int(channel.findtext('epg_current_end').encode('utf-8')))
					self.channels[id].epg = EpgEntry(prog, t_start, t_end)
				if channel.findtext('epg_next_title') and channel.findtext('epg_next_start'):
					prog = channel.findtext('epg_next_title').encode('utf-8') + '\n'
					prog += channel.findtext('epg_next_info').encode('utf-8')
					t_start = datetime.datetime.fromtimestamp(int(channel.findtext('epg_next_start').encode('utf-8')))
					t_end = datetime.datetime.fromtimestamp(int(channel.findtext('epg_next_end').encode('utf-8')))
					self.channels[id].nepg = EpgEntry(prog, t_start, t_end)
				else:
					#print "[RodnoeTV] there is no epg for id=%d on rtv-server" % id
					pass


	def setTimeShift(self, timeShift): #in hours #sets timezone also
		return
		#if self.username == 'demo': return 
		params = {'var': 'time_shift', #FIXME api bug!!!!
				  'val': timeShift*60 }
		return self.getData(site+"/set?"+urllib.urlencode(params), "setting time shift to %s" % timeShift)

	def getChannelsList(self):
		params = {  }
		return self.getData(site+"/get_list_tv"+urllib.urlencode(params), "channels list") 

	def getStreamUrl(self, id):
		params = {"cid": id}
		if self.channels[id].is_protected:
			params["protect_code"] = self.protect_code
		if self.aTime:
			params["lts"] = (syncTime() + secTd(self.aTime)).strftime("%s")		  
		root = self.getData(site+"/get_url_tv?"+urllib.urlencode(params), "stream url")
		return root.findtext("url").encode("utf-8")
	
	def getChannelsEpg(self, cids): #RodnoeTV hasn't got this function in API. Got epg for all instead.
		params = {}
		if len(cids) == 1:
			params['cid'] = cids[0]
		root = self.getData(site+"/get_epg_current?"+urllib.urlencode(params), "getting epg of all channels")
		for channel in root.find('channels'):
			id = int(channel.findtext('id').encode("utf-8"))
			prog = channel.find('current')
			if prog and prog.findtext('begin') and prog.findtext('title'):
				title = prog.findtext('title').encode('utf-8') + '\n'
				title += prog.findtext('info').encode('utf-8')
				t_start = datetime.datetime.fromtimestamp(int(prog.findtext('begin').encode('utf-8')))
				t_end = datetime.datetime.fromtimestamp(int(prog.findtext('end').encode('utf-8')))
				self.channels[id].epg = EpgEntry(title, t_start, t_end)
			prog = channel.find('next')
			if prog and prog.findtext('begin') and prog.findtext('title'):
				title = prog.findtext('title').encode('utf-8') + '\n'
				title += prog.findtext('info').encode('utf-8')
				t_start = datetime.datetime.fromtimestamp(int(prog.findtext('begin').encode('utf-8')))
				t_end = datetime.datetime.fromtimestamp(int(prog.findtext('end').encode('utf-8')))
				self.channels[id].nepg = EpgEntry(title, t_start, t_end)
			else:
				self.channels[id].lastUpdateFailed = True
			#	print "[KartinaTV] INFO there is no epg for id=%d on ktv-server" % id
				pass
	
	def epgNext(self, cid): #do Nothing
		self.trace("NO epgNext in API!")
		pass 
	
	def getDayEpg(self, id, date = None):
		if not date:
			date = syncTime()
		params = {"cid": id,
				  "day": date.strftime("%y%m%d")}
		root = self.getData(site+"/get_epg?"+urllib.urlencode(params), "EPG for channel %s" % id)
		epglist = []
		self.channels[id].lepg[date.strftime("%y%m%d")] = []
		for prog in root.find('channels').find('item').find('epg'):
			title = prog.findtext('title').encode('utf-8') + '\n'
			title += prog.findtext('info').encode('utf-8')
			t_start = datetime.datetime.fromtimestamp(int(prog.findtext('begin').encode('utf-8')))
			t_end = datetime.datetime.fromtimestamp(int(prog.findtext('end').encode('utf-8')))
			self.channels[id].lepg[date.strftime("%y%m%d")] += [EpgEntry(title, t_start, t_end)]
			epglist += [(t_start, title.split('\n')[0], title.split('\n')[1])]
		return epglist
	
	def getGmtEpg(self, cid):
		t = syncTime() + secTd(self.aTime)
		print self.channels[cid].lepg.has_key(t.strftime("%y%m%d"))
		lepg = self.channels[cid].lepg[t.strftime("%y%m%d")]
		self.trace("get gmt epg")
		print t
		for x in lepg:
			print x.tend
			if x.tend > t:
				self.channels[cid].aepg = x
				return
		

	def authorize(self):
		self.trace("Username is "+self.username)
		self.cookiejar.clear()	
		#self.opener.addheaders += [("X-Requested-With", "XMLHttpRequest")] 		
		params = urllib.urlencode({"login" : self.username,
								   "pass" : md5(md5(self.username).hexdigest()+md5(self.password).hexdigest()).hexdigest(),
								   "ext" : '' })
		self.trace("Authorization started (%s)" % (site+"/login?"+ params))
		httpstr = self.opener.open(site+"/login?"+ params).read()
		#print httpstr
		#handleError() #TODO!
		root = fromstring(httpstr)
		if root.find('error'):
			err = root.find('error')
			raise Exception(err.find('code').text.encode('utf-8')+" "+err.find('message').text.encode('utf-8')) 
		self.sid = root.find('sid').text.encode('utf-8')
		self.sid_name = root.find('sid_name').text.encode('utf-8') 				  
		#checking cookies
		cookies = list(self.cookiejar)
		cookiesdict = {}
		hasSSID = False
		deleted = False
		for cookie in cookies:
			cookiesdict[cookie.name] = cookie.value
			if (cookie.name.find('SSID') != -1):
				hasSSID = True
			if (cookie.value.find('deleted') != -1):
				deleted = True
		#if (not hasSSID):
		#	raise Exception(self.username+": Authorization of user failed!")
		#if (deleted):
		#	raise Exception(self.username+": Wrong authorization request")
		self.packet_expire = None #XXX: no info in api..
		self.opener.addheaders += [("Cookie", "%s=%s" % (self.sid_name, self.sid) )]
		self.trace("Authorization returned: %s" % urllib.urlencode(cookiesdict))
		self.SID = True
		
		settings = root.find('settings')
		self.protect_code = settings.findtext('parental_pass').encode("utf-8")
		self.trace('protectcode %s' % self.protect_code)
		print settings.findtext('time_zone')
	 	if Timezone != int(settings.findtext('time_zone')) or self.time_shift*60 != int(settings.findtext('time_shift')):
	 		return 1
	 	return 0
				
	def getData(self, url, name):
		if not self.SID:
			self.authorize()
		self.SID = False 
		self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
		except:
			reply = ""
		#print reply
		try:
			root = fromstring(reply)
		except:
			raise Exception("Failed to parse xml response")
		if root.find('error'):
			err = root.find('error')
			raise Exception(err.find('code').text.encode('utf-8')+" "+err.find('message').text.encode('utf-8'))
		self.SID = True
		return root

	def trace(self, msg):
		if self.traces:
			print "[RodnoeTV] api: %s" % (msg)
		
if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	#ktv.authorize()
	ktv.start()
#	ktv.setTimeShift(0)
	ktv.setChannelsList()
#	ktv.sortByName()
#	ktv.sortByGroup()
#	ktv.getChannelsEpg([1,2,3,4])
	for x in ktv.channels.keys():
		print x, ktv.channels[x].name, ktv.channels[x].archive#, ktv.channels[x].epg.tstart, ktv.channels[x].epg.tend,  ktv.channels[x].epg.name
	#print ktv.getDayEpg(x)[2][3]
	print ktv.getStreamUrl(66)
#	ktv.getChannelsEpg([x])
