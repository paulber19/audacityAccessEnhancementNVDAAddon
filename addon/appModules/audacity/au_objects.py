# -*- coding: UTF-8 -*-
# appModules\audacity\au_objects.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018-2020,paulber19
# This file is covered by the GNU General Public License.


from logHandler import log
import api
import gui
import wx
from oleacc import *  # noqa: F401, F403
import addonHandler
import os
import sys
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from au_py3Compatibility import rangeGen  # noqa E402
del sys.path[-1]
addonHandler.initTranslation()

# object hierarchy
HIE_TrackView = 1
HIE_ToolDock1 = 2
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
HIE_SelectionCenter = 15
HIE_AudacityTranscriptionToolbar = 16
HIE_PlaybackSpeedSlider = 17
HIE_RecordMeterPeak = 18
HIE_PlayMeterPeak = 19
HIE_RecordingSlider = 20
HIE_PlaybackSlider = 21
HIE_TimePane = 22
HIE_TimeAudioPosition = 23
HIE_SelectionAudioPosition = 24

_controlIDs = {
	HIE_TrackView: 1003,  # unknown role in  mainPanelObject
	HIE_ToolDock1: 1,  # pane in topPanelObject
	HIE_ToolDock2: 2,  # pane in mainFrame object
	HIE_SelectionToolBar: 10,  # pane in toolDock2 object
	HIE_SelectionChoice: 2704,  # comboBox object in selectionToolBarObject
	HIE_SelectionStart: 2705,  # text  object in selectionToolbarObject
	HIE_SelectionDuration: 2706,  # text  object in selectionToolbarObject
	HIE_SelectionCenter: 2707,  # text  object in selectionToolbarObject
	HIE_SelectionEnd: 2708,  # text  object in selectionToolbarObject
	HIE_SelectionAudioPosition: 2709,  # text in selectionToolBar object
	HIE_TimePane: 12,  # pane in selectionToolbar object
	HIE_TimeAudioPosition: 2801,  # text in timePane object
	HIE_PauseButton: 11000,  # button in transportToolBar object
	HIE_PlayButton: 11001,  # button in transportToolBar object
	HIE_StopButton: 11002,  # button in transportToolBar object
	HIE_RecordButton: 11005,  # button in transportToolBar object
}



# for audacity 3.0.0
_hierarchy_3000 = {
	HIE_PlaybackSpeedSlider: "2",  # from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1",  # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1",  # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider: "2",  # from MixerToolbarObject
	HIE_PlaybackSlider: "4",  # from MixerToolbarObject
}


# for audacity 2.4.2
_hierarchy_2420 = {
	HIE_PlaybackSpeedSlider: "2",  # from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1",  # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1",  # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider: "2",  # from MixerToolbarObject
	HIE_PlaybackSlider: "4",  # from MixerToolbarObject
}

# for audacity 2.4.1
_hierarchy_2410 = {
	HIE_PlaybackSpeedSlider: "2",  # from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1",  # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1",  # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider: "2",  # from MixerToolbarObject
	HIE_PlaybackSlider: "4",  # from MixerToolbarObject
}

# for audacity 2.3.3
_hierarchy_2330 = {
	HIE_PlaybackSpeedSlider: "2",  # from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1",  # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1",  # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider: "2",  # from MixerToolbarObject
	HIE_PlaybackSlider: "4",  # from MixerToolbarObject
}
# for audacity 2.3.2
_hierarchy_2320 = {
	HIE_PlaybackSpeedSlider: "2",  # from PlayAtSpeedToolBarObject
	HIE_RecordMeterPeak: "1",  # from HIE_RecordingMeterToolbar
	HIE_PlayMeterPeak: "1",  # from HIE_PlaybackMeterToolbar
	HIE_RecordingSlider: "2",  # from MixerToolbarObject
	HIE_PlaybackSlider: "4",   # from MixerToolbarObject
}


_addonSummary = _curAddon.manifest['summary']
_audacityHierarchyPaths = None
_audacityVersionID = None


