#*****************************************************
#
#	ccDataReceiver
#
#	Clive Carrington
#	Version 0.4
#	11th April 2014
#
#	History:
#		0.4. To fix bug in processLine when receiving History, there's
#			a index out of range error at line 171
#		0.5. To add a /Heating to the mix from Bit0
#		0.6. To stop history lines being included in master list.
#		0.7. To add MySQL access (hard wiresd at first)
#		0.8. Now references heatingToSQL13.py for route to access dB
#		0.9. Checks for duplicates, and only creates new dB record is different

# Definitions

logRoot = "../log"

# Definitions for MySQL boolean entries (using short Int)
SQL_On = 0
SQL_Off = 1
SQL_Unk = 99

# Imports

import datetime
import sys
import serial
from heatingToMySQL_AWS import sendHeatingData		# Varient of this file that writes to 192.168.1.13


#*******************************************************
#
#	Import from PC. Routines to create a CSV file of 
#	readings for power and CH
#
#********************************************************

# Definitions

inputFilename="lastCC.csv"

inputMode = "Realtest"		# Sets the mode to open the lastCC.csv file rather than the main serial input 
valueLife=10	# the number of output lines before a value is nulled
				# if no new values are received	

# Routines
#
#	Loads configuration in from log/ccConfigCH.txt
#
####################################################

def configCH():
	global baseDate, logRoot, readList, fieldList, reading
	fieldList = []
	readList = []
	reading = []
	conf = open("../config/ccConfigCH.txt")
	for entry in conf:
		#print entry
		if entry.find(",")>= 0:
			entryItem = entry.split(",")
			print ">"+entryItem[0]+"<"
			if entryItem[0] == "ccBaseDate":
				print "Found baseDate"
				(baseDay,baseMonth,baseYear) = entryItem[1].split("/")
				baseDate = datetime.date(int(baseYear),int(baseMonth),int(baseDay))
			if entryItem[0] == "logRoot":
				print "Found logRoot " + entryItem[1],
				logRoot = entryItem[1]
# Section for reading in the ranges of values to be converted back into digital 

			if entryItem[0] == "read":
				readList.append([int(entryItem[1]), int(entryItem[2]), int(entryItem[3])])

# Section for defining the fields in the output table
			if entryItem[0] == "field":
				appendField(entryItem[1].strip())

	return(0)
	
	


#*********************************************************
#
#	Set of routines dealing with creating and amending the output record
#
#	constructOutputRecord creates a CSV string from the current record
#	updateField(Name, Value)
#	
#**********************************************************

def appendField(name):
	global fieldList, valueLife
	
	fieldList.append([name, 0, valueLife])
	
def updateField(field,value):	# field is the name of the field to be updated
	global fieldList, valueLife
	returnValue = -1
	index = 0
	for eachItem in fieldList:
		#print eachItem
		if eachItem[0] == field:
			#print "Set value"
			fieldList[index][1] = value
			fieldList[index][2] = valueLife
			returnValue = 0
			#print eachItem
		index += 1

def reduceLife():	# Reduce the life of each data item by onew

	index = 0
	for eachItem in fieldList:
		fieldList[index][2] -= 1
		index += 1	

def verticalSlice(listOfEntries,elementToSlice):	# two dimensional list
	newList = []
	for element in listOfEntries:
		newList.append(element[elementToSlice])
	return newList


def ref(fieldName):

	global fieldList
	for eachItem in fieldList:
		if (eachItem[0] == fieldName):
			return(eachItem[1])
	return(0)
	
def writeToSQL():

# SQL writing routine:
	sendHeatingData ( 0 , ref("roomTemp"), ref("tempTopTank"), ref("tempBottomTank"), \
						ref("askForHeating"), ref("askForHotWater"), ref("roomStatOn"), \
						ref("tankStatOn"), ref("boilerOn"), \
						ref("solarReceived"), ref("houseTotal"), ref("waterHeating") )

def constructOutputRecord(recordType="output"):
	outputString =""
	global fieldList
	
	if (recordType=="fieldNames"):
		for eachItem in fieldList:
			outputString = outputString + eachItem[0]+","
	else:
		for eachItem in fieldList:
			if eachItem[2]>0:
				outputString = outputString + str(eachItem[1]) + ","
			else:
				# If reading has expired, just print a blank
				outputString = outputString + " ,"	
	return(outputString)

