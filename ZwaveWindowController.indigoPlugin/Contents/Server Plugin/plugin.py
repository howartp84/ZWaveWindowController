#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

import os
import sys

import time
import datetime
import fnmatch

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

########################################
# Tiny function to convert a list of integers (bytes in this case) to a
# hexidecimal string for pretty logging.
def convertListToHexStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get("showDebugInfo", True)
		self.version = pluginVersion

		self.events = dict()
		self.events["cmdReceived"] = dict()

		self.controllerIDs = list()

		self.zedFromDev = dict()
		self.zedFromNode = dict()
		self.devFromZed = dict()
		self.devFromNode = dict()
		self.nodeFromZed = dict()
		self.nodeFromDev = dict()

		self.delayFromNode = dict()

	########################################
	def startup(self):
		self.debugLog(u"startup called -- subscribing to all incoming Z-Wave commands")
		self.debugLog("Plugin version: {}".format(self.version))
		#indigo.zwave.subscribeToIncoming()

	def shutdown(self):
		self.debugLog(u"shutdown called")

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here.
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			#self.sceneDevID = valuesDict.get("sceneDevID", 200)
			#self.sceneDevNode = indigo.devices[int(self.sceneDevID)].ownerProps['address']
			#indigo.server.log("Scene Device: {}".format(indigo.devices[int(self.sceneDevID)].name))
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")

	def deviceStartComm(self, dev):
		dev.stateListOrDisplayStateIdChanged()
		if (dev.deviceTypeId == "sceneController"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			repeatDelay = dev.ownerProps.get('repeatDelay',0)

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.delayFromNode[int(nodeID)] = int(repeatDelay)

			self.controllerIDs.append(nodeID)

	def deviceStopComm(self, dev):
		if (dev.deviceTypeId == "sceneController"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.delayFromNode.pop(int(nodeID),None)

			self.controllerIDs.remove(nodeID)

	def updateDevScene(self, inNode, inButton, inAction):
		for dev in indigo.devices.iter("self"):
			dNode = indigo.devices[int(dev.ownerProps['deviceId'])].ownerProps['address']
			if (int(dNode) == int(inNode)):
				self.debugLog(u"Updating device {} with button {}".format(dev.name,inButton))
				dev.updateStateOnServer("currentScene", "Scene {}".format(inButton))

	def cmdRaise(self,pluginAction):
		self.debugLog("cmdRaise called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 4, 96, 0]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x04 SWITCH_MULTILEVEL_START_LEVEL_CHANGE
			#96 = Up, Ignore Start
			#00 = Start Level

		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def cmdLower(self,pluginAction):
		self.debugLog("cmdLower called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 4, 32, 0]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x04 SWITCH_MULTILEVEL_START_LEVEL_CHANGE
			#32 = Down, Ignore Start
			#00 = Start Level

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def cmdOpen(self,pluginAction):
		self.debugLog("cmdOpen called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 1, 99]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x01 SWITCH_MULTILEVEL_SET
			#99 = Full Open (0-99 = 1-100)

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def cmdClose(self,pluginAction):
		self.debugLog("cmdClose called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 1, 0]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x01 SWITCH_MULTILEVEL_SET
			#0 = Full Open (0-99 = 1-100)

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def cmdPrevious(self,pluginAction):
		self.debugLog("cmdPrevious called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 1, 255]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x04 SWITCH_MULTILEVEL_SET
			#255 = Previous position

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def cmdPosition(self,pluginAction):
		self.debugLog("cmdPosition called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		position = int(pluginAction.position)

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 1, int(position)]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x04 SWITCH_MULTILEVEL_SET
			#xx = Go to position (0-99 = 1-100)

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)


	def cmdStop(self,pluginAction):
		self.debugLog("cmdStop called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		cmdClass = int(pluginAction.props["cmdClass"])

		if (cmdClass == 26): #COMMAND_CLASS_SWITCH_MULTILEVEL
			codeStr = [38, 5]
			#38 = 0x26 COMMAND_CLASS_SWITCH_MULTILEVEL
			#04 = 0x04 SWITCH_MULTILEVEL_STOP_LEVEL_CHANGE

			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)




