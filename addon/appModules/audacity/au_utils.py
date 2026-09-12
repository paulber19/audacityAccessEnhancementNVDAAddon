# appModules\audacity\au_utils.py
# A part of audacityAccessEnhancement add-on
# Copyright (C) 2018-2026, paulber19
# This file is covered by the GNU General Public License.

import addonHandler
import ui
import queueHandler
import speech.speech

speakOnDemand = speech.speech.SpeechMode.onDemand

addonHandler.initTranslation()

# winuser.h constant

WM_SYSCOMMAND = 0x112


def isOpened(dialog):
	if dialog._instance is None:
		return False
	# Translators: the label of a dialog box message.
	msg = _("%s dialog is allready open") % dialog.title
	queueHandler.queueFunction(queueHandler.eventQueue, ui.message, msg)
	return True


def makeAddonWindowTitle(dialogTitle):
	curAddon = addonHandler.getCodeAddon()
	addonSummary = curAddon.manifest['summary']
	# Translators:  title of all add-on dialog boxs.
	return _("{addonSummary}'s add-on - {dialogTitle}").format(
		addonSummary=addonSummary, dialogTitle=dialogTitle)


def executeWithSpeakOnDemand(func, *args, **kwargs):
	from speech.speech import _speechState, SpeechMode
	if not speakOnDemand or _speechState.speechMode != SpeechMode.onDemand:
		return func(*args, **kwargs)
	_speechState.speechMode = SpeechMode.talk
	ret = func(*args, **kwargs)
	_speechState.speechMode = SpeechMode.onDemand
	return ret


def messageWithSpeakOnDemand(msg):
	executeWithSpeakOnDemand(ui.message, msg)
