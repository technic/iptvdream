#  Dreambox Enigma2 IPtvDream player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/


from newrus_api import NewrusAPI, Ktv as NewrusKtv

class MegaimpulsAPI(NewrusAPI):

	iProvider = "megaimpuls"
	site = "http://iptv.megaimpuls.com"

class Ktv(MegaimpulsAPI, NewrusKtv):
	
	iName = "Megaimpuls"
	iTitle = "Megaimpuls"