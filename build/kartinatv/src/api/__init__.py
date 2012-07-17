import sys
#sys.path.append("../") 
try:
	from Plugins.Extensions.KartinaTV.utils import *
	import Plugins.Extensions.KartinaTV.jtvreader as jtvreader
except ImportError:
	from utils import *
	import jtvreader