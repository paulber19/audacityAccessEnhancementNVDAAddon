# appModules\audacity\au_timerControl.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2018-2022, Paulber19
# This file is covered by the GNU General Public License.

from logHandler import log
try:
	# for nvda version >= 2021.2
	from controlTypes.state import State
	STATE_INVISIBLE = State.INVISIBLE
	STATE_UNAVAILABLE = State.UNAVAILABLE
except ImportError:
	from controlTypes import (
		STATE_INVISIBLE, STATE_UNAVAILABLE
	)

import ui
import api
from .au_time import formatTime, isNullDuration, getTimeMessage
from . import au_objects
from .au_objects import selectionChoiceObject
import addonHandler
addonHandler.initTranslation()

SELFOR_SECONDS = 0
SELFOR_HHMMSS = 1
SELFOR_DDHHMMSS = 2
SELFOR_HHMMSS_HUNDREDTHS = 3
SELFOR_HHMMSS_MILLISECONDS = 4
SELFOR_HHMMSS_SAMPLES = 5
SELFOR_SAMPLES = 6

_selectionFormatIDs = {
	"seconds": SELFOR_SECONDS,  # XXX,YYY seconds
	"hh:mm:ss": SELFOR_HHMMSS,  # 00 h 00 m 00 s
	"dd:hh:mm:ss": SELFOR_DDHHMMSS,  # 00 days 00 h 00 m 00 s
	"hh:mm:ss + hundredths": SELFOR_HHMMSS_HUNDREDTHS,  # 00 h 00 m 01.00 s
	"hh:mm:ss + milliseconds": SELFOR_HHMMSS_MILLISECONDS,  # 00 h 00 m 01.000 s
	"hh:mm:ss + samples": SELFOR_HHMMSS_SAMPLES,  # 00 h 00 m 01 s+00000 samples
	"samples": SELFOR_SAMPLES,  # 000,000,000 samples
	"hh:mm:ss + film frames (24 fps)": 7,  # 00 h 00 m 00 s+00 frames
	"film frames (24 fps)": 8,  # 000,000 frames
	"hh:mm:ss + NTSC drop frames": 9,  # 00 h 00 m 00 s+00 frames
	"NTSC frames": 11,  # 000,030 frames
	"hh:mm:ss + PAL frames (25 fps)": 12,  # 00 h 00 m 01 s+01 frames
	"PAL frames (25 fps)": 13,  # 000,026 frames
	"hh:mm:ss + CDDA frames (75 fps)": 14,  # 00 h 00 m 00 s+02 frames
	"CDDA frames (75 fps)": 15,  # XXX,YYY frames,  # 000,077 frames
}


def format_XXXYYY(text):
	text = text.replace(",", "")
	lTemp = text.split(" ")
	return " ".join(lTemp[:-1])


def format_HHMMSS(text):
	return text


def format_DDHHMMSS(text):
	return text


def format_HHMMSS_samples(text):
	lTemp = text.split(" ")
	return " ".join(lTemp[:-1])


def format_samples(text):
	text = text.replace(",", "")
	lTemp = text.split(" ")
	return "+" + lTemp[0]


def sayMessage(msg):
	api.processPendingEvents()
	ui.message(msg)


_selectionFormats = {
	"seconds": (2, format_XXXYYY),  # XXX,YYY seconds
	"hh:mm:ss": (6, format_HHMMSS),  # 00 h 00 m 00 s
	"dd:hh:mm:ss": (8, format_DDHHMMSS),  # 00 days 00 h 00 m 00 s
	"hh:mm:ss + hundredths": (6, format_HHMMSS),  # 00 h 00 m 01.00 s
	"hh:mm:ss + milliseconds": (6, format_HHMMSS),  # 00 h 00 m 01.000 s
	"hh:mm:ss + samples": (7, format_HHMMSS_samples),
	"samples": (2, format_samples),  # 000,000,000 samples
	"hh:mm:ss + film frames (24 fps)": None,
	"film frames (24 fps)": None,  # 000,000 frames
	"hh:mm:ss + NTSC drop frames": None,  # 00 h 00 m 00 s+00 frames
	"hh:mm:ss + NTSC drop frames": None,  # 00 h 00 m 00 s+000 frames
	"NTSC frames": None,  # 000,030 frames
	"hh:mm:ss + PAL frames (25 fps)": None,  # 00 h 00 m 01 s+01 frames
	"PAL frames (25 fps)": None,  # 000,026 frames
	"hh:mm:ss + CDDA frames (75 fps)": None,  # 00 h 00 m 00 s+02 frames
	"CDDA frames (75 fps)": None,  # XXX,YYY frames,  # 000,077 frames
}


