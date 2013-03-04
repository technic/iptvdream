from twisted.internet import reactor
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.error import ErrorPage
from twisted.python import urlpath
from twisted.web import resource, util

from plugin import runManager

class RedirectToStream(resource.Resource):
	isLeaf = True
	
	def _threadedRender(self, request):
		print "[KartinaTV] render"
		req = request.path.split('/')
		if len(req) == 3:
			try:
				cid = int(req[2])
			except ValueError:
				return ErrorPage(404, 'wrong request format', '').render(request)
			url = runManager.getStream(req[1], cid, None)
			if url:
				print '[KartinaTV] server redirecting'
				ret = util.redirectTo(url, request)
			else:
				ret = ErrorPage(404, 'api getStreamUrl failed', '').render(request)
		else:
			ret = ErrorPage(404, 'wrong request format', '').render(request)
		request.write(ret)
		request.finish()
	
	def render(self, request):
		reactor.callInThread(self._threadedRender, request)
		return NOT_DONE_YET
	
reactor.listenTCP(9000, Site(RedirectToStream()))
