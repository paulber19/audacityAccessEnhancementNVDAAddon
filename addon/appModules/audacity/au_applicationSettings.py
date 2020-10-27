# appModules/audacity/au_applicationSettings.py.
# a part of audacityAccessEnhancement add-on
# Copyright 2018-2020 paulber19
# This file is covered by the GNU General Public License.

import os
from logHandler import log
import shlobj
import codecs
import addonHandler
import sys
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from au_py3Compatibility import importStringIO  # noqa E402
del sys.path[-1]
StringIO = importStringIO()
addonHandler.initTranslation()


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
			dir = os.path.join(
				shlobj.SHGetFolderPath(0, shlobj.CSIDL_APPDATA),
				self._settingsFolderName)
		except WindowsError:
			log.warning("%ssettings directory not found" % self.settingsFolderName)
			return None
		if os.path.exists(dir):
			return dir
		return None

	def getSettings(self):
		if not self.initialized:
			return None
		settings = AudacityCFGFileHandler(self.settingsDir).settings
		return settings

	def getAudioTimeFormat(self):
		settings = self.getSettings()
		key = "AudioTimeFormat"
		return settings[key]

	def getSelectionFormat(self):
		settings = self.getSettings()
		key = "SelectionFormat"
		return settings[key]


class AudacityCFGFileHandler(object):
	_fileName = "audacity.cfg"
	_defaultSettings = {
		"SelectionFormat": "hh:mm:ss + milliseconds",
		"AudioTimeFormat": "hh:mm:ss + milliseconds",
	}

	def __init__(self, settingsDir):
		super(AudacityCFGFileHandler, self).__init__()
		self.audacityCFGFilePath = os.path.join(settingsDir, self._fileName)
		# load audacity settings
		self.settings = self._load()

	def _load(self):
		settings = self._defaultSettings.copy()
		if not os.path.exists(self.audacityCFGFilePath):
			return settings
		src = codecs.open(self.audacityCFGFilePath, "r", "utf_8", errors="replace")
		for line in src:
			lineList = line.split("=")
			if len(lineList) != 2:
				continue
			k = lineList[0].strip()
			if k in self._defaultSettings:
				settings[k] = lineList[1].strip()
		return settings