class TimerControl(object):
	def __init__(self, obj, editFormat):
		self.obj = obj
		if obj is None:
			# error
			log.warning("error, not timerControl object %s" % self.__class__)
			self.name = ""
		else:
			self.name = self.obj.IAccessibleObject.accName(0) if self.obj is not None else None
		self.selectionFormat = editFormat
		self.selectionFormatID = _selectionFormatIDs[self.selectionFormat]

	def getLabelAndTime(self):

		def getTime(text):
			t = text.split(" ")
			if len(t) > 1:
				t = t[:-1]
			t = "".join(t)
			return t

		def getLabel(text, nb):
			lTemp = text.split(" ")
			lTemp = lTemp[:-nb]
			return " ".join(lTemp)

		timerControlName = self.name
		if timerControlName is None:
			return (timerControlName, None)
		try:
			(nb, funct) = _selectionFormats[self.selectionFormat]
		except Exception:
			return (None, None)
		label = getLabel(timerControlName, nb)
		timerControlName = timerControlName.replace(label, "").strip()
		sTime = funct(timerControlName)
		sTime = formatTime(sTime)
		return (label, sTime)

	def isAvailable(self):
		if (
			self.obj is None
			or len(self.obj.states) == 0
			or STATE_INVISIBLE in self.obj.states
			or STATE_UNAVAILABLE in self.obj.states):
			return False
		return True

	def check(self):
		if not self.isAvailable():
			return False
		(sLabel, sTime) = self.getLabelAndTime()
		if sTime is None:
			return False

		sTemp = ""
		for c in sTime:
			if c in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
				sTemp = sTemp + "*"
			else:
				sTemp = sTemp + c
		if sTemp.lower() in ["**:**:**", "**:**:**.**", "**:**:**.***"]:
			return True
		return False


class AudioTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.audioPositionObject()
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getAudioTimeFormat()
		super(AudioTimerControl, self).__init__(obj, editFormat)

	def getAudioPosition(self):
		return self.getLabelAndTime()

	def getAudioPositionMessage(self):
		if not self.isAvailable():
			return None
		sAudioPosition = self.getLabelAndTime()
		if sAudioPosition is None:
			# error
			return None
		(sAudioPositionLabel, sAudioPositionTime) = sAudioPosition
		selection = SelectionTimers().getSelection()
		if selection is None:
			return None

		(
			(sSelectionStartLabel, sSelectionStartTime), (sSelectionEndLabel, sSelectionEndTime),
			selectionDuration, selectionCenter) = selection
		msg = self.getIfAudioAtStartOfSelectionMessage(sAudioPosition, selection)
		if not isNullDuration(sSelectionStartTime) and msg is not None:
			pass
		else:
			# not selection  or selection at start of track
			if isNullDuration(sAudioPositionTime):
				# Translators: message to the user
				# to inform that audio position is at track start.
				msg = _("Audio position at start of track")
			else:
				msg = sAudioPositionLabel
				msg = "%s %s" % (msg, getTimeMessage(sAudioPositionTime))
		return msg
		return None

	def getIfAudioAtStartOfSelectionMessage(self, sAudioPosition, selection):
		msg = None
		(sAudioPositionLabel, sAudioPositionTime) = sAudioPosition
		(
			(sSelectionStartLabel, sSelectionStartTime), (sSelectionEndLabel, sSelectionEndTime),
			selectionDuration, selectionCenter) = selection
		if not isNullDuration(sSelectionStartTime):
			# there is a selection and  selection start is not start of track
			if (
				sAudioPositionTime == sSelectionStartTime
				or isNullDuration(sAudioPositionTime)):
				# Translators: message to the user
				# to inform that the  audio position is at selection start.
				msg = "%s %s" % (_("Audio position at selection's start"), getTimeMessage(sSelectionStartTime))
		return msg


class SelectionStartTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.selectionStartObject()
		if obj is None:
			log.warning("no selectionStart object")
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(SelectionStartTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SelectionEndTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.selectionEndObject()
		if obj is None:
			log.warning("no selectionEnd object")
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(SelectionEndTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SelectionDurationTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.selectionDurationObject()
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(SelectionDurationTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SelectionCenterTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.selectionCenterObject()
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(SelectionCenterTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SelectionTimers(object):
	def __init__(self):
		self.selectionStart = SelectionStartTimerControl()
		self.selectionEnd = SelectionEndTimerControl()
		self.selectionDuration = SelectionDurationTimerControl()
		self.selectionCenter = SelectionCenterTimerControl()
		self.selectionChoice = selectionChoiceObject()

	def isAvailable(self):
		return (self.selectionStart and self.selectionEnd) is not None

	def getSelection(self):
		selectionStart = self.selectionStart.getLabelAndTime()
		selectionEnd = self.selectionEnd.getLabelAndTime()
		selectionDuration = self.selectionDuration.getLabelAndTime()
		selectionCenter = self.selectionCenter.getLabelAndTime()
		return (selectionStart, selectionEnd, selectionDuration, selectionCenter)

	def getSelectionMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		(
			(selectionStartLabel, selectionStartTime), (selectionEndLabel, selectionEndTime),
			selectionDuration, selectionCenter) = selection
		if (selectionStartTime, selectionEndTime) == (None, None):
			return None
		if self.sayIfNoSelection(selectionStartTime, selectionEndTime):
			return None
		# report start and end of selection
		textList = []
		# Translators: message to user to indicate selection informations.
		textList.append(_("Selection: "))
		textList.append(selectionStartLabel)
		textList.append(getTimeMessage(selectionStartTime))
		textList.append(selectionEndLabel)
		textList.append(getTimeMessage(selectionEndTime))
		return " ".join(textList)

	def getSelectionDurationMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection is None:
			return None
		(
			(selectionStartLabel, selectionStartTime), (selectionEndLabel, selectionEndTime),
			selectionDuration, selectionCenter) = selection
		if selectionDuration[1] is None:
			return None
		if self.sayIfNoSelection(selectionStartTime, selectionEndTime):
			return None
		(selectionDurationLabel, selectionDurationTime) = selectionDuration
		textList = []
		# Translators: message to user to indicate selection informations.
		textList.append(_("Selection: "))
		textList.append(selectionDurationLabel)
		textList.append(getTimeMessage(selectionDurationTime))
		return " ".join(textList)

	def getSelectionCenterMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection is None:
			return None
		(
			(selectionStartLabel, selectionStartTime), (selectionEndLabel, selectionEndTime),
			selectionDuration, selectionCenter) = selection
		if selectionCenter[1] is None:
			return None
		if self.sayIfNoSelection(selectionStartTime, selectionEndTime):
			return None
		(selectionCenterLabel, selectionCenterTime) = selectionCenter
		textList = []
		# Translators: message to user to indicate selection informations.
		textList.append(_("Selection: "))
		textList.append(selectionCenterLabel)
		textList.append(getTimeMessage(selectionCenterTime))
		return " ".join(textList)

	def sayIfNoSelection(self, selectionStartTime, selectionEndTime):
		if (selectionStartTime == selectionEndTime) and isNullDuration(selectionStartTime):
			# Translators: message to the user to inform that there is no selection.
			sayMessage(_("no selection"))
			return True
		return False

	def getIfNoSelectionMessage(self, selectionStartTime, selectionEndTime):
		if selectionStartTime is None or selectionEndTime is None:
			return None
		if (selectionStartTime == selectionEndTime) and isNullDuration(selectionStartTime):
			# Translators: message to the user that there is no selection.
			return _("no selection")
		return None

	def getSelectionStartMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection is None:
			return None
		(
			(selectionStartLabel, selectionStartTime), (selectionEndLabel, selectionEndTime),
			selectionDuration, selectionCenter) = selection
		textList = []
		# sayMessage (selectionStartLabel)
		textList.append(selectionStartLabel)
		textList.append(getTimeMessage(selectionStartTime))
		return " ".join(textList)

	def getSelectionEndMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection is None:
			return None

		(
			(selectionStartLabel, selectionStartTime), (selectionEndLabel, selectionEndTime),
			selectionDuration, selectionCenter) = selection
		return "%s %s" % (selectionEndLabel, getTimeMessage(selectionEndTime))
