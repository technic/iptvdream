# -*- coding: utf-8 -*-
#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

#using external player by A. Latsch & Dr. Best (c)
#Hardly improved by technic(c) for KartinaTV/RodnoeTV compatibility and buffering possibility!!!
import servicewebts

from Plugins.Plugin import PluginDescriptor

def Plugins(path, **kwargs):
	return [ 
	PluginDescriptor(name="RodnoeTV", description="Iptv player for RodnoeTV", icon="plugin-rtv.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = ROpen),
	PluginDescriptor(name="KartinaTV", description="Iptv player for KartinaTV", icon="plugin-ktv.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = KOpen), 
	PluginDescriptor(name="KartinaTV", description="Iptv player for KartinaTV", where = PluginDescriptor.WHERE_MENU, fnc = menuktv),
	PluginDescriptor(name="RodnoeTV", description="Iptv player for RodnoeTV", where = PluginDescriptor.WHERE_MENU, fnc = menurtv) 
	]

from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger, getConfigListEntry, ConfigYesNo, ConfigSubDict, getKeyNumber, KEY_ASCII, KEY_NUMBERS
from Components.ConfigList import ConfigListScreen
import kartina_api, rodnoe_api
from Components.Label import Label
from Components.Slider import Slider
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarPlugins, InfoBarExtensions, InfoBarAudioSelection, NumberZap, InfoBarSubtitleSupport, InfoBarNotifications, InfoBarSeek
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import PinInput, InputBox
from Components.SelectionList import SelectionList
from Screens.VirtualKeyBoard import VirtualKeyBoard, VirtualKeyBoardList
from Tools.BoundFunction import boundFunction
from enigma import eServiceReference, iServiceInformation, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, gFont, eTimer, iPlayableServicePtr, iStreamedServicePtr, getDesktop, eLabel, eSize, ePoint, getPrevAsciiCode, iPlayableService
from Components.ParentalControl import parentalControl
#from threading import Thread
from Tools.LoadPixmap import LoadPixmap
#from Components.Pixmap import Pixmap
from skin import loadSkin, parseFont, colorNames, SkinError
def parseColor(str): #FIXME: copy-paste form skin source
	if str[0] != '#':
		print colorNames
		try:
			return colorNames[str]
		except:
			raise SkinError("color '%s' must be #aarrggbb or valid named color" % (str))
	return int(str[1:], 0x10)

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Components.GUIComponent import GUIComponent
from Components.Sources.Boolean import Boolean
import datetime
from utils import Bouquet, BouquetManager, tdSec, secTd, syncTime

#for localized messages
from . import _

sz_w = 0
try:
	sz_w = getDesktop(0).size().width()
	if sz_w > 1000:
		skinHD = True
	else:
		skinHD = False
	print "[KartinaTV] skin width = ", sz_w
except:
	skinHD = False
	
SKIN_PATH = '/usr/share/enigma2/KartinaTV_skin'

if skinHD:
	loadSkin(SKIN_PATH + '/kartina_skin.xml')
else:
	loadSkin(SKIN_PATH + '/kartina_skinsd.xml')

#text that contain only 0-9 characters..	
class ConfigNumberText(ConfigText):
	def __init__(self, default = ""):
		ConfigText.__init__(self, default, fixed_size = False)

	def handleKey(self, key):
		if key in KEY_NUMBERS or key == KEY_ASCII:
			if key == KEY_ASCII:
				ascii = getPrevAsciiCode()
				if not (48 <= ascii <= 57):
					return
			else:
				ascii = getKeyNumber(key) + 48
  			newChar = unichr(ascii)
			if self.allmarked:
				self.deleteAllChars()
				self.allmarked = False
			self.insertChar(newChar, self.marked_pos, False)
			self.marked_pos += 1
		else:
			ConfigText.handleKey(self, key)

	def onSelect(self, session):
		self.allmarked = (self.value != "")

	def onDeselect(self, session):
		self.marked_pos = 0
		self.offset = 0
		if not self.last_value == self.value:
			self.changedFinal()
			self.last_value = self.value

class VirtualKeyBoardRu(VirtualKeyBoard):
	def __init__(self, session, title="", text=""):
		Screen.__init__(self, session)
		self.keys_list = []
		self.shiftkeys_list = []
		self.keys_list = [
			[u"EXIT", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0", u"BACKSPACE"],
			[u"а", u"б", u"в", u"г", u"д", u"е", u"ж", u"з", u"и", u"й", u"к", u"л"],
			[u"м", u"н", u"о", u"п", u"р", u"с", u"т", u"у", u"ф", u"х", u"ц", "ч"],
			[u"ш", u"щ", u"ь", u"ы", u"ъ", u"э", u"ю", u"я", u"-", ".", u",", u"CLEAR"],
			[u"SHIFT", u"SPACE", u"OK"]]
			
		self.shiftkeys_list = [
			[u"EXIT", u"!", u'"', u"§", u"$", u"%", u"&", u"/", u"(", u")", u"=", u"BACKSPACE"],
			[u"Q", u"W", u"E", u"R", u"T", u"Z", u"U", u"I", u"O", u"P", u"*"],
			[u"A", u"S", u"D", u"F", u"G", u"H", u"J", u"K", u"L", u"'", u"?"],
			[u">", u"Y", u"X", u"C", u"V", u"B", u"N", u"M", u";", u":", u"_", u"CLEAR"],
			[u"SHIFT", u"SPACE", u"OK"]]
		
		self.shiftMode = False
		self.text = text
		self.selectedKey = 0
		
		self["header"] = Label(title)
		self["text"] = Label(self.text)
		self["list"] = VirtualKeyBoardList([])
		
		self["actions"] = ActionMap(["OkCancelActions", "WizardActions", "ColorActions"],
			{
				"ok": self.okClicked,
				"cancel": self.exit,
				"left": self.left,
				"right": self.right,
				"up": self.up,
				"down": self.down,
				"red": self.backClicked,
				"green": self.ok
			}, -2)
		
		self.onLayoutFinish.append(self.buildVirtualKeyBoard)
	
		self.max_key=47+len(self.keys_list[4])

	  

#Initialize Configuration #kartinatv
config.plugins.KartinaTv = ConfigSubsection()
config.plugins.KartinaTv.login = ConfigNumberText(default="145")
config.plugins.KartinaTv.password = ConfigNumberText(default="541")
config.plugins.KartinaTv.timeshift = ConfigInteger(0, (0,12) )
config.plugins.KartinaTv.lastroot = ConfigText(default="[]")
config.plugins.KartinaTv.lastcid = ConfigInteger(0, (0,1000))
config.plugins.KartinaTv.favourites = ConfigText(default="[]")
config.plugins.KartinaTv.usesrvicets = ConfigYesNo(default=True)
config.plugins.KartinaTv.sortkey = ConfigSubDict()
config.plugins.KartinaTv.sortkey["all"] = ConfigInteger(1, (1,2))
config.plugins.KartinaTv.sortkey["By group"] = ConfigInteger(1, (1,2))
config.plugins.KartinaTv.sortkey["in group"] = ConfigInteger(1,(1,2))
config.plugins.KartinaTv.numsonpage = ConfigInteger(20,(1,100))
config.plugins.KartinaTv.in_mainmenu = ConfigYesNo(default=True) 
#rodnoetv
config.plugins.rodnoetv = ConfigSubsection()
config.plugins.rodnoetv.login = ConfigText(default="demo", visible_width = 50, fixed_size = False)
config.plugins.rodnoetv.password = ConfigText(default="demo", visible_width = 50, fixed_size = False)
config.plugins.rodnoetv.timeshift = ConfigInteger(0, (0,12) ) ##NOT USED!!! ADDED FOR COMPATIBILITY
config.plugins.rodnoetv.lastroot = ConfigText(default="[]")
config.plugins.rodnoetv.lastcid = ConfigInteger(0, (0,1000))
config.plugins.rodnoetv.favourites = ConfigText(default="[]")
config.plugins.rodnoetv.usesrvicets = ConfigYesNo(default=True)
config.plugins.rodnoetv.sortkey = ConfigSubDict()
config.plugins.rodnoetv.sortkey["all"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.sortkey["By group"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.sortkey["in group"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.in_mainmenu = ConfigYesNo(default=False)
#buftime is general
config.plugins.KartinaTv.buftime = ConfigInteger(1500, (300,7000) ) #milliseconds!!!

def menuktv(menuid):
	if menuid == "mainmenu" and config.plugins.KartinaTv.in_mainmenu.value:
		return [("Kartina.TV", KOpen, "kartinatv", 9)]
	return []

def menurtv(menuid):
	if menuid == "mainmenu" and config.plugins.rodnoetv.in_mainmenu.value:
		return [("Rodnoe.TV", ROpen, "rodnoetv", 8)]
	return []

def KOpen(session, **kwargs):	
	print "[KartinaTV] plugin started"
	global Ktv, cfg, favouritesList, iName
	Ktv = kartina_api.Ktv
	cfg = config.plugins.KartinaTv
	iName = "KartinaTV"
	favouritesList = eval(cfg.favourites.value)
	if KartinaPlayer.instance is None: #avoid recursing
		session.open(KartinaPlayer) 
	else:
		print "[KartinaTV] error: already running!"
		return

def ROpen(session, **kwargs):
	print "[RodnoeTV] plugin started"
	global Ktv, cfg, favouritesList, iName
	Ktv = rodnoe_api.Ktv
	cfg = config.plugins.rodnoetv
	iName = "RodnoeTV"
	favouritesList = eval(cfg.favourites.value)
	if KartinaPlayer.instance is None: #avoid recursing
		session.open(KartinaPlayer) 
	else:
		print "[KartinaTV] error: already running!"
		return
	
rec_png = LoadPixmap(cached=True, path='/usr/share/enigma2/KartinaTV_skin/rec.png')
EPG_UPDATE_INTERVAL = 60 #Seconds, in channel list.
PROGRESS_TIMER = 1000*60 #Update progress in infobar.
PROGRESS_SIZE = 500
ARCHIVE_TIME_FIX = 5 #sec. When archive paused, we could miss some video
AUTO_AUDIOSELECT = True
USE_VIRTUAL_KB = 1 #XXX: not used!
POSTER_CACHE = 0
POSTER_PATH = '/hdd/'

	
def setServ():
	global SERVICE_KARTINA
	if cfg.usesrvicets.value:
		SERVICE_KARTINA = 4112 #ServiceTS
	else:
		SERVICE_KARTINA = 4097 #Gstreamer

def fakeReference(cid):
	sref = eServiceReference(4112, 0, '') #these are fake references;) #always 4112 because of parental control
	if iName == "RodnoeTV":
		sref.setData(6, 1)
	sref.setData(7, int(str(cid), 16) )
	return sref

#  Reimplementation of InfoBarShowHide
class MyInfoBarShowHide:
	STATE_HIDDEN = 0
	STATE_SHOWN = 1
	
	def __init__(self):
		self.__state = self.STATE_SHOWN

		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(5000, True)
		
		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)
		self.__locked = 0
	
	def serviceStarted(self):
		if self.execing:
			if config.usage.show_infobar_on_zap.value:
				self.doShow()

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		self.startHideTimer()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN:
			idx = config.usage.infobar_timeout.index
			if idx:
				self.hideTimer.start(idx*1000, True)

	def __onHide(self):
		self.__state = self.STATE_HIDDEN

	def doShow(self):
		self.show()
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		if self.__state == self.STATE_SHOWN:
			self.hide()

	def toggleShow(self):
		if self.__state == self.STATE_SHOWN:
			self.hide()
			self.hideTimer.stop()
		elif self.__state == self.STATE_HIDDEN:
			self.show()
	def lockShow(self):
		self.__locked = self.__locked + 1
		if self.execing:
			self.show()
			self.hideTimer.stop()

	def unlockShow(self):
		self.__locked = self.__locked - 1
		if self.execing:
			self.startHideTimer()

class KartinaPlayer(Screen, InfoBarBase, InfoBarMenu, InfoBarPlugins, InfoBarExtensions, InfoBarAudioSelection, MyInfoBarShowHide, InfoBarSubtitleSupport, InfoBarNotifications, InfoBarSeek):
	
	subtitles_enabled = False
	ALLOW_SUSPEND = True
	instance = None
	
	def __init__(self, session):
		KartinaPlayer.instance = self
		Screen.__init__(self, session)
		InfoBarBase.__init__(self, steal_current_service=True)
		InfoBarMenu.__init__(self)
		InfoBarExtensions.__init__(self)
		InfoBarPlugins.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarNotifications.__init__(self)
		MyInfoBarShowHide.__init__(self) #Use myInfoBar because image developers modify InfoBarGenerics
		InfoBarSeek.__init__(self)
		
		self.setTitle(iName)
		
		self["channelName"] = Label("")
		self["currentName"] = Label("")
		self["nextName"] = Label("")
		self["currentTime"] = Label("")
		self["nextTime"] = Label("")
		self["currentDuration"] = Label("")
		self["nextDuration"] = Label("")
		self["progressBar"] = Slider(0, PROGRESS_SIZE)
		
		self["archiveDate"] = Label("")
		self["playPause"] = Label("")
		self["KartinaInArchive"] = Boolean(False)
		
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedInfo: self.audioSelect
			})
		self.__audioSelected = False
		
		#TODO: actionmap add help.
		
		#TODO: split and disable/enable action map
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "ChannelSelectEPGActions", "InfobarChannelSelection", "InfobarActions"], 
		{
			"cancel": self.hide, 
			"green" : self.kartinaConfig,
			"red" : self.archivePvr,
			"yellow" : self.playpauseArchive,
			"zapUp" : self.previousChannel,
			"zapDown" : self.nextChannel, 
			"ok" : self.toggleShow,
			"switchChannelUp" : self.showList,  
			"switchChannelDown" : self.showList, 
			"openServiceList" : self.showList,  
			"historyNext" : self.historyNext, 
			"historyBack" : self.historyBack,
			"showEPGList" : self.showEpg,
			"showTv" : self.exit,
			"showMovies" : self.showVideoList
		}, -1)
		
		self["NumberActions"] = NumberActionMap(["NumberActions"],
			{
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal,
			})
		
		self["NumberActions"].setEnabled(False)
			
		self.setTitle(iName)		
		
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		
		self.epgTimer = eTimer()
		self.epgProgressTimer = eTimer()
		self.epgTimer.callback.append(self.epgEvent)
		self.epgProgressTimer.callback.append(self.epgUpdateProgress)
		
		#Standby notifier!!
		config.misc.standbyCounter.addNotifier(self.standbyCountChanged, initial_call = False)
		
		self.onClose.append(self.__onClose)
		self.onShown.append(self.start)


	def standbyCountChanged(self, configElement):
		from Screens.Standby import inStandby
		if bouquet and ktv.SID:
			inStandby.onClose.append(self.play) #in standby stream stops, so we need reconnect..
	
	def __onClose(self):
		KartinaPlayer.instance = None
		print "[KartinaTV] set instance to None"
	
	def start(self):		
		if self.start in self.onShown:
			self.onShown.remove(self.start)		
		setServ()
		
		self.archive_pause = 0
		self.current = 0
		self.oldcid = None
		
		print "[KartinaTV] Using service:", SERVICE_KARTINA
		
		global ktv
		ktv = Ktv(cfg.login.value, cfg.password.value)
		global bouquet
		bouquet = BouquetManager()
		try: #TODO: handle different exceptions
			ktv.start()
			ktv.setTimeShift(cfg.timeshift.value)
			ktv.setChannelsList()
		except:
			print "[KartinaTV] ERROR login/init failed!"
			self.session.openWithCallback(self.errorCB, MessageBox, _("Login or initialization failed!\nEdit options?"), type = MessageBox.TYPE_YESNO)
			return

		#init bouquets
		print "[KartinaTV] Favourites ids", favouritesList
		fav = Bouquet(Bouquet.TYPE_MENU, 'favourites')
		for x in favouritesList:
			if x in ktv.channels.keys():
				fav.append(Bouquet(Bouquet.TYPE_SERVICE, x))
		bouquet.appendRoot(ktv.sortByName())
		bouquet.appendRoot(ktv.sortByGroup())
		bouquet.appendRoot(fav)
		
		#sort bouquets #TODO: move sorting to utils
		def sortBouquet():
			for x in range(len(bouquet.getList())):
				bouquet.goIn()
				if bouquet.current.type == Bouquet.TYPE_SERVICE:
					bouquet.goOut()
					return
				n = bouquet.current.name
				if cfg.sortkey.has_key(n):
					bouquet.current.sortByKey(cfg.sortkey[n].value)
				else:
					bouquet.current.sortByKey(cfg.sortkey['in group'].value)
				if bouquet.current.type == Bouquet.TYPE_MENU:
					sortBouquet()
				bouquet.goOut()
				bouquet.current.index += 1
			bouquet.current.index = 0
		
		sortBouquet()
		bouquet.current = bouquet.root
	
		#apply parentalControl
		for x in Ktv.locked_cids: #Ktv.locked_ids:
			sref = fakeReference(x)
			print "[KartinaTV] protect", sref.toCompareString()
			parentalControl.protectService(sref.toCompareString())
		
		#startup service
		print "[KartinaTV] set path to", cfg.lastroot.value, cfg.lastcid.value
		bouquet.setPath(eval(cfg.lastroot.value), cfg.lastcid.value)
		print "[KartinaTV] now bouquet.current is", bouquet.current.name 
		if bouquet.current.type == Bouquet.TYPE_MENU:
			self.showList()
		elif bouquet.current.type == Bouquet.TYPE_SERVICE:
			self.current = bouquet.getCurrent()
			bouquet.historyAppend()
			self.play()

	def nextChannel(self):
		if ktv.aTime:
			self.session.openWithCallback(self.fwdSeekTo, MinuteInput)
		elif ktv.videomode:
			pass
		else:
			self.current = bouquet.goNext()
			bouquet.historyAppend()
			self.switchChannel()
			
	def previousChannel(self):
		if ktv.aTime:
			self.session.openWithCallback(self.rwdSeekTo, MinuteInput)
		elif ktv.videomode:
			pass
		else:
			self.current = bouquet.goPrev()
			bouquet.historyAppend()
			self.switchChannel()
	
	#FIXME: history and channel zapping forget archive position!   
	def historyNext(self):
		if ktv.videomode:
			return
		if bouquet.historyNext():
			self.current = bouquet.getCurrent()
			self.switchChannel()
	
	def historyBack(self):
		if ktv.videomode:
			pass
		if bouquet.historyPrev():
			self.current = bouquet.getCurrent()
			self.switchChannel()
	
	def fwdSeekTo(self, minutes):
		print "[KartinaTV] Seek", minutes, "minutes forward"
		ktv.aTime += minutes*60
		self.play()

	def rwdSeekTo(self, minutes):
		print "[KartinaTV] rwdSeekTo", minutes
		ktv.aTime -= minutes*60
		self.play()
		
	def playpauseArchive(self):
		if ktv.aTime: #Check if we in archive #TODO: Enable and disable play-pause action map on starting and stoping archive 
			if self.archive_pause: #do unpause
				ktv.aTime -= tdSec(syncTime()-self.archive_pause)-ARCHIVE_TIME_FIX 
				self.archive_pause = None
				self.play()
			else: #do pause
				self.archive_pause = syncTime()
				self.session.nav.stopService()
		elif ktv.videomode:
			#TODO: implement pause
			pass
		else:
			self.archive_pause = None
	
	def play(self): #check parental control		
		print "[KartinaTV] access channel id=", self.current 
		cid = self.current
		#if cid not changed (probably we are in  archive)
		if cid == self.oldcid:
			self.startPlay() 
			return
		self.session.nav.stopService()
		
		#Use many hacks, because it's no possibility to change enigma :(
		#fake reference has no path and used for parental control
		fakeref = fakeReference(cid)
		print fakeref.toCompareString()
		if parentalControl.isServicePlayable(fakeref, boundFunction(self.startPlay)):
			self.startPlay()
		else:
			self["channelName"].setText(ktv.channels[cid].name)
			self.epgEvent()	

	def startPlay(self, **kwargs):
		print "[KartinaTV] play channel id=", self.current 
		cid = self.current
		self.oldcid = cid
		try:
			uri = ktv.getStreamUrl(cid)
		except:
			print "[KartinaTV] Error: getting stream uri failed!"
			self.session.open(MessageBox, _("Error while getting stream uri"), type = MessageBox.TYPE_ERROR, timeout = 5)
			return -1
		srv = SERVICE_KARTINA
		if not uri.startswith('http://'):
			srv = 4097
		sref = eServiceReference(srv, 0, uri) 
		sref.setData(7, int(str(cid), 16) ) #picon hack.
		if iName == "RodnoeTV":
			sref.setData(6,1) #again hack;)	
		
		#self.session.nav.stopService() #FIXME: do we need it?? some bugs in servicets?
		self.session.nav.playService(sref) 
		self.__audioSelected = False
		self["channelName"].setText(ktv.channels[cid].name)
		self.epgEvent()	

	
	def epgEvent(self):
		#first stop timers
		self.epgTimer.stop()
		self.epgProgressTimer.stop()
		cid = self.current
		
		#EPG is valid only if bouth tstart and tend specified!!! Check API.
		
		def setEpgCurrent():
			if ktv.aTime:
				if not ktv.channels[cid].hasAEpg(ktv.aTime): return False
				curr = ktv.channels[cid].aepg
			else:
				if not  ktv.channels[cid].hasEpg(): return False
				curr = ktv.channels[cid].epg
			
			self.currentEpg = curr
			self["currentName"].setText(curr.name)
			self["currentTime"].setText(curr.tstart.strftime("%H:%M"))
			self["nextTime"].setText(curr.tend.strftime("%H:%M"))
			self.epgTimer.start(curr.getTimeLeft(ktv.aTime)*1000 ) #milliseconds
			self["currentDuration"].setText("+%d min" % (curr.getTimeLeft(ktv.aTime) / 60) )
			self["progressBar"].setValue(PROGRESS_SIZE * curr.getTimePass(ktv.aTime) / curr.duration)
			self.epgProgressTimer.start(PROGRESS_TIMER)
			if ktv.aTime:
				self["archiveDate"].setText(curr.tstart.strftime("%d.%m"))
				self["archiveDate"].show()
			else:
				self["archiveDate"].hide()
			return True
		
		if not setEpgCurrent():
			try:
				if ktv.aTime:
					ktv.getGmtEpg(cid)
				else:
					ktv.getChannelsEpg([cid])
			except:
				print "[KartinaTV] ERROR load epg failed! cid =", cid, bool(ktv.aTime)		
			if not setEpgCurrent():	
				self["currentName"].setText('')
				self["currentTime"].setText('')
				self["nextTime"].setText('')
				self["currentDuration"].setText('')
				self["progressBar"].setValue(0)	
				
		def setEpgNext():
			if ktv.aTime: return False
			if ktv.channels[cid].hasEpgNext():
				next = ktv.channels[cid].nepg
				self['nextName'].setText(next.name)
				self['nextDuration'].setText("%d min" % (next.duration/ 60))
				return True
			return False
		
		if not setEpgNext():
			try:
				ktv.epgNext(cid)
			except:
				print "[KartinaTV] load epg next failed!"
			if not setEpgNext():
				self["nextName"].setText('')
				self["nextDuration"].setText('')
						
		self.serviceStarted() #ShowInfoBar #FIXME: only if focused
		
	def epgUpdateProgress(self):
		self["currentDuration"].setText("+%d min" % (self.currentEpg.getTimeLeft(ktv.aTime)/60) )
		self["progressBar"].setValue(PROGRESS_SIZE * self.currentEpg.getTimePass(ktv.aTime) / self.currentEpg.duration)
		self.epgProgressTimer.start(PROGRESS_TIMER)
	
	
	def archivePvr(self):
		if ktv.aTime:
			self.switchChannel()
		elif ktv.videomode:
			ktv.videomode = False
			if ktv.aTime:
				self.playpauseArchive()
			else:
				self.play()
		else:
			return #Videothek disabled now
			ktv.videomode = True
			if ktv.videomode: #Api can not allow to set videomode, because it isn't available. 
				self.showVideoList()

	def showVideoList(self):
		self.session.openWithCallback(self.showVideoCB, KartinaVideoList)
	
	def switchChannel(self):
		self["KartinaInArchive"].setBoolean(False)
		ktv.aTime = 0
		self.play()
	
	def showList(self):
		if ktv.videomode:
			self.showVideoList()
		else:	
			self.session.openWithCallback(self.showListCB, KartinaChannelSelection)
	
	def showListCB(self, changed=False, time = None):
		if time:
			print "[KartinaTV] list returned archive" 
			self.showEpgCB(time)
			return
		elif changed:
			self.current = bouquet.getCurrent()
			bouquet.historyAppend()
			self.switchChannel()
			
	def errorCB(self, edit = False):
		if edit:
			self.kartinaConfig()
		else:
			self.exit()
			
	def showEpg(self):
		self.session.openWithCallback(self.showEpgCB, KartinaEpgList, self.current)
	
	def showEpgCB(self, time= None):
		if time:
			self.current = bouquet.getCurrent()
			ktv.aTime = tdSec(time-syncTime()) #aTime < 0
			self["KartinaInArchive"].setBoolean(True)
			self.play()
	
	def showVideoCB(self, vid= None):
		if vid:
			ktv.videomode = True
			if ktv.aTime:
				self.playpauseArchive()
			else:
				pass #stop stream
			self.vid = vid
			self.playVideo()
		else:
			ktv.videomode = False
	
	def playVideo(self):
		print "[KartinaTV] play video id=", self.vid 
		vid = self.vid
		#TODO: seeking in c++ part
		try:
			uri = ktv.getVideoUrl(vid)
		except:
			print "[KartinaTV] Error: getting video uri failed!"
			self.session.open(MessageBox, _("Error while getting video uri"), type = MessageBox.TYPE_ERROR, timeout = 5)
			return -1
		sref = eServiceReference(4097, 0, uri) #TODO: 4112 
		#self.session.nav.stopService() #FIXME: do we need it?? some bugs in servicets?
		self.session.nav.playService(sref)
		self["channelName"].setText(ktv.filmFiles[vid]['title'])
	
	def kartinaConfig(self):
		self.session.openWithCallback(self.restart, KartinaConfig)

	def restart(self, config_changed):
		if config_changed:
			self.session.nav.stopService()
			self.start()
		elif not ktv.SID:
			self.exit()
	
	def exit(self):
		self.session.nav.stopService()
		self.session.nav.playService(self.oldService)
		if bouquet:
			cfg.lastroot.value = str(bouquet.getPath())
			cfg.lastcid.value = self.current
			print "[KartinaTV] save path", cfg.lastroot.value, cfg.lastcid.value
			cfg.lastroot.save()
			cfg.lastcid.save()
			cfg.favourites.value = str(favouritesList)
			cfg.favourites.save()
			cfg.sortkey.save()
			if iName == "KartinaTV":
				cfg.numsonpage.save()
		print "[KartinaTV] exiting"
		self.close()
	
	def generate_error(self):
		print "[KartinaTV] User generate error for debug"
		raise Exception("User generate error to view log")
	
	def runPlugin(self, plugin):
		try:
			plugin(session = self.session)
		except:
			self.session.open(MessageBox, _("You can't run this plugin in KartinaTV mode"), MessageBox.TYPE_ERROR)
	
	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number)
	
	def numberEntered(self, num):
		if num > 0:
			lastroot = bouquet.current
			bouquet.current = bouquet.root
			bouquet.goIn(2)
			num -= 1 #True enumeration starts from zero :)
			if num < len(bouquet.current.content):
				bouquet.setIndex(num)
				bouquet.goIn()
				self.current = bouquet.getCurrent()
				bouquet.historyAppend()
				self.switchChannel()
			else:
				bouquet.current = lastroot
	
	def audioSelect(self):
		print "[KartinaTV] event audio select"
		if self.__audioSelected or not AUTO_AUDIOSELECT: return
		self.__audioSelected = True
		service = self.session.nav.getCurrentService()
		audio = service and service.audioTracks()
		n = audio and audio.getNumberOfTracks() or 0
		if n > 0:
			selectedAudio = audio.getCurrentTrack()
			for x in range(n):
				language = audio.getTrackInfo(x).getLanguage()
				print "[KartinaTV] scan langstr:", x, language
				if language.find('rus') > -1 and x != selectedAudio:
					if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > x:
						audio.selectTrack(x)
						break
										

				
