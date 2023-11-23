# appModules\audacity\au_timerControl.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2018-2023, Paulber19
# This file is covered by the GNU General Public License.

from logHandler import log
from controlTypes.state import State
import ui
import api
from .au_time import formatTime, isNullDuration, getTimeMessage
from . import au_objects
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
			self.name = self.obj.name
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
			or State.INVISIBLE in self.obj.states
			or State.UNAVAILABLE in self.obj.states):
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
		if sAudioPosition == (None, None):
			# error or no track
			return None
		(sAudioPositionLabel, sAudioPositionTime) = sAudioPosition
		selection = SelectionTimers().getSelection()
		if selection is None:
			return None
		(
			(sfirstSelectionLabel, sfirstSelectionTime), (ssecondSelectionLabel, ssecondSelectionTime)
		) = selection
		msg = None
		if not isNullDuration(sfirstSelectionTime) and msg is not None:
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
			(sfirstSelectionLabel, sfirstSelectionTime), (ssecondSelectionLabel, ssecondSelectionTime)
		) = selection
		if not isNullDuration(sfirstSelectionTime):
			# there is a selection and  selection start is not start of track
			if (
				sAudioPositionTime == sfirstSelectionTime
				or isNullDuration(sAudioPositionTime)):
				# Translators: message to the user
				# to inform that the  audio position is at selection start.
				msg = "%s %s" % (_("Audio position at selection's start"), getTimeMessage(sfirstSelectionTime))
		return msg


class FirstSelectionTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.firstSelectionTimerObject()
		if obj is None:
			log.warning("no firstSelectionTimer object")
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(FirstSelectionTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SecondSelectionTimerControl(TimerControl):
	def __init__(self):
		obj = au_objects.secondSelectionTimerObject()
		if obj is None:
			log.warning("no secondSelectionTimer object")
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		editFormat = applicationSettingsManager.getSelectionFormat()
		super(SecondSelectionTimerControl, self).__init__(obj, editFormat)

	def getSelection(self):
		return self.getLabelAndTime()


class SelectionTimers(object):
	def __init__(self):
		self.firstSelectionTimer = FirstSelectionTimerControl()
		self.secondSelectionTimer = SecondSelectionTimerControl()

	def isAvailable(self):
		return (self.firstSelectionTimer and self.secondSelectionTimer) is not None

	def getSelection(self):
		firstSelectionLabelAndTime = self.firstSelectionTimer.getLabelAndTime()
		secondSelectionLabelAndTime = self.secondSelectionTimer.getLabelAndTime()
		return (firstSelectionLabelAndTime, secondSelectionLabelAndTime)

	def getSelectionMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		(
			(firstSelectionLabel, firstSelectionTime), (secondSelectionLabel, secondSelectionTime)
		) = selection
		if (firstSelectionTime, secondSelectionTime) == (None, None):
			return None

		# report timers of selection
		textList = []
		# Translators: message to user to indicate selection informations.
		textList.append(_("Selection: "))
		textList.append(firstSelectionLabel)
		textList.append(getTimeMessage(firstSelectionTime))
		textList.append(secondSelectionLabel)
		textList.append(getTimeMessage(secondSelectionTime))
		return " ".join(textList)

	def sayIfNoSelection(self, firstSelectionTime, secondSelectionTime):
		if (firstSelectionTime == secondSelectionTime) and isNullDuration(firstSelectionTime):
			# Translators: message to the user to inform that there is no selection.
			sayMessage(_("no selection"))
			return True
		return False

	def getIfNoSelectionMessage(self, firstSelectionTime, secondSelectionTime):
		if firstSelectionTime is None or secondSelectionTime is None:
			return None
		if (firstSelectionTime == secondSelectionTime) and isNullDuration(firstSelectionTime):
			# Translators: message to the user that there is no selection.
			return _("no selection")
		return None

	def getFirstSelectionTimerMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection == (None, None):
			return None
		(
			(firstSelectionLabel, firstSelectionTime), (secondSelectionLabel, secondSelectionTime)
		) = selection
		textList = []
		textList.append(firstSelectionLabel)
		textList.append(getTimeMessage(firstSelectionTime))
		return " ".join(textList)

	def getSecondSelectionTimerMessage(self, selection=None):
		if selection is None:
			selection = self.getSelection()
		if selection == (None, None):
			return None
		(
			(firstSelectionLabel, firstSelectionTime), (secondSelectionLabel, secondSelectionTime)
		) = selection
		textList = []
		textList.append(secondSelectionLabel)
		textList.append(getTimeMessage(secondSelectionTime))
		return " ".join(textList)
