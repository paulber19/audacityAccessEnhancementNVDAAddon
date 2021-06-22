# shared\au_addonConfigManager.py
# a part of audacityAccessEnhancement add-on
# Copyright 2021,paulber19
# released under GPL.


from logHandler import log
import addonHandler
import os
import config
import globalVars
from configobj import ConfigObj
from configobj.validate import Validator

from io import StringIO

addonHandler.initTranslation()

# config section
SCT_General = "General"
SCT_Options = "Options"

# general section items
ID_ConfigVersion = "ConfigVersion"
ID_AutoUpdateCheck = "AutoUpdateCheck"
ID_UpdateReleaseVersionsToDevVersions = "UpdateReleaseVersionsToDevVersions"
# Options items
ID_AutomaticSelectionChangeReport = "AutomaticSelectionChangeReport"
ID_ReportToolbarsName = "ReportayToolbarNameOnFocusEntered"
ID_UseSpaceBarToPressButton = "UseSpaceBarToPressButton"
ID_EditSpinBoxEnhancedAnnouncement = "EditSpinBoxEnhancedAnnouncement"
_curAddon = addonHandler.getCodeAddon()
_addonName = _curAddon.manifest["name"]


class BaseAddonConfiguration(ConfigObj):
	_version = ""
	""" Add-on configuration file. It contains metadata about add-on . """
	_GeneralConfSpec = """[{section}]
	{idConfigVersion} = string(default = " ")

	""".format(
		section=SCT_General,
		idConfigVersion=ID_ConfigVersion)

	configspec = ConfigObj(StringIO("""# addon Configuration File
	{general}""".format(general=_GeneralConfSpec, )
	), list_values=False, encoding="UTF-8")

	def __init__(self, input):
		""" Constructs an L{AddonConfiguration} instance from manifest string data
		@param input: data to read the addon configuration information
		@type input: a fie-like object.
		"""
		super(BaseAddonConfiguration, self).__init__(input, configspec=self.configspec, encoding='utf-8', default_encoding='utf-8')  # noqa:E501
		self.newlines = "\r\n"
		self._errors = []
		val = Validator()
		result = self.validate(val, copy=True, preserve_errors=True)
		if not result:
			self._errors = result

	@property
	def errors(self):
		return self._errors


class AddonConfiguration10(BaseAddonConfiguration):
	_version = "1.0"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	{autoUpdateCheck} = boolean(default=True)
	{updateReleaseVersionsToDevVersions} = boolean(default=False)
	""".format(
		section=SCT_General,
		configVersion=ID_ConfigVersion,
		version=_version,
		autoUpdateCheck=ID_AutoUpdateCheck,
		updateReleaseVersionsToDevVersions=ID_UpdateReleaseVersionsToDevVersions)

	_OptionsConfSpec = """[{section}]
	{automaticSelectionChangeReport} = boolean(default=True)
	{reportToolbarsName} = boolean(default=True)
	{useSpaceBarToPressButton} = boolean(default=True)
	""".format(
		section=SCT_Options,
		automaticSelectionChangeReport=ID_AutomaticSelectionChangeReport,
		reportToolbarsName=ID_ReportToolbarsName,
		useSpaceBarToPressButton=ID_UseSpaceBarToPressButton)

	#: The configuration specification
	configspec = ConfigObj(StringIO("""# addon Configuration File
{general}\r\n{options}
""".format(general=_GeneralConfSpec, options=_OptionsConfSpec)
), list_values=False, encoding="UTF-8")  # noqa:E122


class AddonConfiguration11(BaseAddonConfiguration):
	_version = "1.1"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	{autoUpdateCheck} = boolean(default=True)
	{updateReleaseVersionsToDevVersions} = boolean(default=False)
	""".format(
		section=SCT_General,
		configVersion=ID_ConfigVersion,
		version=_version,
		autoUpdateCheck=ID_AutoUpdateCheck,
		updateReleaseVersionsToDevVersions=ID_UpdateReleaseVersionsToDevVersions)

	_OptionsConfSpec = """[{section}]
	{automaticSelectionChangeReport} = boolean(default=True)
	{reportToolbarsName} = boolean(default=True)
	{useSpaceBarToPressButton} = boolean(default=True)
	{editSpinBoxEnhancedAnnouncement} = boolean(default=True)
	""".format(
		section=SCT_Options,
		automaticSelectionChangeReport=ID_AutomaticSelectionChangeReport,
		reportToolbarsName=ID_ReportToolbarsName,
		useSpaceBarToPressButton=ID_UseSpaceBarToPressButton,
		editSpinBoxEnhancedAnnouncement=ID_EditSpinBoxEnhancedAnnouncement)

	#: The configuration specification
	configspec = ConfigObj(StringIO("""# addon Configuration File
{general}\r\n{options}
""".format(general=_GeneralConfSpec, options=_OptionsConfSpec)
), list_values=False, encoding="UTF-8")  # noqa:E122

	def mergeWithPreviousConfigurationVersion(self, previousConfig):
		previousVersion = previousConfig[SCT_General][ID_ConfigVersion]
		# configuration 1.0 to 1.1
		#  keep all previous settings, excluded version
		del previousConfig[SCT_General][ID_ConfigVersion]
		self[SCT_General].update(previousConfig[SCT_General])
		self[SCT_Options].update(previousConfig[SCT_Options])
		log.warning("%s: Merge with previous configuration version: %s" % (_addonName, previousVersion))  # noqa:E501


