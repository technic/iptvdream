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
from xml.etree.cElementTree import fromstring, ElementTree
import datetime
from Plugins.Extensions.KartinaTV.utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel
from os import listdir, path

DIRECTORY = '/etc/iptvdream/'

class Ktv(AbstractAPI):
	
	iName = "m3uPlaylist"		
	locked_cids = []
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		self.channels = {}
		self.aTime = 0

		self.groups = {}
	def start(self):
		pass		
					
	def setTimezone(self):
		pass

	
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
		for fname in os.listdir(DIRECTORY):
			if fname.endswith('.m3u'):
				self.loadFile(path.join(DIRECTORY, fname))
	
	def loadFile(self, filename):
		self.trace("parsing %s", filename)
		fd = open(filename, 'r')
		if fd.readline().rstrip() != "#EXTM3U":
			raise Exception("Wrong header. #EXTM3U expected")
		
		default_group = filename.split('/')[-1]
		needinfo = True
		cid = len(self.channels)
		gid = len(self.groups)
		while True:
			line = fd.readline()
			if line == '':
				break #end of file
			line = line.rstrip()
			if line.startswith('#EXTINF:'):
				line = line.split('#')[1]
				if not needinfo or not (line.find(',') > -1):
					raise Exception("Error while parsing m3u file")
				title = line.split(',')[1]
				if title.find(' - ') > -1:
					title = title.partition(' - ')
					name = title[2]
					group = title[0]
				else:
					name = title
					group = default_group
				needinfo = False
			elif line != '':
				line = line.partition('#')[0]
				if needinfo:
					raise Exception("Error while parsing m3u file %s" % line)
				else:
					url = line
					if group not in self.groups.keys():
						self.groups[group] = gid
						gid += 1
					self.channels[cid] = Channel(name, group, cid, self.groups[group])
					self.channels[cid].stream_url = url
					cid += 1
					needinfo = True
				
	def setTimeShift(self, timeShift):
		pass

	def getStreamUrl(self, id):
		return self.channels[id].stream_url 
	
	def getChannelsEpg(self, cids):
		pass		
			
	def getGmtEpg(self, id):
		pass		
	
	def getDayEpg(self, cid, date = None):
		return []
		
	def epgNext(self, cid):
		pass

if __name__ == "__main__":
	import sys
	ktv = Ktv(sys.argv[1], sys.argv[2])
	ktv.start()
	ktv.setChannelsList()
	print ktv.getStreamUrl(39)	
	ktv.getChannelsEpg(ktv.channels.keys())
	for x in ktv.channels.keys():
		y = ktv.channels[x]
		print x, y.name, y.group, y.num, y.gid
