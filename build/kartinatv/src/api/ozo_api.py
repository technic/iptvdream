#  Dreambox Enigma2 KartinaTV/OzoTV player
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
from json import loads as json_loads
from datetime import datetime
from md5 import md5
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
	
class OzoAPI(AbstractAPI):
	
	iProvider = "ozo"
	NUMBER_PASS = False
	
	site = "http://file-teleport.com/iptv/api/v1/json"

	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		
		self.time_shift = 0
		self.time_zone = 0
		self.protect_code = ''

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5'),
					('Connection', 'Close'), 
					('Accept', 'application/json, text/javascript, */*'),
					('X-Requested-With', 'XMLHttpRequest'), ('Content-Type', 'application/x-www-form-urlencoded')]
		
	def start(self):
		if self.authorize():
			params = {'var': 'time_zone,time_shift',
					  'val':  '%s,%s' % (Timezone, 0) }
			self.getData(self.site+"/set?"+urllib.urlencode(params), "setting time zone %s and time shift %s" % (Timezone, self.time_shift) )	
	
	def setTimeShift(self, timeShift): #in hours #sets timezone also
		return
		#if self.username == 'demo': return 
		params = {'var': 'time_shift', #FIXME api bug!!!!
				  'val': timeShift*60 }
		return self.getData(self.site+"/set?"+urllib.urlencode(params), "setting time shift to %s" % timeShift)

	def authorize(self):
		self.trace("Username is "+self.username)
		self.cookiejar.clear()
		md5pass = md5(md5(self.username).hexdigest() + md5(self.password).hexdigest()).hexdigest()
		params = urllib.urlencode({"login" : self.username,
		                           "pass" : md5pass})
		self.trace("Authorization started (%s)" % (self.site+"/login?"+ params))
		response = self.getData(self.site+"/login?"+ params, "authorize", 1)
		
		if 'sid' in response:
			self.sid = response['sid'].encode("utf-8")
			self.SID = True
	
		if 'settings' in response:
			if 'time_shift' in response['settings']:
				self.time_shift = response['settings']['time_shift']
			if 'time_zone' in response['settings']:
				self.time_zone = response['settings']['time_zone']
				
		self.packet_expire = None #XXX: no info in api..
	 	return 0
				
	def getData(self, url, name, fromauth=None):
		if not self.SID and not fromauth:
			self.authorize()
		self.SID = False 
		self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
		except:
			reply = ""
		#print reply
		try:
			json = loads(reply)
		except:
			raise APIException("Failed to parse json response")
		if 'error' in json:
			error = json['error']
			raise APIException(error['code']+" "+error['message'].encode('utf-8'))
		self.SID = True
		return json 

	
class Ktv(OzoAPI, AbstractStream):
	
	iName = "OzoTV"
	MODE = MODE_STREAM
	
	locked_cids = [155, 156, 157, 158, 159]
	
	def __init__(self, username, password):
		OzoAPI.__init__(self, username, password)
		AbstractStream.__init__(self)
	def setChannelsList(self):
		params = urllib.urlencode({"with_epg":1,"time_shift": self.time_shift}) 
		response = self.getData(self.site+"/get_list_tv?"+params, "channels list")
#		if 'servertime' in response:
#			servertime = int(response['servertime'])
#		else:
#			servertime = time()
			
		self.trace('server time %s' % datetime.fromtimestamp(servertime))
