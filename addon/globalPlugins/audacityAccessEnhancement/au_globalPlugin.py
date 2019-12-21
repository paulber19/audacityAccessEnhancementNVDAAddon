#globalPlugins\audacityAccessEnhancement\au_globalPlugin.py
# a part of audacityAccessEnhancement add-on
#Copyright (C) 2019 Paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
import globalPluginHandler
from logHandler import log,_getDefaultLogFilePath
import gui
import wx
import os
import globalVars
import sys
addon = addonHandler.getCodeAddon()
path = os.path.join(addon.path, "shared")
sys.path.append(path)
from  au_addonConfigManager import _addonConfigManager
del sys.path[-1]

class AudacityGlobalPlugin(globalPluginHandler.GlobalPlugin):
	
	def __init__(self, *args, **kwargs):
		super(AudacityGlobalPlugin, self).__init__(*args, **kwargs)
		self.installSettingsMenu()
		from . updateHandler import autoUpdateCheck
		if _addonConfigManager.toggleAutoUpdateCheck(False):
			autoUpdateCheck(releaseToDev = _addonConfigManager.toggleUpdateReleaseVersionsToDevVersions     (False))
	def installSettingsMenu(self):
		self.preferencesMenu= gui.mainFrame.sysTrayIcon.preferencesMenu
		from .au_configGui import AudacitySettingsDialog
		self.menu = self.preferencesMenu.Append(wx.ID_ANY,
			AudacitySettingsDialog.title + " ...",
			"")
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onMenu, self.menu)
	
	def deleteSettingsMenu(self):
		try:
			if wx.version().startswith("4"):
				# for wxPython 4
				self.preferencesMenu.Remove (self.menu )
			else:
				# for wxPython 3
				self.preferencesMenu.RemoveItem (self.menu )
		except:
			pass
	
	def onMenu(self, evt):
		from .au_configGui import AudacitySettingsDialog
		gui.mainFrame._popupSettingsDialog(AudacitySettingsDialog)

	def terminate(self):
		self.deleteSettingsMenu()
		super(AudacityGlobalPlugin, self).terminate()
	
	
	