#TODO: BouquetManager guiContent. Don't recreate and refill ChannelSelection if possible
class ChannelList(MenuList):
	
	def __init__(self):
		MenuList.__init__(self, [], content = eListboxPythonMultiContent)
		self.col = {}
		
		self.pixmapProgressBar = None
		self.pixmapArchive = None
		self.itemHeight = 28
		self.l.setFont(0, parseFont("Regular;22", ((1,1),(1,1))) )
		self.l.setFont(1, parseFont("Regular;18", ((1,1),(1,1))) )
		self.l.setFont(2, parseFont("Regular;20", ((1,1),(1,1))) )
		self.num = 0
		
		for x in ["colorEventProgressbar", "colorEventProgressbarSelected", "colorEventProgressbarBorder", "colorEventProgressbarBorderSelected", "colorServiceDescription", "colorServiceDescriptionSelected"]:
			self.col[x] = None
	
	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.showEpgProgress = config.usage.show_event_progress_in_servicelist.value
		#Can't access eTextPara directly :(
		self.fontCalc = [eLabel(self.instance), eLabel(self.instance), eLabel(self.instance)]
		self.fontCalc[0].setFont(parseFont("Regular;22", ((1,1),(1,1))) )
		self.fontCalc[1].setFont(parseFont("Regular;18", ((1,1),(1,1))) )
		self.fontCalc[2].setFont(parseFont("Regular;20", ((1,1),(1,1))) )
		
		
	def applySkin(self, desktop, parent):
		if self.skinAttributes is not None:
			attribs = [ ]
			for (attrib, value) in self.skinAttributes:
