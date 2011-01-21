#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#

from Plugins.Plugin import PluginDescriptor

#using external player by A. Latsch & Dr. Best (c)
#Hardly improved by technic(c) for KartinaTV/RodnoeTV compatibility and buffering possibility!!!
import servicewebts

def Plugins(path, **kwargs):
	return [ 
	PluginDescriptor(name="RodnoeTV", description="Iptv player for RodnoeTV", icon="plugin-rtv.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = ROpen),
	PluginDescriptor(name="KartinaTV", description="Iptv player for KartinaTV", icon="plugin-ktv.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = KOpen), 
	PluginDescriptor(name="KartinaTV", description="Iptv player for KartinaTV", where = PluginDescriptor.WHERE_MENU, fnc = menuktv),
	PluginDescriptor(name="RodnoeTV", description="Iptv player for RodnoeTV", where = PluginDescriptor.WHERE_MENU, fnc = menurtv) 
	]

from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger, getConfigListEntry, ConfigYesNo, ConfigSubDict
from Components.ConfigList import ConfigListScreen
import kartina_api, rodnoe_api
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Slider import Slider
from Components.Button import Button
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarPlugins, InfoBarExtensions, InfoBarAudioSelection, NumberZap, InfoBarSubtitleSupport, InfoBarNotifications, InfoBarSeek
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.ChoiceBox import ChoiceBox
from Tools.BoundFunction import boundFunction
from enigma import eServiceReference, iServiceInformation, eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont, eTimer, iPlayableServicePtr, iStreamedServicePtr, getDesktop
from Components.ParentalControl import parentalControl
#from threading import Thread
from Tools.LoadPixmap import LoadPixmap
from Components.Pixmap import Pixmap
import datetime
from utils import Bouquet, BouquetManager, tdSec, secTd, syncTime
import skin_data
#from Components.ServiceList import ServiceList

#for localized messages
from . import _

sz_w = 0
try:
	sz_w = getDesktop(0).size().width()
except:
	skinHD = False
print "[KartinaTV] skin width = ", sz_w
if sz_w > 1000:
	skinHD = True
else:
	skinHD = False
if skinHD:
	ch = skin_data.channels_list_hd
else:
	ch = skin_data.channels_list_sd  

#Initialize Configuration #kartinatv
config.plugins.KartinaTv = ConfigSubsection()
config.plugins.KartinaTv.login = ConfigText(default="145", visible_width = 50, fixed_size = False)
config.plugins.KartinaTv.password = ConfigText(default="541", visible_width = 50, fixed_size = False)
config.plugins.KartinaTv.timeshift = ConfigInteger(0, (0,12) )
config.plugins.KartinaTv.lastroot = ConfigText(default="[]")
config.plugins.KartinaTv.lastcid = ConfigInteger(0, (1,1000))
config.plugins.KartinaTv.favourites = ConfigText(default="[]")
config.plugins.KartinaTv.usesrvicets = ConfigYesNo(default=True)
config.plugins.KartinaTv.sortkey = ConfigSubDict()
config.plugins.KartinaTv.sortkey["all"] = ConfigInteger(1, (1,2))
config.plugins.KartinaTv.sortkey["By group"] = ConfigInteger(1, (1,2))
config.plugins.KartinaTv.sortkey["in group"] = ConfigInteger(1,(1,2))
config.plugins.KartinaTv.numsonpage = ConfigInteger(15,(1,100))
config.plugins.KartinaTv.in_mainmenu = ConfigYesNo(default=True) 
#rodnoetv
config.plugins.rodnoetv = ConfigSubsection()
config.plugins.rodnoetv.login = ConfigText(default="demo", visible_width = 50, fixed_size = False)
config.plugins.rodnoetv.password = ConfigText(default="demo", visible_width = 50, fixed_size = False)
config.plugins.rodnoetv.timeshift = ConfigInteger(0, (0,12) ) ##NOT USED!!! ADDED FOR COMPATIBILITY
config.plugins.rodnoetv.lastroot = ConfigText(default="[]")
config.plugins.rodnoetv.lastcid = ConfigInteger(0, (1,1000))
config.plugins.rodnoetv.favourites = ConfigText(default="[]")
config.plugins.rodnoetv.usesrvicets = ConfigYesNo(default=True)
config.plugins.rodnoetv.sortkey = ConfigSubDict()
config.plugins.rodnoetv.sortkey["all"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.sortkey["By group"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.sortkey["in group"] = ConfigInteger(1,(1,2))
config.plugins.rodnoetv.in_mainmenu = ConfigYesNo(default=False)
#bufsize is general
config.plugins.KartinaTv.bufsize = ConfigInteger(256, (50,2560) ) #TODO: replace bufsize with buftime because stream rates are different

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
	global Ktv, cfg, favouritesList,  iName
	Ktv = rodnoe_api.Ktv
	cfg = config.plugins.rodnoetv
	iName = "RodnoeTV"
	favouritesList = eval(cfg.favourites.value)
	if KartinaPlayer.instance is None: #avoid recursing
		session.open(KartinaPlayer) 
	else:
		print "[KartinaTV] error: already running!"
		return
	
rec_png = LoadPixmap(cached=True, path='/usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/rec.png')
EPG_UPDATE_INTERVAL = 60 #Seconds, in channel list.
PROGRESS_TIMER = 1000*60 #Update progress in infobar.
PROGRESS_SIZE = 200
	
def setServ():
	global SERVICE_KARTINA
	if cfg.usesrvicets.value:
		SERVICE_KARTINA = 4112 #ServiceWebTS
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
	
	if skinHD:
		skin = skin_data.infobar_hd
	else:
		skin = skin_data.infobar_sd
	
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
		#InfoBarSeek.__init__(self)
		
		self["caption"] = Label("")
		self["currprg"] = Label("")
		self["nextprg"] = Label("")
		self["currtime"] = Label("")
		self["nexttime"] = Label("")
		self["currdur"] = Label("")
		self["nextdur"] = Label("")
		self["archivedate"] = Label("")
		self["currentprg_bar"] = Slider(0, PROGRESS_SIZE)
		
		#FIXME: actionmap add help.
		#TODO: Create own actionmap
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "ChannelSelectEPGActions", "InfobarChannelSelection", "TvRadioActions"], 
		{
			"cancel": self.exit, #Exit
			"green" : self.kartinaConfig, #Options
			"red" :self.archivePvr,
			"yellow" :self.playpauseArchive,
			#"blue" :self.doNothing,
			"zapUp" : self.previousChannel,
			"zapDown" : self.nextChannel,
			"ok" : self.toggleShow,
			"switchChannelUp" : self.showList,
			"switchChannelDown" : self.showList,
			"openServiceList" : self.showList,
			"historyNext" : self.historyNext,
			"historyBack" : self.historyBack,
			"showEPGList" :self.showEpg
		}, -1)
		
		self["NumberActions"] = NumberActionMap( [ "NumberActions"],
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
			
		self.setTitle(iName)		
		
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		
		self.current = 0
		self.oldcid = None
		
		self.epgTimer = eTimer()
		self.epgProgressTimer = eTimer()
		self.epgTimer.callback.append(self.epgEvent)
		self.epgProgressTimer.callback.append(self.epgUpdateProgress)
		
		self.onClose.append(self.__onClose)
		self.onShown.append(self.start)
	
	def __onClose(self):
		KartinaPlayer.instance = None
		print "[KartinaTV] set instance to None"
	
	def start(self):
		if self.start in self.onShown:
			self.onShown.remove(self.start)		
		setServ()
		print "[KartinaTV] Using service:", SERVICE_KARTINA
		self.archive_pause = 0
		global ktv
		ktv = Ktv(cfg.login.value, cfg.password.value)
		global bouquet
		bouquet = BouquetManager()
		try: #TODO: handle different exceptions
			ktv.start()
			ktv.setTimeShift(cfg.timeshift.value)
			ktv.setChannelsList()
			#ktv.loadEpg() #TODO: Thread for Epg
		except:
			print "[KartinaTV] ERROR login/init failed!"
			self.session.openWithCallback(self.errorCB, MessageBox, _("Login or initialization failed!\nEdit options?"), type = MessageBox.TYPE_YESNO)
			return
		#init bouquets
		self.oldsid = None
		print "[KartinaTV] Favourites ids", favouritesList
		fav = Bouquet(Bouquet.TYPE_MENU, 'favourites')
		for x in favouritesList:
			if x in ktv.channels.keys():
				fav.append(Bouquet(Bouquet.TYPE_SERVICE, x))
		bouquet.appendRoot(ktv.sortByName())
		bouquet.appendRoot(ktv.sortByGroup())
		bouquet.appendRoot(fav)
		#apply parentalControl
		for x in Ktv.locked_cids: #Ktv.locked_ids:
			sref = fakeReference(x)
			print "[KartinaTV] protect", sref.toCompareString()
			parentalControl.protectService(sref.toCompareString())
		
		#startup service
		print "[KartinaTV] set path to", cfg.lastroot.value
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
			self.archiveDisable()  #already has play
			#self.session.archive = True
			#self.play()
	
	def previousChannel(self):
		if ktv.aTime:
			self.session.openWithCallback(self.rwdSeekTo, MinuteInput)
		elif ktv.videomode:
			pass
		else:
			self.current = bouquet.goPrev()
			bouquet.historyAppend()
			self.archiveDisable()
			#self.play()
	
	#FIXME: history and channel zapping forget archive position!   
	def historyNext(self):
		if ktv.videomode:
			return
		if bouquet.historyNext():
			self.current = bouquet.getCurrent()
			self.archiveDisable()
			#ktv.aTime = 0
			#self.play()
	
	def historyBack(self):
		if ktv.videomode:
			pass
		if bouquet.historyPrev():
			self.current = bouquet.getCurrent()
			self.archiveDisable()
			#ktv.aTime = 0
			#self.play()
	
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
				ktv.aTime -= tdSec(syncTime()-self.archive_pause)-5 #manually -5sec TODO: use config or global constant 
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
		if isinstance( self.current, int ):
			cid = self.current
			if cid == self.oldcid:
				self.startPlay() #for archive
				return
			self.session.nav.stopService()
			#Use many hacks, because it's no possibility to change enigma :(
			#fake reference has no path and used for parental control
			fakeref = fakeReference(cid) #parentalControl hack.
			print fakeref.toCompareString()
			if parentalControl.isServicePlayable(fakeref, boundFunction(self.startPlay)):
				self.startPlay()
			else:
				self["caption"].setText(ktv.channels[cid].name)
				self.epgEvent()	
				#self.current = bouquet.getCurrent()
				#self.play()

	def startPlay(self, **kwargs):
		print "[KartinaTV] play channel id=", self.current 
		if isinstance( self.current, int ):
			cid = self.current
			self.oldcid = cid
			#TODO: mirror getting url and seeking to c++ part
			#print "[KartinaTV] getting stream uri: dream-time =", datetime.datetime.now().strftime("%s")
			try:
				uri = ktv.getStreamUrl(cid)
			except:
				print "[KartinaTV] Error: getting stream uri failed!"
				self.session.open(MessageBox, _("Error while getting stream uri"), type = MessageBox.TYPE_ERROR, timeout = 5)
				return -1
			#uri = 'http://192.168.0.2/stream.ts' #XXX: FOR TESTING ONLY COMMENT!!!!!
			srv = SERVICE_KARTINA
			if not uri.startswith('http://'):
				srv = 4097
			sref = eServiceReference(srv, 0, uri) 
			#print "[KartinaTV] got stream uri: dream-time =", datetime.datetime.now().strftime("%s")
			sref.setData(7, int(str(cid), 16) ) #picon hack;)
			if iName == "RodnoeTV":
				sref.setData(6,1) #again hack;)	
			#self.session.nav.stopService() #FIXME: do we need it?? some bugs in servicets?
			self.session.nav.playService(sref)
			self["caption"].setText(ktv.channels[cid].name)
			self.epgEvent()	

	
	def epgEvent(self):
		self.epgTimer.stop() #first stop timers 
		self.epgProgressTimer.stop()
		cid = self.current
		curr = None
		if ktv.aTime:
			if not ktv.channels[cid].haveAEpg(ktv.aTime):
				try:
					ktv.getGmtEpg(cid)
				except:
					print "[KartinaTV] ERROR load archive epg failed! cid =", cid
			curr =  ktv.channels[cid].aepg		   
		else:
			if not ktv.channels[cid].haveEpg():
				try:
					ktv.getChannelsEpg([cid])
				except:
					print "[KartinaTV] ERROR load epg failed! cid =", cid
			curr =  ktv.channels[cid].epg
		print "[KartinaTV]", ktv.aTime
		#if curr:
		#	#print "[KartinaTV] curr not None"
		#	if curr.end(ktv.aTime):
		#		print "[KartinaTV] epg end"
		if not (curr and not curr.end(ktv.aTime)):
			print "[KartinaTV] there is no EPG to show:(", cid
			self["currprg"].setText('')
			self["currtime"].setText('')
			self["nextprg"].setText('')
			self["nexttime"].setText('')
			self["currdur"].setText('')
			self["nextdur"].setText('')
			self["currentprg_bar"].setValue(0)	
			self.serviceStarted() #ShowInfoBar
			return
		
		self.currentEpg = curr
		self["currprg"].setText(curr.name)
		self["currtime"].setText(curr.tstart.strftime("%H:%M"))
		self["nexttime"].setText(curr.tend.strftime("%H:%M"))
		self.epgTimer.start( curr.getTimeLeft(ktv.aTime)*1000 ) #milliseconds
		self["currdur"].setText("+%d min" % (curr.getTimeLeft(ktv.aTime) / 60) )
		self["currentprg_bar"].setValue(PROGRESS_SIZE * curr.getTimePass(ktv.aTime) / curr.duration)
		self.epgProgressTimer.start(1000*60) #1 minute
		if ktv.aTime: #TODO: new record label
			self["archivedate"].setText(curr.tstart.strftime("%d.%m.%y"))
			self["archivedate"].show()
		else:
			self["archivedate"].hide()
		
		def setEpgNext():
			if ktv.aTime:
				next = None
			else:
				next = ktv.channels[cid].nepg
			if next and curr.tend <= next.tstart and next.tstart > syncTime():
				self['nextprg'].setText(next.name)
				self['nextdur'].setText("%d min" % (next.duration/ 60))
				return True
			return False
		
		if not setEpgNext():
			try:
				ktv.epgNext(cid)
				setEpgNext()
			except:
				pass
						
		self.serviceStarted() #ShowInfoBar #FIXME: only if focused
		
	def epgUpdateProgress(self):
		self["currdur"].setText("+%d min" % (self.currentEpg.getTimeLeft(ktv.aTime)/60) )
		self["currentprg_bar"].setValue(PROGRESS_SIZE * self.currentEpg.getTimePass(ktv.aTime) / self.currentEpg.duration)
		self.epgProgressTimer.start(1000*60)
	
	
	def archivePvr(self):
		if ktv.aTime:
			self.archiveDisable()
		elif ktv.videomode:
			ktv.videomode = False
			if ktv.aTime:
				self.playpauseArchive()
			else:
				self.play()
		else:
			ktv.videomode = True
			if ktv.videomode: #I'm not idiot:) Api can not allow to set videomode, because it isn't available. 
				self.showVideoList()
			#show Pvr Menu
	def showVideoList(self):
		self.session.openWithCallback(self.showVideoCB, KartinaVideoList)
	
	def archiveDisable(self):
		#hide pixmap
		#self.session.archive = False
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
			ktv.aTime = 0
			bouquet.historyAppend()
			self.play()
	
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
			self.session.archive = True
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
		#TODO: mirror getting url and seeking to c++ part
		try:
			uri = ktv.getVideoUrl(vid)
		except:
			print "[KartinaTV] Error: getting video uri failed!"
			self.session.open(MessageBox, _("Error while getting video uri"), type = MessageBox.TYPE_ERROR, timeout = 5)
			return -1
		#uri = 'http://192.168.0.2/mp4' #XXX: FOR TESTING ONLY COMMENT!!!!!
		sref = eServiceReference(4097, 0, uri) #TODO: SERVICE_KARTINA 
		#self.session.nav.stopService() #FIXME: do we need it?? some bugs in servicets?
		self.session.nav.playService(sref)
		#self["caption"].setText(ktv.videos[cid].name)
	
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
			print "[KartinaTV] save path", cfg.lastroot.value
			cfg.lastroot.save()
			cfg.lastcid.value = self.current
			cfg.lastcid.save()
			cfg.favourites.value = str(favouritesList)
			cfg.favourites.save()
			cfg.sortkey.save()
			if iName == "KartinaTV":
				cfg.numsonpage.save()
		self.close()
	
	def generate_error(self):
		print "[KartinaTV] User generate error for debug"
		raise Exception("User generate error for debug")
	
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
				ktv.aTime = 0
				self.play()
			else:
				bouquet.current = lastroot
				
r1 = ch['chname_rect']
r2 = ch['chepg_rect']

def kartinaChannelEntry(entry, num):
	if entry.type == Bouquet.TYPE_MENU:
		return [
			(entry.name),
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 1, 300, 25, 0, RT_HALIGN_LEFT, entry.name)
		]
	elif entry.type == Bouquet.TYPE_SERVICE:
		cid = entry.name
		if num:
			x = [(cid),
				(eListboxPythonMultiContent.TYPE_TEXT, r1.x+20, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT, ktv.channels[cid].name),
				(eListboxPythonMultiContent.TYPE_TEXT, 0, 1, 20, r1.h, 0, RT_HALIGN_LEFT, str(num) ) ]
		else:
			x = [(cid),
				(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT, ktv.channels[cid].name) ]
		if ktv.channels[cid].haveEpg():
			curr = ktv.channels[cid].epg
			x += [(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r2.h, 1, RT_HALIGN_LEFT, curr.name)]
		if ch.has_key('charchive_rect') and ktv.channels[cid].archive:
			r3 = ch['charchive_rect']
			x += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, r3.w, r3.h, rec_png)]
		if ch.has_key('chprogress_rect') and ktv.channels[cid].haveEpg() and ktv.channels[cid].epg.duration:
			r4 = ch['chprogress_rect']
			percent = ktv.channels[cid].epg.getTimePass(ktv.aTime)*100 / ktv.channels[cid].epg.duration
			if ch.has_key('chprogress_pixmap'):
				bg = ch['chprogress_pixmap_bg']
				fg = ch['chprogress_pixmap_fg']
			#	x += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r4.x, r4.y, r4.w, r4.h, bg)]
			#	x += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r4.x, r4.y, r4.w * ktv.channels[cid].epg.getTimePass() / ktv.channels[cid].epg.duration, r4.h, fg)]					
			else:
				x += [(eListboxPythonMultiContent.TYPE_PROGRESS, r4.x, r4.y, r4.w, r4.h, percent)]	
		return x

