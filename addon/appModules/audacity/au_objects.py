# appModules\audacity\au_objects.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018-2023,paulber19
# This file is covered by the GNU General Public License.


import addonHandler
from logHandler import log
import api
import ui
from oleacc import (
	STATE_SYSTEM_PRESSED, STATE_SYSTEM_UNAVAILABLE, STATE_SYSTEM_INVISIBLE,
)


addonHandler.initTranslation()
# Translators: name of upper panel
upperPanelName = _("Upper panel")
# Translators: name of lower panel
lowerPanelName = _("Lower panel")
# Translators: name of main panel
mainPanelName = _("Main panel")


# object hierarchy ids
HIE_TopPanel = 1
HIE_TrackView = 2
HIE_ToolDock1 = 3
HIE_ToolDock2 = 4
HIE_TransportToolBar = 5
HIE_PauseButton = 6
HIE_PlayButton = 7
HIE_StopButton = 8
HIE_RecordButton = 9
HIE_AudioPosition = 10
HIE_FirstSelectionTimer = 11
HIE_SecondSelectionTimer = 12
HIE_AudacityTranscriptionToolbar = 13
HIE_PlaybackSpeedSlider = 14
HIE_RecordMeterPeak = 15
HIE_PlayMeterPeak = 16
HIE_RecordingSlider = 17
HIE_PlaybackSlider = 18
HIE_TimeAudioPosition = 19
HIE_RecordingMeterToolbar = 21
HIE_TimePane = 22
HIE_PlaybackMeterToolBar = 23

# for audacity 3.4.0
# no change from base version
_controlIDs_3400 = {}

# base control IDs for audacity from version v3.3.0
_controlIDsBase = {
	HIE_TrackView: 1003,  # in mainPanelObject
	HIE_SecondSelectionTimer: 1,  # text  object in selectionToolbarObject
	HIE_TimeAudioPosition: 2801,  # text in timePane object
	HIE_PauseButton: 11000,  # button in transportToolBar object
	HIE_PlayButton: 11001,  # button in transportToolBar object
	HIE_StopButton: 11002,  # button in transportToolBar object
	HIE_RecordButton: 11005,  # button in transportToolBar object
}

# object hierarchy paths
# for audacity 3.3.x
_hierarchy_3300 = {
	HIE_TopPanel: "0",  # from mainFrame object
	HIE_ToolDock1: "0|0",  # from mainFrame object
	HIE_ToolDock2: "3",  # from mainFrame object
	HIE_RecordingMeterToolbar: "7",  # from tooldock1 object
	HIE_RecordingSlider: "0",  # from RecordingMeterToolbar object
	HIE_RecordMeterPeak: "2",  # from HIE_RecordingMeterToolbar
	HIE_PlaybackMeterToolBar: "6",  # from tooldock1 object
	HIE_PlaybackSlider: "0",  # from playbackMeterToolbar
	HIE_PlayMeterPeak: "2",  # from PlaybackMeterToolbar
	HIE_TransportToolBar: "2",  # from tooldock1 object
	HIE_PlaybackSpeedSlider: "5|2",  # from tooldock2  object
	HIE_TimePane: "3",  # from tooldock2 object
	HIE_FirstSelectionTimer: "0|2",  # from tooldock2 object
	HIE_SecondSelectionTimer: "0|4",  # from tooldock2 object
}


_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']
_audacityHierarchyPaths = None
_audacityVersionID = None
_controlIDs = None


def initialize(appModule):
	global _audacityHierarchyPaths, _audacityVersionID, _controlIDs
	version = appModule._get_productVersion()
	_audacityVersionID = int("".join(version.split(",")))
	id = _hierarchy_3300
	_controlIDs = _controlIDsBase.copy()
	if _audacityVersionID >= 3400:
		_controlIDs.update(_controlIDs_3400)
	if _audacityVersionID >= 3300:
		pass
	else:
		log.warning(
			"This version %s of Audacity is not supported" % version)
	_audacityHierarchyPaths = id


def get_audacityVersionID():
	return _audacityVersionID


def getObjectByHierarchy(oParent, iHierarchy):
	sHierarchy = _audacityHierarchyPaths.get(iHierarchy)
	if sHierarchy is None:
		return None
	hierarchy = sHierarchy.split("|")
	o = oParent
	try:
		for i in hierarchy:
			iChild = int(i)
			if o and iChild < o.childCount:
				o = o.getChild(iChild)
			else:
				# error, no child
				log.error("no object or no child: %s, child: %s" % (o, iChild))
				return None
		return o
	except Exception:
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
	o = mainFrameObject()
	if o:
		o = getObjectByHierarchy(o, HIE_TopPanel)
		if o:
			return o
	log.warning("topPanelObject not found")
	return None


