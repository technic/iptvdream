#  Dreambox Enigma2 Rodnoe/KartinaTV player!
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
#You can modify skin data file for you tastes
#TODO: A LOT OF SKIN WORK!
from utils import Rect

#--------------INFO BAR--------------
infobar_hd = """
<screen name="KartinaPlayer" position="center,550" size="1120,150" title="IPTV">
	<!-- Channellogo (Picon) -->
	<widget source="session.CurrentService" render="Picon" position="10,50" zPosition="1" size="100,60" alphatest="on">
		<convert type="ServiceName">Reference</convert>
	</widget>
	<!-- Videoformat icon (16:9?) -->
	<ePixmap position="600,10" zPosition="0" size="36,20" pixmap="KartinaTV_skin/ico_format_off.png" />
	<widget source="session.CurrentService" render="Pixmap" pixmap="KartinaTV_skin/ico_format_on.png" position="600,10" zPosition="1" size="36,20" alphatest="on">
		<convert type="ServiceInfo">IsWidescreen</convert>
		<convert type="ConditionalShowHide" />
	</widget>
	<!-- HDTV icon -->
	<widget source="session.CurrentService" render="Pixmap" pixmap="KartinaTV_skin/ico_hd_off.png" position="645,10" size="29,20" zPosition="1" alphatest="blend">
		<convert type="ServiceInfo">VideoWidth</convert>
		<convert type="ValueRange">0,720</convert>
		<convert type="ConditionalShowHide" />
   	</widget>
	<widget source="session.CurrentService" render="Pixmap" pixmap="KartinaTV_skin/ico_hd_on.png" position="645,10" size="29,20" zPosition="2" alphatest="blend">
		<convert type="ServiceInfo">VideoWidth</convert>
		<convert type="ValueRange">721,1980</convert>
		<convert type="ConditionalShowHide" />
    </widget>
	<widget name="caption" position="145,10" zPosition="1" size="300,23" font="Regular;25" transparent="1" halign="left"/>
	<widget name="currentprg_bar" position="122,87" size="500,12" pixmap="skin_default/progress_medium.png" borderWidth="2" borderColor="#cccccc"/>
	<widget name="currtime" position="122,50" zPosition="1" size="100,25" font="Regular;24" transparent="1" halign="left"/>
	<widget name="nexttime" position="122,105" zPosition="1" size="100,25" font="Regular;24" transparent="1" halign="left" foregroundColor="#c3c3c9"/>
	<widget name="currprg" position="222,50" zPosition="1" size="600,24" font="Regular;24" transparent="1" halign="left"/>
	<widget name="nextprg" position="222,105" zPosition="1" size="600,24" font="Regular;24" transparent="1" halign="left" foregroundColor="#c3c3c9"/>
	<widget name="currdur" position="835,50" zPosition="1" size="180,24" font="Regular;24" transparent="1" halign="right"/>
	<widget name="nextdur" position="920,105" zPosition="1" size="85,24" font="Regular;24" transparent="1" halign="right" foregroundColor="#c3c3c9"/>
	<widget name="archivedate" position="820,120" zPosition="1" size="150,24" font="Regular;24" transparent="1" halign="right" foregroundColor="#f63737"/>
	<widget font="Regular;25" halign="center" position="10,10" render="Label" size="100,25" source="global.CurrentTime" zPosition="1">
		<convert type="ClockToText"/>
	</widget>
</screen>"""


