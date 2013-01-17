#  Dreambox Enigma2 IPtvDream player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/


from newrus_api import Ktv as NewrusKtv

class Ktv(NewrusKtv):

	iProvider = "megaimpuls"
	site = "http://iptv.megaimpuls.com"
	
	iName = "Megaimpuls"
	iTitle = "Megaimpuls"