# appModules\audacity\__init__.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2018-2022, Paulber19
# This file is covered by the GNU General Public License.
# Released under GPL 2

import addonHandler
import appModuleHandler
import inputCore
from versionInfo import version_year, version_major
NVDAVersion = [version_year, version_major]
if NVDAVersion >= [2021, 3]:
	# for nvda version >= 2021.3
	from controlTypes.role import Role
	ROLE_TABLEROW = Role.TABLEROW
	ROLE_UNKNOWN = Role.UNKNOWN
	ROLE_TABLE = Role.TABLE
	ROLE_BUTTON = Role.BUTTON
	ROLE_STATICTEXT = Role.STATICTEXT
	ROLE_PANE = Role.PANE
	from controlTypes.state import State
	STATE_UNAVAILABLE = State.UNAVAILABLE
	STATE_INVISIBLE = State.INVISIBLE
	STATE_FOCUSABLE = State.FOCUSABLE
	STATE_SELECTED = State.SELECTED
	# adding role for audacity
	ROLE_TRACKVIEW = None
	ROLE_TRACK = None
	from controlTypes.role import _roleLabels as roleLabels
else:
	# for nvda version <2021.3
	from controlTypes import (
		ROLE_TABLEROW, ROLE_UNKNOWN,
		ROLE_TABLE, ROLE_BUTTON,
		ROLE_STATICTEXT, ROLE_PANE,
		roleLabels
	)
	from controlTypes import (
		STATE_UNAVAILABLE, STATE_INVISIBLE, STATE_FOCUSABLE,
		STATE_SELECTED
	)
	# role for audacity
	ROLE_TRACKVIEW = 300
	ROLE_TRACK = 301
# no label for this role
roleLabels[ROLE_TRACKVIEW] = ""
roleLabels[ROLE_TRACK] = ""

import os
import eventHandler
import queueHandler
import scriptHandler
import gui
import wx
import ui
import speech
import api
import NVDAObjects
from functools import wraps
import tones
import winInputHook
from . import au_time
from . import au_timerControl
from . import au_objects
from .au_timerControl import (
	SELFOR_SECONDS, SELFOR_HHMMSS, SELFOR_DDHHMMSS,
	SELFOR_HHMMSS_HUNDREDTHS, SELFOR_HHMMSS_MILLISECONDS, SELFOR_HHMMSS_SAMPLES,
	SELFOR_SAMPLES,
)

from .au_utils import isOpened, makeAddonWindowTitle
from .au_NVDAStrings import NVDAString
import sys
_curAddon = addonHandler.getCodeAddon()
debugToolsPath = os.path.join(_curAddon.path, "debugTools")
sys.path.append(debugToolsPath)
try:
	from appModuleDebug import AppModuleDebug as AppModule
	from appModuleDebug import printDebug, toggleDebugFlag
except ImportError:
	from appModuleHandler import AppModule as AppModule

	def printDebug(msg):
		return

	def toggleDebugFlag(debug=False):
		return
del sys.path[-1]
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from au_addonConfigManager import _addonConfigManager
del sys.path[-1]

addonHandler.initTranslation()

# to save current winInputHook keyDownCallback function before hook
_winInputHookKeyDownCallback = None


# timer for repeatCount management
GB_taskTimer = None
# timer to monitor audio and selection changes
GB_monitorTimer = None
# audio position  monitor
GB_audioPosition = None
# selection monitor
GB_selection = None
# record button state monitor
GB_recordButtonIsPressed = False


_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']
_addonVersion = _curAddon.manifest['version']
_addonName = _curAddon.manifest['name']
_scriptCategory = str(_addonSummary)


def monitorAudioAndSelectionChanges():
	global GB_monitorTimer, GB_audioPosition,\
		GB_selection, GB_recordButtonIsPressed

	def getRecordChangeMessage():
		global GB_recordButtonIsPressed
		recordButtonIsPressed = au_objects.isPressed("record")
		msg = None
		if not recordButtonIsPressed and GB_recordButtonIsPressed:
			# Translators: message to the user to report state of record button.
			msg = _("Recording stopped")
		elif recordButtonIsPressed and not GB_recordButtonIsPressed:
			# Translators: message to the user to report state of record button.
			msg = _("Recording")
		GB_recordButtonIsPressed = recordButtonIsPressed
		return msg

	def getSelectionChangeMessage(audioChangeMessage):
		global GB_selection, GB_audioPosition
		selectionTimer = au_timerControl.SelectionTimers()
		if not selectionTimer.isAvailable:
			return None
		newSelection = selectionTimer.getSelection()
		msgList = []
		if _addonConfigManager .toggleAutomaticSelectionChangeReportOption(False):
			if GB_selection is None:
				GB_selection = newSelection
			(
				(selectionStartLabel, selectionStartTime),
				(selectionEndLabel, selectionEndTime),
				selectionDuration, selectionCenter) = newSelection
			(
				(selectionStartLabel, oldSelectionStartTime),
				(selectionEndLabel, oldSelectionEndTime),
				selectionDuration, selectionCenter) = GB_selection
			# change to no selection ?
			msg = selectionTimer.getIfNoSelectionMessage(selectionStartTime, selectionEndTime)
			if (
				(selectionStartTime != oldSelectionStartTime or selectionEndTime != oldSelectionEndTime)
				and msg is not None):
				msgList.append(msg)
			else:
				# no
				if selectionStartTime != oldSelectionStartTime:
					audioTimer = au_timerControl.AudioTimerControl()
					if not audioTimer.isAvailable():
						return None
					msg = audioTimer.getIfAudioAtStartOfSelectionMessage(GB_audioPosition, newSelection)
					if msg is not None:
						if msg != audioChangeMessage:
							newAudioPosition = audioTimer.getAudioPosition()
							GB_audioPosition = newAudioPosition
						else:
							msg = None
					else:
						msg = selectionTimer.getSelectionStartMessage(newSelection)
					if msg is not None:
						msgList.append(msg)
				if selectionEndTime != oldSelectionEndTime:
					msg = selectionTimer.getSelectionEndMessage(newSelection)
					if msg is not None:
						msgList.append(msg)
		GB_selection = newSelection
		if len(msgList):
			return " ".join(msgList)
		return None

	def getAudioChangeMessage():
		global GB_audioPosition
		audioTimer = au_timerControl.AudioTimerControl()
		if not audioTimer.isAvailable():
			return None
		newAudioPosition = audioTimer.getAudioPosition()
		msg = None
		if newAudioPosition != GB_audioPosition:
			msg = audioTimer.getAudioPositionMessage()
		GB_audioPosition = newAudioPosition
		return msg

	obj = api.getFocusObject()
	if obj.appModule.appName != "audacity"\
		or not obj.appModule.inTrackView(obj, False):
		return

	# record change
	msg = getRecordChangeMessage()
	if msg is not None:
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, msg)
		return

	if (
		GB_recordButtonIsPressed
		or (au_objects.isPressed("play") and not au_objects.isPressed("pause"))):
		# don't speak selection or audio position
		return
	if obj.role == ROLE_TRACKVIEW and obj.childCount == 0:
		# no track in track view, so no selection and audio
		return

	# audio change
	textList = []
	msg = getAudioChangeMessage()
	if msg is not None:
		textList.append(msg)
	# selectionchange
	msg = getSelectionChangeMessage(msg)
	if msg is not None:
		textList.append(msg)
	if len(textList):
		msg = " ".join(textList)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, msg)


