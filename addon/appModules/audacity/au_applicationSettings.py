# appModules/audacity/au_applicationSettings.py.
# a part of audacityAccessEnhancement add-on
# Copyright 2018 paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
import os
from logHandler import log
import shutil
import shlobj
import gui
import speech
import wx
from configobj import ConfigObj, ConfigObjError

import sys
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from au_py3Compatibility import importStringIO 
del sys.path[-1]
StringIO = importStringIO()




class ApplicationSettingsManager(object):
	_applicationName = "Audacity"
	_programName = "audacity.exe"
	_settingsFolderName = "audacity"

	
	def __init__(self):
		self.settingsDir = self._getSettingsFolderPath()
	@property
	def initialized(self):
		return self.settingsDir is not None
	
	def _getSettingsFolderPath(self):
		try:
			dir = os.path.join(shlobj.SHGetFolderPath(0, shlobj.CSIDL_APPDATA), self._settingsFolderName)
		except WindowsError:
			log.warning("%ssettings directory not found"%self.settingsFolderName)
			return None
		if os.path.exists(dir):
			return dir
		return None

	def getSettings(self):
		if not self.initialized:
			return None
		settings = SettingsFileHandler(self.settingsDir).settings
		return settings
		
	def getSelectionFormat (self):
		if not self.initialized:
			return None
		settings = self.getSettings()
		key = "SelectionFormat"
		return  settings[key] if key in settings else None

class SettingsFileHandler(object):
	_fileName = "audacity.cfg"
	def __init__(self, settingsDir):
		super(SettingsFileHandler, self).__init__()
		self.initialized = False
		self.settingsDir = settingsDir
		self.filePath = os.path.join(settingsDir, self._fileName)
		if not os.path.exists(self.filePath):
			return
		# read the file
		self.settings= self._load()
		if self.settings is not None:
			self.initialized = True


	def _load(self):
		confspec = ConfigObj(StringIO(""), list_values=False, encoding="UTF-8")
		confspec.newlines = "\r\n"
		try:
			settings = ConfigObj(self.filePath, configspec = confspec, indent_type = "\t", encoding="UTF-8")
		except ConfigObjError as e:
			log.warning("error: cannot read %s file"%self.filePath)
			settings = None

		return settings


			
