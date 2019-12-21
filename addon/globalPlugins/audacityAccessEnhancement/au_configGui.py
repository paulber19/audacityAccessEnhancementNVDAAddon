#globalPlugins\audacityAccessEnhancement\au_configGui.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018,paulber19
# released under GPL.

import addonHandler
addonHandler.initTranslation()
from logHandler import log
import os
import wx
import gui
from gui.settingsDialogs import SettingsDialog
import sys
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from  au_addonConfigManager import _addonConfigManager
del sys.path[-1]

_addonSummary = _curAddon.manifest['summary']

class AudacitySettingsDialog(SettingsDialog):
	# Translators: This is the label for the Audacity settings  dialog.
	title = _("%s add-on - settings")%_addonSummary
	
	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox in the AudacitySettingsDialog.
		labelText= _("Report automaticaly selection's changes")
		self.AutomaticSelectionChangeReportBox =sHelper.addItem(wx.CheckBox(self,wx.NewId(),label=labelText))
		self.AutomaticSelectionChangeReportBox .SetValue(_addonConfigManager .toggleAutomaticSelectionChangeReportOption(False))
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox in the AudacitySettingsDialog.
		labelText= _("Use space bar and Enter keys to press button")
		self.UseSpaceBarToPressButtonBox =sHelper.addItem(wx.CheckBox(self,wx.NewId(),label=labelText))
		self.UseSpaceBarToPressButtonBox .SetValue(_addonConfigManager .toggleUseSpaceBarToPressButtonOption(False))
		# Translators: This is the label for a checkbox in the AudacitySettingsDialog.
		labelText= _("Report toolbars's name ")
		self.reportToolbarNameOnFocusEnteredBox =sHelper.addItem(wx.CheckBox(self,wx.NewId(),label=labelText))
		self.reportToolbarNameOnFocusEnteredBox  .SetValue(_addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(False))
		# Translators: This is the label for a group of editing options in the Audacity settings panel.
		groupText = _("Update")
		group = gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=groupText), wx.VERTICAL))
		sHelper.addItem(group)
		# Translators: This is the label for a checkbox in the Audacity SettingsDialog.
		labelText = _("Automatically check for &updates ")
		self.autoCheckForUpdatesCheckBox=group.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.autoCheckForUpdatesCheckBox.SetValue(_addonConfigManager.toggleAutoUpdateCheck(False))
		# Translators: This is the label for a checkbox in the Audacity settings panel.
		labelText = _("Update also release versions to &developpement versions")
		self.updateReleaseVersionsToDevVersionsCheckBox=group.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.updateReleaseVersionsToDevVersionsCheckBox.SetValue(_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions     (False))
		# translators: label for a button in Audacity settings panel.
		labelText = _("&Check for update")
		checkForUpdateButton= wx.Button(self, label=labelText)
		group.addItem (checkForUpdateButton)
		checkForUpdateButton.Bind(wx.EVT_BUTTON,self.onCheckForUpdate)
	
	def onCheckForUpdate(self, evt):
		from .updateHandler import addonUpdateCheck
		wx.CallAfter(addonUpdateCheck, auto = False, releaseToDev = _addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))
		self.Close()
	
	def postInit(self):
		self.AutomaticSelectionChangeReportBox.SetFocus()
	
	def saveSettingChanges (self):
		if self.AutomaticSelectionChangeReportBox.IsChecked() != _addonConfigManager .toggleAutomaticSelectionChangeReportOption(False):
			_addonConfigManager .toggleAutomaticSelectionChangeReportOption(True)
		
		if self.UseSpaceBarToPressButtonBox .IsChecked() != _addonConfigManager .toggleUseSpaceBarToPressButtonOption(False):
			_addonConfigManager .toggleUseSpaceBarToPressButtonOption(True)
		if self.reportToolbarNameOnFocusEnteredBox   .IsChecked() != _addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(False):
			_addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(True)
		if self.autoCheckForUpdatesCheckBox.IsChecked() != _addonConfigManager .toggleAutoUpdateCheck(False):
			_addonConfigManager .toggleAutoUpdateCheck(True)
		if self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() != _addonConfigManager .toggleUpdateReleaseVersionsToDevVersions     (False):
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions     (True)			
	
	def onOk(self,evt):
		self.saveSettingChanges()
		super(AudacitySettingsDialog, self).onOk(evt)