#		setSyncTime(datetime.fromtimestamp(servertime))
		
		for group in response['groups']:
			gid = group['id']
			groupname = group['name'].encode('utf-8')
			for channel in group['channels']: 
				id = channel['id']
				name = channel['name'].encode('utf-8')
				num = channel['number'] 
				archive = ('has_archive' in channel) and (int(channel['has_archive']))
				self.channels[id] = Channel(name, groupname, num, gid, archive)
				self.channels[id].is_protected = ('protected' in channel) and (int(channel['protected']))
				if 'epg' in channel and 'current' in channel:
					ts_fix = 0
					if 'time_shift' in channel['epg']:
						ts_fix = int(channel["epg"]["time_shift"])
					prog = channel['epg']['current']
					txt = prog['title'].encode('utf-8') + '\n' + prog['info'].encode('utf-8')
					t_start = datetime.fromtimestamp(int(prog['begin'])+ts_fix)
					t_end = datetime.fromtimestamp(int(prog['end'])+ts_fix)
					self.channels[id].epg = EpgEntry(txt, t_start, t_end)
				if 'epg' in channel and 'next' in channel:
					ts_fix = 0
					if 'time_shift' in channel['epg']:
						ts_fix = int(channel["epg"]["time_shift"])
					prog = channel['epg']['next']
					txt = prog['title'].encode('utf-8') + '\n' + prog['info'].encode('utf-8')
					t_start = datetime.fromtimestamp(int(prog['begin'])+ts_fix)
					t_end = datetime.fromtimestamp(int(prog['end'])+ts_fix)
					self.channels[id].nepg = EpgEntry(txt, t_start, t_end)
				else:
					#print "[RodnoeTV] there is no epg for id=%d on rtv-server" % id
					pass

	def getStreamUrl(self, cid, pin, time = None):
		params = {"cid": cid, "time_shift": self.time_shift}
		if self.channels[cid].is_protected:
			params["protect_code"] = self.protect_code
		if time:
			params["uts"] = time.strftime("%s")
		response = self.getData(self.site+"/get_url_tv?"+urllib.urlencode(params), "stream url")
		return response["url"].encode("utf-8")
	
	def getChannelsEpg(self, cids): #RodnoeTV hasn't got this function in API. Got epg for all instead.
		params = {}
		if len(cids) == 1:
			params['cid'] = cids[0]
		response = self.getData(self.site+"/get_epg_current?"+urllib.urlencode(params), "getting epg of all channels")
		for prog in response['channels']:
			id = prog['id']
			if 'current' in prog and 'begin' in prog and 'title' in prog:
				ts_fix = self.time_shift *3600
				if 'time_shift' in channel:
					int(channel["time_shift"])*60
				title = prog['title'].encode('utf-8') + '\n' + prog['info'].encode('utf-8')
				t_start = datetime.fromtimestamp(int(prog['begin'])+ts_fix)
				t_end = datetime.fromtimestamp(int(prog['end'])+ts_fix)
				self.channels[id].epg = EpgEntry(title, t_start, t_end)
			if 'next' in prog and 'begin' in prog and 'title' in prog:
				ts_fix = self.time_shift *3600
				if 'time_shift' in channel:
					int(channel["time_shift"])*60
				title = prog['title'].encode('utf-8') + '\n' + prog['info'].encode('utf-8')
				t_start = datetime.fromtimestamp(int(prog['begin'])+ts_fix)
				t_end = datetime.fromtimestamp(int(prog['end'])+ts_fix)
				self.channels[id].epg = EpgEntry(title, t_start, t_end)
			else:
				self.channels[id].lastUpdateFailed = True
			#	print "[KartinaTV] INFO there is no epg for id=%d on ktv-server" % id
				pass
	
	def getCurrentEpg(self, cid):
		return self.getChannelsEpg([cid])
	
	def getDayEpg(self, id, dt = None):
		if not dt:
			dt = time.replace(0, 0, 0) 
		params = {"cid": id,
				  "from_uts": dt,
				  "hours" : 24, "time_shift": self.time_shift }
		response = self.getData(self.site+"/get_epg?"+urllib.urlencode(params), "EPG for channel %s" % id)
		epglist = []
		for channel in response['channels']:
			for prog in channel['epg']:
				if 'time_shift' in channel:
					ts_fix = int(channel["time_shift"])*60
				else:
					ts_fix = self.time_shift *3600
				title = prog['title'].encode('utf-8') + '\n' + prog['info'].encode('utf-8')
				t_start = datetime.fromtimestamp(int(prog['begin'])+ts_fix)
				t_end = datetime.fromtimestamp(int(prog['end'])+ts_fix)
				epglist.append (EpgEntry(title, t_start, t_end))
		self.channels[id].pushEpgSorted(epglist)
