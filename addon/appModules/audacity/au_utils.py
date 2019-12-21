#appModules\audacity\au_utils.py
#A part of audacityAccessEnhancement add-on
#Copyright (C) 2018, paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
import wx
import api
import speech
import winUser
import time
from keyboardHandler import KeyboardInputGesture
from logHandler import log
import queueHandler
import gui
import config

# winuser.h constant

WM_SYSCOMMAND = 0x112
MOUSEEVENTF_WHEEL=0x0800

def isOpened(dialog):
	if dialog._instance is None:
		return False
	# Translators: the label of a dialog box message.
	msg = _("%s dialog is allready open") %dialog.title
	queueHandler.queueFunction(queueHandler.eventQueue, speech.speakMessage, msg)
	return True

def makeAddonWindowTitle(dialogTitle):
	curAddon = addonHandler.getCodeAddon()
	addonSummary = curAddon.manifest['summary']
	# Translators:  title of all add-on dialog boxs.
	return  _("{addonSummary}'s add-on - {dialogTitle}").format(addonSummary = addonSummary, dialogTitle = dialogTitle)

def messageBox(message, caption=wx.MessageBoxCaptionStr, style=wx.OK | wx.CENTER, parent=None):
	option = config.conf["presentation"]["reportObjectDescriptions"]
	config.conf["presentation"]["reportObjectDescriptions"] = True
	ret = gui.messageBox(message, caption, style, parent)
	config.conf["presentation"]["reportObjectDescriptions"] = option
	return ret


def getPositionXY (obj):
	location=obj.location
	(x, y)=(int(location[0])+int(location[2]/2),int(location[1])+int(location[3]/2))
	return (x, y)

def mouseClick(obj, rightButton=False, twice = False):
	api.moveMouseToNVDAObject(obj)
	api.setMouseObject(obj)
	if not rightButton :
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		if twice:
			time.sleep(0.1)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
	
	else:
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)
		if twice:
			time.sleep(0.1)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN,0,0,None,None)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP,0,0,None,None)

def MouseWheelForward():
	winUser.mouse_event(MOUSEEVENTF_WHEEL,0,0,120,None)

def MouseWheelBack():
	winUser.mouse_event(MOUSEEVENTF_WHEEL,0,0,-120,None)
