#  Copyright (c) 2012 Alex Revetchi
#  enigma2-iptv-plugin  is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from abstract_api import MODE_STREAM, AbstractAPI, AbstractStream
import cookielib, urllib, urllib2, Cookie #TODO: optimize imports
import json
import os, subprocess
from datetime import datetime
from uuid import getnode as get_mac
from . import tdSec, secTd, setSyncTime, syncTime, Bouquet, EpgEntry, Channel, unescapeEntities, Timezone, APIException, SettEntry


class TvtekaAPI(AbstractAPI):

	iProvider = "tvtekatv"
	iName = "TvtekaTV"
        iTitle = "TvtekaTV"
	NEXT_API = None
	MODE = MODE_STREAM
	NUMBER_PASS = False
	                                                
	site = "http://tvteka.com"

	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)

                self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPRedirectHandler(), urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.addheaders = [('content-length', '0'),('Accept', 'application/vnd.tvp.glavnee+json'),('Connection', 'Keep-Alive')]
                self.deviceid = get_mac()
                self.token = ""
#                self.rtmpgw = subprocess.Popen(['/usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/rtmp/rtmpgw', '-g 8080', '-q', '-D 127.0.0.1'],
#                                               env=dict(os.environ, LD_LIBRARY_PATH='/usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/rtmp'),
#                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

#        def __del__(self):
#                if self.rtmpgw is not None:
#                    self.rtmpgw.stdin.write('q')
#                    self.rtmpgw.kill()
#                    self.rtmpgw.poll()

	def start(self):
                if not self.tokenVerify():
                    self.getToken()

        def tokenVerify(self):
                if not len(self.token):
                        return False
                self.setCookieToken()
                reply = self.opener.open(self.site+'/session/verify').read()
                print reply
                if reply=='OK':
                        return True
                else:
                        return False

        def getToken(self):
                self.trace("Authorization started")
                params = urllib.urlencode({"session[login]" : self.username, "session[password]" : self.password, "device[type]": "enigma2", "device[id]": self.deviceid})
                reply = self.opener.open(self.site+'/session/register?', params).read()
                c=json.loads(reply)
                if type(c) == type(dict()) and len(c['token'])>0:
                        self.token = c['token']
                else:
                        self.trace("Authorization failed...")
                        raise Exception(reply)

	def getData(self, path, name):
                self.setCookieToken()
                try:
                        reply = self.opener.open(self.site+path).read()
                except:
                        raise APIException("Failed to read from url: " + self.site+path)

                try:
                        reply = json.loads(reply)
                except:
                         raise APIException("Failed to parse json response")

                return reply

        def setCookieToken(self):
                 c=cookielib.Cookie(version=0, 
                                    name="deviceToken", value=self.token, 
                                    port=None, port_specified=False, 
                                    domain='', domain_specified=False, domain_initial_dot=False, 
                                    path='/', path_specified=False, 
                                    secure=False, expires=None, discard=False, 
                                    comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                 self.cookiejar.set_cookie(c)


class Ktv(TvtekaAPI, AbstractStream):

	def __init__(self, username, password):
		TvtekaAPI.__init__(self, username, password)
		AbstractStream.__init__(self)
                self.chs = {}

	def setChannelsList(self):
		c = self.getChannelsList()
		lst = []
		num = -1
		for ch in c:
			if ch['videostatus']=='full_access':
				name = ch['name'].encode("utf-8")
				archive = 0
                        	num += 1
				self.channels[num] = Channel(name, "ALL", num, 1, archive)
                        	self.chs[num] = ch
	
	def getChannelsList(self):
		self.setCookieToken()
		reply = self.getData('/live', 'fetch channels list')
                if reply.has_key('channels'):
                         channels = reply['channels']
                else:
                         raise APIException("No channels found in the reply")
                return channels
	
	def getStreamUrl(self, cid, pin, time = None):
                link="http://127.0.0.1:8080/?r="
                ch=self.chs[cid]
                u=ch['streaming_urls'][0]
                request=("rtmp://" + u['host']
                        + "/" + u['app']
                        + "&y=" + u['playpath']
                        + "&a=" + u['app']
                        + "&t=" + u['host'] + "/" + u['app']
                        + "&C=O:1&C=NS:userId:"+str(ch['user_id'])+"&C=NS:sessionId:"+ch['session_id']+"&C=O:0")
                url = link + urllib.quote(request, '')
		return url 
        	
	def getStreamUrlDirect(self, cid, pin, time = None):
	        ch=self.chs[cid]
	        u=ch['streaming_urls'][0]
	        url=("rtmp://" + u['host'] + "/" + u['app'] + "/" + u['playpath']
	             + " rtmp_playpath=" + u['playpath']
	             + " rtmp_app=" + u['app']
	             + " rtmp_tcurl=" + u['host'] + "/" + u['app']
	             +" rtmp_conn=O:1 rtmp_conn=NS:userId:"+str(ch['user_id'])+" rtmp_conn=NS:sessionId:"+ch['session_id']+ " rtmp_conn=O:0")
