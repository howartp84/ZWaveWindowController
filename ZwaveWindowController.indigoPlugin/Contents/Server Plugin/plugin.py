#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

#Thanks to Scott Ainsworth, a SmartThings user, who worked out how to get RFWC5 working with ST - and thus enabled me to implement
#the same logic in this plugin.  Why oh why Cooper have to defy the zwave spec I don't understand, but at least we got there in the end!

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
			#indigo.server.log("Scene Device: %s" % indigo.devices[int(self.sceneDevID)].name)
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

	########################################
	def zwaveCommandReceived(self, cmd):
		byteList = cmd['bytes']			# List of the raw bytes just received.
		byteListStr = convertListToHexStr(byteList)
		nodeId = cmd['nodeId']			# Can be None!
		endpoint = cmd['endpoint']		# Often will be None!

		bytes = byteListStr.split()

		if (int(bytes[5],16) == 82):			#Add node IDs here for debugging
			self.debugLog(u"Raw Node 82 command: %s" % (byteListStr))

		if (int(bytes[5],16) == 85):			#Add node IDs here for debugging
			self.debugLog(u"Raw Node 85 command: %s" % (byteListStr))

		if (int(bytes[5],16)) not in self.controllerIDs:
			#self.debugLog(u"Node %s is not a scene controller - ignoring" % (int(bytes[5],16)))
			return
		else:
			self.debugLog(u"Node ID %s found in controllerIDs" % (int(bytes[5],16)))

		if (int(bytes[5],16) == 34):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 34 command: %s" % (byteListStr))

		if (int(bytes[5],16) == 35):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 35 command: %s" % (byteListStr))

		if (int(bytes[5],16) == 44):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 44 command: %s" % (byteListStr))

		if (int(bytes[5],16) == 61):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 61 command: %s" % (byteListStr))



		#######
		#
		# Action Map Description
		#
		#<List>
			#<Option value="0">Click</Option>
			#<Option value="1">Double-Click</Option>
			#<Option value="2">Triple-Click</Option>
			#<Option value="3">Quadruple-Click</Option>
			#<Option value="4">Quintuple-Click</Option>
			#<Option value="a">---</Option>
			#<Option value="5">Hold    (*Central Scene mode)</Option>
			#<Option value="6">Release</Option>
			#<Option value="b">---</Option>
			#<Option value="7">Brighten Start (*Basic Scene mode)</Option>
			#<Option value="8">Brighten Stop</Option>
			#<Option value="9">Dim Start</Option>
			#<Option value="10">Dim Stop</Option>
			#<Option value="c">---</Option>
			#<Option value="11">On</Option>
			#<Option value="12">Off</Option>
		#</List>
		#actions = ["-","Click","Double-Click","Brighten Start", "Dim Start", "Brighten Stop", "Dim Stop", "Triple-Click", "Quad-Click", "Quint-Click"]
		#actionMap = {1:0, 2:1, 3:7, 4:9, 5:8, 6:10, 7:2, 8:3, 9:4}
		#
		#actions = ["Click","Release","Hold", "Double-Click", "Triple-Click", "Quad-Click", "Quint-Click"]
		#actionMap = {0:0, 1:6, 2:5, 3:1, 4:2, 5:3, 6:4}

		if (bytes[7] == "2B") and (bytes[8] == "01"): #Basic Scene
			actions = ["-","Click","Double-Click","Brighten Start", "Dim Start", "Brighten Stop", "Dim Stop", "Triple-Click", "Quad-Click", "Quint-Click"]
			actionMap = {1:0, 2:1, 3:7, 4:9, 5:8, 6:10, 7:2, 8:3, 9:4}
			#ActionByte of 1 = Click, so actionMap[1] = actions[0], or {1:0, ...]
			self.debugLog(u"-----")
			self.debugLog(u"Version: %s" % self.version)
			self.debugLog(u"Basic Scene Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"NodeID:      %s" % (nodeId))

			actionRaw = int(bytes[9],16)
			self.debugLog(u"ActionRaw: %s" % (actionRaw))
			if (actionRaw < 10):
				self.debugLog(u"Button:    %s" % (str(int(bytes[9],16))))
				self.debugLog(u"ActionID:  1")
				self.debugLog(u"Action:    %s" % (actions[1]))
				actionIn = "1"
				action = str(actionMap[int(actionIn)])
				button = str(int(bytes[9],16))
			else:
				self.debugLog(u"Button:    %s" % (str(int(bytes[9],16))[0:1]))
				self.debugLog(u"ActionID:  %s" % (str(int(bytes[9],16))[1:2]))
				self.debugLog(u"Action:    %s" % (actions[int(str(int(bytes[9],16))[1:2])]))
				actionIn = str(int(bytes[9],16))[1:2]
				action = str(actionMap[int(actionIn)])
				button = str(int(bytes[9],16))[0:1]
			self.debugLog(u"-----")

			if (int(bytes[5],16)) in self.controllerIDs: #Has dummy device
				devID = self.devFromNode[int(bytes[5],16)]
				dev = indigo.devices[int(devID)]
				lastScene = dev.states['currentScene']
				repeatCount = dev.states['repeatCount']
				repeatStart = dev.states['repeatStart']
				if (repeatStart == ""):
					repeatStart = 0
				timeDif = time.time() - float(repeatStart)
				if ((lastScene == button) and (repeatCount < 4) and (timeDif < 2000)):
					dev.updateStateOnServer("repeatCount", repeatCount+1)
				else:
					dev.updateStateOnServer("repeatCount", 0)
					dev.updateStateOnServer("repeatStart", time.time())
					self.triggerEvent("cmdReceived",bytes[5],button,action)
					self.updateDevScene(int(bytes[5],16),button,action)
			else:
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)

		if (bytes[6] == "05") and (bytes[7] == "5B"): #Central Scene
			if (int(bytes[10],16) > 127):
				self.debugLog(u"B10: %s" % (int(bytes[10],16)))
				x = (int(bytes[10],16)-128)
				self.debugLog(u"X10: %s" % (x))
				bytes[10] = hex(x)[2:]
				self.debugLog(u"B10: %s" % (int(bytes[10],16)))
			actions = ["Click","Release","Hold", "Double-Click", "Triple-Click", "Quad-Click", "Quint-Click"]
			actionMap = {0:0, 1:6, 2:5, 3:1, 4:2, 5:3, 6:4}
			#ActionByte of 0 = Click, so actionMap[0] = actions[0], or {0:0, ...]
			self.debugLog(u"-----")
			self.debugLog(u"Version: %s" % self.version)
			self.debugLog(u"Central Scene Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			#self.debugLog(u"0x03:    %s" % (int(bytes[8],16))) #This is 0x03 Report (ie not Get/Set)
			self.debugLog(u"Node:    %s" % (int(bytes[5],16)))
			self.debugLog(u"Button:  %s" % (int(bytes[11],16)))
			self.debugLog(u"ActionID:  %s" % (int(bytes[10])))
			self.debugLog(u"Action:  %s" % (actions[int(bytes[10])]))
			#self.debugLog(u"FireID:  %s" % (int(bytes[9],16)))
			self.debugLog(u"-----")

			action = str(actionMap[int(bytes[10])])
			button = str(int(bytes[11],16))
			#if (self.fireHash <> None):
				#self.debugLog(u"Hash <> none")
			#if (self.fireHash <> (str(int(bytes[9],16))[0:1] + str(int(bytes[9],16)))):
				#self.debugLog(u"Hash <> strint")
			if (self.fireHash <> None) and (self.fireHash <> (str(int(bytes[9],16))[0:1] + str(int(bytes[9],16)))):
				#self.debugLog(u"Triggering button %s, action %s" % (button,action))
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)
			self.fireHash = str(int(bytes[9],16))[0:1] + str(int(bytes[9],16))
			self.debugLog(self.fireHash)

		if (bytes[7] == "20") and (bytes[8] == "01"): #Basic Set On/Off
			actions = ["Off","On"]
			actionMap = {0:12, 1:11}
			#ActionByte of 0 = Off,  so actionMap[0] = actions[12], or {0:12, ...]
			#ActionByte of 255 = 1 = On, so actionMap[1] = actions[11], or {1:11, ...]  as we've mapped 1 to 255 further down
			self.debugLog(u"-----")
			self.debugLog(u"On/Off Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"NodeID:    %s" % (nodeId))

			actionRaw = int(bytes[9],16)
			if (actionRaw == 255):
				actionRaw = 1
			self.debugLog(u"ActionRaw: %s" % (actionRaw))
			self.debugLog(u"Button:    1")
			self.debugLog(u"ActionID:  %s" % (actionMap[actionRaw]))
			self.debugLog(u"Action:    %s" % (actions[actionRaw]))
			action = str(actionMap[int(actionRaw)])
			button = str(1)

			if (int(bytes[5],16)) in self.controllerIDs: #Has dummy device
				devID = self.devFromNode[int(bytes[5],16)]
				dev = indigo.devices[int(devID)]
				#lastScene = dev.states['currentScene']
				repeatCount = dev.states['repeatCount']
				repeatStart = dev.states['repeatStart']
				if (repeatStart == ""):
					repeatStart = 0
				timeDif = time.time() - float(repeatStart)
				repeatDelay = self.delayFromNode[int(bytes[5],16)]
				if (timeDif < repeatDelay):
					#Ignore command
					dev.updateStateOnServer("repeatCount", repeatCount+1)
				else:
					#Update time of last successful command, and trigger it
					dev.updateStateOnServer("repeatCount", 0)
					dev.updateStateOnServer("repeatStart", time.time())
					self.triggerEvent("cmdReceived",bytes[5],button,action)
					self.updateDevScene(int(bytes[5],16),button,action)
			else:
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)
			self.debugLog(u"-----")

		if (bytes[7] == "25") and (bytes[8] == "03"): #Switch Binary
			actions = ["Off","On"]
			actionMap = {0:12, 1:11}
			#ActionByte of 0 = Off,  so actionMap[0] = actions[12], or {0:12, ...]
			#ActionByte of 255 = 1 = On, so actionMap[1] = actions[11], or {1:11, ...]  as we've mapped 1 to 255 further down
			self.debugLog(u"-----")
			self.debugLog(u"Version: %s" % self.version)
			self.debugLog(u"On/Off Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"NodeID:    %s" % (nodeId))

			actionRaw = int(bytes[9],16)
			if (actionRaw == 255):
				actionRaw = 1
			self.debugLog(u"ActionRaw: %s" % (actionRaw))
			self.debugLog(u"Button:    1")
			self.debugLog(u"ActionID:  %s" % (actionMap[actionRaw]))
			self.debugLog(u"Action:    %s" % (actions[actionRaw]))
			action = str(actionMap[int(actionRaw)])
			button = str(1)

			if (int(bytes[5],16)) in self.controllerIDs: #Has dummy device
				devID = self.devFromNode[int(bytes[5],16)]
				dev = indigo.devices[int(devID)]
				#lastScene = dev.states['currentScene']
				repeatCount = dev.states['repeatCount']
				repeatStart = dev.states['repeatStart']
				if (repeatStart == ""):
					repeatStart = 0
				timeDif = time.time() - float(repeatStart)
				repeatDelay = self.delayFromNode[int(bytes[5],16)]
				if (timeDif < repeatDelay):
					#Ignore command
					dev.updateStateOnServer("repeatCount", repeatCount+1)
				else:
					#Update time of last successful command, and trigger it
					dev.updateStateOnServer("repeatCount", 0)
					dev.updateStateOnServer("repeatStart", time.time())
					self.triggerEvent("cmdReceived",bytes[5],button,action)
					self.updateDevScene(int(bytes[5],16),button,action)
			else:
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)
			self.debugLog(u"-----")

		if (bytes[7] == "2C") and (bytes[8] == "02"): #Scene Actuator Conf Get (probably from Enerwave)
			self.debugLog(u"-----")
			self.debugLog(u"Version: %s" % self.version)
			self.debugLog(u"Actuator Config Get received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"Scene:      %s" % (int(bytes[9],16)))

			self.updateDevScene(int(bytes[5],16),int(bytes[9],16),"")

		if (bytes[7] == "2D") and (bytes[8] == "03"): #Scene Controller Config Report
			self.debugLog(u"-----")
			self.debugLog(u"Version: %s" % self.version)
			self.debugLog(u"Controller Config Report received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"Group:      %s" % (int(bytes[9],16)))
			self.debugLog(u"Scene:      %s" % (int(bytes[10],16)))

			self.updateDevScene(int(bytes[5],16),int(bytes[10],16),"")



	def triggerStartProcessing(self, trigger):
		self.debugLog(u"Start processing trigger " + unicode(trigger.name))
		self.events[trigger.pluginTypeId][trigger.id] = trigger
		#self.debugLog(str(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"]))
		#self.debugLog(str(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"]))
		#self.debugLog(u"-----")
		#self.debugLog(u"Model ID:" + str(indigo.devices[int(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"])].ownerProps['zwModelId']))
		#self.debugLog(u"-----")
		#self.debugLog(str(indigo.devices[575842701]))
		#dev = indigo.devices[575842701]
		#self.debugLog(dev.ownerProps['address'])

	def triggerStopProcessing(self, trigger):
		self.debugLog(u"Stop processing trigger " + unicode(trigger.name))
		if trigger.pluginTypeId in self.events:
			if trigger.id in self.events[trigger.pluginTypeId]:
				del self.events[trigger.pluginTypeId][trigger.id]

	def triggerEvent(self,eventType,deviceAddress,deviceButton,deviceAction):
		#self.plugin.debugLog(u"triggerEvent called")
		for trigger in self.events[eventType]:

			triggered = False #Default value

			for i in range(5): #i = 0-4
				if triggered:
					self.debugLog("Skipping %s as Triggered" % i)
					continue #Skip remaining deviceAddresses in a given Trigger
				dA = "deviceAddress" + str(i)
				if str(dA) == "deviceAddress0":
					dA = "deviceAddress"  #Handle backwards compatibility
				#self.debugLog("dA List: %s" % dA)

				try:
					dAddress = self.events[eventType][trigger].pluginProps[str(dA)]
				except KeyError as k:
					#self.debugLog("Please edit and save trigger %s" % indigo.triggers[trigger].name)
					continue #Perfectly acceptable for backward compatibility
				if dAddress <> "":
					dDev = indigo.devices.get(int(dAddress),None)
					#self.debugLog(str(dDev))
					self.debugLog("dA: %s" % deviceAddress)
					#self.debugLog("dA: %s" % dDev.ownerProps['address'])
					if (fnmatch.fnmatch(str(int(deviceAddress,16)),str(dDev.ownerProps['address']))):
						if (fnmatch.fnmatch(str(int(deviceButton)),self.events[eventType][trigger].pluginProps["deviceButton"])):
							if (fnmatch.fnmatch(str(int(deviceAction)),self.events[eventType][trigger].pluginProps["deviceAction"])):
								indigo.trigger.execute(trigger)
								triggered = True
								#return #don't execute twice if same device selected
			triggered = False #Reset for next Trigger


	#SCENE_ACTIVATION 			0x2B	43
	#SCENE_ACTUATOR_CONF		0x2C	44
	#SCENE_CONTROLLER_CONF 	0x2D	45

	#SCENE_ACTIVATION_SET			0x01

	#SCENE_CONTROLLER_CONF_SET		0x01
	#SCENE_CONTROLLER_CONF_GET		0x02
	#SCENE_CONTROLLER_CONF_REPORT	0x03

	def testGet1(self):
		self.debugLog("MenuItem Get Button 1 called")
		codeStr = [45, 2, 1]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testGet2(self):
		self.debugLog("MenuItem Get Button 2 called")
		codeStr = [45, 2, 2]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testGet3(self):
		self.debugLog("MenuItem Get Button 3 called")
		codeStr = [45, 2, 3]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet1(self):
		self.debugLog("MenuItem Set Button 1 called")
		codeStr = [45, 1, 1, 1, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet2(self):
		self.debugLog("MenuItem Set Button 2 called")
		codeStr = [45, 1, 2, 2, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet3(self):
		self.debugLog("MenuItem Set Button 3 called")
		codeStr = [45, 1, 3, 3, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testHex(self):
		#cmd = {'bytes': [0x01,0x0A,0x00,0x04,0x08,0x26,0x04,0x2B,0x01,0x01,0xFF,0x21], 'nodeId': None, 'endpoint': None} #Button 1, no action
		cmd = {'bytes': [0x01,0x0A,0x00,0x04,0x00,0x26,0x04,0x2B,0x01,0x0B,0xFF,0x0D], 'nodeId': None, 'endpoint': None} #Button 1, Click
		self.zwaveCommandReceived(cmd)

	#SCENE_ACTIVATION 			0x2B	43
	#SCENE_ACTUATOR_CONF		0x2C	44
	#SCENE_CONTROLLER_CONF 	0x2D	45

	#ASSOCIATION 						0x85	133
	#ASSOCIATION_COMMAND_CONFIGURATION	0x98	152

	#ASSOCIATION_SET			0x01
	#ASSOCIATION_GET			0x02
	#ASSOCIATION_REPORT		0x03
	#ASSOCIATION_REMOVE		0x04

	#CONFIGURATION 					0x70	112
	#CONFIGURATION_SET			0x03			(Not 1 as normal!!)
	#CONFIGURATION_GET			0x04			(Not 2 as normal!!)
	#CONFIGURATION_REPORT		0x05			(Not 3 as normal!!)

	#SCENE_ACTIVATION_SET			0x01

	#SCENE_CONTROLLER_CONF_SET		0x01
	#SCENE_CONTROLLER_CONF_GET		0x02
	#SCENE_CONTROLLER_CONF_REPORT	0x03

	#SWITCH_MULTILEVEL		0x26	38

	#SWITCH_MULTILEVEL_SET		0x01
	#SWITCH_MULTILEVEL_GET		0x02
	#SWITCH_MULTILEVEL_REPORT	0x03
	#SWITCH_MULTILEVEL_START_LEVEL_CHANGE		0x04
	#SWITCH_MULTILEVEL_STOP_LEVEL_CHANGE		0x05

	#COMMAND_CLASS_INDICATOR	0x87


	def updateDevScene(self, inNode, inButton, inAction):
		for dev in indigo.devices.iter("self"):
			dNode = indigo.devices[int(dev.ownerProps['deviceId'])].ownerProps['address']
			if (int(dNode) == int(inNode)):
				self.debugLog(u"Updating device %s with button %s" % (dev.name,inButton))
				dev.updateStateOnServer("currentScene", "Scene %s" % (inButton))

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




