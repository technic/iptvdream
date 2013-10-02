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

global Timezone
import time
Timezone = -time.timezone / 3600
print "[KartinaTV] dreambox timezone is GMT", Timezone

def tdSec(td):
	return int(td.total_seconds())
def tdmSec(td):
	#Add +1. Timer should wait for next event until event happened exactly.
	#Otherwise inaccuracy in round may lead to mistake.
	return int(tdSec(td) * 1000)+1
def secTd(sec):
	return datetime.timedelta(sec / 86400, sec % 86400)
def tupleTd(tup):
	return secTd(tup[0]*60*60 + tup[1]*60)
	
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
		self.progDescr = ''
		if name_split:
			self.progName = name_split[0]
			if len(name_split)>1:
				self.progDescr = name_split[1]
		else:
			self.progName = name
		self.tstart = t_start
		self.tend = t_end
	
	#EPG is valid only if both tstart and tend specified!!!
	def isValid(self):
		return self.tstart and self.tend
	
	def startDefined(self):
		return self.tstart
	
	def getDuration(self):
		return tdSec(self.tend - self.tstart)

	duration = property(getDuration)
	
	def getTimePass(self, now = None):
		if not now: now = syncTime() 
		return tdSec(now-self.tstart)
	
	def getTimeLeft(self, now):
		return tdSec(self.tend - now)
	
	def getTimeLeftmsec(self, time): #More accurancy, milliseconds
		return tdmSec(self.tend-time)

	#programm is now and tstart and tend defined
	def isNow(self, t): 
		if self.isValid():
			return self.tstart <= t and t < self.tend  
		return None
	
	def get_time(self):
		return self.tend or self.tstart
	
	time = property(get_time)
	
	def __str__(self):
		return ("%s--%s %s") % (self.tstart.__str__(), self.tend.__str__(), self.progName)
	
	def __repr__(self):
		return self.__str__()

	def __cmp__(self, other):
		return int(tdSec(self.tstart - other.tstart))
		
	def __hash__(self):
		return int(time.mktime(self.tstart.timetuple()))