def checkReadings (listOfReadings):
	""" Function doc """
	if len(listOfReadings) == 7:	# i.e. it has the right number of entries to be a valid record
		if listOfReadings[0] == 30:	# Temp 1
			topTankTemp = listOfReadings[2]*16 + listOfReadings[4]
			if topTankTemp < 100:
				updateField("topTankTemp",topTankTemp)
				updateField("tempTopTank", topTankTemp)		# For the new MySQL database
		if listOfReadings[0] == 40:	# Temp 2
			bottomTankTemp = listOfReadings[2]*16 + listOfReadings[4]
			if bottomTankTemp < 100:
				updateField("bottonTankTemp",bottomTankTemp)
				updateField("tempBottomTank",bottomTankTemp)		# For the new MySQL database
		if listOfReadings[0] == 50:	# CH status
			

###	Combinations to code

#boilerOn. Boiler = False = Boiler On
#AskForHeating. /Heat = True = Heating On
#AskForHotWater. HW = True and /HW = False = HW Off, tankStat On

#				HW = False and /HW = True = HW On, tankStat On

#				HW = /HW  = FALSE		tankStat Off

#roomStatOn. Stat = False = Stat On
#tankStatOn. HW not equal to /HW = tankStatOn

#field, askForHeating,19
#field, askForHotWater,20
#field, roomStatOn,21
#field, tankStatOn,22
#field, boilerOn,23
##### End of Combinations to code			
			CHOff = listOfReadings[4] & 1 == 0
			CHOn =  listOfReadings[4] & 2 == 0
			HWOn = listOfReadings[4] & 8 == 0
			HWOff = listOfReadings[2] & 1 == 0
			BoilerOn = listOfReadings[2] & 2 == 0
			if not CHOff:		# As /CH is unconnected, this should always be correct
				updateField("askForHeating",SQL_On)
			else:
				updateField("askForHeating",SQL_Off)


		# Provided CH is ON we can take the reading from roomSta, but if CH is off, we don't know whether Room Stat is on or not
			roomStatOn = listOfReadings[4] & 4 == 0
			if roomStatOn and CHOn:
				updateField("roomStatOn",SQL_On)
			if not roomStatOn and CHOn:
				updateField("roomStatOn",SQL_Off)
			
			if 	HWOn and not HWOff:
				updateField("askForHotWater",SQL_On)
				updateField("tankStatOn",SQL_On)
			if not HWOn and HWOff:
				updateField("askForHotWater",SQL_Off)
				updateField("tankStatOn",SQL_On)
			if HWOn and HWOff:
				updateField("askForHotWater",SQL_Unk)
				updateField("tankStatOn",SQL_Off)
				
		
			updateField("heatingOff",listOfReadings[4] & 1 == 1)
			updateField("heatingOn",listOfReadings[4] & 2 == 2)
			updateField("roomThermostatOn",listOfReadings[4] & 4 == 4)
			updateField("hotWaterOn",listOfReadings[4] & 8 == 8)
			updateField("hotWaterOff",listOfReadings[2] & 1 == 1)
			updateField("boiler",listOfReadings[2] & 2 == 2)
			# if Boiler is False, the boiler is on
			
			if BoilerOn:
				updateField("boilerOn",SQL_On)
			else:
				updateField("boilerOn",SQL_Off)
			
				
		#print listOfReadings
		#reduceLife()
		strVal=constructOutputRecord()

		#print strVal

def valueOfReading (reading):
	global readList
	data = -1
	for item in readList:
#		print "The current reading item is "
#		print item
		if reading > item[1] and reading < item[2]:
			data = item[0]
#	print "The reading was " + str(reading)+ ". the value is " + str(data)
	return data


def appendToFile(outputString, outputFileHandle):
	#global fileName
	if outputFileHandle != "":
		#fileName = logRoot + "/live/" + fileName
		#print "Filename to use is " + fileName
		outputFile = open (outputFileHandle,'a')
		outputFile.write(outputString)
		outputFile.write("\n")
		outputFile.close()
	

def processLine(csvLine):	# a single line of CSV data

	global reading, fileName
	lineItem = csvLine.split(",")
	if len(lineItem) >= 15:
		if lineItem[2]== "dsb":

#	Added new code to set fileName to format "ccYYYYMMDD.csv" based on baseDate			
			incrementDate = lineItem[3]
			thisDate = datetime.date.fromordinal(baseDate.toordinal() + int(incrementDate))
			fileName = logRoot + "/master/cc"+ thisDate.strftime("%Y%m%d") +".csv"
			updateField("dataDate",thisDate.strftime("%Y%m%d"))
			updateField("dataTime",lineItem[5])
			if lineItem[6] == "tmpr":
				updateField("roomTemp",lineItem[7])	
			