def kartinaVideoEntry(entry):
	res = [
		(entry),
		(eListboxPythonMultiContent.TYPE_TEXT, 145, 2, 580, 24, 0, RT_HALIGN_LEFT, entry[u'name'].encode('utf-8') )
	]
	return res
		
class KartinaChannelSelection(Screen):
	
	if skinHD:
		skin = skin_data.channels_hd
	else:
		skin = skin_data.channels_sd
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_red"] = Button(_("All"))
		self["key_green"] = Button(_("Groups"))
		self["key_yellow"] = Button(_("Add"))
		self["key_blue"] = Button(_("Favourites"))
		self.list = MenuList([], enableWrapAround=True, content = eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", ch['chname_font']))
		self.list.l.setFont(1, gFont("Regular", ch['chepg_font']))
		self.list.l.setItemHeight(ch['item_height'])
		self["list"] = self.list
		
		self["epgname"]=Label()
		self["epgtime"]=Label()
		self["epgchannel"]=Label()
		self["epgprogress"]=Slider(0, 100)
		self["epgnexttime"]=Label()
		self["epgnextname"]=Label()
		self["epgnextname"]=Label()
		
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
		
		self.list.onSelectionChanged.append(self.updateEpgInfo)
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
		bouquet.setIndex(self.list.getSelectionIndex())
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
		if not self.lastEpgUpdate or syncTime() - self.lastEpgUpdate > secTd(EPG_UPDATE_INTERVAL):
			for x in bouquet.getList():
				if isinstance(x.name, int):
					if not ktv.channels[x.name].haveEpg():
						uplist += [x.name]
		if uplist: 
			try:
				ktv.getChannelsEpg(uplist)
				self.lastEpgUpdate = syncTime()
			except:
				print "[KartinaTV] failed to get epg for uplist"
		
		self.setTitle(_("Channel Selection")+" / "+" / ".join(map(_, bouquet.getPathName())) )
	
		self.fillingList = True #simple hack
		if bouquet.current.name == 'favourites':
			self["key_yellow"].setText(_("Delete"))
			self.list.setList(map(kartinaChannelEntry, bouquet.getList(), range(1, len(bouquet.current.content)+1) ))
		else:
			self["key_yellow"].setText(_("Add"))
			n = bouquet.current.name
			if cfg.sortkey.has_key(n):
				bouquet.current.sortByKey(cfg.sortkey[n].value)
			else:
				bouquet.current.sortByKey(cfg.sortkey['in group'].value)
			self.list.setList(map(kartinaChannelEntry, bouquet.getList(), []) )
		self.list.moveToIndex(bouquet.current.index)
		self.fillingList = False
		self.updateEpgInfo() #previous line already calls this
		
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
		
	def updateEpgInfo(self):
		if self.fillingList: return			#simple hack
		idx = self.list.getSelectionIndex()
		if self.editMoving and self.lastIndex != idx:
			print "[KartinaTV] moving entry", idx
			if self.lastIndex > idx:
				bouquet.current.moveOneUp()
			else:
				bouquet.current.moveOneDown()
			self.lastIndex = idx
			self.fillList()
		bouquet.setIndex(self.list.getSelectionIndex())
		print "[KartinaTV]", bouquet.current.index, bouquet.current.name
		curr = bouquet.getCurrentSel()
		type = None
		if curr:
			(cid, type) = curr
		if type == Bouquet.TYPE_SERVICE:
			self["epgchannel"].setText(ktv.channels[cid].name)
			self["epgchannel"].show()
			text = ""
			if ktv.channels[cid].haveEpg(): #Not ktv.aTime but zero
				curr = ktv.channels[cid].epg
				text += "%s - %s\n" % (curr.tstart.strftime("%H:%M"), curr.tend.strftime("%H:%M"))
				text += curr.name
				self["epgname"].show()
				self["epgtime"].show()
				self["epgprogress"].setValue(100*curr.getTimePass(0) / curr.duration) #Not ktv.aTime but zero
				self["epgprogress"].show()
			else:
				self.hideEpgLabels()
			if ktv.channels[cid].haveEpgNext():
				text += '\n'
				curr = ktv.channels[cid].nepg
				text += "%s - %s\n" % (curr.tstart.strftime("%H:%M"), curr.tend.strftime("%H:%M"))
				text += curr.name
			#else:
			#	self.hideEpgNextLabels()
			self["epgname"].setText(text)
		else:
			self["epgchannel"].setText("")
			self.hideEpgLabels()
	
	def hideEpgLabels(self):
		self["epgname"].hide()
		self["epgtime"].hide()
		#self["epgchannel"].hide()
		self["epgprogress"].hide()
	
#	def hideEpgNextLabels(self):
#		self["epgnextname"].hide()
#		self["epgnexttime"].hide()
	
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
			if bouquet.current.canMoveOneUp():
				lst += [( _("Move one position up"), 'move_up')]		
			if bouquet.current.canMoveOneDown():
				lst += [( _("Move one position down"), 'move_down')]
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
		elif entry == 'move_to':
			pass
		elif entry == 'move_up':
			bouquet.current.moveOneUp()
			favouritesList = [x.name for x in bouquet.getList()]
			self.fillList()
		elif entry == 'move_down':
			bouquet.current.moveOneDown()
			favouritesList = [x.name for x in bouquet.getList()]
			self.fillList()
		elif entry == 'start_edit':
			self.editMode = True
		elif entry == 'stop_edit':
			self.editMode = False
			self.editMoving = False
			favouritesList = [x.name for x in bouquet.getList()]
			print "[KartinaTV] now fav are:", favouritesList
			self.fillList()
	
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
	
	if skinHD:
		skin = skin_data.epg_hd
	else:
		skin = skin_data.epg_sd
		
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
		self["epginfo"] = Label()
		self["epgdur"] = Label()
		self["epgtime"] = Label()
		
		self["sepginfo"] = Label()
		self["sepgdur"] = Label()
		self["sepgtime"] = Label()
		
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
			(eListboxPythonMultiContent.TYPE_TEXT, 18, 2, 30, 22, 0, RT_HALIGN_LEFT, _(entry[0].strftime('%a')) ), #TODO: different colors for next and prev
			(eListboxPythonMultiContent.TYPE_TEXT, 50, 2, 90, 22, 0, RT_HALIGN_LEFT, entry[0].strftime('%H:%M')), #or some record label + now playing label
			(eListboxPythonMultiContent.TYPE_TEXT, 145, 2, 580, 24, 1, RT_HALIGN_LEFT, entry[1])]
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
			self[s % "epginfo"].setText("%s\n%s" % (entry[1], entry[2]) )
			self[s % "epgtime"].setText(entry[0].strftime("%d.%m %H:%M"))
			self[s % "epginfo"].show()
			self[s % "epgtime"].show()
			if len(self.list.list) > idx+1:
				next = self.list.list[idx+1][0]
				self[s % "epgdur"].setText("%s min" % (tdSec(next[0]-entry[0])/60))
				self[s % "epgdur"].show()
			else:
				self[s % "epgdur"].hide()
	
	def hideLabels(self, s = "%s"):
		print "hide", s
		self[s % "epginfo"].hide()
		self[s % "epgtime"].hide()
		self[s % "epgdur"].hide()
		
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