infobar_sd = """
	<!-- Main infobar -->
	<screen name="InfoBar" flags="wfNoBorder" position="0,380" size="720,160" title="InfoBar" backgroundColor="transparent">
		<!-- Background -->
		<ePixmap position="0,0" zPosition="-1" size="720,160" pixmap="skin_default/info-bg.png" />
		<ePixmap position="27,73" size="665,71" pixmap="skin_default/screws.png" alphatest="on" transparent="1" />
		<!-- Channellogo (Picon) -->
		<widget source="session.CurrentService" render="Picon" position="49,4" zPosition="1" size="70,53" alphatest="on">
			<convert type="ServiceName">Reference</convert>
		</widget>
		<!-- Service name -->
		<widget name="caption" position="130,30" size="360,27" font="Regular;21" valign="center" halign="right" noWrap="1" backgroundColor="#263c59" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1"/>
		<!-- Time -->
		<ePixmap pixmap="skin_default/icons/clock.png" position="600,23" size="14,14" alphatest="on" />
		<widget source="global.CurrentTime" render="Label" position="615,21" size="55,24" font="Regular;21" halign="right" backgroundColor="#4e5a74" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<ePixmap position="563,48" zPosition="0" size="107,15" pixmap="skin_default/icons/icons_off.png"/>
		<!-- Videoformat icon (16:9?) -->
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/icon_format.png" position="611,48" zPosition="1" size="29,16" alphatest="on">
			<convert type="ServiceInfo">IsWidescreen</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<!-- Audio icon (is there multichannel audio?) -->
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/icon_dolby.png" position="645,48" zPosition="1" size="26,16" alphatest="on">
			<convert type="ServiceInfo">IsMultichannel</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<!-- Progressbar (current event duration)-->
		<ePixmap pixmap="skin_default/progress_bg.png" position="48,77" size="84,7" transparent="1" alphatest="on" />
		<widget name="currentprg_bar" pixmap="skin_default/progress_small.png" position="50,78" zPosition="1" size="80,5" transparent="1"/>
		<!-- Event (now) -->
		<ePixmap pixmap="skin_default/icons/icon_event.png" position="182,78" size="15,10" alphatest="on" />
		<widget name="currtime" position="205,73" size="60,24" font="Regular;20" backgroundColor="#34406f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1"/>
		<widget name="currprg" position="265,73" size="320,24" font="Regular;20" noWrap="1" backgroundColor="#34406f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1"/>
		<widget name="currdur" position="585,73" size="85,24" font="Regular;20" backgroundColor="#34406f" shadowColor="#1d354c" shadowOffset="-1,-1" halign="right" transparent="1"/>
		<!-- Event (next) -->
		<widget name="nexttime" position="205,97" size="60,24" font="Regular;20" backgroundColor="#071f38" foregroundColor="#c3c3c9" transparent="1"/>
		<widget name="nextprg" position="265,97" size="320,24" font="Regular;20" noWrap="1" backgroundColor="#071f38" foregroundColor="#c3c3c9" transparent="1"/>
		<widget name="nextdur" position="585,97" size="85,24" font="Regular;20" backgroundColor="#071f38" foregroundColor="#c3c3c9" halign="right" transparent="1"/>
	</screen>
"""   

#--------------CHANNEL SELECTION---------- 
channels_hd = """
<screen name="KartinaChannelSelection" position="35,70" size="1210,620" title="Channel Selection">
	<eLabel backgroundColor="#006D87" foregroundColor="#00ACD1" position="30,5" size="1150,2"/>
	<eLabel backgroundColor="#006D87" foregroundColor="#00ACD1" position="812,20" size="2,540"/>
	<widget name="list" position="15,11" size="790,542" transparent="1" scrollbarMode="showOnDemand"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonRed.png" position="80,579" size="250,38" zPosition="1"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonGreen.png" position="350,579" size="250,38" zPosition="1"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonYellow.png" position="620,579" size="250,38" zPosition="1"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonBlue.png" position="890,579" size="250,38" zPosition="1"/>
	<widget backgroundColor="#9f1313" font="Regular;24" halign="center" name="key_red" position="80,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget backgroundColor="#1f771f" font="Regular;24" halign="center" name="key_green" position="350,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget backgroundColor="#a08500" font="Regular;24" halign="center" name="key_yellow" position="620,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget backgroundColor="#18188b" font="Regular;24" halign="center" name="key_blue" position="890,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget font="Regular;24" foregroundColor="#00ACD1" halign="center" position="821,15" size="371,25" name="epgchannel" zPosition="1"/>
	<widget font="Regular;20" halign="right" position="950,85" size="180,22" name="epgtime" zPosition="1"/>
	<widget borderWidth="1" pixmap="KartinaTV_skin/progress.png" position="855,90" size="83,15" name="epgprogress" transparent="1"/>
	<widget font="Regular;20" foregroundColor="#ffa550" position="825,115" size="366,312" name="epgname" zPosition="1"/>
	<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="955,55" size="14,14" zPosition="1"/>
	<widget font="Regular;22" halign="center" position="975,50" render="Label" size="70,20" source="global.CurrentTime" zPosition="1">
		<convert type="ClockToText"/>
	</widget>
</screen>"""

#set parameters of item in list #TODO: move to skin xml string
channels_list_hd = {
	"item_height" : 28,
	"chname_font" : 22,
	"chepg_font" : 20,
	"chname_rect" : Rect(38, 1, 280, 25),
	"chepg_rect" : Rect(328, 1, 480, 25),
	"charchive_rect" : Rect(5, 0, 16, 16),
	"chprogress_rect" : Rect(18, 5, 20, 16)
	#color, color_sel, backcolor, backcolor_sel, border_width, border_color #Colors not implemented yet
}
	 

