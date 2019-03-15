# -*- coding: UTF-8 -*-
# install.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018 paulber19
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
addonHandler.initTranslation()

previousNameAndAuthor = ("audacity", "paulber007")
previousConfigFileName = "audacityAddon.ini"
saveConfigFileName = "addonConfig_old.ini"

def uninstallPreviousVersion():
	for addon in addonHandler.getAvailableAddons():
		if (addon.manifest["name"], addon.manifest["author"]) == previousNameAndAuthor:
			addon.requestRemove()
			break

def onInstall():
	import os
	import shutil
	import globalVars
	import wx
	import gui
	import sys
	from logHandler import log
	curPath = os.path.dirname(__file__).decode("mbcs")
	sys.path.append(curPath)
	import buildVars
	addonName = buildVars.addon_info["addon_name"]
	addonSummary= _(buildVars.addon_info["addon_summary"])
	del sys.path[-1]
	# add-on name has  changed. We must uninstall previous version.
	uninstallPreviousVersion()
	# save old configuration
	userConfigPath = globalVars.appArgs.configPath
	curConfigFileName = "%sAddon.ini"%addonName
	for fileName in [curConfigFileName, previousConfigFileName]:
		f= os.path.join(userConfigPath, fileName)
		if not os.path.exists(f):
			continue
		if gui.messageBox(
			# Translators: the label of a message box dialog  to ask the user if he wants keep current configuration settings.
			_("Do you want to keep current add-on configuration settings ?"),
			# Translators: the title of a message box dialog.
			_("%s - installation"%addonSummary),
			wx.YES|wx.NO|wx.ICON_WARNING)==wx.YES:
			try:
				path = os.path.join(curPath, saveConfigFileName )
				shutil.copy(f, path)
				os.remove(f)
				log.warning("%s file copied and deleted"%f)
			except:
				log.warning("Error: %s file cannot be copied or deleted"%f)
		break

def deleteAddonConfig():
	import os
	import globalVars
	from logHandler import log
	import sys
	curPath = os.path.dirname(__file__).decode("mbcs")
	sys.path.append(curPath)
	import buildVars
	addonName = buildVars.addon_info["addon_name"]
	del sys.path[-1]
	configFile = os.path.join(globalVars.appArgs.configPath, "%sAddon.ini"%addonName)
	if not os.path.exists(configFile):
		return
	os.remove(configFile )
	if os.path.exists(configFile):
		log.warning("Error on deletion of%s  file"%configFile)
	else:
		log.warning("%s file deleted"%configFile)

	
def onUninstall():
	deleteAddonConfig(  )