#				if attrib == "foregroundColorMarked":
#					self.col[attrib] = parseColor(value)
#				elif attrib == "foregroundColorMarkedSelected":
#					self.col[attrib] = parseColor(value)
#				elif attrib == "backgroundColorMarked":
#					self.col[attrib] = parseColor(value)
#				elif attrib == "backgroundColorMarkedSelected":
#					self.col[attrib] = parseColor(value)
#				elif attrib == "foregroundColorServiceNotAvail":
#					self.col[attrib] = parseColor(value)
				if attrib == "colorEventProgressbar":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarBorder":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarBorderSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServiceDescription":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServiceDescriptionSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "picServiceEventProgressbar":
					pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
					if pic:
						self.pixmapProgressBar = pic
				elif attrib == "picServiceArchive":
					pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
					if pic:
						self.pixmapArchive = pic
				elif attrib == "serviceItemHeight":
					self.itemHeight = int(value)
				elif attrib == "serviceNameFont":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))) )
					self.fontCalc[0].setFont( parseFont(value, ((1,1),(1,1))) )
				elif attrib == "serviceInfoFont":
					self.l.setFont(1, parseFont(value, ((1,1),(1,1))) )
					self.fontCalc[1].setFont( parseFont(value, ((1,1),(1,1))) )
				elif attrib == "serviceNumberFont":
					self.l.setFont(2, parseFont(value, ((1,1),(1,1))) )
					self.fontCalc[2].setFont( parseFont(value, ((1,1),(1,1))) )
				else:
					attribs.append((attrib, value))
					
		self.skinAttributes = attribs
		res = GUIComponent.applySkin(self, desktop, parent)
		
		self.l.setItemHeight(self.itemHeight)
		self.itemWidth = self.instance.size().width()
		for x in self.fontCalc:
			#resize and move away.			
			x.resize(eSize(self.itemWidth, self.itemHeight)) #?
			x.move(ePoint(int(self.instance.size().width()+10), int(self.instance.size().height()+10)))
			x.setNoWrap(1)
		return res
	
	def setEnumerated(self, enumerated):
		if enumerated:
			self.num = 1
		else:
			self.num = 0
	
	def setList(self, list):
		self.l.setList(map(self.buildChannelEntry, list))
		if self.num:
			self.num = 1
	
	def calculateWidth(self, text, font):
		self.fontCalc[font].setText(text)
		return self.fontCalc[font].calculateSize().width()
	
	
	def buildChannelEntry(self, entry):
		defaultFlag = RT_HALIGN_LEFT | RT_VALIGN_CENTER
		if entry.type == Bouquet.TYPE_MENU:
			return [
				(entry.name),
				( eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.itemWidth, self.itemHeight, 0, defaultFlag, entry.name )]
		
		#Filling from left to rigth
		elif entry.type == Bouquet.TYPE_SERVICE:
			
			cid = entry.name
			lst = [(cid)]
			xoffset = 1
			
			if self.num:
				xoffset += 55
				text = str(self.num)
				lst += [(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, xoffset-5, self.itemHeight, 2, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text )]
				self.num += 1
			
			if self.pixmapArchive: 
				width = self.pixmapArchive.size().width()
				height = self.pixmapArchive.size().height()
				if ktv.channels[cid].archive:
					lst += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, xoffset, (self.itemHeight-height)/2, width, height, self.pixmapArchive)]  	
				xoffset += width+5
				
			if self.showEpgProgress: 
				width = 52
				height = 6
				if ktv.channels[cid].hasEpg():
					percent = 100*ktv.channels[cid].epg.getTimePass(0) / ktv.channels[cid].epg.duration
					lst += [(eListboxPythonMultiContent.TYPE_PROGRESS, xoffset+1, (self.itemHeight-height)/2, width, height, percent, 0, self.col['colorEventProgressbar'], self.col['colorEventProgressbarSelected'] ),
							(eListboxPythonMultiContent.TYPE_PROGRESS, xoffset, (self.itemHeight-height)/2 -1, width+2, height+2, 0, 1, self.col['colorEventProgressbarBorder'], self.col['colorEventProgressbarBorderSelected'] )]	
				xoffset += width+7
			
			#skin_local colors...
			text = str(ktv.channels[cid].name)
			width = self.calculateWidth(text, 0)
			lst += [(eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width, self.itemHeight, 0, defaultFlag, text )]
			xoffset += width+10
			
			if ktv.channels[cid].hasEpg():
				text = '(%s)' % ktv.channels[cid].epg.progName #sholdn't contain \n
				#width = self.calculateWidth(text, 1)
				lst += [(eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, self.itemWidth, self.itemHeight, 1, defaultFlag, text, self.col['colorServiceDescription'], self.col['colorServiceDescriptionSelected'] )]
			
			return lst
	