def initialize(appModule):
	global _audacityHierarchyPaths, _audacityVersionID
	version = appModule._get_productVersion()
	_audacityVersionID = int("".join(version.split(",")))

	if _audacityVersionID in [2420, 3000]:
		id = _hierarchy_2420
	elif _audacityVersionID == 2410:
		id = _hierarchy_2410
	elif _audacityVersionID == 2330:
		id = _hierarchy_2330
	elif _audacityVersionID == 2320:
		id = _hierarchy_2320
	else:
		id = _hierarchy_2420
		log.warning("This version %s of Audacity is perhaps not  compatible with the add-on" % version)  # noqa: E501 line too long
		wx.CallLater(
			1000, gui.messageBox,
			# Translators: the label of a dialog box message.
			_("The add-on has not been tested with this version of Audacity and may not be compatible with it."),
			# Translators: the label of a dialog box title.
			_("%s add-on - warning") % _addonSummary,  # noqa: F405,E501 '_' may be undefined, or defined from star, line too long
			wx.OK | wx.ICON_WARNING)

	_audacityHierarchyPaths = id


def getObjectByHierarchy(oParent, iHierarchy):
	try:
		sHierarchy = _audacityHierarchyPaths[iHierarchy]
	except:  # noqa: E722 Bare except
		return None
	try:
		o = oParent
		if len(sHierarchy):
			Hierarchy = sHierarchy.split("|")
			for i in Hierarchy:
				iChild = int(i)
				if o and iChild <= o.childCount:
					o = o.getChild(iChild)
				else:
					# error, no child
					return None
			return o
	except:  # noqa: E722 Bare except
		log.error("error getObjectByHierarchy: %s, parent: %s" % (
			sHierarchy, oParent.name))
	return None


def findObjectByControlID(obj, controlID):
	for i in range(0, obj.childCount):
		o = obj.getChild(i)
		if o.windowControlID == _controlIDs[controlID]:
			return o
	return None


def mainFrameObject():
	oDesktop = api.getDesktopObject()
	desktopName = oDesktop.name.lower()
	o = api.getFocusObject()
	while o:
		oGParent = o.parent.parent
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
		log.warning("topPanelObject not found")
	return None


def mainPanelObject():
	oDeb = mainFrameObject()
	if oDeb:
		for i in rangeGen(oDeb.childCount):
			o = oDeb.getChild(i)
			if o.name == "Main Panel":
				return o
		log.warning("mainPanelObject not found")
	return None


def toolDock1Object():
	o = topPanelObject()
	if o:
		o = findObjectByControlID(o, HIE_ToolDock1)
		if o:
			return o
		log.warning("toolDock1Object not found")
	return None


def _toolDock2Object():
	mainFrame = mainFrameObject()
	if mainFrame:
		o = findObjectByControlID(mainFrame, HIE_ToolDock2)
		if o:
			return o
		log.warning("toolDock2Object not found")
	return None


def _selectionToolBarObject():
	o = _toolDock2Object()
	if o:
		o = findObjectByControlID(o, HIE_SelectionToolBar)
		if o:
			return o
		log.warning("selectionToolbarObject not found")
	return None


def _timePaneObject():
	o = _toolDock2Object()
	if o:
		o = findObjectByControlID(o, HIE_TimePane)
		if o:
			return o
		log.warning("timePaneObject not found")
	return None


def audioPositionObject():
	if _audacityVersionID >= 2410:
		# position audio is now under time  pane
		o = _timePaneObject()
		if o is not None:

			if _audacityVersionID == 2410:
				# in v2.4.1 audioPosition object has no controlID
				o = o.getChild(1)
			else:
				o = findObjectByControlID(o, HIE_TimeAudioPosition)
			if o:
				return o
			log.warning("audioPositionObject not found in timeToolBar object")
	else:
		o = _selectionToolBarObject()
		if o is not None:
			o = findObjectByControlID(o, HIE_SelectionAudioPosition)
			if o:
				return o
			log.warning("audioPositionObject not found in selectionToolBar object")
	return None


def selectionChoiceObject():
	o = _selectionToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_SelectionChoice)
		if o:
			return o
		log.warning("selectionChoiceObject not found")
	return None


def selectionStartObject():
	o = _selectionToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_SelectionStart)
		if o:
			return o
		log.warning("selectionStartObject  not found")
	return None