#			print "date is "+ thisDate.strftime("%Y%m%d")		

		if lineItem[9] == "0":		#This is the main house power usage item
			if len(lineItem) >= 20 and lineItem[14] == "watts":
				updateField("solarReceived",int(lineItem[19]))
				updateField("waterHeating",int(lineItem[17]))
				updateField("houseTotal",int(lineItem[15]))
				updateField("houseImport",int(lineItem[15]) - int(lineItem[19]))
				updateField("houseNett",int(lineItem[15]) - int(lineItem[17]))			

		if lineItem[9] == "8":
			# This is a CH Reading
			dataRead = valueOfReading(int(lineItem[15]))
			if dataRead != -1:
				readSize = len(reading)
				if readSize > 0:
					if dataRead != reading[readSize-1]:
						reading.append(dataRead)
				if readSize == 0:
					reading.append(dataRead)
#			print readSize
			
			#print reading
			if int(lineItem[15]) < 30:
				checkReadings(reading)
				reading = []		


#*********************  End of New Routines *************

def print_lol (the_list,level):
	
	for each_item in the_list:
		if isinstance(each_item,list):
			print_lol(each_item, level+1)
		else:
			for tab_stop in range(level):
#				print("\t", end=" ")
				print("\t")
			print(each_item)


def config():
	global baseDate, logRoot
	conf = open("../config/ccConfig.txt")
	for entry in conf:
		print entry
		if entry.find(",")>= 0:
			entryItem = entry.split(",")
			#print ">"+entryItem[0]+"<"
			if entryItem[0] == "ccBaseDate":
				print "Found baseDate"
				(baseDay,baseMonth,baseYear) = entryItem[1].split("/")
				baseDate = datetime.date(int(baseYear),int(baseMonth),int(baseDay))
			if entryItem[0] == "logRoot":
				print "Found logRoot " + entryItem[1],
				logRoot = entryItem[1]
	return(0)


def openInputChannel():

	global inputMode
	if inputMode == "test":
		inputHandle = open(inputFilename,"r")
	else:
		inputHandle = serial.Serial('/dev/ttyUSB0', 57600, timeout=15)

	return inputHandle
	

# Start of Main()

def convertLine(each_line):
	""" Function doc """
	global fileName
	outputString = ""
	print "Original XML" + each_line
	if each_line.find("<msg>")>= 0:
		lineItem = each_line.split("<")
		fileName = "errorLog"	# setup default value
		logType = "live"
		for eachItem in lineItem:		# Find dsb and thus the file to write to
			eachSubItem = eachItem.split(">")

#	Added new code to set fileName to format "ccYYYYMMDD.csv" based on baseDate			
			if eachSubItem[0] == "dsb":
				incrementDate = eachSubItem[1]
				thisDate = datetime.date.fromordinal(baseDate.toordinal() + int(incrementDate))
				fileName = "cc"+ thisDate.strftime("%G%m%d") +".csv"			


			if eachSubItem[0] == "hist":
				logType = "history"
		fileName = logRoot + "/" + logType + "/" + fileName
		print "Filename to use is " + fileName
		
		for eachItem in lineItem:
			#print "eachItem: " + eachItem
			eachSubItem = eachItem.split(">")
			if len(eachSubItem) == 2:
				if eachSubItem[1] != "" and eachSubItem[0] != "/msg":
					#print eachSubItem[0]+","+eachSubItem[1]+"," ,
					#outputFile.write(eachSubItem[0]+","+eachSubItem[1]+",")
					outputString = outputString + eachSubItem[0]+","+eachSubItem[1]+","

	return outputString

# *******************************
#
#	Example of Main routine using new functions
#
#*********************************

def main_CHroutine():
	
	global fileName
	oldList = []
	newList = []
	configCH()
	#strVal=constructOutputRecord("fieldNames")	# Construct field name list
	#appendToFile(strVal)	
	
	
# Open up the input channel
	inputChannel = openInputChannel()

# SET up the main loop to receive data

	if inputMode == "test":
		while inputChannel :
			each_line = inputChannel.readline()
			processLine(each_line)
			dataString = constructOutputRecord()
			
			appendToFile(dataString,fileName)
		inputChannel.close()				
	else:
				
		while inputChannel.isOpen() :
			#print "Waiting for a line"
			each_line = inputChannel.readline()
			csvLine = convertLine(each_line)
			if csvLine != "":
				#print each_line
				#print csvLine
				appendToFile(csvLine, fileName)
				processLine(csvLine)
				dataString = constructOutputRecord()
				newList = verticalSlice(fieldList[2:],1)
				if cmp(newList,oldList) != 0:
					writeToSQL()
					appendToFile(dataString, fileName)
				oldList = newList
		inputchannel.close()

	return 0
	
if __name__ == '__main__':
	main_CHroutine()
