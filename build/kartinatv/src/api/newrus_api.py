#  Dreambox Enigma2 IPtvDream player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/


from abstract_api import MODE_STREAM, AbstractAPI, AbstractStream
import cookielib, urllib, urllib2 #TODO: optimize imports
from json import loads as json_loads
from datetime import datetime
from . import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, unescapeEntities, Timezone, APIException, SettEntry

# hack !
class JsonWrapper(dict):
	def find(self, key):
		if isinstance(self[key], dict):
			return JsonWrapper(self[key].values())
		if isinstance(self[key], list):
			return map(JsonWrapper, self[key])
		else:
			return self[key]
	def findtext(self, key):
		return unicode(self[key])

def loads(jsonstr):
	return JsonWrapper(json_loads(jsonstr))

class API(AbstractAPI):
	
	iProvider = "newrustv"
	NUMBER_PASS = True
	
	site = "http://iptv.new-rus.tv:8501"
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)

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
		reply = self.opener.open(self.site+'/api/json/login.php?'+params).read()
		
		reply = loads(reply)
		if reply.has_key("error"):
			raise APIException(reply['error']['message'])
	
		self.sidval = urllib.urlencode({reply['sid_name']: reply['sid'] })
		self.trace(self.sidval)
		
		try:
			self.packet_expire = datetime.fromtimestamp(int(reply['account']['packet_expire']))
		except ValueError:
			pass
		
		#Load settings here, because kartina api is't friendly
		self.trace("Packet expire: %s" % self.packet_expire)
		
		#Load settings here, because kartina api is't friendly
		self.settings = []
		sett = reply["settings"]
		for (tag,s) in sett.items():
			if tag == "http_caching": continue
			value = s['value']
			vallist = []
			if tag == "stream_server":
				for x in s['list']:
					vallist += [(x['ip'].encode('utf-8'), x['desc'].encode('utf-8'))]
			elif s.has_key('list'):
				for x in s['list']:
					vallist += [str(x)]
			self.settings += [SettEntry(tag, value, vallist)]
		for x in self.settings:
			self.trace(x)
		
		self.SID = True	
	
	def getData(self, url, name):
		self.SID = False
		url = self.site + url + "&" + self.sidval
		
		self.trace("Getting %s" % (name))
		#self.trace("Getting %s (%s)" % (name, url))
		try:
			reply = self.opener.open(url).read()
		except:
			reply = ""
		#print reply
		try:
			if reply.startswith('1234'):
				reply = reply[4:]
			reply = loads(reply)
		except:
			raise APIException("Failed to parse json response")

		if reply.has_key("error"):
			self.trace("Authorization missed or lost")
			self.authorize()
			self.trace("Second try to get %s (%s)" % (name, url))
			reply = self.opener.open(url).read()
			try:
				reply = loads(reply)
			except:
				raise APIException("Failed to parse json response")
			if reply.has_key("error"):
				err = reply["error"]
				raise APIException(err['message'].encode('utf-8'))
		
		self.SID = True
		return reply

class Ktv(API, AbstractStream):
	
	iName = "NewrusTV"
	MODE = MODE_STREAM
	
	HAS_PIN = True
	
	def __init__(self, username, password):
		API.__init__(self, username, password)
		AbstractStream.__init__(self)
	
	def setChannelsList(self):
	  	root = self.getData("/api/json/channel_list.php?", "channels list")
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
	
	def setTimeShift(self, timeShift):
		params = {"var" : "timeshift",
				  "val" : timeShift}
		self.getData("/api/json/settings_set.php?"+urllib.urlencode(params), "time shift new api %s" % timeShift) 

	def getStreamUrl(self, cid, pin, time = None):
		params = {"cid" : cid}
		if time:
			params["gmt"] = time.strftime("%s")
		if pin:
			params["protect_code"] = pin
		root = self.getData("/api/json/get_url.php?"+urllib.urlencode(params), "URL of stream %s" % cid)
		url = root.findtext("url").encode("utf-8").split(' ')[0].replace('http/ts://', 'http://')
		if url == "protected": return self.ACCESS_DENIED
		return url
	
	def getChannelsEpg(self, cids):
		params = {"cids" : ",".join(map(str, cids))}
		root = self.getData("/api/json/epg_current.php?"+urllib.urlencode(params), "getting epg of cids = %s" % cids)
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
		root = self.getData("/api/json/epg.php?"+urllib.urlencode(params), "day EPG for channel %s" % cid)
		epglist = []
		for program in root.find('epg'):
			t = int(program.findtext("ut_start").encode("utf-8"))
			time = datetime.fromtimestamp(t)
			progname = unescapeEntities(program.findtext("progname")).encode("utf-8")
			epglist += [EpgEntry(progname, time, None)]
		self.channels[cid].pushEpgSorted(epglist)

	def getCurrentEpg(self, cid):
		return self.getDayEpg(cid, syncTime())

	def getNextEpg(self, cid):
		params = {"cid": cid}
		root = self.getData("/api/json/epg_next.php?"+urllib.urlencode(params), "EPG next for channel %s" % cid)
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
			self.getData("/api/json/settings_set.php?"+urllib.urlencode(params), "setting %s" % x[0])
