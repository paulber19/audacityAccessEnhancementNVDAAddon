# globalPlugins\audacityAccessEnhancement\au_globalPlugin.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2019-2020 Paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import globalPluginHandler
import gui
import wx
import os
import sys
addon = addonHandler.getCodeAddon()
path = os.path.join(addon.path, "shared")
sys.path.append(path)
from au_addonConfigManager import _addonConfigManager  # noqa:E402
del sys.path[-1]
addonHandler.initTranslation()


class AudacityGlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(AudacityGlobalPlugin, self).__init__(*args, **kwargs)
		self.installSettingsMenu()
		from . updateHandler import autoUpdateCheck
		if _addonConfigManager.toggleAutoUpdateCheck(False):
			autoUpdateCheck(_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))  # noqa:E501

	def installSettingsMenu(self):
		self.preferencesMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
		from .au_configGui import AddonSettingsDialog
		self.menu = self.preferencesMenu.Append(
			wx.ID_ANY,
			AddonSettingsDialog.title + " ...",
			"")
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onMenu, self.menu)

	def deleteSettingsMenu(self):
		try:
			self.preferencesMenu.Remove(self.menu)

		except:  # noqa:E722
			pass

	def onMenu(self, evt):
		from .au_configGui import AddonSettingsDialog
		wx.CallAfter(gui.mainFrame._popupSettingsDialog, AddonSettingsDialog)

	def terminate(self):
		self.deleteSettingsMenu()
		super(AudacityGlobalPlugin, self).terminate()
