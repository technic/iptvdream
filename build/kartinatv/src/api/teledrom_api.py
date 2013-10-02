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
import os
import time as mtime
from json import loads as json_loads
from datetime import datetime
from . import tdSec, secTd, setSyncTime, syncTime, EpgEntry, Channel, Timezone, APIException, SettEntry

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
		self.settings = {} 

		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 technic-plugin-1.5'),
					('Connection', 'Close'), 
					('Accept', 'application/json, text/javascript, */*'),
					('X-Requested-With', 'XMLHttpRequest'), ('Content-Type', 'application/x-www-form-urlencoded')]
		
	def start(self):
		self.authorize()
	
	def setTimeShift(self, timeShift): #in hours #sets timezone also
		params = {'MWARE_SSID':self.sid, 'var': 'timeshift', 'val': timeShift*60 }
		return self.getData(self.site+"/settings_set?"+urllib.urlencode(params), "setting time shift to %s" % timeShift)

	def authorize(self):
		self.cookiejar.clear()
		params = urllib.urlencode({'login' : self.username, 'pass' : self.password, 'tz':Timezone, 'settings':'all'})
		response = self.getData(self.site+"/login?"+ params, "authorize", 1)
		
		if 'sid' in response:
			self.sid = response['sid'].encode("utf-8")

		if 'settings' in response:
			try:
				self.parseSettings(response['settings'])
			except:
				self.settings={}
			if 'timeshift' in response['settings']:
				self.time_shift = int(response['settings']['timeshift']['value'])
				
		if 'account' in response:
			if 'packet_expire' in response['account']:
				self.packet_expire = datetime.fromtimestamp(int(response['account']['packet_expire']))
			if 'pcode' in response['account']:
				self.protect_code = response['account']['pcode']

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
		self.ssclient = os.path.dirname( __file__ ) + '/ssclient' 

	def __del__(self):
		os.system('start-stop-daemon -K -x '+self.ssclient)

	def addChannelEpg(self, ch_epg, epg_info, epg_type):
		program = epg_info[etype]
		txt = (prog['title']+'\n'+prog['info']).encode('utf-8')
		start = datetime.fromtimestamp(int(program['begin'])+self.time_shift)
		end   = datetime.fromtimestamp(int(program['end'])+self.time_shift)
		ch_epg = EpgEntry(txt, start, end)

	def addChannel(self, channel, groupname, gid):
		id = channel['id']
		name = channel['name'].encode('utf-8')
		archive = ('have_archive' in channel) and (bool(channel['have_archive']))
		ch = Channel(name, groupname, id, gid, archive)
		ch.is_protected = ('protected' in channel) and (bool(channel['protected']))
		self.channels[id] = ch
		if 'epg' in channel and 'current' in channel:
			self.addChannelEpg(ch.epg, channel['epg'], 'current')
		if 'epg' in channel and 'next' in channel:
			self.addChannelEpg(ch.nepg, channel['epg'], 'next')

	def setChannelsList(self):
		params = urllib.urlencode({'MWARE_SSID':self.sid}) 
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
		params = {'MWARE_SSID':self.sid,'cid': cid}
		if self.channels[cid].is_protected:
			params["protect_code"] = self.protect_code
		response = self.getData(self.site+"/get_url?"+urllib.urlencode(params), "stream url")
		if not 'sstp' in response:
			raise APIException("Response does not conatin streamming url.")	
		sstp = response['sstp']
		os.system('start-stop-daemon -K -x '+self.ssclient)
		os.system('start-stop-daemon -b -S -x '+self.ssclient + ' --  -P 5000 -i ' + sstp['ip']+' -p '+sstp['port']+' -u '+sstp['login']+' -k '+sstp['key']+' -d 2 -b 64')
		return "http://127.0.0.1:5000"
	
	def getChannelsEpg(self, cids):
		for c  in cids:
			self.getCurrentEpg(c)
	
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
				epglist.append (EpgEntry(title, t_start, None))
			self.channels[id].pushEpgSorted(epglist)

	def getSettings(self):
		return self.settings

	def parseSettings(self, rawsett):
		self.settings['Language'] = SettEntry('lang', rawsett['lang']['value'], rawsett['lang']['list']['item'])
		self.settings['HTTP caching'] = SettEntry('http_caching', rawsett['http_caching']['value'], rawsett['http_caching']['list']['item'])
		self.settings['Bitrate'] = SettEntry('bitrate', rawsett['bitrate']['value'], rawsett['bitrate']['list']['item'])
		self.settings['Timeshift'] = SettEntry('timeshift', int(rawsett['timeshift']['value']), range(0,24))
		self.settings['HLS enabled']=SettEntry('hls_enabled', str(rawsett['hls_enabled']['value']),['yes','no'])
		self.settings['Cache size(seconds)']=SettEntry('fwcaching', int(rawsett['fwcaching']['value']), rawsett['fwcaching']['list']['item'])
		ar=[]
		for a in rawsett['ar']['list']['item']:
			ar += [(a['age'],a['descr'])]
		self.settings['Archive']=SettEntry('ar', rawsett['ar']['descr'], ar)
		if isinstance(rawsett['stream_server']['list']['item'], list):
			ss=[]
			for s in rawsett['stream_server']['list']['item']:
				ss += [(s['ip'],s['descr'])]
			self.settings['Stream server']=SettEntry('stream_server', rawsett['stream_server']['value'].encode('utf-8'), ss)

	def pushSettings(self, sett):
		keys=[]
		values=[]
		for s in sett:
			keys+=[s[0]]
			values+=[s[1]]
			
		var=','.join(keys)
		val=','.join(values)

		params = urllib.urlencode({'MWARE_SSID':self.sid,'var':var,'val':val,'code':self.protect_code})	
		self.getData(self.site+"/settings_set?"+params, "Push new setting.")
