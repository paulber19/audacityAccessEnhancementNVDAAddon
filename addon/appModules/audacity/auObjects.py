# -*- coding: UTF-8 -*-
#appModules/audacity/au_objects.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018,paulber19
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
addonHandler.initTranslation()
from logHandler import log
import api
import gui
import wx
from oleacc import *
from controlTypes import *
from .au_py3Compatibility import rangeGen

#object hierarchy
HIE_TrackView= 1
HIE_ToolDock1  = 2
HIE_ToolDock2 = 3
HIE_TransportToolBar = 4
HIE_PauseButton = 5
HIE_PlayButton = 6
HIE_StopButton = 7
HIE_RecordButton = 8
HIE_SelectionToolBar = 9
HIE_AudioPosition = 10
HIE_SelectionChoice = 11
HIE_SelectionStart = 12
HIE_SelectionEnd = 13
HIE_SelectionDuration = 14
HIE_SelectionCenter =  15
HIE_AudacityTranscriptionToolbar = 16
HIE_PlaybackSpeedSlider = 17
HIE_RecordMeterPeak = 18
HIE_PlayMeterPeak = 19
HIE_RecordingSlider = 20
HIE_PlaybackSlider= 21

# for audacity 2.3.0
hie_2300 = {
	HIE_TrackView: "3|0", # from mainFrameObject
	HIE_ToolDock1 : "1|0", # from mainFrameObject
	HIE_PauseButton : "1", # from HIE_TransportToolBar  object
	HIE_PlayButton : "2", # from HIE_TransportToolBar
	HIE_StopButton : "3", # from HIE_TransportToolBar
	HIE_RecordButton : "6", # from HIE_TransportToolBar
	HIE_PlaybackSpeedSlider: "2", #  from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1", # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1", # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider : "2",# from MixerToolbarObject
	HIE_PlaybackSlider   :"4", # from MixerToolbarObject
	HIE_ToolDock2 : "2", # from mainFrameObject
	HIE_AudioPosition : "12", # from HIE_SelectionToolBar object
	HIE_SelectionChoice : "7", # from  HIE_SelectionToolBar
	HIE_SelectionStart :  "14", # from  HIE_SelectionToolBar object
	HIE_SelectionDuration : "15", # from HIE_SelectionToolBar object
	HIE_SelectionCenter : "16", # from HIE_SelectionToolBar object
	HIE_SelectionEnd : "17", # from HIE_SelectionToolBar object
	}


_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']
def initialize(appModule):
	global _audacityHierarchyID
	version = appModule._get_productVersion()
	audacityID  = int("".join(version.split(",")))
	if audacityID >= 2300:
		id = hie_2300
	else:
		log.warning("This version %s of Audacity is not  compatible with the add-on"%version)
		wx.CallLater(1000, gui.messageBox,
			# Translators: the label of a dialog box message.
			_("This version %s of Audacity is not  compatible with the add-on")%version,
			# Translators: the label of a dialog box title.
			_("%s add-on - warning")%_summary,
			wx.OK|wx.ICON_WARNING)
		id = None
	_audacityHierarchyID = id

def getObjectByHierarchy ( oParent, iHierarchy):
	try:
		sHierarchy = _audacityHierarchyID[iHierarchy]
	except:
		return None
	try:
		o = oParent
		if len(sHierarchy):
			Hierarchy = sHierarchy.split("|")
			for i in Hierarchy:
				iChild  = int(i)
				if o and iChild <= o.childCount:
					o = o.getChild(iChild)
				else:
					# error, no child
					return None
			return o
	except:
		log.error("error getObjectByHierarchy: %s, parent: %s" %(sHierarchy, oParent.name))
	return None

def mainFrameObject():
	oDesktop = api.getDesktopObject()
	desktopName = oDesktop.name.lower()
	o = api.getFocusObject()
	while o:
		oGParent= o.parent.parent
		if oGParent and oGParent.name and oGParent.name.lower() == desktopName:
			return o
		
		o = o.parent
	log.error("error no mainFrameObject")
	return None

def topPanelObject():
	oDeb = mainFrameObject()
	if oDeb:
		for i in rangeGen(oDeb.childCount):
			o = oDeb.getChild(i)
			if o.name == "Top Panel":
				return o
	return None
	

