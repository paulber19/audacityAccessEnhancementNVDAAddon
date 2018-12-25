#appModules/audacity/au_configGui.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018,paulber19
# released under GPL.
#See the file COPYING for more details.

import addonHandler
addonHandler.initTranslation()
from logHandler import log
import wx
import gui
from gui.settingsDialogs import SettingsDialog
from au_configManager import _addonConfigManager
_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']

class AudacitySettingsDialog(SettingsDialog):
	# Translators: This is the label for the Audacity settings  dialog.
	title = _("%s add-on - settings")%_addonSummary
	
	def makeSettings(self, settingsSizer):
		from au_configManager import _addonConfigManager
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
	
	def postInit(self):
		self.AutomaticSelectionChangeReportBox.SetFocus()
	
	def saveSettingChanges (self):
		from au_configManager import _addonConfigManager
		if self.AutomaticSelectionChangeReportBox.IsChecked() != _addonConfigManager .toggleAutomaticSelectionChangeReportOption(False):
			_addonConfigManager .toggleAutomaticSelectionChangeReportOption(True)
		
		if self.UseSpaceBarToPressButtonBox .IsChecked() != _addonConfigManager .toggleUseSpaceBarToPressButtonOption(False):
			_addonConfigManager .toggleUseSpaceBarToPressButtonOption(True)
		if self.reportToolbarNameOnFocusEnteredBox   .IsChecked() != _addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(False):
			_addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(True)
			
	def onOk(self,evt):
		self.saveSettingChanges()
		super(AudacitySettingsDialog, self).onOk(evt)
