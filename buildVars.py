# -*- coding: UTF-8 -*-

import os.path

# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.


# Full getext (please don't change)
def _(arg):
	return arg


# Add-on information variables
addon_info = {
	# for previously unpublished addons,
	# please follow the community guidelines at:
	# https://bitbucket.org/nvdaaddonteam/todo/raw/master/guideLines.txt
	# add-on Name, internal for nvda
	"addon_name": "audacityAccessEnhancement",
	# Add-on summary, usually the user visible name of the addon.
	# Translators: Summary for this add-on
	# to be shown on installation and add-on information.
	"addon_summary": _("Audacity multi-track editor: accessibility enhancement"),
	# Add-on description
	# Translators: Long description to be shown for this add-on
	# on add-on information from add-ons manager
	"addon_description": _("""This add-on adds extra functionality when working with Audacity

* a script to report the audio position,
* a script to report the selection,
* a script to announce the state of the  "Pause",  "Play" and "record" buttons,
* automatic audio position changes report ,
* automatic selection changes report (can be disabled),
* time spin box editting support,
* use of spacebar to press a button,
* script to report playback/recording peak level,
* script to report playback/record slider level,
* script to report playback speed,
* script to display add-on user manual,
* script to display audacity guide written by David Bailes.


This addon's version has been tested with audacity 3.4, 3.4.2, 3.3.0 and 3.3.3.
Prior  versions of Audacity are not  supported.
"""),

	# version
	"addon_version": "3.0",
	# Author(s)
	"addon_author": "paulber19",
	# URL for the add-on documentation support
	"addon_url": "https://github.com/paulber19/audacityAccessEnhancementNVDAAddon.git",
	# URL for the add-on repository where the source code can be found
	"addon_sourceURL": "https://github.com/paulber19/audacityAccessEnhancementNVDAAddon.git",
	# Documentation file name
	"addon_docFileName": "addonUserManual.html",
	# Minimum NVDA version supported (e.g. "2018.3")
	"addon_minimumNVDAVersion": "2022.1",
	# Last NVDA version supported/tested (e.g. "2018.4", ideally more recent than minimum version)
	"addon_lastTestedNVDAVersion": "2023.3",
	# Add-on update channel (default is stable or None)
	"addon_updateChannel": None,
	# Add-on license such as GPL 2
	"addon_license": "GPL v2",
	# URL for the license document the ad-on is licensed under
	"addon_licenseURL": "https://www.gnu.org/licenses/gpl-2.0.html",
}


# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = [
	os.path.join("addon", "*.py"),
	os.path.join("addon", "shared", "*.py"),
	os.path.join("addon", "appModules", "audacity", "*.py"),
	os.path.join("addon", "globalPlugins", "audacityAccessEnhancement", "*.py"),
	os.path.join(
		"addon", "globalPlugins", "audacityAccessEnhancement", "updateHandler", "*.py"),
]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles = []

# Base language for the NVDA add-on
# If your add-on is written in a language other than english, modify this variable.
# For example, set baseLanguage to "es" if your add-on is primarily written in spanish.
baseLanguage = "en"

# Markdown extensions for add-on documentation
# Most add-ons do not require additional Markdown extensions.
# If you need to add support for markup such as tables, fill out the below list.
# Extensions string must be of the form "markdown.extensions.extensionName"
# e.g. "markdown.extensions.tables" to add tables.
markdownExtensions = []
