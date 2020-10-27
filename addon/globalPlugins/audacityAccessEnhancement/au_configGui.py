# globalPlugins\audacityAccessEnhancement\au_configGui.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018-2020,paulber19
# released under GPL.

import addonHandler
import os
import wx
import gui
from gui.settingsDialogs import MultiCategorySettingsDialog, SettingsPanel
import sys
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from au_addonConfigManager import _addonConfigManager  # noqa:E402
del sys.path[-1]
addonHandler.initTranslation()


class OptionsSettingsPanel(SettingsPanel):
	# Translators: This is the label for the Audacity settings dialog.
	title = _("Options")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox
		# in the OptionsSettingsPanel
		labelText = _("Report automaticaly selection's changes")
		self.AutomaticSelectionChangeReportBox = sHelper.addItem(
			wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.AutomaticSelectionChangeReportBox .SetValue(
			_addonConfigManager .toggleAutomaticSelectionChangeReportOption(False))
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox
		# OptionsSettingsPanel
		labelText = _("Use space bar and Enter keys to press button")
		self.UseSpaceBarToPressButtonBox = sHelper.addItem(wx.CheckBox(
			self, wx.ID_ANY, label=labelText))
		self.UseSpaceBarToPressButtonBox .SetValue(
			_addonConfigManager .toggleUseSpaceBarToPressButtonOption(False))
		# Translators: This is the label for a checkbox
		# OptionsSettingsPanel
		labelText = _("Report toolbars's name ")
		self.reportToolbarNameOnFocusEnteredBox = sHelper.addItem(wx.CheckBox(
			self, wx.ID_ANY, label=labelText))
		self.reportToolbarNameOnFocusEnteredBox.SetValue(
			_addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(False))
		# Translators: This is the label for a checkbox
		# OptionsSettingsPanel
		labelText = _("EnhancedAnnouncement  of edit spin boxes")
		self.editSpinBoxEnhancedAnnouncementBox = sHelper.addItem(wx.CheckBox(
			self, wx.ID_ANY, label=labelText))
		self.editSpinBoxEnhancedAnnouncementBox.SetValue(
			_addonConfigManager .toggleEditSpinBoxEnhancedAnnouncementOption(False))

	def postInit(self):
		self.AutomaticSelectionChangeReportBox.SetFocus()

	def saveSettingChanges(self):
		if self.AutomaticSelectionChangeReportBox.IsChecked() != _addonConfigManager .toggleAutomaticSelectionChangeReportOption(False):  # noqa:501
			_addonConfigManager .toggleAutomaticSelectionChangeReportOption(True)
		if self.UseSpaceBarToPressButtonBox .IsChecked() != _addonConfigManager .toggleUseSpaceBarToPressButtonOption(False):  # noqa:E501
			_addonConfigManager .toggleUseSpaceBarToPressButtonOption(True)
		if self.reportToolbarNameOnFocusEnteredBox .IsChecked() != _addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(False):  # noqa:E501
			_addonConfigManager .toggleReportToolbarNameOnFocusEnteredOption(True)
		if self.editSpinBoxEnhancedAnnouncementBox.IsChecked() != _addonConfigManager .toggleEditSpinBoxEnhancedAnnouncementOption(False):  # noqa:E501
			_addonConfigManager .toggleEditSpinBoxEnhancedAnnouncementOption(True)

	def postSave(self):
		pass

	def onSave(self):
		self.saveSettingChanges()


class UpdateSettingsPanel(SettingsPanel):
	# Translators: This is the label for the Advanced settings panel.
	title = _("Update")

	def __init__(self, parent):
		super(UpdateSettingsPanel, self).__init__(parent)

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox
		# UpdateSettingsPanel
		labelText = _("Automatically check for &updates ")
		self.autoCheckForUpdatesCheckBox = sHelper.addItem(wx.CheckBox(
			self, wx.ID_ANY, label=labelText))
		self.autoCheckForUpdatesCheckBox.SetValue(
			_addonConfigManager.toggleAutoUpdateCheck(False))
		# Translators: This is the label for a checkbox
		# UpdateSettingsPanel
		labelText = _("Update also release versions to &developpement versions")
		self.updateReleaseVersionsToDevVersionsCheckBox = sHelper.addItem(
			wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.updateReleaseVersionsToDevVersionsCheckBox.SetValue(
			_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))
		# translators: label for a button
		# UpdateSettingsPanel
		labelText = _("&Check for update")
		checkForUpdateButton = wx.Button(self, label=labelText)
		sHelper.addItem(checkForUpdateButton)
		checkForUpdateButton.Bind(wx.EVT_BUTTON, self.onCheckForUpdate)

	def onCheckForUpdate(self, evt):
		from .updateHandler import addonUpdateCheck
		releaseToDevVersion = self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked()  # noqa:E501
		wx.CallAfter(addonUpdateCheck, auto=False, releaseToDev=releaseToDevVersion)
		self.Close()

	def saveSettingChanges(self):
		if self.autoCheckForUpdatesCheckBox.IsChecked() != _addonConfigManager .toggleAutoUpdateCheck(False):  # noqa:E501
			_addonConfigManager .toggleAutoUpdateCheck(True)
		if self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() != _addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(False):  # noqa:E501
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(True)

	def postSave(self):
		pass

	def onSave(self):
		self.saveSettingChanges()


class AddonSettingsDialog(MultiCategorySettingsDialog):
	# translators: title of the dialog.
	dialogTitle = _("Settings")
	title = "% s - %s" % (_curAddon.manifest["summary"], dialogTitle)
	INITIAL_SIZE = (1000, 480)
	MIN_SIZE = (470, 240)

	categoryClasses = [
		OptionsSettingsPanel,
		UpdateSettingsPanel,
		]

	def __init__(self, parent, initialCategory=None):
		super(AddonSettingsDialog, self).__init__(parent, initialCategory)
