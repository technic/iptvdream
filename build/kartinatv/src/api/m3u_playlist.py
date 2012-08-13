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
from . import tdSec, secTd, setSyncTime, syncTime, EpgEntry, Channel, APIException
from os import listdir, path
from jtvepg import JTVEpg
import re

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
		self.channels = {}
		for fname in listdir(DIRECTORY):
			if fname.endswith('.m3u'):
				self.loadFile(path.join(DIRECTORY, fname))
	
	def loadFile(self, filename):
		self.trace("parsing %s" % filename)
		fd = open(filename, 'r')
		self.parse_m3u(fd.readlines(), filename.split('/')[-1])

class M3UReader():
	def parse_m3u(self, lines, default_group):
		if len(lines) == 0:
			raise APIException("Empty M3U list")
		BOM = u'\ufeff'.encode('utf-8')
		if lines[0].find(BOM) > -1:
			print 'remove BOM'
			lines[0] = lines[0][3:]
		linen = 0
		if not lines[linen].rstrip().startswith("#EXTM3U"):
			raise APIException("Wrong header. #EXTM3U expected")
		linen += 1
		cid = len(self.channels)
		gid = len(self.groups)
		needinfo = True
		tvgregexp = re.compile('#EXTINF:.*tvg-name="(.*)"')
		while linen < len(lines):
			line = lines[linen]
			if line == '':
				break #end of file
			line = line.rstrip()
			if line.startswith('#EXTINF:'):
				line = line.split('#')[1]
				if not needinfo or not (line.find(',') > -1):
					raise APIException("Error while parsing m3u file at line %s" % linen+1)
				title = line.split(',')[1]
				if title.find(' - ') > -1:
					title = title.partition(' - ')
					name = title[2]
					group = title[0]
				else:
					name = title
					group = default_group
				epginfo = tvgregexp.match(line)
				if epginfo:
					epginfo = epginfo.group(1)
				else:
					epginfo = name
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
					self.channels[cid].epg_name = epginfo
					cid += 1
					needinfo = True
			linen += 1;
				
	def setTimeShift(self, timeShift):
		pass

	def getStreamUrl(self, id, pin, time = None):
		return self.channels[id].stream_url

class Ktv(M3UReader, JTVEpg, Playlist):
	def __init__(self, username, password):
		Playlist.__init__(self, username, password)
		JTVEpg.__init__(self)

	def start(self):
		self.load_epg()