#  Dreambox Enigma2 KartinaTV/RodnoeTV player! (by technic)
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from abstract_api import MODE_VIDEOS
from russiantelek_api import RussianTelekAPI, JsonWrapper

import urllib
from xml.etree.cElementTree import fromstring
from . import tdSec, secTd, syncTime, Bouquet, Video, unescapeEntities

VIDEO_CACHING = True #TODO: cache...??

class Ktv(RussianTelekAPI):
	
	MODE = MODE_VIDEOS
	iName = "russiantelekMovies"
	NEXT_API = "RussianTelek"
	
	def __init__(self, username, password):
		RussianTelekAPI.__init__(self, username, password)
		
		self.video_genres = []
		self.videos = {}
		self.filmFiles = {}
		self.currentPageIds = []
	
	def getVideos(self, stype='last', page=1, genre=[],  nums_onpage=20, query=''):
		if not VIDEO_CACHING:
			self.videos = {}
		if genre:
			genre_arg = genre[0]
		else:
			genre_arg = 0
		params = {"type" : stype,
				  "nums" : nums_onpage,
				  "page" : page,
				  "genre" : genre_arg }
		if stype == 'text':
			params['query'] = query
		#root = self.getData("/api/json/vod_list?"+urllib.urlencode(params), "getting video list by type %s" % stype)
		root = self.getData("/api/json/vod_list.php?"+urllib.urlencode(params), "getting video list by type %s" % stype)
		videos_count = int(root.findtext('total'))
		
		self.currentPageIds = []
		for v in root.find('rows'):
			vid = int(v.findtext('id'))
			self.currentPageIds += [vid]
			name = v.findtext('name').encode('utf-8')
			video = Video(name)
			video.name_orig = v.findtext('name_orig').encode('utf-8')
			video.descr = unescapeEntities(v.findtext('description')).encode('utf-8')
			video.image = v.findtext('poster')
			video.year = v.findtext('year').encode('utf-8')
#			video.rate_imdb = floatConvert(v.findtext('rate_imdb'))
#			video.rate_kinopoisk = floatConvert(v.findtext('rate_kinopoisk'))
#			video.rate_mpaa = v.findtext('rate_mpaa')
			video.country = v.findtext('country').encode('utf-8')
			video.genre = v.findtext('genre_str').encode('utf-8')
			self.videos[vid] = video				
		return videos_count 
	
	def getVideoInfo(self, vid):
		params = {"id": vid}
		root = self.getData("/api/json/vod_info.php?"+urllib.urlencode(params), "getting video info %s" % vid)
		v = root.find('film')
		name = v.findtext('name').encode('utf-8')
		video = Video(name)
		
#		video.name_orig = v.findtext('name_orig').encode('utf-8')
		video.descr = unescapeEntities(v.findtext('description')).encode('utf-8')
		video.image = v.findtext('poster')
		video.year = v.findtext('year').encode('utf-8')
#		video.rate_imdb = floatConvert(v.findtext('rate_imdb'))
#		video.rate_kinopoisk = floatConvert(v.findtext('rate_kinopoisk'))
#		video.rate_mpaa = v.findtext('rate_mpaa')
		video.country = v.find('country').findtext('name').encode('utf-8')
		video.genre = v.findtext('genre_str').encode('utf-8')
#		video.length = v.findtext('length') and int(v.findtext('length'))
		video.director = v.findtext('director').encode('utf-8')
#		video.scenario = v.findtext('scenario').encode('utf-8')
		video.actors = v.findtext('actors').encode('utf-8')
		video.studio = v.findtext('studio')
		video.awards = v.findtext('awards')
		video.budget = v.findtext('budget')
		video.files = []
		for f in v.find('videos'):
			episode = {}
			fid = int(f.findtext('id'))
			episode["format"] = f.findtext('format').encode('utf-8')
			episode["length"] = 0 #f.findtext('length')
			episode["title"] = f.findtext('title').encode('utf-8') or video.name
			episode["tracks"] = []
			episode_name = ""
			if episode['title'] != video.name:
				episode_name = episode['title']
			episode["name"] = video.name + " " + episode_name 
			i = 1
			while True:
				if f.find("track%d_codec" % i):
					episode["tracks"] += ["%s-%s" % (f.findtext("track%d_codec" % i).encode('utf-8'),
					                                 f.find("track%d_lang" % i))]
					i +=1
				else:
					break
			video.files += [fid]
			self.filmFiles[fid] = episode 
		self.videos[vid]= video
	
	def getVideoUrl(self, fid):
		params = {"fileid" : fid}
		root = self.getData("/api/json/vod_geturl.php?"+urllib.urlencode(params), "getting video url %s" % fid)
		return root.findtext('url').encode('utf-8').split(' ')[0]
	
	def getVideoGenres(self):
		root = self.getData("/api/json/vod_genres.php?", "getting genres list")		
		self.video_genres = []
		for genre in root.find('genres'):
			self.video_genres += [{"id": genre.findtext('id'), "name": genre.findtext('name').encode('utf-8')}]
	
	def getPosterPath(self, vid, local=False):
		if local:
			return self.videos[vid].image.split('/')[-1].encode('utf-8') 
		else:	
			return self.site+self.videos[vid].image
		
	
	def buildVideoBouquet(self):
		movs = Bouquet(Bouquet.TYPE_MENU, 'films')
		for x in self.currentPageIds:
			 mov = Bouquet(Bouquet.TYPE_MENU, x, self.videos[x].name, self.videos[x].year) #two sort args [name, year]
			 movs.append(mov)
		return movs
	
	def buildEpisodesBouquet(self, vid):
		files = Bouquet(Bouquet.TYPE_MENU, vid) 
		for x in self.videos[vid].files:
			print 'add fid', x, 'to bouquet'
			file = Bouquet(Bouquet.TYPE_SERVICE, x)
			files.append(file)
		return files

def floatConvert(s):
	return s and int(float(s)*10) or 0 


