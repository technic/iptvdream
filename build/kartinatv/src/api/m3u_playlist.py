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
import datetime
from Plugins.Extensions.KartinaTV.utils import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, APIException
from os import listdir, path

DIRECTORY = '/etc/iptvdream/'

class Playlist(AbstractAPI, AbstractStream):
	
	iName = "m3uPlaylist"		
	locked_cids = []
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		AbstractStream.__init__(self)

		self.groups = {}

	def start(self):
		pass		
					
	def setTimezone(self):
		pass


	def setChannelsList(self):
		for fname in listdir(DIRECTORY):
			if fname.endswith('.m3u'):
				self.loadFile(path.join(DIRECTORY, fname))
	
	def loadFile(self, filename):
		self.trace("parsing %s" % filename)
		fd = open(filename, 'r')
		self.parse_m3u(fd.readlines(), filename.split('/')[-1])

class M3UReader():
	def parse_m3u(self, lines, default_group):
		linen = 0
		if lines[linen].rstrip() != "#EXTM3U":
			raise Exception("Wrong header. #EXTM3U expected")
		linen += 1
		cid = len(self.channels)
		gid = len(self.groups)
		needinfo = True
		while linen < len(lines):
			line = lines[linen]
			if line == '':
				break #end of file
			line = line.rstrip()
			if line.startswith('#EXTINF:'):
				line = line.split('#')[1]
				if not needinfo or not (line.find(',') > -1):
					raise APIException("Error while parsing m3u file")
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
					raise APIException("Error while parsing m3u file %s" % line)
				else:
					url = line
					if group not in self.groups.keys():
						self.groups[group] = gid
						gid += 1
					self.channels[cid] = Channel(name, group, cid, self.groups[group])
					self.channels[cid].stream_url = url
					cid += 1
					needinfo = True
			linen += 1;
				
	def setTimeShift(self, timeShift):
		pass

	def getStreamUrl(self, id):
		return self.channels[id].stream_url

class Ktv(M3UReader, Playlist):
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
