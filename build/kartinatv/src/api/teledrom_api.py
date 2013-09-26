#  Dreambox Enigma2 KartinaTV/TeledromTV player
#
#  Copyright (c) 2013 Alex Revetchi <revetski@gmail.com>
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from abstract_api import MODE_STREAM, AbstractAPI, AbstractStream
import cookielib, urllib, urllib2 #TODO: optimize imports
import os, subprocess, signal
import time as mtime
from json import loads as json_loads
from datetime import datetime
from . import tdSec, secTd, setSyncTime, syncTime, EpgEntry, Channel, Timezone, APIException

# hack !
class JsonWrapper(dict):
	def find(self, key):
		if isinstance(self[key], dict):
			return JsonWrapper(self[key])
		if isinstance(self[key], list):
			return map(JsonWrapper, self[key])
		else:
			return self[key]
	def findtext(self, key):
		return unicode(self[key])
                                                                                                               
def loads(jsonstr):
	return JsonWrapper(json_loads(jsonstr))
	
class TeledromAPI(AbstractAPI):
	
	iProvider = "teledrom"
	NUMBER_PASS = True
	
	site = "http://a01.teledrom.tv/api/json" 

	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		
		self.time_shift = 0
		self.time_zone = 0
		self.protect_code = ''
		self.sid = None

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5'),
					('Connection', 'Close'), 
					('Accept', 'application/json, text/javascript, */*'),
					('X-Requested-With', 'XMLHttpRequest'), ('Content-Type', 'application/x-www-form-urlencoded')]
		
	def start(self):
		self.authorize()
	
	def setTimeShift(self, timeShift): #in hours #sets timezone also
		params = {'var': 'timeshift', 'val': timeShift*60 }
		return self.getData(self.site+"/settings_set?"+urllib.urlencode(params), "setting time shift to %s" % timeShift)

	def authorize(self):
		self.cookiejar.clear()
		params = urllib.urlencode({"login" : self.username, "pass" : self.password})
		response = self.getData(self.site+"/login?"+ params, "authorize", 1)
		
		if 'sid' in response:
			self.sid = response['sid'].encode("utf-8")
	
		if 'settings' in response:
			if 'timeshift' in response['settings']:
				self.time_shift = response['settings']['timeshift']
			if 'timezone' in response['settings']:
				self.time_zone = response['settings']['timezone']
				
		self.packet_expire = None #XXX: no info in api..
	 	return 0
				
	def getData(self, url, name, fromauth=None):
		if not self.sid and not fromauth:
			self.authorize()
		self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
		except:
			reply = ""
			self.sid = None
		#print reply
		try:
			json = loads(reply)
		except:
			raise APIException("Failed to parse json response")
		if 'error' in json:
			error = json['error']
			raise APIException(error['code']+" "+error['message'].encode('utf-8'))
		return json 

	
class Ktv(TeledromAPI, AbstractStream):
	
	iName = "TeledromTV"
	MODE = MODE_STREAM
	
	locked_cids = [155, 156, 157, 158, 159]
	
	def __init__(self, username, password):
		TeledromAPI.__init__(self, username, password)
		AbstractStream.__init__(self)
		self.ssclient = os.path.dirname( __file__ ) + '/play.sh' 

	def __del__(self):
		subprocess.Popen(['killall', 'ssclient'])

	def addChannelEpg(self, ch_epg, epg_info, epg_type):
		ts_fix = 0
		if 'time_shift' in epg_info:
			ts_fix = int(epg_info['time_shift'])
		program = epg_info[etype]
		txt = (prog['title']+'\n'+prog['info']).encode('utf-8')
		start = datetime.fromtimestamp(int(program['begin'])+ts_fix)
		end   = datetime.fromtimestamp(int(program['end'])+ts_fix)
		ch_epg = EpgEntry(txt, start, end)

	def addChannel(self, channel, groupname, gid):
		id = channel['id']
		name = channel['name'].encode('utf-8')
		archive = ('has_archive' in channel) and (int(channel['has_archive']))
		ch = Channel(name, groupname, id, gid, archive)
		ch.is_protected = ('protected' in channel) and (bool(channel['protected']))
		self.channels[id] = ch
		if 'epg' in channel and 'current' in channel:
			self.addChannelEpg(ch.epg, channel['epg'], 'current')
		if 'epg' in channel and 'next' in channel:
			self.addChannelEpg(ch.nepg, channel['epg'], 'next')

	def setChannelsList(self):
		params = urllib.urlencode({"MWARE_SSID":self.sid}) 
		response = self.getData(self.site+"/channel_list?"+params, "channels list")
		
		for group in response['groups']['item']:
			gid = group['id']
			groupname = group['name'].encode('utf-8')
			if isinstance(group['channels']['item'], list):
				for channels in group['channels']['item']:
					self.addChannel(channels, groupname, gid)
			else:
				self.addChannel(group['channels']['item'], groupname, gid)

	def getStreamUrl(self, cid, pin, time = None):
		params = {"MWARE_SSID":self.sid,"cid": cid}
		if self.channels[cid].is_protected:
			params["protect_code"] = self.protect_code
		response = self.getData(self.site+"/get_url?"+urllib.urlencode(params), "stream url")
		if not 'sstp' in response:
			print response
			raise APIException("Response does not conatin streamming url.")	
		sstp = response['sstp']
		#subprocess.Popen([self.ssclient, sstp['ip'], sstp['port'], sstp['login'], sstp['key']], close_fds=True)
		#os.spawnv(os.P_NOWAIT, self.ssclient, [sstp['ip'], sstp['port'], sstp['login'], sstp['key']])
		os.system(self.ssclient + ' ' + sstp['ip']+' '+sstp['port']+' '+sstp['login']+' '+sstp['key'])
		#subprocess.Popen(['start-stop-daemon', '-S', '-x', self.ssclient, ' -- -i '+sstp['ip']+' -p '+sstp['port']+' -u '+sstp['login']+' -k '+ sstp['key']])
		mtime.sleep(2)
		return "http://127.0.0.1"
	
	def getChannelsEpg(self, cids):
		pass
	
	def getCurrentEpg(self, cid):
		return self.getDayEpg(cid)
	
	def getDayEpg(self, id, dt = None):
		if not dt:
			day = mtime.strftime("%d%m%y",mtime.localtime()) 
		else:
			day = dt.strftime("%d%m%y")

		params = {"MWARE_SSID":self.sid, "cid": id, "day": day}
		response = self.getData(self.site+"/epg?"+urllib.urlencode(params), "EPG for channel %s" % id)
		if 'epg' in response and 'item' in response['epg']:
			epglist = []
			for epg in response['epg']['item']:
				title = ""
				try:
					title = epg['progname'].encode('utf-8') 
				except:
					pass
				try:	
					title += '\n' + epg['description'].encode('utf-8')
				except:
					pass
				t_start = datetime.fromtimestamp(int(epg['ut_start'])+self.time_shift)
				#if len(epglist):
				#	epglist[len(epglist)-1].tend = t_start
				epglist.append (EpgEntry(title, t_start, None))
			self.channels[id].pushEpgSorted(epglist)