channels_sd = """
<screen name="KartinaChannelSelection" position="center,center" size="650,440" title="Channel Selection">
	<ePixmap name="red" position="0,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
	<ePixmap name="green" position="140,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
	<ePixmap name="yellow" position="280,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
	<ePixmap name="blue" position="420,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
	<widget name="key_red" position="0,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="key_green" position="140,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="key_yellow" position="280,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="key_blue" position="420,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="list" position="0,60" scrollbarMode="showOnDemand" size="650,330" />
	<widget name="epgname" position="5,400" zPosition="1" size="500, 20" font="Regular;20" transparent="1" halign="left"/>
	<widget name="epgtime" position="120,420" zPosition="1" size="200, 20" font="Regular;20" transparent="1" halign="left"/>
	<widget name="epgprogress" position="5,420" size="100,12" pixmap="skin_default/progress_medium.png" borderWidth="2" borderColor="#cccccc"/>
	<widget name="epgchannel" position="349,420" zPosition="1" size="300,21" font="Regular;21" transparent="1" halign="right"/>
	<widget source="global.CurrentTime" render="Label" position="600,400" size="82,21" font="Regular;21">
	    <convert type="ClockToText">Default</convert>
	</widget>    
</screen>"""

channels_list_sd = {
	"item_height" : 28,
	"chname_font" : 22,
	"chepg_font" : 20,
	"chname_rect" : Rect(0, 2, 200, 22),
	"chepg_rect" : Rect(200, 2, 450, 22)
}

#--------------EPG MENU-------------------
epg_hd =  """
<screen name="KartinaEpgList" position="35,70" size="1210,620" title="EPG">
	<eLabel backgroundColor="#999999" position="30,5" size="1150,2"/>
	<eLabel backgroundColor="#999999" position="812,20" size="2,540"/>
	<widget name="list" position="15,11" size="790,542" transparent="1" scrollbarMode="showOnDemand"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonRed.png" position="80,579" size="250,38" zPosition="1"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonGreen.png" position="350,579" size="250,38" zPosition="1"/>
	<ePixmap alphatest="blend" pixmap="KartinaTV_skin/ButtonYellow.png" position="620,579" size="250,38" zPosition="1"/>
	<widget backgroundColor="#9f1313" font="Regular;24" halign="center" name="key_red" position="80,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget backgroundColor="#1f771f" font="Regular;24" halign="center" name="key_green" position="350,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget backgroundColor="#a08500" font="Regular;24" halign="center" name="key_yellow" position="620,578" size="250,38" transparent="1" valign="center" zPosition="2"/>
	<widget font="Regular;24" foregroundColor="#00ACD1" halign="center" position="821,15" size="371,25" name="epgtime" zPosition="1"/>
	<widget font="Regular;20" halign="right" position="950,85" size="180,22" name="epgdur" zPosition="1"/>
	<widget font="Regular;20" foregroundColor="#ffa550" position="825,115" size="366,412" name="epginfo" zPosition="1"/>
	<widget font="Regular;24" foregroundColor="#00ACD1" position="20,527" size="371,32" name="sepgtime" zPosition="1"/>
	<widget font="Regular;26" halign="right" position="600,525" size="200,32" name="sepgdur" zPosition="1"/>
	<widget font="Regular;26" foregroundColor="#ffa550" position="15,11" size="790,520" name="sepginfo" zPosition="1"/>
	<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="955,55" size="14,14" zPosition="1"/>
	<widget font="Regular;22" halign="center" position="975,50" render="Label" size="70,20" source="global.CurrentTime" zPosition="1">
		<convert type="ClockToText"/>
	</widget>
</screen>"""

epg_sd = """
<screen name="KartinaEpgList" position="center,center" size="650,400" title="EPG">
	<ePixmap name="red" position="0,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
	<ePixmap name="green" position="140,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
	<ePixmap name="yellow" position="280,0" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
	<widget name="key_red" position="0,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="key_green" position="140,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="key_yellow" position="280,0" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	<widget name="list" position="0,60" scrollbarMode="showOnDemand" size="650,340" />
	<widget name="epginfo" position="10,60" zPosition="1" size="0,0" font="Regular;22" transparent="1" halign="left"/>
	<widget name="epgtime" position="5,370" zPosition="1" size="0,0" font="Regular;22" transparent="1" halign="left"/>
	<widget name="epgdur" position="130,370" zPosition="1" size="0,0" font="Regular;22" transparent="1" halign="left"/>
	<widget name="sepginfo" position="10,60" zPosition="1" size="500,200" font="Regular;22" transparent="1" halign="left"/>
	<widget name="sepgtime" position="5,370" zPosition="1" size="200,24" font="Regular;22" transparent="1" halign="left"/>
	<widget name="sepgdur" position="130,370" zPosition="1" size="85,24" font="Regular;22" transparent="1" halign="left"/>
</screen>"""