#TODO: some verification algoritm, if tend is None
#TODO: thread safe @decorator for future backgroud epg loader ;)
class Channel(object):
	def __init__(self, name, group, num, groupnum, archive=0):
		self.name = name
		self.group = group
		self.num = num
		self.groupnum = groupnum
		self.archive = archive
		self.q = []
		self.lastUpdateFailed = False
	
	#EPG is valid only if bouth tstart and tend specified!!!
	#in this case epgSmth() returns True
	
	#TODO: GLOBAL currently epg is stored in ram and handeld by python
	#It is for algoritm testing purpose, db backend should be implemented.
	
	def pushEpg(self, epg):
		self.pushEpgSorted([epg])
	
	def pushEpgSorted(self, epglist):
		if not epglist or len(epglist)<1:
			return

		l = len(epglist)
		for e in epglist:
			if not e.tend:
				index = epglist.index(e)
				if index < (l-1):
					e.tend = epglist[index+1].tstart
		if not len(self.q):
			self.q = epglist
			return

		s_org = set(self.q)
		s_new = set(epglist)
		# intersect existing with new
		s_common = s_org & s_new
		# substract common items from existing list
		s_org_diff = s_org - s_common
		# substract common items from the new list
		s_new_diff = s_new - s_common
		# build the new sorted list
		self.q = []
		if len(s_org_diff):
			self.q = self.q + list(s_org_diff)
		if len(s_common):
			self.q = self.q + list(s_common)
		if len(s_new_diff):
			self.q = self.q + list(s_new_diff)
		self.q.sort()

	
	#TODO: add Heuristik. continue search from last position
	#TODO: And optimisations.. binary search
	def findEpg(self, time):
		for e in self.q:
			if e.isNow(time):
				return e 
		return None
	
	def findEpgFirst(self, start, end, stype):
		"""stype=0 closer to start. stype=1 closer to end"""
		
	
	def epgCurrent(self, time = None):
		if not time: time = syncTime()
		e = self.findEpg(time)
		if e and e.isValid(): return e
	
	def epgNext(self, time = None):
		if not time: time = syncTime()
		e = self.findEpg(time)
		if e:
			index = self.q.index(e) + 1
			if index < len(self.q) and self.q[index].isValid():
				return self.q[index]
		return None

	def overlap(self, a,b,c,d):
		print "o", a, b, c, d
		if c <= a and a <= d:
			return min(b,d)-a
		elif a <= c and c <= b:
			return min(b,d)-c
		return secTd(0)

	def epgPeriod(self, start, end, duration):
		if not self.q: return []
		i=0
		for e in self.q:
			if e.time >= start:
				i = self.q.index(e)
				break
		a = i
		maxoverlap = secTd(0)
		maxoveridx = (a,a)
		print "start at", self.q[a].tstart
		while (i < len(self.q)) and self.q[i].tstart < end:
			#print self.q[i]
			if i+1 == len(self.q) or self.q[i+1].tstart >= end or self.q[i].tend != self.q[i+1].tstart:
				print i
				over = self.overlap(self.q[a].tstart, self.q[i].time, start, end)
				if over > maxoverlap:
					maxoverlap = over
					maxoveridx = (a, i)
				a = i+1
			i += 1
		if maxoverlap >= duration:
			a,b = maxoveridx
			print "length", maxoverlap
			return self.q[a:b+1]
		else:
			return []

	def epgDay(self, date):
		date = datetime.datetime(date.year, date.month, date.day)
		return self.epgPeriod(date - secTd(6*60*60), date + secTd(30*60*60), secTd(18*60*60))
		
	epg = property(fset = pushEpg)

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
		self.sortedkey = -1 #XXX: Think more!!!
		self.index = 0
	
	def append(self, entry):
		entry.parent = self
		self.__content += [entry]
	
	def extend(self, boquet):
		for entry in bouquet.content:
			self.append(entry)
	
	def remove(self, id=None):
		if not id:
			id = self.index
		del self.__content[id]
		if self.index == len(self.content):
			self.index -= 1
	
	def sortByKey(self, keyn):
		if keyn == self.sortedkey: return
		print "[KartinaTV] sorting", self.name, keyn
		if keyn == 1:
			self.__content.sort(key= attrgetter('key1'))
			self.sortedkey = keyn
		elif keyn == 2:
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
		
		self.page = 1
		self.genres = []
		self.count = 0
		self.stype = 'last'
		self.query = ''
		self.saveDbselectVal()
	
	def saveDbselectVal(self):
		self._dbval_stored = (self.page, self.genres, self.count, self.stype, self.query)
	
	def restoreDbselectVal(self):
		(self.page, self.genres, self.count, self.stype, self.query) = self._dbval_stored
		
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
			#FIXME: optimizations?? store parent_index in current?
			try:
				idx = self.current.parent.content.index(self.current)
			except ValueError:
				idx = 0
			self.current.parent.index = idx
			self.current = self.current.parent
			print "[KartinaTV] bouquet Out", self.current.name, self.current.index
		#return self.getList()
  
	def getList(self):
		return [x for x in self.current.content] #TODO: return only type and name
	
	def getCurrentSel(self):
		if len(self.current.content):
			return self.current.content[self.current.index]
	
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
		
class Video():
	def __init__(self, name):
		self.name = name
		self.name_orig = ''
		self.descr = ''
		self.image = ''
		self.year = ''
		self.rate_imdb = 0
		self.rate_kinopoisk = 0
		self.rate_mpaa = 0
		self.country = ''
		self.genre = ''
		self.length = 0
		self.director = ''
		self.scenario = ''
		self.actors = ''
		self.studio = ''
		self.awards = ''
		self.budget = ''
		self.files = []
		#TODO: set ALL fields!
		return

import re, htmlentitydefs

def unescapeEntities(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class APIException(Exception):
	def __init__(self, msg):
	  self.msg = msg
	def __str__(self):
	  return str(self.msg)

class SettEntry():
	#TODO: Is it better to use enigma2 config classes directly ?
	"""I assume that each config Entry is integer, string, or selection from list."""
	"""<name> will be returned to pushSettings as an argument"""
	"""<value> is of type int or str"""
	"""<vallist> is an array or an array of tuples (value, description)"""
	"""<limits> is for config entries of type int"""
	def __init__(self, name, value, vallist = None, limits = None):
		self.name = name
		if vallist and not len(vallist): vallist = None
		self.value = value
		if vallist:
			vallist = map(lambda x: isinstance(x, int) and str(x) or x, vallist)
		self.vallist = vallist
		self.limits = limits or (-9999, 9999)
	
	def __repr__(self):
		return "Name: %s current value: %s Available values: %s" % (self.name,  self.value, self.vallist)
