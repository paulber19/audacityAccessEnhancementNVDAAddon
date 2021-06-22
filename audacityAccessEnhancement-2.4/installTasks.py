# -*- coding: UTF-8 -*-
# install.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018-2020 paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import os
from logHandler import log
previousNameAndAuthor = ("audacity", "paulber007")
previousConfigFileName = "audacityAddon.ini"
addonHandler.initTranslation()


def uninstallPreviousVersion():
	for addon in addonHandler.getAvailableAddons():
		if (addon.manifest["name"], addon.manifest["author"]) == previousNameAndAuthor:  # noqa:E501
			addon.requestRemove()
			break


def saveFile(theFile, path):
	import shutil
	if not os.path.exists(theFile):
		return
	try:
		shutil.copy(theFile, path)
		os.remove(theFile)
		log.warning("%s file copied in %s and deleted" % (path, theFile))
	except:  # noqa:E722
		log.warning("Error: %s file cannot be move to %s" % (theFile, path))


def onInstall():
	import globalVars
	import wx
	import gui
	import sys
	if sys.version.startswith("3"):
		curPath = os.path.dirname(__file__)
	else:
		curPath = os.path.dirname(__file__).decode("mbcs")
	from addonHandler import _availableAddons
	addon = _availableAddons[curPath]
	addonName = addon.manifest["name"]
	addonSummary = addon.manifest["summary"]
	# add-on name has  changed. We must uninstall previous version.
	uninstallPreviousVersion()
	# save old configuration
	userConfigPath = globalVars.appArgs.configPath
	curConfigFileName = "%sAddon.ini" % addonName
	for fileName in [curConfigFileName, previousConfigFileName]:
		f = os.path.join(userConfigPath, fileName)
		if not os.path.exists(f):
			continue
		if gui.messageBox(
			# Translators: the label of a message box dialog
			# to ask the user if he wants keep current configuration settings.
			_("Do you want to keep current add-on configuration settings ?"),
			# Translators: the title of a message box dialog.
			_("%s - installation" % addonSummary),
			wx.YES | wx.NO | wx.ICON_WARNING) == wx.YES:
			path = os.path.join(curPath, curConfigFileName)
			saveFile(f, path)
		break


def deleteFile(theFile):
	if not os.path.exists(theFile):
		return
	os.remove(theFile)
	if os.path.exists(theFile):
		log.warning("Error on deletion of%s  file" % theFile)
	else:
		log.warning("%s file deleted" % theFile)


def deleteAddonConfig():
	import globalVars
	import sys
	if sys.version.startswith("3"):
		curPath = os.path.dirname(__file__)
	else:
		curPath = os.path.dirname(__file__).decode("mbcs")
	sys.path.append(curPath)
	import buildVars
	addonName = buildVars.addon_info["addon_name"]
	del sys.path[-1]
	configFile = os.path.join(
		globalVars.appArgs.configPath, "%sAddon.ini" % addonName)
	deleteFile(configFile)
	autoReadingSynthFile = os.path.join(
		globalVars.appArgs.configPath, "%s_autoReadingSynth.pickle" % addonName)
	deleteFile(autoReadingSynthFile)


def onUninstall():
	deleteAddonConfig()