def finally_(func, final):
	"""Calls final after func, even if it fails."""
	def wrap(f):
		@wraps(f)
		def new(*args, **kwargs):
			try:
				func(*args, **kwargs)
			finally:
				final()
		return new
	return wrap(final)


def stopTaskTimer():
	global GB_taskTimer
	if GB_taskTimer is not None:

		GB_taskTimer .Stop()
		GB_taskTimer = None


class Slider(object):
	def __init__(self):
		self.obj = None

	def isAvailable(self):
		if self.obj is None:
			return False
		states = self.obj.states
		if (
			STATE_UNAVAILABLE in states
			or STATE_INVISIBLE in states
			or STATE_FOCUSABLE not in states):
			name = self.obj.name if self.obj.name is not None else ""
			# Translators: message to user to inform  that slider is not available.
			msg = _("%s not available") % name
			ui.message(msg)
			return False
		return True

	def reportLevel(self):
		if not self.isAvailable():
			return
		name = self.obj.name
		value = self.obj.value
		ui.message("%s: %s" % (name, value))


class PlaybackSlider(Slider):
	def __init__(self):
		self.obj = au_objects.playbackSliderObject()


class RecordingSlider(Slider):
	def __init__(self):
		self.obj = au_objects.recordingSliderObject()


class MeterPeak (object):
	def __init__(self):
		self.obj = None

	def isAvailable(self):
		if self.obj is None:
			return False
		states = self.obj.states
		if (
			STATE_UNAVAILABLE in states
			or STATE_INVISIBLE in states
			or STATE_FOCUSABLE not in states):
			name = self.obj.name if self.obj.name is not None else ""
			if len(name):
				name = " ".join(name.split(" ")[:-2])
			# Translators: message to user to inform that meter peak is not available.
			msg = _("%s not available") % name
			ui.message(msg)
			return False
		return True

	def reportLevel(self):
		if not self.isAvailable():
			return
		peak = self.obj.name.replace(" - ", ": ")
		ui.message(peak)

	def setFocus(self):
		# nothing works !!!
		def callback():
			self.obj.IAccessibleObject.accSelect(1, 0)

		if self.isAvailable():
			wx.CallAfter(callback)


class PlayMeterPeak(MeterPeak):
	def __init__(self):
		self.obj = au_objects.playMeterPeakObject()


class RecordMeterPeak(MeterPeak):
	def __init__(self):
		self.obj = au_objects.recordMeterPeakObject()


class TrackView (NVDAObjects.NVDAObject):
	def _get_role(self):
		return ROLE_TRACKVIEW

	def event_gainFocus(self):
		super(TrackView, self).event_gainFocus()
		if self.childCount == 0:
			# Translators: message to user that there is no track in tracks view.
			ui.message(_("No track"))
		else:
			global GB_monitorTimer, GB_audioPosition, GB_selection, GB_recordButtonIsPressed
			GB_audioPosition = None
			GB_selection = None
			GB_recordButtonIsPressed = None
			wx.CallLater(200, monitorAudioAndSelectionChanges)


class Track(NVDAObjects.NVDAObject):
	def initOverlayClass(self):
		pass

	def _get_role(self):
		return ROLE_TRACK

	def _get_roleText(self):
		return ""

	def _get_states(self):
		states = super(Track, self)._get_states()
		if STATE_SELECTED in states:
			# selection state is already set in name bby audacity , so remove this state
			states.remove(STATE_SELECTED)
		return states

	def event_gainFocus(self):
		super(Track, self).event_gainFocus()

	@staticmethod
	def check(obj):
		# check if it is a track in tracks panel view
		try:
			if ((
				obj.role in [ROLE_TABLEROW, ROLE_UNKNOWN]
				and obj.windowControlID == 1003)
				and obj.parent.windowControlID == 1003):
				return True
		except Exception:
			pass
		return False


class TimerControlEdit(NVDAObjects.NVDAObject):
	def initOverlayClass(self):
		self.bindGesture("kb:nvda+upArrow", "sayTimer")

	def script_sayTimer(self, gesture):
		tc = au_timerControl.TimerControl(self)
		(sLabel, sTime) = tc.getLabelAndTime()
		msg = "%s" % au_time.getTimeMessage(sTime)
		ui.message(msg)

	def event_gainFocus(self):
		tc = au_timerControl.TimerControl(self)
		(sLabel, sTime) = tc.getLabelAndTime()
		try:
			msg = "%s %s" % (sLabel, au_time.getTimeMessage(sTime))
			ui.message(msg)
		except Exception:
			super(TimerControlEdit, self).event_gainFocus()


# digit groups IDs
DGROUP_HOURS = 1
DGROUP_MINUTES = 2
DGROUP_SECONDS = 3
DGROUP_SECOND_THOUSANDS = 4
DGROUP_SECONDS_HUNDREDTHS = 5
DGROUP_MILLISECONDS = 6
DGROUP_DAYS = 7
DGROUP_SAMPLES = 8
DGROUP_SAMPLE_THOUSANDS = 9

# digit IDs
DIGIT_HOUR_UNITS = 1
DIGIT_HOUR_DOZENS = 2
DIGIT_MINUTE_UNITS = 3
DIGIT_MINUTE_DOZENS = 4
DIGIT_SECOND_UNITS = 5
DIGIT_SECOND_DOZENS = 6
DIGIT_SECOND_HUNDREDS = 7
DIGIT_SECOND_THOUSANDS = 8
DIGIT_SECOND_TENS_THOUSANDS = 9
DIGIT_SECOND_HUNDREDS_THOUSANDS = 10
DIGIT_SECOND_TENTHS = 11
DIGIT_SECOND_HUNDREDTHS = 12
DIGIT_SECOND_THOUSANDTHS = 13
DIGIT_DAY_UNITS = 14
DIGIT_DAY_DOZENS = 15
DIGIT_UNITS = 16
DIGIT_DOZENS = 17
DIGIT_HUNDREDS = 18
DIGIT_THOUSANDS = 19
DIGIT_TENS_THOUSANDS = 20
DIGIT_HUNDREDS_THOUSANDS = 21
DIGIT_MILLIONS = 22
DIGIT_SAMPLE_UNITS = 23
DIGIT_SAMPLE_DOZENS = 24
DIGIT_SAMPLE_HUNDREDS = 25
DIGIT_SAMPLE_THOUSANDS = 26
DIGIT_SAMPLE_TENS_THOUSANDS = 27
DIGIT_SAMPLE_HUNDREDS_THOUSANDS = 28

