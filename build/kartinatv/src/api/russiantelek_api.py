#  Dreambox Enigma2 IPtvDream player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/

from newrus_api import NewrusAPI, Ktv as NewrusKtv

class RussianTelekAPI(NewrusAPI):
	
	iProvider = "russiantelek"
	site = "http://iptv.russiantelek.com"

class Ktv(NewrusKtv, RussianTelekAPI):
	
	iName = "RussianTelek"
	iTitle = "RussianTelek"