class KartinaChannelSelection(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_red"] = Button(_("All"))
		self["key_green"] = Button(_("Groups"))
		self["key_yellow"] = Button(_("Add"))
		self["key_blue"] = Button(_("Favourites"))
		
		self["list"] = ChannelList()
		self.list = self["list"]
		
		self["epgName"]=Label("")
		self["epgTime"]=Label("")
		self["epgDiscription"] = Label("")
		self["channelName"]=Label()
		self["epgProgress"]=Slider(0, 100)
		self["epgNextTime"]=Label()
		self["epgNextName"]=Label()
		self["epgNextDiscription"]=Label()
		
		self["packetExpire"] = Label()
		if ktv.packet_expire:
			self["packetExpire"].setText(_("Expire on")+" "+ktv.packet_expire.strftime('%d.%m %H:%M'))		
		
		self["actions"] = ActionMap(["OkCancelActions", "ChannelSelectBaseActions", "DirectionActions", "ChannelSelectEditActions", "ChannelSelectEPGActions"], 
		{
			"cancel": self.exit,
			"ok" : self.ok,
			"showAllServices" : self.showAll,
			"showSatellites" : self.showByGroup,
			"showProviders" : self.addremoveFavourites,
			"showFavourites" : self.showFavourites,
			"contextMenu" : self.showMenu,
			"showEPGList" : self.showEpgList,
			"nextBouquet" : self.nextBouquet,
			"prevBouquet" : self.prevBouquet
		}, -1)
		
		self.list.onSelectionChanged.append(self.selectionChanged)
		self.lastroot = bouquet.current
		self.editMode = False
		self.editMoving = False
		self.lastEpgUpdate = None
		#need to create GUI first for changing it's parameters later
		#for example list.moveToIndex don't work otherwise		  
		self.onLayoutFinish.append(self.start)
		
		
	def start(self):
		if bouquet.root == bouquet.current:
			print "[KartinaTV] lastroot not found show All"
			self.showByGroup()
		else:
			bouquet.goOut()
			self.fillList()
	
	def ok(self):
		if self.editMode:
			self.editMoving = not self.editMoving
			self.lastIndex = self.list.getSelectionIndex()
			return
		bouquet.goIn()
		if bouquet.current.type == Bouquet.TYPE_SERVICE:
			print "[KartinaTV] ChannelSelection close"
			self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
			self.close(True)
		elif bouquet.current.type == Bouquet.TYPE_MENU:
			self.fillList()
	
	def exit(self):
		self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
		if self.lastroot.type == Bouquet.TYPE_MENU:
			self.showAll()
			bouquet.goIn() #FIXME: if user really want select None
			print "[KartinaTV] ChannelSelection selected None so set default"
			self.close(True)
		else:
			bouquet.current = self.lastroot
			self.close(False)
	
	def fillList(self):
		#FIXME: optimizations? Autoupdate.
		uplist = []
		
		timeout = not self.lastEpgUpdate or syncTime() - self.lastEpgUpdate > secTd(EPG_UPDATE_INTERVAL)
		for x in ktv.channels.keys():
			if isinstance(x, int):
				if (not ktv.channels[x].hasEpg()) and (not ktv.channels[x].lastUpdateFailed or timeout):
					uplist += [x]
		if uplist: 
			try:
				ktv.getChannelsEpg(uplist)
				self.lastEpgUpdate = syncTime()
			except:
				print "[KartinaTV] failed to get epg for uplist"
		
		self.setTitle(iName+" / "+" / ".join(map(_, bouquet.getPathName())) )
	
		self.fillingList = True #simple hack
		if bouquet.current.name == 'favourites':
			self["key_yellow"].setText(_("Delete"))
			self.list.setEnumerated(1)
			self.list.setList(bouquet.getList())
		else:
			self["key_yellow"].setText(_("Add"))
			n = bouquet.current.name
			if cfg.sortkey.has_key(n):
				bouquet.current.sortByKey(cfg.sortkey[n].value)
			else:
				bouquet.current.sortByKey(cfg.sortkey['in group'].value)
			self.list.setEnumerated(0)
			self.list.setList(bouquet.getList())
		self.list.moveToIndex(bouquet.current.index)
		self.fillingList = False
		self.selectionChanged()
		
	def showByGroup(self):
		if self.editMode: return
		if bouquet.current.parent == None or bouquet.current.parent == bouquet.root:
			bouquet.current = bouquet.root
			bouquet.goIn(1)
		else:
			bouquet.goOut()
		self.fillList()
	
	def showAll(self):
		if self.editMode: return
		bouquet.current = bouquet.root
		bouquet.goIn(0)
		self.fillList()
		
	def showFavourites(self):
		if self.editMode: return
		bouquet.current = bouquet.root
		bouquet.goIn(2)
		self.fillList()
	
	def nextBouquet(self):
		if self.editMode: return
		print bouquet.current.name, bouquet.current.parent.name
		if bouquet.current.parent.name != 'By group': return 
		bouquet.goNext()
		self.fillList()	

	def prevBouquet(self):
		if self.editMode: return
		if bouquet.current.parent.name != 'By group': return
		bouquet.goPrev()
		self.fillList()
	
	def addremoveFavourites(self):
		if self.editMode: return
		global favouritesList
		bouquet.setIndex(self.list.getSelectionIndex())
		curr = bouquet.getCurrentSel()
		if curr:
			(cid, type) = curr
			if bouquet.getCurrent() == 'favourites':
				bouquet.current.remove()
				favouritesList.remove(cid)
				self.showFavourites()
			else:
				if type == Bouquet.TYPE_SERVICE:
					favouritesList += [cid]
					bouquet.root.content[2].append(Bouquet(Bouquet.TYPE_SERVICE, cid))
			print "[KartinaTV] Now favouritesList is:", favouritesList
		
	def selectionChanged(self):
		if self.fillingList: return			#simple hack
		idx = self.list.getSelectionIndex()
		if self.editMoving and self.lastIndex != idx:
			print "[KartinaTV] moving entry", idx
			if self.lastIndex > idx:
				bouquet.current.moveOneUp()
			else:
				bouquet.current.moveOneDown()
			self.lastIndex = idx
			self.fillList() #TODO: optimize!!!
		bouquet.setIndex(self.list.getSelectionIndex())
		self.updateEpgInfo()
				
	def updateEpgInfo(self):		
		print "[KartinaTV]", bouquet.current.index, bouquet.current.name
		curr = bouquet.getCurrentSel()
		type = None
		if curr:
			(cid, type) = curr
		if type == Bouquet.TYPE_SERVICE:
			self["channelName"].setText(ktv.channels[cid].name)
			self["channelName"].show()
			if ktv.channels[cid].hasEpg():
				curr = ktv.channels[cid].epg
				self["epgTime"].setText("%s - %s" % (curr.tstart.strftime("%H:%M"), curr.tend.strftime("%H:%M")))
				self["epgName"].setText(curr.progName)
				self["epgName"].show()
				self["epgTime"].show()
				self["epgProgress"].setValue(100*curr.getTimePass(0) / curr.duration) #Not ktv.aTime but zero
				self["epgProgress"].show()
				self["epgDiscription"].setText(curr.progDescr)
				self["epgDiscription"].show()
			else:
				self.hideEpgLabels()
			if ktv.channels[cid].hasEpgNext():
				curr = ktv.channels[cid].nepg
				self["epgNextTime"].setText("%s - %s" % (curr.tstart.strftime("%H:%M"), curr.tend.strftime("%H:%M")))
				self["epgNextName"].setText(curr.progName)
				self["epgDiscription"].setText(curr.progDescr)
				self["epgNextName"].show()
				self["epgNextTime"].show()
				self["epgDiscription"].show()
			else:
				self.hideEpgNextLabels()
			
		else:
			self["channelName"].setText("")
			self.hideEpgLabels()
			self.hideEpgNextLabels()
	
	def hideEpgLabels(self):
		self["epgName"].hide()
		self["epgTime"].hide()
		#self["channelName"].hide()
		self["epgProgress"].hide()
		self["epgDiscription"].hide()
	
	def hideEpgNextLabels(self):
		self["epgNextName"].hide()
		self["epgNextTime"].hide()	
	
	def showMenu(self):
		lst = []
		if bouquet.current.name != 'favourites':
			lst += [(_("Sort by name"), 1),
				   (_("Sort by default"), 2)]
		curr = bouquet.getCurrentSel()
		if curr and curr[1] == Bouquet.TYPE_SERVICE and config.ParentalControl.configured.value:
			cid = curr[0]
			if parentalControl.getProtectionLevel(fakeReference(cid).toCompareString()) == -1:
				lst += [( _("add to parental protection"), 'add')]
			else:
				lst += [( _("remove from parental protection"), 'rm')]
		if bouquet.current.name == 'favourites':
			if not self.editMode:
				lst += [( _("Enter edit mode"), 'start_edit')]
			else:
				lst += [( _("Exit edit mode"), 'stop_edit')]
		self.session.openWithCallback(self.showMenuCB, ChoiceBox, _("Context menu"), lst )
	
	def showMenuCB(self, entry = None):
		if entry is None: return
		entry = entry[1]
		global favouritesList
		print "[KartinaTV] sort type is", entry
		if (entry in [1,2]):			
			n = bouquet.current.name
			print "[KartinaTV] sorting", n
			if n != 'favourites':
				if cfg.sortkey.has_key(n):
					cfg.sortkey[n].value = entry
				else:
					cfg.sortkey['in group'].value = entry
				bouquet.current.sortByKey(entry)
	
			self.fillList()
		elif entry == 'add':
			service = fakeReference(bouquet.getCurrentSel()[0])
			parentalControl.protectService(service.toCompareString())
		elif entry ==  'rm':
			service = fakeReference(bouquet.getCurrentSel()[0])
			self.session.openWithCallback(
			  boundFunction(self.pinEntered, service.toCompareString()), PinInput, pinList =
			  [config.ParentalControl.servicepin[0].value], triesEntry = config.ParentalControl.retries.servicepin, title = _("Enter the service pin"),
			  windowTitle = _("Change pin code"))
		elif entry == 'start_edit':
			self.editMode = True
		elif entry == 'stop_edit':
			self.editMode = False
			self.editMoving = False
			favouritesList = [x.name for x in bouquet.getList()]
			print "[KartinaTV] now fav are:", favouritesList
			self.fillList()

	def pinEntered(self, service, result):
		if result:
			parentalControl.unProtectService(service)
			self.exit()
		else:
			self.session.openWithCallback(self.exit, MessageBox, _("The pin code you entered is wrong."), MessageBox.TYPE_ERROR)
	
	def showEpgList(self):
		if self.editMode: return
		(id, type) =  bouquet.getCurrentSel()
		if type == Bouquet.TYPE_SERVICE:
			self.session.openWithCallback(self.showEpgCB, KartinaEpgList, id)
	
	def showEpgCB(self, time=None):
		print "[KartinaTV] showEpgCB", time
		if time:
			bouquet.goIn()
			self.close(False, time)
	 
		
class KartinaEpgList(Screen):
		
	def __init__(self, session, current):
		Screen.__init__(self, session)
		
		self["key_red"] = Button(_("Archive"))
		self["key_green"] = Button(_("Fully"))
		self["key_yellow"] = Button("")
		self.list = MenuList([], content = eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", 20))
		self.list.l.setFont(1, gFont("Regular", 20))
		self.list.l.setItemHeight(28)
		self["list"] = self.list
		self["epgName"] = Label()
		self["epgDiscription"] = Label()
		self["epgTime"] = Label()
		self["epgDuration"] = Label()
		
		self["sepgName"] = Label()
		self["sepgDiscription"] = Label()
		self["sepgTime"] = Label()
		self["sepgDuration"] = Label()
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "EPGSelectActions"], 
		{
			"cancel": self.exit,
			"red" : self.archive,
			"ok": self.archive,
		#	"yellow": self.selectChannel,
			"nextBouquet" : self.nextDay,
			"prevBouquet" :self.prevDay,
			"green" : self.showSingle
		}, -1)		
		self.lastroot = bouquet.current
		self.current = current
		self.day = 0
		self.single = False
		self.epgDownloaded = False
		self.list.onSelectionChanged.append(self.updateEpg)
		self.onLayoutFinish.append(self.fillList)
	
	def kartinaEpgEntry(self, entry):
		res = [
			(entry),
			(eListboxPythonMultiContent.TYPE_TEXT, 18, 2, 30, 22, 0, RT_HALIGN_LEFT, _(entry[0].strftime('%a')) ), 
			(eListboxPythonMultiContent.TYPE_TEXT, 50, 2, 90, 22, 0, RT_HALIGN_LEFT, entry[0].strftime('%H:%M')),
			(eListboxPythonMultiContent.TYPE_TEXT, 130, 2, 595, 24, 1, RT_HALIGN_LEFT, entry[1])]
		if ktv.channels[self.current].archive and entry[0] < syncTime():
			res += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 5, 16, 16, rec_png)]
		return res
		
	def fillList(self):
		self.hideLabels("s%s")
		self.list.show()
		if self.epgDownloaded: return
		d = syncTime()+datetime.timedelta(self.day)
		try:
			epglist = ktv.getDayEpg(self.current, d)
		except:
			print "[KartinaTV] load day epg failed cid = ", self.current
			return
		self.list.setList(map(self.kartinaEpgEntry, epglist))
		self.setTitle("EPG / %s / %s %s" % (ktv.channels[self.current].name, d.strftime("%d"), _(d.strftime("%b")) ))
		x = 0
		for x in xrange(len(epglist)):
			if epglist[x][0] and (epglist[x][0] > syncTime()):
				break
		if x > 0: x-=1
		self.list.moveToIndex(x)
		self.epgDownloaded = True
		#self.ok()
	
	def selectChannel(self):
		self.session.openWithCallback(self.currentChanged, KartinaChannelSelection)
	
	def currentChanged(self, changed):
		if changed:
			self.current = bouquet.getCurrent()
			self.day = 0
			self.single = False
			self["key_green"].setText(_("Fully"))
			self.fillList() #FIXME: too many show-hide-show-hide.
	
	def updateEpg(self):
		self.fillEpgLabels()
	
	def fillEpgLabels(self, s = "%s"):
		idx = self.list.getSelectionIndex()
		if len(self.list.list):
			entry = self.list.list[idx][0]
			self[s % "epgName"].setText(entry[1])
			self[s % "epgTime"].setText(entry[0].strftime("%d.%m %H:%M"))
			self[s % "epgDiscription"].setText(entry[2])
			self[s % "epgDiscription"].show()
			self[s % "epgName"].show()
			self[s % "epgTime"].show()
			if len(self.list.list) > idx+1:
				next = self.list.list[idx+1][0]
				self[s % "epgDuration"].setText("%s min" % (tdSec(next[0]-entry[0])/60))
				self[s % "epgDuration"].show()
			else:
				self[s % "epgDuration"].hide()
	
	def hideLabels(self, s = "%s"):
		print "hide", s
		self[s % "epgName"].hide()
		self[s % "epgTime"].hide()
		self[s % "epgDuration"].hide()
		self[s % "epgDiscription"].hide()
		
	def showSingle(self):
		if not self.single:
			self["key_green"].setText("")
			self.single = True
			self.hideLabels()
			self.list.hide()
			self.fillEpgLabels("s%s")
	
	def archive(self):
		idx = self.list.getSelectionIndex()
		if len(self.list.list) > idx:
			if ktv.channels[self.current].archive:
				self.close(self.list.list[idx][0][0])
	
	def exit(self):
		if self.single: #If single view then go to list. Else close all
			self.single = False
			self["key_green"].setText(_("Fully"))
			self.fillList()
			self.fillEpgLabels()
			return
		bouquet.current = self.lastroot
		self.close()
	
	def nextDay(self):
		if self.single: return
		self.day+=1
		self.epgDownloaded = False
		self.fillList()
	
	def prevDay(self):
		if self.single: return
		self.day-=1
		self.epgDownloaded = False
		self.fillList()

