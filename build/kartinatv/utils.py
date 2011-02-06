#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

import datetime
from operator import attrgetter

def tdSec(td):
	return td.days * 86400 + td.seconds
def secTd(sec):
	return datetime.timedelta(sec / 86400, sec % 86400)
	
print "[KartinaTV] resetting time delta !!!"
time_delta = secTd(0)
	
def setSyncTime(time):
	global time_delta
	time_delta = time-datetime.datetime.now()
	print "[KartinaTV] set time delta to", tdSec(time_delta)

def syncTime():
	#print "[KartinaTV] time delta = ", tdSec(time_delta)
	return datetime.datetime.now() + time_delta

class EpgEntry():
	def __init__(self, name, t_start, t_end):
		self.name = name #all available info
		#no \n using in List
		name_split = self.name.split('\n')
		if name_split:
			self.progName = name_split[0]
		else:
			self.progName = name
		if len(name_split)>1:
			self.progDescr = name_split[1]
		else:
			self.progDescr = ''
		self.tstart = t_start
		self.tend = t_end
	
	#EPG is valid only if bouth tstart and tend specified!!!
	def isValid(self):
		return self.tstart and self.tend
	
	def startDefined(self):
		return self.tstart
	
	def getDuration(self):
		return tdSec(self.tend - self.tstart)

	duration = property(getDuration)
	
	def getTimePass(self, delta):
		now = syncTime()+secTd(delta)
		return tdSec(now-self.tstart)
	
	def getTimeLeft(self, delta):
		now = syncTime()+secTd(delta)
		return tdSec(self.tend-now)
	
	#programm is now and tstart and tend defined
	def isNow(self, delta): 
		if self.isValid():
			return self.tstart <= syncTime()+secTd(delta) and syncTime()+secTd(delta) < self.tend  
		return None

class Channel():
	def __init__(self, name, group, num, gid, archive=0):
		self.name = name
		self.gid = gid
		self.num = num
		self.group = group
		self.archive = archive
		self.epg = None #epg for current program
		self.aepg = None #epg of archive
		self.nepg = None #epg for next program
		self.lepg = {}
		self.lastUpdateFailed = False
	
	#EPG is valid only if bouth tstart and tend specified!!!
	#in this case hasSmth returns True
	
	def hasEpg(self):
		return self.epg and self.epg.isNow(0)
	
	def hasAEpg(self, delta):
		return self.aepg and self.aepg.isNow(delta)
	
	def hasEpgNext(self):
		if self.epg and self.epg.isValid() and self.nepg and self.nepg.isValid():
			return self.epg.tend <= self.nepg.tstart and self.nepg.tstart > syncTime()
		return False
	
class Bouquet():
	TYPE_SERVICE = 0
	TYPE_MENU = 1
	sort_keys_num = 10
	def __init__(self, type, name = None, key1 = None, key2 = None):
		self.type = type
		self.parent = None
		self.__content = []
		self.name = name
		self.key1 = key1
		self.key2 = key2
		self.sortedkey = 0
		self.index = 0
	
	def append(self, entry):
		entry.parent = self
		self.__content += [entry]
	
	def remove(self, id=None):
		if not id:
			id = self.index
		del self.__content[id]
		if self.index == len(self.content):
			self.index -= 1
	
	def sortByKey(self, keyn):
		print "[KartinaTV] sorting", self.name, keyn 
		if keyn == self.sortedkey: return
		if keyn == 1:
			self.__content.sort(key= attrgetter('key1'))
			self.sortedkey = keyn
		if keyn == 2:
			self.__content.sort(key= attrgetter('key2'))
			self.sortedkey = keyn
		self.index = 0
	
	def canMoveOneUp(self):
		return self.index > 0
	
	def moveOneUp(self):
		if self.canMoveOneUp():
			tmp = self.__content[self.index]
			self.__content[self.index] = self.__content[self.index-1]
			self.__content[self.index-1] =tmp
			self.index -= 1
	
	def canMoveOneDown(self):
		return self.index < len(self.__content)-1
	
	def moveOneDown(self):
		if self.canMoveOneDown():
			tmp = self.__content[self.index]
			self.__content[self.index] = self.__content[self.index+1]
			self.__content[self.index+1] =tmp
			self.index += 1
	
	def canInsertTo(self, pos):
		return 0 <= pos and pos <= len(self.__content)
	
	def insertTo(slef, pos):
		if self.canInsertTo(pos):
			self.__content.insert(pos, slef.__content[self.index])
			if pos <= self.index:
				self.__content.pop(self.index+1)
			else:
				self.__content.pos(self.index)
	
	def getContent(self):
		return self.__content
	
	content = property(getContent)

