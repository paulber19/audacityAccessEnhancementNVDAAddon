# appModules/audacity/configManager.py
# a part of audacityAccessEnhancement add-on
# Copyright 2018,paulber19
# released under GPL.
#See the file COPYING for more details.

from logHandler import log
import addonHandler
addonHandler.initTranslation()
import os
from cStringIO import StringIO
from configobj import ConfigObj
from validate import Validator
import globalVars

# config section
SCT_General = "General"
SCT_Options = "Options"

# general section items
ID_ConfigVersion = "ConfigVersion"

# Options items
ID_AutomaticSelectionChangeReport = "AutomaticSelectionChangeReport"
ID_ReportToolbarsName = "ReportayToolbarNameOnFocusEntered"
ID_UseSpaceBarToPressButton = "UseSpaceBarToPressButton"

class BaseAddonConfiguration(ConfigObj):
	_version = ""
	""" Add-on configuration file. It contains metadata about add-on . """
	_GeneralConfSpec = """[{section}]
	{idConfigVersion} = string(default = " ")
	
	""".format(section = SCT_General,idConfigVersion = ID_ConfigVersion)
	
	configspec = ConfigObj(StringIO("""# addon Configuration File
	{0}""".format(_GeneralConfSpec, )
	), list_values=False, encoding="UTF-8")
	
	def __init__(self,input ) :
		""" Constructs an L{AddonConfiguration} instance from manifest string data
		@param input: data to read the addon configuration information
		@type input: a fie-like object.
		"""
		super(BaseAddonConfiguration, self).__init__(input, configspec=self.configspec, encoding='utf-8', default_encoding='utf-8')
		
		self.newlines = "\r\n"
		self._errors = []
		val = Validator()
		result = self.validate(val, copy=True, preserve_errors=True)
		if result != True:
			self._errors = result
	
	
	@property
	def errors(self):
		return self._errors

class AddonConfiguration10(BaseAddonConfiguration):
	_version = "1.0"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	""".format(section = SCT_General,configVersion = ID_ConfigVersion, version = _version)
	
	_OptionsConfSpec = """[{section}]
	{automaticSelectionChangeReport} = boolean(default=True)
	{reportToolbarsName} = boolean(default=True)
	{useSpaceBarToPressButton} = boolean(default=True)
	""".format(section = SCT_Options, automaticSelectionChangeReport = ID_AutomaticSelectionChangeReport, reportToolbarsName= ID_ReportToolbarsName, useSpaceBarToPressButton = ID_UseSpaceBarToPressButton)

	#: The configuration specification
	configspec = ConfigObj(StringIO("""# addon Configuration File
{0}\r\n{1}
""".format(_GeneralConfSpec, _OptionsConfSpec)
), list_values=False, encoding="UTF-8")



	
class AddonConfigurationManager():
	_currentConfigVersion = "1.0"
	_versionToConfiguration = {
		"1.0" : AddonConfiguration10,
		}
	def __init__(self, ) :
		curAddon = addonHandler.getCodeAddon()
		addonName = curAddon.manifest["name"]
		self.configFileName  = "%sAddon.ini"%addonName
		self.loadSettings()


	def loadSettings(self):
		addonConfigFile = os.path.join(globalVars.appArgs.configPath, self.configFileName)
		configFileExists = False
		if os.path.exists(addonConfigFile):
			baseConfig = BaseAddonConfiguration(addonConfigFile)
			if baseConfig[SCT_General][ID_ConfigVersion] != self._currentConfigVersion :
				# old config file must not exist here. Must be deleted
				os.remove(addonConfigFile)
				log.warning(" Old config file removed")
			else:
				configFileExists = True
		
		self.addonConfig = self._versionToConfiguration[self._currentConfigVersion](addonConfigFile)
		if self.addonConfig.errors != []:
			log.warning("Addon configuration file error")
			self.addonConfig = None
			return

		curPath = os.path.dirname(__file__).decode("mbcs")
		oldConfigFileName = "addonConfig_old.ini"
		oldConfigFile = os.path.join(curPath,  oldConfigFileName)
		if os.path.exists(oldConfigFile):
			if not configFileExists:
				self.mergeSettings(oldConfigFile)
				self.saveSettings()
			os.remove(oldConfigFile)
		if not configFileExists:
			self.saveSettings()
		#log.warning("Configuration loaded")
	
	def mergeSettings(self, oldConfigFile):
		log.warning("Merge settings with old configuration")
		baseConfig = BaseAddonConfiguration(oldConfigFile)
		version = baseConfig[SCT_General][ID_ConfigVersion]
		if version not in self._versionToConfiguration.keys():
			log.warning("Configuration merge error: unknown configuration version")
			return
		oldConfig = self._versionToConfiguration[version](oldConfigFile)
		for sect in self.addonConfig.sections:
			for k in self.addonConfig[sect].keys():
				if sect == SCT_General and k == ID_ConfigVersion:
					continue
				if sect in oldConfig.sections  and k in oldConfig[sect].keys():
					self.addonConfig[sect][k] = oldConfig[sect][k]
	
	def saveSettings(self):
		#We never want to save config if runing securely
		if globalVars.appArgs.secure: return
		if self.addonConfig  is None: return

		try:
			val = Validator()
			self.addonConfig.validate(val, copy = True)
			self.addonConfig.write()
		
		except Exception, e:
			log.warning("Could not save configuration - probably read only file system")
			raise e
	
	def terminate(self):
		self.saveSettings()
	def toggleOption (self, id, toggle = True):
		conf = self.addonConfig
		if toggle:
			conf[SCT_Options][id] = not conf[SCT_Options][id]
			self.saveSettings()
		return conf[SCT_Options][id]
	def toggleReportToolbarNameOnFocusEnteredOption(self, toggle = True):
		return self.toggleOption(ID_ReportToolbarsName , toggle)
	
	def toggleAutomaticSelectionChangeReportOption(self, toggle = True):
		return self.toggleOption(ID_AutomaticSelectionChangeReport , toggle)
		
	def toggleUseSpaceBarToPressButtonOption (self, toggle = True):
		return self.toggleOption (ID_UseSpaceBarToPressButton, toggle)


# singleton for addon config manager
_addonConfigManager = AddonConfigurationManager()