class multiListHandler():
    def __init__(self, menu_lists):
	self.count = len(menu_lists)
	self.curr = menu_lists[0]
	self.lists = menu_lists
	self.is_selection = False
	
	self["multiActions"] = ActionMap(["DirectionActions"], 
	{
	    "right": self.doNothing,
	    "rightRepeated": self.doNothing,
	    "rightUp": self.pageDown,
	    "left": self.doNothing,
	    "leftRepeated": self.doNothing,
	    "leftUp": self.pageUp,
	    
	    "up": self.up,
	    "upRepeated": self.up,
	    "upUp": self.doNothing,
	    "down": self.down,
	    "downRepeated": self.down,
	    "downUp": self.doNothing,
	}, -2)
    
    def doNothing(self): #moves away annoing messages in log
	pass
    
    def selectList(self, curr):
	self.curr = curr
	for i in self.lists:
	    self[i].selectionEnabled(0)
	self[self.curr].selectionEnabled(1)
	self.is_selection = isinstance(self[self.curr], SelectionList)
	print "[KartinaTV] select list", self.curr, "selection", self.is_selection
    
    def ok(self): #returns if selection action applied
	if self.is_selection:
	    self[self.curr].toggleSelection()
	    return True
	return False
    
    def down(self):
	    self[self.curr].down()
    
    def up(self):
	    self[self.curr].up()
    
    def pageDown(self):
	    self[self.curr].pageDown()
    
    def pageUp(self):
	    self[self.curr].pageUp()