def selectionEndObject():
	o = _selectionToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_SelectionEnd)
		if o:
			return o
		log.warning("selectionEndObject  not found")
	return None


def selectionDurationObject():
	o = _selectionToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_SelectionDuration)
		if o:
			return o
		log.warning("selectionDurationObject  not found")

	return None


def selectionCenterObject():
	o = _selectionToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_SelectionCenter)
		if o:
			return o
		log.warning("selectionCenterObject ")
	return None


def transportToolBarObject():
	obj = toolDock1Object()
	if obj:
		# the only solution to find transport toolbar
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 0 and o.childCount == 7:
				return o
	return None


def pauseButtonObject():
	o = transportToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_PauseButton)
		if o:
			return o
		log.warning("pauseButtonObject  not found")
	return None


def playButtonObject():
	o = transportToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_PlayButton)
		if o:
			return o
		log.warning("playButtonObject  not found")
	return None


def stopButtonObject():
	o = transportToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_StopButton)
		if o:
			return o
		log.warning("stopButtonObject  not found")
	return None


def recordButtonObject():
	o = transportToolBarObject()
	if o:
		o = findObjectByControlID(o, HIE_RecordButton)
		if o:
			return o
		log.warning("recordButtonObject  not found")
	return None


_buttonObjectsDic = {
	"play": playButtonObject,
	"pause": pauseButtonObject,
	"stop": stopButtonObject,
	"record": recordButtonObject
}


def isPressed(button):
	try:
		o = _buttonObjectsDic[button]()
	except:  # noqa: E722 Bare except
		log.warning("Button %s not found" % button)
		o = None
	if o and o.IAccessibleObject.accState(0) & STATE_SYSTEM_PRESSED:  # noqa: F405,E501 'STATE_SYSTEM_PRESSED' may be undefined, or defined from star, line too long
		return True
	return False


def isAvailable(button):
	try:
		o = _buttonObjectsDic[button]()
	except:  # noqa: E722 Bare except
		log.warning("Button %s not found" % button)
		o = None
	if (
			o and (o.IAccessibleObject.accState(0) & STATE_SYSTEM_UNAVAILABLE  # noqa: F405,E501
				or o.IAccessibleObject.accState(0) & STATE_SYSTEM_INVISIBLE)):  # noqa: F405,E501
		return False
	return True


def recordingMeterToolbarObject():
	obj = toolDock1Object()
	if obj:
		# the only solution to find transport toolbar
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 3 and o.childCount == 3:
				return o
	log.warning("error: recordingMeterToolbarObject not found")
	return None


def recordMeterPeakObject():
	o = recordingMeterToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_RecordMeterPeak)
		if o:
			return o
		log.warning("recordMeterPeakObject not found")
	return None


def playbackMeterToolbarObject():
	obj = toolDock1Object()
	if obj:
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 4 and o.childCount == 3:
				return o
	log.warning("error: playbackMeterToolbarObject not found")
	return None


def playMeterPeakObject():
	o = playbackMeterToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_PlayMeterPeak)
		if o:
			return o
		log.warning("playMeterPeakObject not found")
	return None


def mixerToolbarObject():
	obj = toolDock1Object()
	if obj:
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 5 and o.childCount == 6:
				return o
	log.warning("mixerToolbarObject not found")
	return None


def recordingSliderObject():
	o = mixerToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_RecordingSlider)
		if o:
			return o
		log.warning("recordingSliderObject not found")
	return None


def playbackSliderObject():
	o = mixerToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_PlaybackSlider)
		if o:
			return o
		log.warning("playbackSliderObject not found")
	return None


def PlayAtSpeedToolBarObject():
	obj = toolDock1Object()
	if obj:
		for i in rangeGen(obj.childCount):
			o = obj.getChild(i)
			if o.windowControlID == 7 and o.childCount == 4:
				return o
	log.warning("PlayAtSpeedToolBarObject not found")
	return None


def playbackSpeedSliderObject():
	o = PlayAtSpeedToolBarObject()
	if o:
		return getObjectByHierarchy(o, HIE_PlaybackSpeedSlider)
	return None
