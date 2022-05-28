# appModules/audacity/au_informationDialog.py
# A part of audacityAccessEnhancement add-on
# Copyright (C) 2018 paulber19
# This file is covered by the GNU General Public License.


import api
import ui
import wx
import time
from gui import guiHelper, mainFrame
from .au_NVDAStrings import NVDAString
from .au_utils import isOpened, makeAddonWindowTitle
import addonHandler
addonHandler.initTranslation()


class InformationDialog(wx.Dialog):
	_instance = None
	title = None

	def __new__(cls, *args, **kwargs):
		if InformationDialog._instance is not None:
			return InformationDialog._instance
		return super(InformationDialog, cls).__new__(cls, *args, **kwargs)

	def __init__(self, parent, dialogTitle, informationLabel, information):
		if InformationDialog._instance is not None:
			return
		InformationDialog._instance = self
		if dialogTitle == "":
			# Translators: this is the default title of Information dialog.
			dialogTitle = _("Informations")
		title = InformationDialog.title = makeAddonWindowTitle(dialogTitle)
		super(InformationDialog, self).__init__(parent, wx.ID_ANY, title)
		self.informationLabel = informationLabel
		self.information = information
		self.doGui()

	def doGui(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# the text control
		sHelper.addItem(wx.StaticText(self, label=self.informationLabel))
		self.tc = sHelper.addItem(wx.TextCtrl(
			self, id=wx.ID_ANY,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH,
			size=(1000, 600))
		)
		self.tc.AppendText(self.information)
		self.tc.SetInsertionPoint(0)
		# the buttons
		bHelper = sHelper.addDialogDismissButtons(guiHelper.ButtonHelper(
			wx.HORIZONTAL))
		copyToClipboardButton = bHelper.addButton(
			self, id=wx.ID_ANY,
			# Translators: label of copy to clipboard button.
			label=_("Co&py to Clipboard")
		)
		closeButton = bHelper.addButton(
			self,
			id=wx.ID_CLOSE,
			label=NVDAString("&Close")
		)
		mainSizer.Add(
			sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		# events
		copyToClipboardButton.Bind(wx.EVT_BUTTON, self.onCopyToClipboardButton)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())
		self.tc.SetFocus()
		self.SetEscapeId(wx.ID_CLOSE)

	def Destroy(self):
		InformationDialog._instance = None
		super(InformationDialog, self).Destroy()

	def onCopyToClipboardButton(self, event):
		if api.copyToClip(self.information):
			# Translators: message to the user
			# when the information has been copied to clipboard.
			text = _("Copied")
			ui.message(text)
			time.sleep(0.8)
			self.Close()
		else:
			# Translators: message to the user
			# when the information cannot be copied to clipboard.
			text = _("Error, the information cannot be copied to the clipboard")
			ui.message(text)

	@classmethod
	def run(cls, parent, dialogTitle, informationLabel, information):
		if isOpened(InformationDialog):
			return
		if parent is None:
			mainFrame.prePopup()
		d = InformationDialog(
			parent or mainFrame, dialogTitle,
			informationLabel, information)
		d.Center(wx.BOTH | wx.CENTER_ON_SCREEN)
		d.Show()
		if parent is None:
			mainFrame.postPopup()