class AddonConfigurationManager():
	_currentConfigVersion = "1.1"
	_versionToConfiguration = {
		"1.0": AddonConfiguration10,
		"1.1": AddonConfiguration11,
		}

	def __init__(self, ):
		self.configFileName = "%sAddon.ini" % _addonName
		self.loadSettings()
		config.post_configSave.register(self.handlePostConfigSave)

	def loadSettings(self):
		addonConfigFile = os.path.join(
			globalVars.appArgs.configPath, self.configFileName)
		configFileExists = False
		if os.path.exists(addonConfigFile):
			baseConfig = BaseAddonConfiguration(addonConfigFile)
			if baseConfig[SCT_General][ID_ConfigVersion] != self._currentConfigVersion:
				# old config file must not exist here. Must be deleted
				os.remove(addonConfigFile)
				log.warning("%s: Previous  config file removed: %s" % (_addonName, addonConfigFile))  # noqa:E501
			else:
				configFileExists = True
		self.addonConfig = self._versionToConfiguration[self._currentConfigVersion](addonConfigFile)  # noqa:E501
		if self.addonConfig.errors != []:
			log.warning("%s: Addon configuration file error" % _addonName)
			self.addonConfig = None
			return
		curPath = _curAddon.path
		oldConfigFile = os.path.join(curPath,  self.configFileName)
		if os.path.exists(oldConfigFile):
			if not configFileExists:
				self.mergeSettings(oldConfigFile)
			os.remove(oldConfigFile)
		if not configFileExists:
			self.saveSettings(True)

	def mergeSettings(self, previousConfigFile):
		baseConfig = BaseAddonConfiguration(previousConfigFile)
		previousVersion = baseConfig[SCT_General][ID_ConfigVersion]
		if previousVersion not in self._versionToConfiguration:
			log.warning("%s: Configuration merge error: unknown previous configuration version number" % _addonName)  # noqa:E501
			return
		previousConfig = self._versionToConfiguration[previousVersion](previousConfigFile)  # noqa:E501
		if previousVersion == self.addonConfig[SCT_General][ID_ConfigVersion]:
			# same config version, update data from previous config
			self.addonConfig.update(previousConfig)
			log.warning("%s: Configuration updated with previous configuration file" % _addonName)  # noqa:E501
			return
		# different config version, so do a  merge with previous config.
		self.addonConfig.mergeWithPreviousConfigurationVersion(previousConfig)
		try:
			# self.addonConfig.mergeWithPreviousConfigurationVersion(previousConfig)
			pass
		except:  # noqa:E722
			pass

	def saveSettings(self, force=False):
		# We never want to save config if runing securely
		if globalVars.appArgs.secure:
			return
		# We save the configuration, in case the user
			# would not have checked the "Save configuration on exit
			# " checkbox in General settings or force is is True
		if not force and not config.conf['general']['saveConfigurationOnExit']:
			return
		if self.addonConfig is None:
			return
		try:
			val = Validator()
			self.addonConfig.validate(val, copy=True)
			self.addonConfig.write()
			log.warning("%s: configuration saved" % _addonName)
		except:  # noqa:E722
			log.warning("%s: Could not save configuration - probably read only file system" % _addonName)  # noqa:E501

	def handlePostConfigSave(self):
		self.saveSettings(True)

	def terminate(self):
		self.saveSettings()
		config.post_configSave.unregister(self.handlePostConfigSave)

	def toggleOption(self, id, toggle=True):
		conf = self.addonConfig
		if toggle:
			conf[SCT_Options][id] = not conf[SCT_Options][id]
			self.saveSettings()
		return conf[SCT_Options][id]

	def toggleReportToolbarNameOnFocusEnteredOption(self, toggle=True):
		return self.toggleOption(ID_ReportToolbarsName, toggle)

	def toggleAutomaticSelectionChangeReportOption(self, toggle=True):
		return self.toggleOption(ID_AutomaticSelectionChangeReport, toggle)

	def toggleUseSpaceBarToPressButtonOption(self, toggle=True):
		return self.toggleOption(ID_UseSpaceBarToPressButton, toggle)

	def toggleEditSpinBoxEnhancedAnnouncementOption(self, toggle=True):
		return self.toggleOption(ID_EditSpinBoxEnhancedAnnouncement, toggle)

	def toggleGeneralOption(self, id, toggle):
		conf = self.addonConfig
		if toggle:
			conf[SCT_General][id] = not conf[SCT_General][id]
			self.saveSettings()
		return conf[SCT_General][id]

	def toggleAutoUpdateCheck(self, toggle=True):
		return self.toggleGeneralOption(ID_AutoUpdateCheck, toggle)

	def toggleUpdateReleaseVersionsToDevVersions(self, toggle=True):
		return self.toggleGeneralOption(
			ID_UpdateReleaseVersionsToDevVersions, toggle)


# singleton for addon config manager
_addonConfigManager = AddonConfigurationManager()
