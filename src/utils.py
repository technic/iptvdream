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
			return -1
	
	def historyNext(self):
		#print "[KartinaTV]", self.history, self.historyId
		if self.historyId < self.historyEnd and self.historyId > -1:
			self.historyId += 1
			h = self.history[self.historyId]
			self.current = self.root
			self.setPath(h[0], h[1])
			return True
		else: return False
	
	def historyPrev(self):
		#print "[KartinaTV]", self.history, self.historyId
		if self.historyId > 0:
			self.historyId -= 1
			print "[KartinaTV]", self.historyId
			h = self.history[self.historyId]
			self.current = self.root
			self.setPath(h[0], h[1])
			return True
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

#Skin class
class Rect():
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.w = width
		self.h = height  