class KartinaVideoList(Screen):
	
	if skinHD:
		skin = skin_data.epg_hd
	else:
		skin = skin_data.epg_sd

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_red"] = Button(_("Play"))
		self["key_green"] = Button(_("Info"))
		self["key_yellow"] = Button(_("Generes"))
		self["key_blue"] = Button(_("Favourites"))
		self.list = MenuList([], enableWrapAround=True, content = eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", ch['chname_font']))
		self.list.l.setItemHeight(ch['item_height'])
		self["list"] = self.list
		
		#tmp
		self["epginfo"] = Label()
		self["epgdur"] = Label()
		self["epgtime"] = Label()
		
		self["sepginfo"] = Label()
		self["sepgdur"] = Label()
		self["sepgtime"] = Label()
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "EPGSelectActions"], 
		{
			"cancel": self.exit,
			"red" : self.play,
			"ok": self.play,
			"yellow": self.selectGenres,
			"nextBouquet" : self.nextPage,
			"prevBouquet" :self.prevPage,
			"green" : self.showSingle
		}, -1)
		
		self.page = 1
		self.genres = []
		self.count = 0
		self.stype = 'last'
		self.list.onSelectionChanged.append(self.updateInfo)
		self.onLayoutFinish.append(self.fillList)
		
	def fillList(self):
		try:
			l = ktv.getVideos(self.stype, cfg.numsonpage.value, self.page, self.genres)
		except:
			print "[KartinaTV] load videos failed!!!"
			return
		self.count = l['total']
		print "[KartinaTV] total videos", self.count
		self.list.setList(map(kartinaVideoEntry, l['rows']))	
	
	def nextPage(self):
		self.page += 1
		if  (self.page-1)*cfg.numsonpage.value > self.count:
			self.page = 1
		self.fillList()
	
	def prevPage(self):
		self.page -= 1
		if self.page == 0:
			self.page = self.count / cfg.numsopage.value
			if self.count % cfg.numsopage.value != 0:
				self.page += 1
		self.fillList()
	
	def selectGenres(self):
		pass
	
	def showSingle(self):
		pass
	
	def updateInfo(self):
		pass
	
	def play(self):
		idx = self.list.getSelectionIndex()
		if len(self.list.list) > idx:	
			self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
			self.close(self.list.list[idx][0]['id'])
	
	def exit(self):
		self.list.onSelectionChanged.pop() #Do it before close, else event happed while close.
		self.close()
	
		
#----------Config Class----------
class KartinaConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="KartinaConfig" position="center,center" size="550,200" title="IPTV">
			<widget name="config" position="20,10" size="520,150" scrollbarMode="showOnDemand" />
			<ePixmap name="red"	position="0,150" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,150" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,150" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,150" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
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
			getConfigListEntry(_("Buffer size, KB"), config.plugins.KartinaTv.bufsize)
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
