# appModules/audacity/au_py3Compatibility.py
# a part of audacityAccessEnhancement add-on
# Copyright 2019 paulber19
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.


import addonHandler
import os
from logHandler import log
import sys
py3 = sys.version.startswith("3")
# Python 3 preparation (a compatibility layer until Six module is included).
if py3:
	rangeGen = range 
	baseString = str  
	uniCHR = chr
else:
	rangeGen = xrange
	baseString = basestring
	uniCHR = unichr
	

def iterate_items(to_iterate):
	if py3:
		return to_iterate.items()
	else:
		return to_iterate.iteritems()
def _unicode(s):
	if py3:
		return str(s)
	else:
		return unicode(s)
def importStringIO ():
	if py3:
		from io import StringIO
	else:
		from cStringIO import StringIO
		return StringIO
def u(s):
	if py3:
		return s
	else:
		return unicode(s)

def longint(i):
	if py3:
		return i
	else:
		return long(i)

def reLoad(mod):
	if py3:
		import importlib
		importlib.reload(mod)
	else:
		reload(mod)

def getUtilitiesPath():
	curAddon = addonHandler.getCodeAddon()
	if py3:
		return os.path.join(curAddon.path, "utilitiesPy3")
	else:
		return os.path.join(curAddon.path, "utilities")	
