from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.error import ErrorPage
from twisted.python import urlpath
from twisted.web import resource, util

from plugin import runManager

class RedirectToStream(resource.Resource):
	isLeaf = True
	
	def render(self, request):
		print "[KartinaTV] render"
		req = request.path.split('/')
		if len(req) == 3:
			url = runManager.getStream(req[1], req[2], None)
			if url:
				print '[KartinaTV] server redirecting'
				return util.redirectTo(url, request)
			else:
				return ErrorPage(404, 'api getStreamUrl failed', '').render(request)
		else:
			return ErrorPage(404, 'wrong request format', '').render(request)
	
reactor.listenTCP(9000, Site(RedirectToStream()))