def toolDock1Object():
	o = mainFrameObject()
	if o:
		o = getObjectByHierarchy(o, HIE_ToolDock1)
		if o:
			return o
		log.warning("toolDock1Object not found")
	return None


def _toolDock2Object():
	o = mainFrameObject()
	if o:
		o = getObjectByHierarchy(o, HIE_ToolDock2)
		if o:
			return o
		log.warning("toolDock2Object not found")
	return None


def _timePaneObject():
	o = _toolDock2Object()
	if o:
		o = getObjectByHierarchy(o, HIE_TimePane)
		if o:
			return o
		log.warning("timePaneObject not found")
	return None


def audioPositionObject():
	o = _timePaneObject()
	if o is not None:
		o = findObjectByControlID(o, HIE_TimeAudioPosition)
	if o:
		return o
	log.warning("audioPositionObject not found in timeToolBar object")
	return None


def firstSelectionTimerObject():
	o = _toolDock2Object()
	if o:
		o = getObjectByHierarchy(o, HIE_FirstSelectionTimer)
		if o:
			return o
		log.warning("firstSelectionTimerObject  not found")
	return None


def secondSelectionTimerObject():
	o = _toolDock2Object()
	if o:
		o = getObjectByHierarchy(o, HIE_SecondSelectionTimer)
		if o:
			return o
		log.warning("secondSelectionTimerObject  not found")
	return None


def transportToolBarObject():
	obj = toolDock1Object()
	if obj:
		o = getObjectByHierarchy(obj, HIE_TransportToolBar)
		if o:
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
	except Exception:
		log.warning("Button %s not found" % button)
		return False
	# in v3.3.3, pressed state is not available for play and pause buttons
	# so the only thing we can do is to look to the button name
	# name is completed with "button" and "pressed" or "not pressed"
		# if name has 3 words, state is pressed else not pressed
		# we hope this works in all languages

	if button in ["play", "pause"]:
		nameList = o.name.split(" ")
		if len(nameList) == 3:
			return True
		return False
	# for other buttonslike "record" button
	if o.IAccessibleObject.accState(0) & STATE_SYSTEM_PRESSED:
		return True
	return False


def isAvailable(button):
	try:
		o = _buttonObjectsDic[button]()
	except Exception:
		log.warning("Button %s not found" % button)
		o = None
	if (o and (
		o.IAccessibleObject.accState(0) & STATE_SYSTEM_UNAVAILABLE
		or o.IAccessibleObject.accState(0) & STATE_SYSTEM_INVISIBLE)):
		return False
	return True


def recordingMeterToolbarObject():
	o = toolDock1Object()
	if o:
		o = getObjectByHierarchy(o, HIE_RecordingMeterToolbar)
		if o:
			return o
	log.warning("error: recordingMeterToolbarObject not found")
	return None


def recordingSliderObject():
	o = recordingMeterToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_RecordingSlider)
		if o:
			return o
	log.warning("recordingSliderObject not found")
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
	o = toolDock1Object()
	if o:
		o = getObjectByHierarchy(o, HIE_PlaybackMeterToolBar)
		if o:
			return o
	log.warning("error: playbackMeterToolbarObject not found")
	return None


def playbackSliderObject():
	o = playbackMeterToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_PlaybackSlider)
		if o:
			return o
	log.warning("playbackSliderObject not found")
	return None


def playMeterPeakObject():
	o = playbackMeterToolbarObject()
	if o:
		o = getObjectByHierarchy(o, HIE_PlayMeterPeak)
		if o:
			return o
		log.warning("playMeterPeakObject not found")
	return None


def playbackSpeedSliderObject():
	o = _toolDock2Object()
	if o:
		o = getObjectByHierarchy(o, HIE_PlaybackSpeedSlider)
		if o:
			return o
	log.warning("playbackSpeedSliderObjectnot found")
	return None


def reportTransportButtonsState():
	pressed = False
	if isAvailable("record") and isPressed("record"):
		# Translators: message to user when button record is pressed.
		ui.message(_("record button pressed"))
		pressed = True
	o = playButtonObject()
	if o:
		ui.message(o.name)
	o = pauseButtonObject()
	if o:
		# Translators: message to the user when pause button is pressed.
		ui.message(o.name)
		pressed = True

	if not pressed:
		# Translators: message to the user when no button is pressed.
		ui.message(_("No button pressed"))
