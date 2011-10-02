#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

DEBUG = True
MODE_STREAM = 0
MODE_VIDEOS = 1

class AbstractAPI:
	
	MODE = MODE_STREAM
	iProvider = "free"
	iName = "example"
	iTitle = None
	NEXT_API = None 
	NUMBER_PASS = False
	
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.SID = False
		self.packet_expire = None
	
	def start(self):
		"""Functions that runs on start, and needs exception handling"""
		pass
		
	def trace(self, msg):
		"""Use for API debug"""
		if DEBUG:
			print "[KartinaTV] %s: %s" % (self.iName, msg)

class AbstractStream(AbstractAPI):
	def __init__(self, username, password):
		AbstractAPI.__init__(self)
		self.channels = {}
	
	def setTimeShift(self, timeShift):	
		"""Some services provide timeshift. In hours"""
		pass
	
	def setChannelsList(self): 
		"""Main function for your API: load channel list here.
		   May depend on timeshift. setTimeShift() called first"""
		pass
	
	def getChannelsEpg(self, cids):
		"""Plugin call this fucntion if it wants to access epg current (and next if available)
		   of channel list <cids>.
		   Usually we call this function before show channel list"""
		pass
	
	def epgCurrent(self, cid):
		"""Plugin call this fucntion if it wants to access epg current of channel <cid>.
		   If you can download epg next also in this request, do it here to avoid future epgNext() calls"""
		pass

	def epgNext(self, cid): #do Nothing
		"""Plugin call this fucntion if it wants to access epg next of channel <cid>. 
		   Note, usually epgCurrent() was called just before."""
		pass
	
	def getDayEpg(self, cid, date = None):
		"""Plugin call this fucntion if it wants to access epg for one day of the channel <cid>."""
		#TODO: no list here! Use readable and abstract code!
		return []
	
	def getGmtEpg(self, cid):
		"""Plugin call this function if it wants to access epg that was self.aTime seconds before now.
		   If you can download epg next that was self.aTime seconds before also in this request, do it here."""
		#TODO: getGmtEpgNext() !!!!!! Also utils!
		pass
	
	def selectAll(self):
		"""You don't need to override this function"""
		services = Bouquet(Bouquet.TYPE_MENU, 'all')
		for cid in self.channels:
			ch = self.channels[cid]
			services.append(Bouquet(Bouquet.TYPE_SERVICE, cid, ch.name, ch.num )) #two sort args [channel_name, number]
		return services
	
	def selectByGroup(self):
		"""You don't need to override this function"""
		glist = {}
		groups = Bouquet(Bouquet.TYPE_MENU, 'By group')
		for cid in self.channels:
			ch = self.channels[cid]
			groupname = ch.group
			if not (groupname in glist.keys()):
				group = Bouquet(Bouquet.TYPE_MENU, groupname, ch.group, ch.gid) #two sort args [group_name, number]
				groups.append(group)
				glist[groupname] = group
			glist[groupname].append(Bouquet(Bouquet.TYPE_SERVICE, cid, ch.name, ch.num))
		return groups
