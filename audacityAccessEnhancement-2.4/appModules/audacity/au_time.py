# -*- coding: UTF-8 -*-
# appModules\audacity\au_time.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2018, Paulber19
# This file is covered by the GNU General Public License.
# Released under GPL 2


import addonHandler
addonHandler.initTranslation()


def formatTime(sTime):
	# to convert a string like:
	# xx h yy m zz s to xx:yy:zz
	# or xx h yy m zz.www s to xx:yy:zz,www
	# or dd days xx h yy m zz s to dd:xx:yy:zz
	# or dd days xx h yy m zz.www s to dd:xx:yy:zz,www
	# xx h yy m zz s+wwww samples to xx:yy:zz+wwww
	# other format are not supported
	sTemp = sTime.lower()
	sTemp = sTemp.replace("h", ":")
	sTemp = sTemp.replace("m", ":")
	sTemp = sTemp.replace(" s+", "+")
	sTemp = sTemp.replace("s", "")
	sTemp = sTemp.strip()
	sTemp = sTemp.replace(" : ", ":")
	lTemp = sTemp.split(" ")
	if len(lTemp) > 1:
		# time with days
		sTemp = lTemp[0] + ":" + lTemp[-1]
	# sTemp = sTemp.replace(" ", "")
	return sTemp


def getTimeMessage(sTime):
	sep = "," if "," in sTime else "."
	iNotNull = False
	sTemp = sTime
	samples = None
	if "+" in sTime:
		lTemp = sTime.split("+")
		sTemp = lTemp[0] if len(lTemp[0]) else ""
		samples = int(lTemp[1])
	lTime = sTemp.split(":") if len(sTemp) else []
	iDays = 0
	iHours = 0
	iMinutes = 0
	iSeconds = 0
	iMSeconds = 0
	if len(lTime) == 4:
		# time with days
		iDays = int(lTime[0])
		lTime = lTime[1:]
	if len(lTime) == 3:
		iHours = int(lTime[0])
		iMinutes = int(lTime[1])
		temp = lTime[2].split(sep)
		if len(temp) == 2:
			iSeconds = int(temp[0])
			iMSeconds = int(temp[1])
		else:
			iSeconds = int(temp[0])
			iMSeconds = 0
	elif len(lTime) == 2:
		iMinutes = int(lTime[0])
		sTemp = lTime[1].split(sep)
		if len(sTemp) == 2:
			iSeconds = int(sTemp[0])
			iMSeconds = int(sTemp[1])
		else:
			iSeconds = int(sTemp)
			iMSeconds = 0
	elif len(lTime) == 1:
		if len(lTime[0].split(sep)) == 2:
			sTemp = lTime[0].split(sep)
			iSeconds = int(sTemp[0])
			iMSeconds = int(sTemp[1])
		else:
			iSeconds = int(lTime[0])
			iMSeconds = 0
	textList = []
	if iDays:
		if iDays == 1:
			# Translators: a part of message to the user to say one day.
			textList.append(_("one day"))
		else:
			# Translators: a part of message to the user to say number of day.
			textList.append(_("%s days") % iDays)
	if iHours:
		if iHours == 1:
			# Translator: a part of message to the user to say one hour.
			textList.append(_("one hour"))
		else:
			# Translators: a part of message to the user to say  hours.
			textList.append(_("%s hours") % iHours)

	if iMinutes:
		iNotNull = True
		if iMinutes == 1:
			# Translators: a part of message to the user to say  one minute.
			textList.append(_("1 minute"))
		else:
			# Translators: a part of message to the user to say minutes.
			textList.append(_("%s minutes") % iMinutes)
	if iMSeconds:
		iNotNull = True
		if iSeconds:
			if iSeconds == 1:
				# Translators: a part to the user to say one second.
				textList.append(_("1 second {0}") .format(iMSeconds))
			else:
				# Translators: a part of message to  the user to say seconds.
				textList.append(_("{0} seconds {1}") .format(iSeconds, iMSeconds))

		else:
			# Translators: a part of message to the user to say 0 second.
			textList.append(_("0 second %s") % iMSeconds)

	else:
		if iSeconds:
			iNotNull = True
			# Translators: a part of message to the user to say seconds.
			textList.append(_("%s second") % iSeconds)

	if len(lTime) and not iNotNull:
		# Translators: a part of message to the user to say 0 seconds.
		textList.append(_("0 second"))

	if samples is not None:
		if samples == 1:
			# Translators: a part of message to the user to say one sample.
			textList.append(_("one sample"))
		elif samples > 1:
			# Translators: a part of message to the user to say number of samples.
			textList.append(_("%s samples") % samples)
		elif not iNotNull:
			# Translators: a part of message to the user to say 0 sample.
			textList.append(_("0 sample"))
	return " ".join(textList)


def isNullDuration(sDuration):
	for c in sDuration:
		if not c.isdigit():
			continue
		if c != "0":
			return False
	return True