class BouquetManager():
	
	history_len = 10
	
	def __init__(self):
		self.root = Bouquet(Bouquet.TYPE_MENU, 'root')
		self.current = self.root
		self.history = []
		self.historyId = -1
		self.historyEnd = -1
		
	def appendRoot(self, entry):
		self.root.append(entry)
	
	def goNext(self):
		self.goOut()
		self.current.index +=1
		if self.current.index == len(self.current.content):
			self.current.index = 0
		self.goIn()
		return self.getCurrent()
		
	def goPrev(self):
		self.goOut()
		self.current.index -=1
		if self.current.index == -1:
			self.current.index = len(self.current.content)-1
		self.goIn()
		return self.getCurrent()

	def goIn(self, index=None):
		if index != None:
			self.current.index = index
		if self.current.type == Bouquet.TYPE_MENU:
			self.current = self.current.content[self.current.index]
			self.current.index = 0
		print "[KartinaTV] bouquet In", self.current.name, self.current.index
		#return self.getList()
	
	def goOut(self):
		if self.current.parent:
			self.current = self.current.parent
			print "[KartinaTV] bouquet Out", self.current.name, self.current.index
		#return self.getList()
  
	def getList(self):
		return [x for x in self.current.content] #TODO: return only type and name
	
	def getCurrentSel(self):
		if len(self.current.content):
			return (self.current.content[self.current.index].name, self.current.content[self.current.index].type)
	
	def getCurrent(self):
		return self.current.name
	
	def setIndex(self, index):
		self.current.index = index
	
	def getPath(self):
		x = self.current
		path = []
		while x != self.root:
			x = x.parent
			path = [x.index] + path
		return path
	
	def getPathName(self):
		x = self.current
		path = []
		while x != self.root:
			path = [x.name] + path
			x = x.parent
		return path
	
	def setPath(self, path, cid):
		for i in path:
			if i < len(self.current.content):
				self.goIn(i)
			else:
				break;
		if self.getCurrent() != cid:
			print "[KartinaTV] service not found in path!"
			self.current = self.root
			return False
		return True
	
	def historyNext(self):
		#print "[KartinaTV]", self.history, self.historyId
		if self.historyId < self.historyEnd and self.historyId > -1:
			self.historyId += 1
			h = self.history[self.historyId]
			self.current = self.root
			return self.setPath(h[0], h[1])
		else: return False
	
	def historyPrev(self):
		#print "[KartinaTV]", self.history, self.historyId
		if self.historyId > 0:
			self.historyId -= 1
			print "[KartinaTV]", self.historyId
			h = self.history[self.historyId]
			self.current = self.root
			return self.setPath(h[0], h[1])
		else: return False
	
	#FIXME: history stack is ugly!
	def historyAppend(self):
		h = (self.getPath(), self.getCurrent())
		self.historyId += 1
		if self.historyId == self.history_len:
			self.history.pop(0)
			self.historyId -= 1
		if len(self.history) > self.historyId:
			self.history[self.historyId] = h
		else:
			self.history += [h]
		self.historyEnd = self.historyId
		#print "[KartinaTV]", self.history, self.historyId