class KartinaVideoList(Screen, multiListHandler):
	
	MODE_MAIN = 0 
	MODE_GENRES = 1

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_red"] = Button(_("Last"))
		self["key_green"] = Button(_("Genres"))
		self["key_yellow"] = Button(_("Search"))
		self["key_blue"] = Button(_("Best"))
		self.list = MenuList([], enableWrapAround=True, content = eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", 20))
		self.list.l.setItemHeight(28)
		self["list"] = self.list
		
		self.glist = SelectionList()
		self.glist.l.setFont(0, gFont("Regular", 20))
		self.glist.l.setItemHeight(28)
		self["glist"] = self.glist
		self.currList = "list"
		
		multiListHandler.__init__(self, ["list", "glist"])
		
		self["name"] = Label()
		self["description"] = Label()
		self["year"] = Label()
		
		self["sname"] = Label()
		self["sdescription"] = Label()
		self["syear"] = Label()
		self["rate1"] = Slider(0, 100) 
		self["rate2"] = Slider(0, 100)
		self["rate1_back"] = Pixmap()
		self["rate2_back"] = Pixmap()
		self["rate1_text"] = Label("IMDB")
		self["rate2_text"] = Label("Kinopoisk")
		self["moreinfo"] = Label()
		self["poster"] = Pixmap() 
		
		self["pages"] = Label()
		self["genres"] = Label()
		self["genres"].setText(_("Genres: ")+_("all"))
				
		self["actions"] = ActionMap(["OkCancelActions","ColorActions", "EPGSelectActions"], 
		{
			"cancel": self.exit,
			"ok": self.ok,
			"red" : self.showLast,
			"blue" : self.showBest,
			"green": self.selectGenres,
			"yellow": self.search,
			"nextBouquet" : self.nextPage,
			"prevBouquet" :self.prevPage
		}, -1)
		
		self.page = 1
		self.genres = []
		self.count = 0
		self.stype = 'last'
		self.query = ''
		self.mode = self.MODE_MAIN
		
		self.list.onSelectionChanged.append(self.selectionChanged)
		self.editMode = False
		self.editMoving = False
		self.onShown.append(self.start)
		
		global vid_bouquet
		vid_bouquet = BouquetManager()
		
	def start(self):
		if self.start in self.onShown:
			self.onShown.remove(self.start)
		
		self.endSelectGenres()
		
		#try:
		self.count = ktv.getVideos(self.stype, self.page, self.genres, cfg.numsonpage.value, self.query)
		
		#except:
		#	print "[KartinaTV] load videos failed!!!"
		#	self.session.openWithCallback(self.exit, MessageBox, _("Get videos failed!"))
		#	return
		print "[KartinaTV] total videos", self.count
		vid_bouquet.current = vid_bouquet.root
		if vid_bouquet.getList():
			vid_bouquet.root.remove()
			print 'clear bouquet'
		vid_bouquet.appendRoot(ktv.buildVideoBouquet())
		vid_bouquet.goIn()
		
		self.fillList()		
		#buildVideoBouqet already return list sorted by server.. #TODO: Think about local sort.
		#vid_bouquet.current.sortByKey(self.sortkey) 
	
	def kartinaVideoEntry(self, entry):
		vid = entry.name
		res = [
			(vid),
			(eListboxPythonMultiContent.TYPE_TEXT, 2, 2, 580, 24, 0, RT_HALIGN_LEFT, ktv.videos[vid].name )
		]
		return res

	def kartinaVideoSEntry(self, entry):
		fid = entry.name
		print 'file id', fid
		print ktv.filmFiles[fid]
		print ktv.filmFiles[fid]['title']
		res = [
			(fid),
			(eListboxPythonMultiContent.TYPE_TEXT, 20, 2, 580, 24, 0, RT_HALIGN_LEFT, ktv.filmFiles[fid]['title'])
		]
		return res
	
	def fillList(self):			
		print "[KartinaTV] fill video list"
		self.fillingList = True
		self.list.setList(map(self.kartinaVideoEntry, vid_bouquet.getList() ))	
		self.list.moveToIndex(vid_bouquet.current.index)
		self.fillingList = False
		
		self.setTitle(iName+" / Films / "+_(self.stype)+" "+self.query)
		pages = (self.count)/cfg.numsonpage.value
		if self.count % cfg.numsonpage.value != 0:
			pages += 1
		self["pages"].setText("%d / %d" % (self.page,  pages))
		self.hideLabels('s%s')
		self.selectionChanged()
	
	def fillSingle(self):
		t = vid_bouquet.getCurrentSel()
		if not t:
			return
		vid = t[0]
		#try:
		ktv.getVideoInfo(vid)
		#except:
		#	print "[KartinaTV] load videos failed!!!"
		#	self.session.openWithCallback(self.exit, MessageBox, _("Get videos failed!"))
		#	return
		vid_bouquet.goIn()
		for e in ktv.buildEpisodesBouquet(vid).getContent():
			vid_bouquet.current.append(e)
		print vid_bouquet.getList()
				
		self.fillingList = True
		self.list.setList(map(self.kartinaVideoSEntry, vid_bouquet.getList() ))	
		self.fillingList = False
		
		self.setTitle(iName+" / Films / "+ktv.videos[vid].name)
		self.hideLabels('%s')
		self.selectionChanged()
	
	def nextPage(self):
		self.page += 1
		if  (self.page-1)*cfg.numsonpage.value > self.count:
			self.page = 1
		self.start()
	
	def prevPage(self):
		self.page -= 1
		if self.page == 0:
			self.page = self.count / cfg.numsonpage.value
			if self.count % cfg.numsonpage.value != 0:
				self.page += 1
		self.start()
	
	def selectGenres(self):
		#for button click
		if self.mode == self.MODE_GENRES:
			self.endSelectGenres()
			self.start()
			return
		#main code
		if not len(self.glist.list):
			ktv.getVideoGenres()
			idx = 0
			for g in ktv.video_genres:
				self.glist.addSelection(g['name'], g['id'], idx, False)
				idx += 1
		self["key_green"].setText(_("OK"))
		self["genres"].setText(_("Genres: ")+"...")
		self.selectList("glist")
		self.glist.show()
		self.hideLabels('%s')
		self.mode = self.MODE_GENRES
	
	def endSelectGenres(self):
		self["key_green"].setText(_("Genres"))
		self.selectList("list")
		self.genres = [item[1] for item in self.glist.getSelectionsList()]
		genrestxt = [item[0] for item in self.glist.getSelectionsList()]
		self.glist.hide()
		if len(genrestxt):
			self["genres"].setText(_("Genres: ")+', '.join(genrestxt))
		else:
			self["genres"].setText(_("Genres: ")+_("all"))
		self.mode = self.MODE_MAIN
	
	def selectionChanged(self):
		if self.fillingList: return			#simple hack
		idx = self.list.getSelectionIndex()
		if self.editMoving and self.lastIndex != idx:
			print "[KartinaTV] moving entry", idx
			if self.lastIndex > idx:
				vid_bouquet.current.moveOneUp()
			else:
				vid_bouquet.current.moveOneDown()
			self.lastIndex = idx
			self.fillList() #TODO: optimize!!!
		vid_bouquet.setIndex(self.list.getSelectionIndex())
		self.updateInfo()
	
	def updateInfo(self):
		curr = vid_bouquet.getCurrentSel()
		print 'selection=', curr
		type = None
		if curr:
			(cid, type) = curr
		#some specific here
		if type == Bouquet.TYPE_MENU:
			s = "%s"
			pass
		elif type == Bouquet.TYPE_SERVICE:
			s = "s%s"
			cid = vid_bouquet.current.name
			pass
		else:
			s = "%s"	
			self[s % "name"].setText("")
			self[s % "year"].setText("")
			self[s % "description"].setText("")
			self["rate1"].setValue(0)
			self["rate2"].setValue(0)
			return
		
		self["rate1"].setValue(ktv.videos[cid].rate_imdb)
		self["rate2"].setValue(ktv.videos[cid].rate_kinopoisk)
		self[s % "name"].setText(ktv.videos[cid].name)
		self[s % "year"].setText(ktv.videos[cid].year)
		self[s % "description"].setText(ktv.videos[cid].descr)
		self[s % "name"].show()
		self[s % "year"].show()
		self[s % "description"].show()
		self["rate1"].show()
		self["rate2"].show()
		self["rate1_back"].show()
		self["rate2_back"].show()
		self["rate1_text"].show()
		self["rate2_text"].show()
	
	def showLast(self):
		self.stype = 'last'
		self.page = 1
		self.start() 
		
	def showBest(self):
		self.stype = 'best'
		self.page = 1
		self.start()
	
	def search(self):
		self.session.openWithCallback(self.searchCB, VirtualKeyBoardRu, _("Search films"))
	
	def searchCB(self, text):
		if text:
			self.stype = 'text'
			self.query = text
			print "[KartinaTV] searching for", text
			self.page = 1
			self.start()	
		
	def hideLabels(self, s = "%s"):
		#FIXME: non-readable code
		print "hide", s
		self[s % "name"].hide()
		self[s % "year"].hide()
		self[s % "description"].hide()
		self["rate1"].hide()
		self["rate2"].hide()
		self["rate1_back"].hide()
		self["rate2_back"].hide()
		self["rate1_text"].hide()
		self["rate2_text"].hide()
		
	def showElements(self,element_list,hide=False):
		#TODO: use it!!
		if hide:
			for e in element_list:
				self[e].hide()
		else:	
			for e in element_list:
				self[e].show()
		return		
	
	def ok(self):
		if multiListHandler.ok(self):
			return
		t = vid_bouquet.getCurrentSel()
		if not t:
			return
		(vid, type) = t
		print 'type', type, 'file', vid
		if type == Bouquet.TYPE_MENU:
			self.fillSingle()
		elif type == Bouquet.TYPE_SERVICE:
			self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
			self.close(vid)
	
	def exit(self):
		if vid_bouquet.getCurrentSel()[1] == Bouquet.TYPE_SERVICE:
			vid_bouquet.goOut()
			self.fillList()
		else:
			self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
			self.close()
	
		
#----------Config Class----------
class KartinaConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="KartinaConfig" position="center,center" size="550,250" title="IPTV">
			<widget name="config" position="20,10" size="520,150" scrollbarMode="showOnDemand" />
			<ePixmap name="red"	position="0,200" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,200" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		cfglist = [
			getConfigListEntry(_("login"), cfg.login),
			getConfigListEntry(_("password"), cfg.password),
			getConfigListEntry(_("Timeshift"), cfg.timeshift),
			getConfigListEntry(_("Show in mainmenu"), cfg.in_mainmenu), 
			getConfigListEntry(_("Use servicets instead of Gstreamer"), cfg.usesrvicets),
			getConfigListEntry(_("Buffering time, milliseconds"), config.plugins.KartinaTv.buftime)
		]
			
		ConfigListScreen.__init__(self, cfglist, session)
		self.setTitle(iName)
	
	def keySave(self):
		self.saveAll()
		self.close(True)
	
	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

#gettext HACK:
[_("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"), _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov") ] 
[_("all"), _("favourites"), _("By group")]
[_("last"), _("best"), _("text")]
