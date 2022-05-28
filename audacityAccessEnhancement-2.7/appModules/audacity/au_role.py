# appModules\audacity\au_role.py
# a part of audacityAccessEnhancement add-on
# Copyright (C) 2018-2021, Paulber19
# This file is covered by the GNU General Public License.
# Released under GPL 2

import controlTypes


def addControlTypeRole(roleName, value, roleLabel):
	"""
	Allows you to add a role, with its value and its label, in the controlTypes module.
	This feature supports versions of NVDA that only use role constants, as well as those that use
	the controlTypes.Role enumeration class.
	parameters :
	@param roleName : name of the role, which must be written in all caps.
	@type roleName : str.
	@param value : Role value, which must be represented by a decimal number.
	@type value : int.
	@param roleLabel : The name of the role, which must match the type of the newly created role.
	@type roleLabel : str.
	@return : Void.
	@rtype : Void
	"""
	roleName = roleName.upper()
	if hasattr(controlTypes, "Role"):
		from utils.displayString import DisplayStringIntEnum
		names = [(x.name, x.value) for x in controlTypes.Role] + [(roleName, value)]
		Role = DisplayStringIntEnum("Role", names)
		from controlTypes.role import _roleLabels
		roleLabels = dict(_roleLabels)
		roleLabels[getattr(Role, roleName)] = roleLabel
		Role._displayStringLabels = roleLabels
		controlTypes.Role = Role
	else:
		setattr(controlTypes, "ROLE_{}".format(roleName), value)
		controlTypes.roleLabels[getattr(controlTypes, "ROLE_{}".format(roleName))] = roleLabel


_audacityRoles = (
	("TRACKVIEW", 300, ""),
	("TRACK", 301, "")
)


def extendNVDARole(roles=_audacityRoles):
	"""
	Allows you to add some roles, with its value and its label, in the controlTypes module.
	This feature supports versions of NVDA that only use role constants,
	as well as those that use the controlTypes.Role enumeration class.
	parameters :
	@param roles: list which defines for each role:
	@the roleName (type str) name of the role, which must be written in all caps.
	@the Role value(type int), which must be represented by a decimal number.
	@ the roleLabel:  The display name of the role (type str),
	which must match the type of the newly created role.
	@return : new role enum
	@rtype : DisplayStringIntEnum
	"""
	import controlTypes
	names = [(x.name, x.value) for x in controlTypes.Role]
	for roleName, roleValue, roleLabel in roles:
		roleName = roleName.upper()
		names = names + [(roleName, roleValue)]
	from utils.displayString import DisplayStringIntEnum
	Role = DisplayStringIntEnum("Role", names)
	from controlTypes.role import _roleLabels
	roleLabels = dict(_roleLabels)
	for roleName, roleValue, roleLabel in roles:
		roleLabels[getattr(Role, roleName)] = roleLabel
	Role._displayStringLabels = property(lambda self: roleLabels)
	return (Role, roleLabels)