# names of selection format digits
_digitNames = {
	# Translators:  name of a digit in  selection format.
	DIGIT_HOUR_UNITS: _("units of hours"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HOUR_DOZENS: _("dozens of hours"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MINUTE_UNITS: _("units of minutes"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MINUTE_DOZENS: _("dozens of minutes"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_UNITS: _("units of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_DOZENS: _("dozens of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDS: _("hundreds of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_THOUSANDS: _("thounsands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_TENS_THOUSANDS: _("tens thousands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDS_THOUSANDS: _("hundreds thousands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_TENTHS: _("tenths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDTHS: _("hundredths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_THOUSANDTHS: _("thousandths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DAY_UNITS: _("units of days"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DAY_DOZENS: _("dozens of days"),
	# Translators:  name of a digit in  selection format.
	DIGIT_UNITS: _("units"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DOZENS: _("dozens"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HUNDREDS: _("hundreds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_THOUSANDS: _("thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_TENS_THOUSANDS: _("tens of thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HUNDREDS_THOUSANDS: _("hundreds of thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MILLIONS: _("millions"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_UNITS: _("units of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_DOZENS: _("dozens of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_HUNDREDS: _("hundreds of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_THOUSANDS: _("thounsands of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_TENS_THOUSANDS: _("tens thousands of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_HUNDREDS_THOUSANDS: _("hundreds thousands of samples"),
}
# names of selection format digit groups
_digitGroupNames = {
	# Translators: name of a selection format digit group.
	DGROUP_HOURS: _("hours"),
	# Translators: name of a selection format digit group.
	DGROUP_MINUTES: _("minutes"),
	# Translators: name of a selection format digit group.
	DGROUP_SECOND_THOUSANDS: _("thousands seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_SECONDS: _("seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_SECONDS_HUNDREDTHS: _("hundredths seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_MILLISECONDS: _("milliseconds"),
	# Translators: name of a selection format digit group.
	DGROUP_DAYS: _("days"),
	# Translators: name of a selection format digit group.
	DGROUP_SAMPLE_THOUSANDS: _("thousand samples"),
	# Translators: name of a selection format digit group.
	DGROUP_SAMPLES: _("samples"),
}


class AudioPositionTimerControlEdit(NVDAObjects.NVDAObject):
	def initOverlayClass(self):
		self.bindGesture("kb:nvda+upArrow", "sayTimer")

	def script_sayTimer(self, gesture):
		tc = au_timerControl.TimerControl(self)
		(sLabel, sTime) = tc.getLabelAndTime()
		msg = "%s" % au_time.getTimeMessage(sTime)
		ui.message(msg)

	def event_gainFocus(self):
		tc = au_timerControl.TimerControl(self)
		(sLabel, sTime) = tc.getLabelAndTime()
		try:
			msg = "%s %s" % (sLabel, au_time.getTimeMessage(sTime))
			ui.message(msg)
		except Exception:
			super(TimerControlEdit, self).event_gainFocus()


# digit groups IDs
DGROUP_HOURS = 1
DGROUP_MINUTES = 2
DGROUP_SECONDS = 3
DGROUP_SECOND_THOUSANDS = 4
DGROUP_SECONDS_HUNDREDTHS = 5
DGROUP_MILLISECONDS = 6
DGROUP_DAYS = 7
DGROUP_SAMPLES = 8
DGROUP_SAMPLE_THOUSANDS = 9

# digit IDs
DIGIT_HOUR_UNITS = 1
DIGIT_HOUR_DOZENS = 2
DIGIT_MINUTE_UNITS = 3
DIGIT_MINUTE_DOZENS = 4
DIGIT_SECOND_UNITS = 5
DIGIT_SECOND_DOZENS = 6
DIGIT_SECOND_HUNDREDS = 7
DIGIT_SECOND_THOUSANDS = 8
DIGIT_SECOND_TENS_THOUSANDS = 9
DIGIT_SECOND_HUNDREDS_THOUSANDS = 10
DIGIT_SECOND_TENTHS = 11
DIGIT_SECOND_HUNDREDTHS = 12
DIGIT_SECOND_THOUSANDTHS = 13
DIGIT_DAY_UNITS = 14
DIGIT_DAY_DOZENS = 15
DIGIT_UNITS = 16
DIGIT_DOZENS = 17
DIGIT_HUNDREDS = 18
DIGIT_THOUSANDS = 19
DIGIT_TENS_THOUSANDS = 20
DIGIT_HUNDREDS_THOUSANDS = 21
DIGIT_MILLIONS = 22
DIGIT_SAMPLE_UNITS = 23
DIGIT_SAMPLE_DOZENS = 24
DIGIT_SAMPLE_HUNDREDS = 25
DIGIT_SAMPLE_THOUSANDS = 26
DIGIT_SAMPLE_TENS_THOUSANDS = 27
DIGIT_SAMPLE_HUNDREDS_THOUSANDS = 28

# names of selection format digits
_digitNames = {
	# Translators:  name of a digit in  selection format.
	DIGIT_HOUR_UNITS: _("units of hours"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HOUR_DOZENS: _("dozens of hours"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MINUTE_UNITS: _("units of minutes"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MINUTE_DOZENS: _("dozens of minutes"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_UNITS: _("units of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_DOZENS: _("dozens of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDS: _("hundreds of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_THOUSANDS: _("thounsands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_TENS_THOUSANDS: _("tens thousands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDS_THOUSANDS: _("hundreds thousands of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_TENTHS: _("tenths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_HUNDREDTHS: _("hundredths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SECOND_THOUSANDTHS: _("thousandths of seconds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DAY_UNITS: _("units of days"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DAY_DOZENS: _("dozens of days"),
	# Translators:  name of a digit in  selection format.
	DIGIT_UNITS: _("units"),
	# Translators:  name of a digit in  selection format.
	DIGIT_DOZENS: _("dozens"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HUNDREDS: _("hundreds"),
	# Translators:  name of a digit in  selection format.
	DIGIT_THOUSANDS: _("thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_TENS_THOUSANDS: _("tens of thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_HUNDREDS_THOUSANDS: _("hundreds of thousands"),
	# Translators:  name of a digit in  selection format.
	DIGIT_MILLIONS: _("millions"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_UNITS: _("units of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_DOZENS: _("dozens of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_HUNDREDS: _("hundreds of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_THOUSANDS: _("thounsands of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_TENS_THOUSANDS: _("tens thousands of samples"),
	# Translators:  name of a digit in  selection format.
	DIGIT_SAMPLE_HUNDREDS_THOUSANDS: _("hundreds thousands of samples"),
}
# names of selection format digit groups
_digitGroupNames = {
	# Translators: name of a selection format digit group.
	DGROUP_HOURS: _("hours"),
	# Translators: name of a selection format digit group.
	DGROUP_MINUTES: _("minutes"),
	# Translators: name of a selection format digit group.
	DGROUP_SECOND_THOUSANDS: _("thousands seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_SECONDS: _("seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_SECONDS_HUNDREDTHS: _("hundredths seconds"),
	# Translators: name of a selection format digit group.
	DGROUP_MILLISECONDS: _("milliseconds"),
	# Translators: name of a selection format digit group.
	DGROUP_DAYS: _("days"),
	# Translators: name of a selection format digit group.
	DGROUP_SAMPLE_THOUSANDS: _("thousand samples"),
	# Translators: name of a selection format digit group.
	DGROUP_SAMPLES: _("samples"),
}


class TimerControlDigit(NVDAObjects.NVDAObject):
	_selectionFormaElements = {
		SELFOR_SECONDS: (
			DGROUP_SECOND_THOUSANDS,
			DGROUP_SECOND_THOUSANDS, DGROUP_SECOND_THOUSANDS, DGROUP_SECONDS, DGROUP_SECONDS, DGROUP_SECONDS),
		SELFOR_HHMMSS: (
			DGROUP_HOURS, DGROUP_HOURS, DGROUP_MINUTES, DGROUP_MINUTES, DGROUP_SECONDS, DGROUP_SECONDS),
		SELFOR_DDHHMMSS: (
			DGROUP_DAYS, DGROUP_DAYS,
			DGROUP_HOURS, DGROUP_HOURS, DGROUP_MINUTES, DGROUP_MINUTES, DGROUP_SECONDS, DGROUP_SECONDS),
		SELFOR_HHMMSS_HUNDREDTHS: (
			DGROUP_HOURS, DGROUP_HOURS, DGROUP_MINUTES, DGROUP_MINUTES, DGROUP_SECONDS, DGROUP_SECONDS,
			DGROUP_SECONDS_HUNDREDTHS, DGROUP_SECONDS_HUNDREDTHS),
		SELFOR_HHMMSS_MILLISECONDS: (
			DGROUP_HOURS, DGROUP_HOURS, DGROUP_MINUTES, DGROUP_MINUTES, DGROUP_SECONDS,
			DGROUP_SECONDS, DGROUP_MILLISECONDS, DGROUP_MILLISECONDS, DGROUP_MILLISECONDS),
		SELFOR_HHMMSS_SAMPLES: (
			DGROUP_HOURS, DGROUP_HOURS, DGROUP_MINUTES, DGROUP_MINUTES, DGROUP_SECONDS, DGROUP_SECONDS,
			DGROUP_SAMPLES, DGROUP_SAMPLES, DGROUP_SAMPLES,
			DGROUP_SAMPLES, DGROUP_SAMPLES, DGROUP_SAMPLES),
		SELFOR_SAMPLES: (
			DGROUP_SAMPLE_THOUSANDS, DGROUP_SAMPLE_THOUSANDS, DGROUP_SAMPLE_THOUSANDS, DGROUP_SAMPLES,
			DGROUP_SAMPLES, DGROUP_SAMPLES),
	}

	_selectionFormatToDigitIDs = {
		SELFOR_SECONDS: (
			DIGIT_SECOND_HUNDREDS_THOUSANDS, DIGIT_SECOND_TENS_THOUSANDS, DIGIT_SECOND_THOUSANDS,
			DIGIT_SECOND_HUNDREDS, DIGIT_SECOND_DOZENS, DIGIT_SECOND_UNITS),
		SELFOR_HHMMSS: (
			DIGIT_HOUR_DOZENS, DIGIT_HOUR_UNITS, DIGIT_MINUTE_DOZENS, DIGIT_MINUTE_UNITS,
			DIGIT_SECOND_DOZENS, DIGIT_SECOND_UNITS),
		SELFOR_DDHHMMSS: (
			DIGIT_DAY_DOZENS, DIGIT_DAY_UNITS, DIGIT_HOUR_DOZENS, DIGIT_HOUR_UNITS,
			DIGIT_MINUTE_DOZENS, DIGIT_MINUTE_UNITS, DIGIT_SECOND_DOZENS, DIGIT_SECOND_UNITS),
		SELFOR_HHMMSS_HUNDREDTHS: (
			DIGIT_HOUR_DOZENS, DIGIT_HOUR_UNITS, DIGIT_MINUTE_DOZENS, DIGIT_MINUTE_UNITS,
			DIGIT_SECOND_DOZENS, DIGIT_SECOND_UNITS, DIGIT_SECOND_TENTHS, DIGIT_SECOND_HUNDREDTHS),
		SELFOR_HHMMSS_MILLISECONDS: (
			DIGIT_HOUR_DOZENS, DIGIT_HOUR_UNITS, DIGIT_MINUTE_DOZENS, DIGIT_MINUTE_UNITS, DIGIT_SECOND_DOZENS,
			DIGIT_SECOND_UNITS, DIGIT_SECOND_TENTHS, DIGIT_SECOND_HUNDREDTHS, DIGIT_SECOND_THOUSANDTHS),
		SELFOR_HHMMSS_SAMPLES: (
			DIGIT_HOUR_DOZENS, DIGIT_HOUR_UNITS, DIGIT_MINUTE_DOZENS, DIGIT_MINUTE_UNITS, DIGIT_SECOND_DOZENS,
			DIGIT_SECOND_UNITS, DIGIT_SAMPLE_HUNDREDS_THOUSANDS, DIGIT_SAMPLE_TENS_THOUSANDS,
			DIGIT_SAMPLE_THOUSANDS, DIGIT_SAMPLE_HUNDREDS, DIGIT_SAMPLE_DOZENS, DIGIT_SAMPLE_UNITS),
		SELFOR_SAMPLES: (
			DIGIT_SAMPLE_HUNDREDS_THOUSANDS, DIGIT_SAMPLE_TENS_THOUSANDS, DIGIT_SAMPLE_THOUSANDS,
			DIGIT_SAMPLE_HUNDREDS, DIGIT_SAMPLE_DOZENS, DIGIT_SAMPLE_UNITS),
	}

	def event_gainFocus(self):
		printDebug("TimerControlDigit event_gainFocus: %s, childID= %s" % (self.name, self.IAccessibleChildID))
		# When digit gains focus but not after script activation,
		# report audio position.
		tc = au_timerControl.TimerControl(self, self.editFormat)
		(sLabel, sTime) = tc.getLabelAndTime()
		try:
			msg = "%s %s" % (sLabel, au_time.getTimeMessage(sTime))
			ui.message(msg)
		except Exception:
			super(TimerControlDigit, self).event_gainFocus()

	def script_sayTimer(self, gesture):
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		(sLabel, sTime) = tc.getLabelAndTime()
		msg = "%s %s" % (sLabel, au_time.getTimeMessage(sTime))
		ui.message(msg)

	def event_nameChange(self):
		pass

	def script_upOrDownArrow(self, gesture):
		global GB_taskTimer

		def callback():
			stopTaskTimer()
			speech.cancelSpeech()
			obj = api.getFocusObject()
			name = obj.name
			# name form is xxx  s, x. We want only xxx
			name = obj.name.split(" ")[0]
			digitID = obj.IAccessibleChildID - 1
			editFormatElements = TimerControlDigit._selectionFormaElements[obj.editFormatID]
			if editFormatElements is None:
				# format not supported
				ui.message(name)
				return
			element = editFormatElements[digitID]
			unit = _digitGroupNames[element]
			msg = "%s %s" % (int(name), unit)
			ui.message(msg)

		stopTaskTimer()
# disable next event_gainFocus
		self.appModule.trapGainFocus = True
		gesture.send()
		GB_taskTimer = wx.CallLater(300, callback)

	def script_leftOrRightArrow(self, gesture):
		global GB_taskTimer

		def callback():
			stopTaskTimer()
			obj = api.getFocusObject()
			name = obj.name.split(" ")[-1]
			digitID = obj.IAccessibleChildID - 1
			digitIDs = TimerControlDigit._selectionFormatToDigitIDs[obj.editFormatID]
			digitName = _digitNames[digitIDs[digitID]]
			msg = "%s %s" % (digitName, name)
			ui.message(msg)

		stopTaskTimer()
		self.appModule.trapGainFocus = True
		gesture.send()
		GB_taskTimer = wx.CallLater(300, callback)

	__gestures = {
		"kb:NVDA+upArrow": "sayTimer",
		"kb:upArrow": "upOrDownArrow",
		"kb:downArrow": "upOrDownArrow",
		"kb:leftArrow": "leftOrRightArrow",
		"kb:rightArrow": "leftOrRightArrow",
	}


class SelectionTimerControlDigit(TimerControlDigit):
	def initOverlayClass(self):

		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		self.editFormat = applicationSettingsManager.getSelectionFormat()
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		self.editFormatID = tc.selectionFormatID


class SettingSelectionTimerControlDigit(TimerControlDigit):
	def initOverlayClass(self):
		self.bindGesture("kb:shift+f10", "application")
		printDebug("SettingSelectionTimerControlDigit initOverlayClass: name= %s, %s, childID= %s" % (
			self.name, roleLabels.get(self.role), self.IAccessibleChildID))
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		self.editFormat = applicationSettingsManager.getSelectionFormat()
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		self.editFormatID = tc.selectionFormatID

	def script_application(self, gesture):
		ui.message(
			"Disabled by add-on: format must be modified  in selection toolbar")
		# gesture.send()


class AudioPositionTimerControlDigit(TimerControlDigit):
	def initOverlayClass(self):
		from .au_applicationSettings import ApplicationSettingsManager
		applicationSettingsManager = ApplicationSettingsManager()
		self.editFormat = applicationSettingsManager.getAudioTimeFormat()
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		self.editFormatID = tc.selectionFormatID

	def script_upOrDownArrow(self, gesture):
		stopTaskTimer()
		# audio position time cannot be changed (read only)
		gesture.send()


class TimerRecordTimeControlDigit(TimerControlDigit):
	def initOverlayClass(self):
		self.editFormat = "hh:mm:ss"
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		self.editFormatID = tc.selectionFormatID


class TimerRecordDurationControlDigit(TimerControlDigit):
	def initOverlayClass(self):
		self.editFormat = "dd:hh:mm:ss"
		tc = au_timerControl.TimerControl(self.parent, self.editFormat)
		self.editFormatID = tc.selectionFormatID


class Button(NVDAObjects.NVDAObject):
	def initOverlayClass(self):
		if _addonConfigManager.toggleUseSpaceBarToPressButtonOption(False):
			self.bindGesture("kb:space", "spaceKey")
			self.bindGesture("kb:Enter", "spaceKey")

	def _get_name(self):
		name = super(Button, self)._get_name()
		# for some bad translated button label.
		return name.replace("&", "")

	def script_spaceKey(self, gesture):
		obj = api.getFocusObject()
		try:
			obj.doAction()
		except Exception:
			pass

		eventHandler.queueEvent("gainFocus", obj)


def internal_keyDownEventEx(vkCode, scanCode, extended, injected):
	def startMonitoring():
		global GB_monitorTimer
		if GB_monitorTimer is not None:
			GB_monitorTimer.Stop()
			GB_monitorTimer = None
		GB_monitorTimer = wx.CallLater(250, monitorAudioAndSelectionChanges)
	queueHandler.queueFunction(queueHandler.eventQueue, startMonitoring)
	return _winInputHookKeyDownCallback(vkCode, scanCode, extended, injected)


class AppModule(AppModule):
	trapGainFocus = False
	# a dictionnary to map  main script to gestures and install feature option
	_shellGestures = {}
	_mainScriptToGesture = {
		"moduleLayer": ("kb:nvda+space",),
		# "test": ("kb:alt+control+f10",),
	}

	_shellScriptToGestures = {
		"displayHelp": ("kb:h",),
		"displayAddonUserManual": ("kb:g",),
		"displayAudacityGuide": ("kb:control+g",),
		"reportSelectionLimits": ("kb:s",),
		"reportSelectionDuration": ("kb:shift+s",),
		"reportSelectionCenter": ("kb:control+s",),
		"reportAudioPosition": ("kb:a",),
		"toggleSelectionChangeAutomaticReport": ("kb:f4",),
		"reportTransportButtonsState": ("kb:f5",),
		"reportPlayMeterPeak": ("kb:f7",),
		"reportRecordMeterPeak": ("kb:f8",),
		"reportPlaybackSlider": ("kb:f9",),
		"reportRecordingSlider": ("kb:f10",),
		"reportPlaybackSpeed": ("kb:f11",),
	}

	_scriptsToDocsAndCategory = {
		# Translators: Input help mode message for report selection command.
		"reportSelection": (_(
			"report position of start and end of the selection. "
			"Twice: report selection's length. Third: report position of selection's center "), None),
		# Translators: Input help mode message
		# for report selection limits command.
		"reportSelectionLimits": (_("Report position of start and end of the selection"), None),
		# Translators: Input help mode message
		# for report selection duration command.
		"reportSelectionDuration": (_("Report selection's length"), None),
		# Translators: Input help mode message
		# for report selection center command.
		"reportSelectionCenter": (_("Report position of selection's center"), None),
		# Translators: Input help mode message
		# for report audio position command.
		"reportAudioPosition": (_("report audio position"), None),
		# Translators: Input help mode message
		# for toggle selection change automatic report command.
		"toggleSelectionChangeAutomaticReport": (_(
			"Enable or disable automatic report of selection's changes"), None),
		# Translators: Input help mode message
		# for toggle report transport button state command.
		"reportTransportButtonsState": (_("report the pressed state of Pause , Play and  Record buttons"), None),
		# Translators: Input help mode message
		# for report playback meter peak command.
		"reportPlayMeterPeak": (_("Reports the current level of playback meter peak"), None),
		# Translators: Input help mode message
		# for report record meter peak command.
		"reportRecordMeterPeak": (_("Reports the current recording meter peak   level"), None),
		# Translators: Input help mode message
		# for report slider playback command.
		"reportPlaybackSlider": (_("Reports the current level of playback's slider"), None),
		# Translators: Input help mode message
		# for report slider recording command.
		"reportRecordingSlider": (_("Reports the current level of recording's slider"), None),
		# Translators: Input help mode message
		# for report playback speed command.
		"reportPlaybackSpeed": (_("Reports the current playback speed level"), None),
		# Translators: Input help mode message
		# for display add-on user manual command.
		"displayAddonUserManual": (_("Display add-on user manual"), None),
		# Translators: Input help mode message
		# for display audacity guide command.
		"displayAudacityGuide": (_("Display audacity guide"), None),
		# Translators: Input help mode message
		# for launch module layer command.
		"moduleLayer": (_("Launch  command shell"), None),
		# Translators: Input help mode message
		# for display shell command help dialog command.
		"displayHelp": (_("Display shell scripts's list"), None),
	}

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		toggleDebugFlag()
		au_objects.initialize(self)
		self._reportFocusOnToolbar = False
		self._reportSelectionChange = True
		self.toggling = False
		self._bindGestures()
		self._setShellGestures()
		self.installShellScriptDocs()

	def terminate(self):
		global GB_monitorTimer
		if hasattr(self, "checkObjectsTimer") and self.checkObjectsTimer is not None:
			self.checkObjectsTimer.Stop()
			self.checkObjectsTimer = None
		if GB_monitorTimer is not None:
			GB_monitorTimer.Stop()
			GB_monitorTimer = None
		super(AppModule, self).terminate()

	def installAudacityRole(self):
		if hasattr(self, "NVDARole"):
			# allready installed
			return
		import controlTypes
		if NVDAVersion >= [2021, 3]:
			# for NVDA version > 2021.2
			import controlTypes.role
			global ROLE_TRACKVIEW, ROLE_TRACK
			self.NVDARole = controlTypes.Role
			self.NVDARoleLabels = controlTypes.role._roleLabels.copy()
			from .au_role import extendNVDARole
			(audacityRole, audacityRoleLabels) = extendNVDARole()
			controlTypes.Role = audacityRole
			controlTypes.role._roleLabels = audacityRoleLabels.copy()
			ROLE_TRACKVIEW = controlTypes.Role.TRACKVIEW
			ROLE_TRACK = controlTypes.Role.TRACK
		else:
			# for nvda version < 2021.2
			self.NVDARole = None

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		self.installAudacityRole()
		controlID = obj.windowControlID
		role = obj.role
		printDebug("appModule chooseOverlayClass: %s, %s" % (obj.name, roleLabels.get(obj.role)))
		obj.isATrack = Track.check(obj)
		if obj.isATrack:
			clsList.insert(0, Track)
		elif role == ROLE_TABLE and controlID == 1003:
			clsList.insert(0, TrackView)
		elif role == ROLE_BUTTON:
			clsList.insert(0, Button)
		elif role == ROLE_STATICTEXT and (
			_addonConfigManager.toggleEditSpinBoxEnhancedAnnouncementOption(False)):
			parent = obj.parent
			if parent is None:
				return
			if controlID in [2705, 2706, 2707, 2708, 2709]:
				if parent.windowControlID == controlID:
					clsList.insert(0, SelectionTimerControlDigit)
				else:
					clsList.insert(0, TimerControlEdit)
			elif controlID in [10001, 10003]:
				if parent.windowControlID == controlID:
					clsList.insert(0, TimerRecordTimeControlDigit)
				else:
					clsList.insert(0, TimerControlEdit)
			elif controlID == 10004:
				if parent.windowControlID == controlID:
					clsList.insert(0, TimerRecordDurationControlDigit)
				else:
					clsList.insert(0, TimerControlEdit)
			# in audacity 2.4.1, audio position time has moved.
			elif parent.windowControlID == 12:
				clsList.insert(0, AudioPositionTimerControlEdit)
			elif parent.parent and (
				parent.parent.parent and parent.parent.parent.windowControlID == 12):
				clsList.insert(0, AudioPositionTimerControlDigit)
			elif parent.windowClassName == "Button" and parent.windowControlID == 3000:
				clsList.insert(0, TimerControlEdit)
			elif parent .parent and (
				parent.parent.parent
				and parent.parent.parent.windowClassName == "Button"
				and parent.parent.parent.windowControlID == 3000):
				clsList.insert(0, SettingSelectionTimerControlDigit)
		printDebug("appModule chooseOverlayClassout: %s, %s" % (obj.name, roleLabels.get(obj.role)))

	def event_NVDAObject_init(self, obj):
		pass

	def _bindGestures(self):
		for script, gestures in self._mainScriptToGesture.items():
			if gestures is None:
				continue
			for gest in gestures:
				self.bindGesture(gest, script)

	def _setShellGestures(self):
		for script, gestures in self._shellScriptToGestures.items():
			for gest in gestures:
				self._shellGestures[gest] = script

	def installShellScriptDocs(self):
		for script in self._scriptsToDocsAndCategory:
			(doc, category) = self._getScriptDocAndCategory(script)
			commandText = None
			if script in self._shellScriptToGestures:
				gestures = self._shellScriptToGestures[script]
				key = gestures[0].split(":")[-1]
				# Translators: message for indicate shell command in input help mode.
				commandText = _("(command: %s)") % key
			if commandText is not None:
				doc = "%s %s" % (doc, commandText)
			scr = "script_%s" % script
			func = getattr(self, scr)
			func.__func__.__doc__ = doc
			func.__func__.category = category

	def _getScriptDocAndCategory(self, script):
		(doc, category) = self._scriptsToDocsAndCategory[script]
		if category is None:
			category = _scriptCategory
		return (doc, category)

	def event_appModule_gainFocus(self):
		global GB_monitorTimer
		global GB_audioPosition, GB_selection, GB_recordButtonIsPressed, _winInputHookKeyDownCallback
		self.installAudacityRole()
		GB_audioPosition = None
		GB_selection = None
		GB_recordButtonIsPressed = None
		if winInputHook.keyUpCallback != internal_keyDownEventEx:
			_winInputHookKeyDownCallback = winInputHook.keyDownCallback
			winInputHook.setCallbacks(keyDown=internal_keyDownEventEx)
		wx.CallLater(100, monitorAudioAndSelectionChanges)

	def event_appModule_loseFocus(self):
		global GB_monitorTimer
		import controlTypes
		if hasattr(controlTypes, "Role") and hasattr(self, "NVDARole") and self.NVDARole is not None:
			# for nvda version >= 2021.2
			global ROLE_TRACKVIEW, ROLE_TRACK
			import controlTypes.role
			controlTypes.Role = self.NVDARole
			controlTypes.role._roleLabels = self.NVDARoleLabels.copy()
			del ROLE_TRACKVIEW
			del ROLE_TRACK
			del self.NVDARole
			del self.NVDARoleLabels

		winInputHook.setCallbacks(keyDown=_winInputHookKeyDownCallback)
		if GB_monitorTimer is not None:
			GB_monitorTimer.Stop()
			GB_monitorTimer = None

	def event_gainFocus(self, obj, nextHandler):
		printDebug("audacity appModule event_gainFocus: name= %s, %s, childID= %s" % (
			obj.name, roleLabels.get(obj.role), obj.IAccessibleChildID))
		if self.trapGainFocus:
			api.setFocusObject(obj)
			self.trapGainFocus = False
			printDebug("audacity AppModule event_gainFocus trapped")
			return
		if self._reportFocusOnToolbar:
			self.reportFocusOnToolbar(obj)
			self._reportFocusOnToolbar = False
		nextHandler()

	def event_focusEntered(self, obj, nextHandler):
		if _addonConfigManager.toggleReportToolbarNameOnFocusEnteredOption(False):
			if obj.name is not None and (
				obj.role == ROLE_PANE
				and obj.name != "panel"
				and obj.name != ""):
				ui.message(obj.name)
		nextHandler()

	def script_moduleLayer(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		# A run-time binding will occur
			# from which we can perform various layered script commands

		if self.toggling:
			self.script_error(gesture)
			return
		self.bindGestures(self._shellGestures)
		self.toggling = True
		tones.beep(200, 40)

	def getScript(self, gesture):
		from keyboardHandler import KeyboardInputGesture
		if not self.toggling or not isinstance(gesture, KeyboardInputGesture):
			script = appModuleHandler.AppModule.getScript(self, gesture)
			return script
		script = appModuleHandler.AppModule.getScript(self, gesture)
		if not script:
			script = finally_(self.script_error, self.finish)
		return finally_(script, self.finish)

	def finish(self):
		self.toggling = False
		self.clearGestureBindings()
		self._bindGestures()

	def script_error(self, gesture):
		tones.beep(420, 40)

	def script_toggleSelectionChangeAutomaticReport(self, gesture):
		stopTaskTimer()
		_addonConfigManager .toggleAutomaticSelectionChangeReportOption()
		if _addonConfigManager .toggleAutomaticSelectionChangeReportOption(False):
			# Translators: message to the user when the selection changes.
			ui.message(_("Report automaticaly selection's changes"))
		else:
			# Translators: message to the user when selection change cannot be reported.
			ui.message(_("Don't report automaticaly selection change"))

	def inTrackView(self, obj, notify=True):
		if obj.role in [ROLE_TRACK, ROLE_TRACKVIEW, ROLE_TABLEROW]:
			return True
		if notify:
			# Translators: message to the user when object is not in tracks view.
			ui.message(_("Not in tracks view"))
		return False

	def inMainWindow(self, obj):
		# check if obj is in topPanel, track view, or mainPanel
		if self.inTrackView(obj, False):
			return True
		o = obj
		while o:
			if o.parent and (
				o.parent.name in ["Top Panel", "Main Panel"]):
				return True
			o = o.parent
		return False

	def script_reportAudioPosition(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		tc = au_timerControl.AudioTimerControl()
		msg = tc.getAudioPositionMessage()
		if msg is not None:
			ui.message(msg)

	def script_reportSelectionCenter(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		tc = au_timerControl.SelectionTimers()
		msg = tc.getSelectionCenterMessage()
		if msg is not None:
			ui.message(msg)

	def script_reportSelectionDuration(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		tc = au_timerControl.SelectionTimers()
		msg = tc.getSelectionDurationMessage()
		if msg is not None:
			ui.message(msg)

	def script_reportSelectionLimits(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		tc = au_timerControl.SelectionTimers()
		msg = tc.getSelectionMessage()
		if msg is not None:
			ui.message(msg)

	def script_reportSelection(self, gesture):
		global GB_taskTimer
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		count = scriptHandler.getLastScriptRepeatCount()
		if count == 0:
			GB_taskTimer = wx.CallLater(200, self.script_reportSelectionLimits, gesture)
		elif count == 1:
			GB_taskTimer = wx.CallLater(200, self.script_reportSelectionDuration, gesture)
		else:
			self.script_reportSelectionCenter(gesture)

	def script_reportTransportButtonsState(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		pressed = False
		if au_objects.isAvailable("record") and au_objects.isPressed("record"):
			# Translators: message to user when button record is pressed.
			ui.message(_("record button pressed"))
			pressed = True

		if au_objects.isAvailable("play") and au_objects.isPressed("play"):
			# Translators: message to the user when play button is pressed.
			ui.message(_("play button pressed"))
			pressed = True
		if au_objects.isPressed("pause"):
			# Translators: message to the user when pause button is pressed.
			ui.message(_("Pause button pressed"))
			pressed = True

		if not pressed:
			# Translators: message to the user when no button is pressed.
			ui.message(_("No button pressed"))

	def script_reportPlaybackSpeed(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		speed = au_objects.playbackSpeedSliderObject().value
		# Translators: message to the user to report playback speed.
		ui.message(_("playback speed: %s") % speed)

	def script_reportPlayMeterPeak(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return

		PlayMeterPeak().reportLevel()

	def script_reportRecordMeterPeak(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		RecordMeterPeak().reportLevel()

	def script_reportRecordingSlider(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		RecordingSlider().reportLevel()

	def script_reportPlaybackSlider(self, gesture):
		stopTaskTimer()
		if not self.inMainWindow(api.getFocusObject()):
			return
		PlaybackSlider().reportLevel()

	def runScript(self, gesture):
		self.bindGestures(self._shellGestures)
		script = self.getScript(gesture)
		self.clearGestureBindings()
		self._bindGestures()
		queueHandler.queueFunction(queueHandler.eventQueue, script, gesture)

	def script_displayHelp(self, gesture):
		stopTaskTimer()
		ShellScriptsListDialog.run(self)

	def startFile(self, path):
		# Translators: message for user.
		waitMsg = _("Please wait ...")
		ui.message(waitMsg)
		os.startfile(path)

	def script_displayAddonUserManual(self, gesture):
		stopTaskTimer()
		from languageHandler import getLanguage
		lang = getLanguage()
		docPath = os.path.join(_curAddon.path, "doc")
		manual = _curAddon.manifest["docFileName"]
		defaultPath = os.path.join(docPath, "en", manual)
		localePath = os.path.join(docPath, lang, manual)
		if os.path.exists(localePath):
			self.startFile(localePath)
			return
		lang = getLanguage().split("_")[0]
		localePath = os.path.join(docPath, lang, manual)
		if os.path.exists(localePath):
			self.startFile(localePath)
		elif os.path.exists(defaultPath):
			self.startFile(defaultPath)
		else:
			# Translators: message to user when add-on help is not found.
			ui.message(_("Error: Add-on user manual is not found"))

	def script_displayAudacityGuide(self, gesture):
		stopTaskTimer()
		from languageHandler import getLanguage
		lang = getLanguage()
		docPath = os.path.join(_curAddon.path, "doc")
		guide = "audacityGuide.html"
		defaultPath = os.path.join(docPath, "en", guide)
		localePath = os.path.join(docPath, lang, guide)
		if os.path.exists(localePath):
			self.startFile(localePath)
			return
		lang = getLanguage().split("_")[0]
		localePath = os.path.join(docPath, lang, guide)
		if os.path.exists(localePath):
			self.startFile(localePath)
		elif os.path.exists(defaultPath):
			self.startFile(defaultPath)
		else:
			# Translators: message to user when Audacity guide is not found.
			ui.message(_("Error: audacity guide is not found"))

	def script_test(self, gesture):
		speech.speakMessage("test audacity")


class ShellScriptsListDialog(wx.Dialog):
	_instance = None
	title = None

	def __new__(cls, *args, **kwargs):
		if ShellScriptsListDialog._instance is None:
			return wx.Dialog.__new__(cls)
		return ShellScriptsListDialog._instance

	def __init__(self, parent, appModule):
		if ShellScriptsListDialog._instance is not None:
			return
		ShellScriptsListDialog._instance = self
		self.focusObject = api.getFocusObject()
		# Translators: this is the title of Helper dialog.
		dialogTitle = _("Shell's scripts")
		title = ShellScriptsListDialog.title = makeAddonWindowTitle(dialogTitle)
		super(ShellScriptsListDialog, self).__init__(parent, wx.ID_ANY, title)
		self.appModule = appModule
		self.doGui()

	def initList(self):
		self.docToScript = {}
		self.scriptToIdentifier = {}
		for script in self.appModule._scriptsToDocsAndCategory:
			if script not in self.appModule._shellScriptToGestures:
				continue
			identifier = self.appModule._shellScriptToGestures[script][0]
			(doc, category) = self.appModule._scriptsToDocsAndCategory[script]
			self.scriptToIdentifier[script] = identifier
			self.docToScript[doc] = script

	def doGui(self):
		self.initList()
		self.docList = sorted([doc for doc in self.docToScript])
		choice = []
		for doc in self.docList:
			script = self.docToScript[doc]
			identifier = self.scriptToIdentifier[script]
			source, main = inputCore.getDisplayTextForGestureIdentifier(identifier.lower())
			choice.append("%s: %s" % (doc, main))

		from gui import guiHelper
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		# Translators: This is the label of the list
# appearing on Shell Scripts List Dialog.
		labelText = _("scripts:")
		self.scriptsListBox = sHelper.addLabeledControl(
			labelText,
			wx.ListBox,
			id=wx.ID_ANY,
			choices=choice,
			style=wx.LB_SINGLE,
			size=(700, 280))
		if self.scriptsListBox.GetCount():
			self.scriptsListBox.SetSelection(0)
		# Buttons
		bHelper = sHelper.addDialogDismissButtons(guiHelper.ButtonHelper(wx.HORIZONTAL))
		# Translators: This is a label of a button
		# appearing on Shell Scripts List Dialog.
		runScriptButton = bHelper.addButton(
			self,
			id=wx.ID_ANY,
			label=_("&Run script"))
		runScriptButton.SetDefault()
		closeButton = bHelper.addButton(
			self,
			id=wx.ID_CLOSE,
			label=NVDAString("&Close"))
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		# Events
		runScriptButton.Bind(wx.EVT_BUTTON, self.onRunScriptButton)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())
		self.SetEscapeId(wx.ID_CLOSE)

	def Destroy(self):
		ShellScriptsListDialog._instance = None
		super(ShellScriptsListDialog, self).Destroy()

	def onRunScriptButton(self, evt):
		index = self.scriptsListBox.GetSelection()
		doc = self.docList[index]
		script = self.docToScript[doc]
		identifier = self.scriptToIdentifier[script]
		from keyboardHandler import KeyboardInputGesture
		gesture = KeyboardInputGesture.fromName(identifier[3:])
		wx.CallLater(200, speech.cancelSpeech)
		wx.CallLater(1000, self.appModule.runScript, gesture)
		self.Close()

	@classmethod
	def run(cls, globalPlugin):
		if isOpened(cls):
			return
		gui.mainFrame.prePopup()
		d = cls(gui.mainFrame, globalPlugin)
		d.CentreOnScreen()
		d.Show()
		gui.mainFrame.postPopup()
