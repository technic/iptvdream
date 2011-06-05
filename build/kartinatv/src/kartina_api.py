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
from utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, BouquetManager, EpgEntry, Channel, Video

site = "http://iptv.kartina.tv"
VIDEO_CACHING = True

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
		self.video_genres = []
		self.videos = {}
		self.filmFiles = {}
		self.aTime = 0
		self.__videomode = False
		self.SID = False
		self.currentPageIds = []
	
	def setVideomode(self, mode):
		return False
		#self.__videomode = mode
	
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
		root = self.getData(site+"/?"+urllib.urlencode(params), "URL of stream %s" % id)
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
		root = self.getData(site+"/?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
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
		root = self.getData(site+"/?"+urllib.urlencode(params), "URL of stream %s" % id)
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
		root = self.getData(site+"/?"+urllib.urlencode(params), "EPG for channel %s" % cid)
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
		root = self.getData(site+"/api/xml/epg_next?"+urllib.urlencode(params), "EPG next for channel %s" % cid)
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
		#self.trace("username = %s" % self.username)
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
		#not necessary because we use timestamp 
		#self.getData(site+"/api/xml/settings_set?"+urllib.urlencode(params), "time zone new api %s" % Timezone) 

		
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
		try:
			root = fromstring(reply)
		except:
			raise Exception("Failed to parse xml response")
		if root.find('error'):
			err = root.find('error')
			raise Exception(err.find('code').text.encode('utf-8')+" "+err.find('message').text.encode('utf-8'))
		
		self.SID = True
		return root
	
	def getVideos(self, stype='last', page=1, genre=[],  nums_onpage=20, query=''):
		if not VIDEO_CACHING:
			self.videos = {}
						
		params = {"type" : stype,
				  "nums" : nums_onpage,
				  "page" : page,
				  "genre" : "|".join(genre) }
		if stype == 'text':
			params['query'] = query
		root = self.getData(site+"/api/xml/vod_list?"+urllib.urlencode(params), "getting video list by type %s" % stype)
		videos_count = int(root.findtext('total'))
		
		self.currentPageIds = []
		for v in root.find('rows'):
			vid = int(v.findtext('id'))
			self.currentPageIds += [vid]
			name = v.findtext('name').encode('utf-8')
			video = Video(name)
			video.name_orig = v.findtext('name_orig').encode('utf-8')
			video.descr = v.findtext('description').encode('utf-8')
			video.image = v.findtext('poster')
			video.year = v.findtext('year')
			video.rate_imdb = floatConvert(v.findtext('rate_imdb'))
			video.rate_kinopoisk = floatConvert(v.findtext('rate_kinopoisk'))
			video.rate_mpaa = v.findtext('rate_mpaa')
			video.country = v.findtext('country')
			video.genre = v.findtext('genre_str')
			self.videos[vid] = video				
		return videos_count 
	
	def getVideoInfo(self, vid):
		params = {"id": vid}
		root = self.getData(site+"/api/xml/vod_info?"+urllib.urlencode(params), "getting video info %s" % vid)
		v = root.find('film')
		name = v.findtext('name').encode('utf-8')
		video = Video(name)
		
		video.name_orig = v.findtext('name_orig').encode('utf-8')
		video.descr = v.findtext('description').encode('utf-8')
		video.image = v.findtext('poster')
		video.year = v.findtext('year')
		video.rate_imdb = floatConvert(v.findtext('rate_imdb'))
		video.rate_kinopoisk = floatConvert(v.findtext('rate_kinopoisk'))
		video.rate_mpaa = v.findtext('rate_mpaa')
		video.country = v.findtext('country').encode('utf-8')
		video.genre = v.findtext('genre_str').encode('utf-8')
		video.length = v.findtext('length') and int(v.findtext('length'))
		video.director = v.findtext('director')
		video.scenario = v.findtext('scenario')
		video.actors = v.findtext('actors').encode('utf-8')
		video.studio = v.findtext('studio')
		video.awards = v.findtext('awards')
		video.budget = v.findtext('budget')
		video.files = []
		for f in v.find('videos'):
			episode = {}
			fid = int(f.findtext('id'))
			episode["format"] = f.findtext('format')
			episode["length"] = f.findtext('length')
			episode["title"] = f.findtext('title').encode('utf-8') or video.name
			episode["tracks"] = []
			i = 1
			while True:
				if f.find("track%d_codec" % i):
					episode["tracks"] += ["%s-%s" % (f.findtext("track%d_codec" % i), f.find("track%d_lang" % i))]
					i +=1
				else:
					break
			video.files += [fid]
			self.filmFiles[fid] = episode 
		self.videos[vid]= video
	
	def getVideoUrl(self, fid):
		params = {"fileid" : fid}
		root = self.getData(site+"/api/xml/vod_geturl?"+urllib.urlencode(params), "getting video url %s" % fid)
		return root.find('url').text.encode('utf-8').split(' ')[0]
	
	def getVideoGenres(self):
		root = self.getData(site+"/api/xml/vod_genres?", "getting genres list")		
		self.video_genres = []
		for genre in root.find('genres'):
			self.video_genres += [{"id": genre.findtext('id'), "name": genre.findtext('name').encode('utf-8')}]
	
	def getPosterPath(self, vid, local=False):
		if local:
			return self.videos[vid].image.split('/')[-1]
		else:	
			return site+self.videos[vid].image
		
	
	def buildVideoBouquet(self):
		movs = Bouquet(Bouquet.TYPE_MENU, 'films')
		for x in self.currentPageIds:
			 mov = Bouquet(Bouquet.TYPE_MENU, x, self.videos[x].name, self.videos[x].year) #two sort args [name, year]
			 movs.append(mov)
		return movs
	
	def buildEpisodesBouquet(self, vid):
		files = Bouquet(Bouquet.TYPE_MENU, 'episodes') 
		for x in self.videos[vid].files:
			print 'add fid', x, 'to bouquet'
			file = Bouquet(Bouquet.TYPE_SERVICE, x)
			files.append(file)
		return files

	def trace(self, msg):
		if self.traces:
			print "[KartinaTV] api: %s" % (msg)

def floatConvert(s):
	return s and int(float(s)*10) or 0 

if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	ktv.start()
	#ktv.setTimeShift(0)
	#ktv.setChannelsList()
	print ktv.getStreamUrl(39)
	x = ktv.getVideos()
	print ktv.videos.keys()
	x = ktv.getVideoInfo(407)
	print ktv.getVideoUrl(ktv.videos[407].files[0])