def toolDock1Object ():
	o = mainFrameObject()
	if o :
		return getObjectByHierarchy(o, HIE_ToolDock1 )
	return None

def  toolDock2Object():
	o = mainFrameObject()
	if o:
		return  getObjectByHierarchy(o, HIE_ToolDock2)
	return None

def selectionToolBarObject():
	o = toolDock2Object()
	if o :
		for o in o.children:
			if o.childCount >6:
				return o

	log.warning ("no selectionToolBarObject")
	return None

def  audioPositionObject():
	o = selectionToolBarObject()
	if o  is not None:
		return getObjectByHierarchy(o, HIE_AudioPosition)
	return None

def selectionChoiceObject ():
	o = selectionToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_SelectionChoice)
	return None

def selectionStartObject ():
	o = selectionToolBarObject()
	if o :
		return  getObjectByHierarchy(o, HIE_SelectionStart)
	return None
	

def selectionEndObject ():
	o = selectionToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_SelectionEnd)
	return None
def selectionDurationObject ():
	o = selectionToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_SelectionDuration)
	return None
def selectionCenterObject ():
	o = selectionToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_SelectionCenter)
	return None

def transportToolBarObject ():
	obj = toolDock1Object ()
	if obj :
		# the only solution to find transport toolbar
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 0 and o.childCount == 7:
				return o
	return None

def pauseButtonObject ():
	o = transportToolBarObject()
	if o :
		return  getObjectByHierarchy(o, HIE_PauseButton)
	return None

def playButtonObject ():
	o = transportToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_PlayButton)
	return None

def stopButtonObject():
	o = transportToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_StopButton)
	return None

def recordButtonObject():
	o = transportToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_RecordButton)
	return None

_buttonObjectsDic = {
		"play": playButtonObject,
		"pause" : pauseButtonObject,
		"stop": stopButtonObject,
		"record": recordButtonObject
		}

def isPressed( button):
	try:
		o = _buttonObjectsDic[button]()
	except:
		log.warning("Button %s not found"%button)
		o =None
	
	if o and o.IAccessibleObject.accState(0) & STATE_SYSTEM_PRESSED :
		return True
	return False

def isAvailable( button):
	try:
		o = _buttonObjectsDic[button]()
	except:
		log.warning("Button %s not found"%button)
		o =None
	
	if o and (o.IAccessibleObject.accState(0) & STATE_SYSTEM_UNAVAILABLE  or o.IAccessibleObject.accState(0) & STATE_SYSTEM_INVISIBLE ):
		return False
	return True

def recordingMeterToolbarObject():
	obj = toolDock1Object ()
	if obj :
		# the only solution to find transport toolbar
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 3 and o.childCount == 3:
				return o
	log.warning ("error: recordingMeterToolbarObject not found")
	return None

def recordMeterPeakObject():
	o = recordingMeterToolbarObject()
	if o :
		return getObjectByHierarchy(o, HIE_RecordMeterPeak)
	return None
def playbackMeterToolbarObject():
	obj = toolDock1Object ()
	if obj :
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 4 and o.childCount == 3:
				return o
	log.warning ("error: playbackMeterToolbarObject not found")
	return None

def playMeterPeakObject():
	o = playbackMeterToolbarObject()
	if o :
		return getObjectByHierarchy(o, HIE_PlayMeterPeak)
	return None

def mixerToolbarObject():
	obj = toolDock1Object ()
	if obj :
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 5 and o.childCount == 6:
				return o
	log.warning ("error: mixerToolbarObject not found")
	return None


def recordingSliderObject():
	o = mixerToolbarObject()
	if o :
		return getObjectByHierarchy(o, HIE_RecordingSlider)
	return None

def playbackSliderObject():
	o = mixerToolbarObject()
	if o :
		return getObjectByHierarchy(o, HIE_PlaybackSlider)
	return None


def PlayAtSpeedToolBarObject():
	obj = toolDock1Object ()
	if obj :
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 7 and o.childCount == 4:
				return o
	log.warning ("error: PlayAtSpeedToolBarObject not found")
	return None
	
def playbackSpeedSliderObject():
	o = PlayAtSpeedToolBarObject()
	if o :
		return getObjectByHierarchy(o, HIE_PlaybackSpeedSlider)
	return None
	