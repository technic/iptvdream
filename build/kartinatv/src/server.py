from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.error import ErrorPage
from twisted.python import urlpath
from twisted.web import resource, util

from plugin import runManager

class RedirectToStream(resource.Resource):
	isLeaf = 0
	def __init__(self):
		resource.Resource.__init__(self)
		self.url = None
	
	def render(self, request):
		print '[KartinaTV] server redirecting'
		return util.redirectTo(self.url, request)

	def getChild(self, name, request):
		req = request.path.split('/')
		if len(req) == 3:
			url = runManager.getStream(req[1], req[2], None)
			if url:
				self.url = url
				return self
			else:
				return ErrorPage(404, 'api getStreamUrl failed', '')
		else:
			return ErrorPage(404, 'wrong request format', '')

reactor.listenTCP(9000, Site(RedirectToStream()))
