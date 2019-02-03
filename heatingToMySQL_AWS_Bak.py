#!/usr/bin/python
# -*- coding: utf-8 -*-


#import os
#import glob
import time
import MySQLdb as mdb
import sys
Server="ec2-35-176-42-248.eu-west-2.compute.amazonaws.com"

def sendPowerMeasurement(recordDate, houseTotal, waterHeating, solarPower):

	try:
		con = mdb.connect(Server, 'pi_insert', 'XXXXXXXXXX', 'XXXXXXX')
		cur = con.cursor()
		if recordDate == 0:
			cur.execute("""INSERT INTO powerReadings(houseTotal, waterHeating, solarPower) 
			VALUES(%s , %s , %s )""", (houseTotal, waterHeating, solarPower))
		else:
			cur.execute("""INSERT INTO  powerReadings(dtg, houseTotal, waterHeating, solarPower)
			VALUES(%s , %s , %s, %s )""", (dtg, houseTotal, waterHeating, solarPower))
		con.commit()		
	except mdb.Error, e:
		#con.rollback()
		print "Error %d: %s" % (e.args[0],e.args[1])
		sys.exit(1)

def sendTemperatureMeasurement(recordDate, temperature, sensor_id):

	try:
		#con = mdb.connect('35.176.42.248', 'pi_insert', 'xxxxxxxxxx', 'xxxxxxxxx')
		con = mdb.connect(Server, 'pi_insert', 'xxxxxxxxx', 'xxxxxxxxx')
		cur = con.cursor()
		if recordDate == 0:
			cur.execute("""INSERT INTO temperature(sensor_id, temperature) 
			VALUES(%s , %s )""", (sensor_id, temperature))
		else:
			cur.execute("""INSERT INTO  temperature(dtg, sensor_id, temperature)
			VALUES(%s, %s , %s )""", (recordDate, sensor_id, temperature ))
		con.commit()		
	except mdb.Error, e:
		#con.rollback()
		print "Error %d: %s" % (e.args[0],e.args[1])
		sys.exit(1)

def sendHeatingData (recordDate, roomTemp, topTankTemp, bottomTankTemp, \
						askForHeating, askForHotWater, roomStatOn, tankStatOn, boilerOn, \
						solarPower, houseTotal, waterHeating ):
# """ Function doc. Send all data into main centralHeating table """	
#	try:
#		con = mdb.connect('192.168.1.13', 'pi_insert', 'xxxxxxxx', 'xxxxxxxxx')
#		cur = con.cursor()
#		if recordDate == 0:
#			cur.execute("""INSERT INTO centralHeating(tempRoom, tempTopTank, tempBottomTank, askForHeating, \
#			askForHotWater, roomStatOn, tankStatOn, boilerOn, solarPower, houseTotal, waterHeating ) \
#			VALUES(%s , %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )""", \
#			(roomTemp, topTankTemp, bottomTankTemp, askForHeating, askForHotWater, roomStatOn, tankStatOn, boilerOn, solarPower, houseTotal, waterHeating ))
#		else:
#			cur.execute("""INSERT INTO centralHeating(dtg, tempRoom, tempTopTank, tempBottomTank, askForHeating, \
#			askForHotWater, roomStatOn, tankStatOn, boilerOn, solarPower, houseTotal, waterHeating ) \
#			VALUES(%s, %s , %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )""", \
#			(recordDate, roomTemp, topTankTemp, bottomTankTemp, askForHeating, askForHotWater, roomStatOn, tankStatOn, boilerOn, solarPower, houseTotal, waterHeating))
#		con.commit()		
#	except mdb.Error, e:
#		#con.rollback()
#		print "Error %d: %s" % (e.args[0],e.args[1])
#		sys.exit(1)
	sendTemperatureMeasurement(recordDate, roomTemp, "Study")
	sendTemperatureMeasurement(recordDate, topTankTemp, "HW_Tank_Top")
	sendTemperatureMeasurement(recordDate, bottomTankTemp, "HW_Tank_Bottom") 
	sendPowerMeasurement(0, houseTotal, waterHeating, solarPower)
 
##### Converting Date and Time
#
#	The format coming out of the data file:
#	0			1		2	3  4  5     6   7    8      9   10  11  12  13 14  15  16 17 18 19  21  23
#	20150720,06:50:00,27.1,52,24,True,True,True,False,True,502,274,228,481,21,False,0,52,24,1,1,0,0,1,
#	The format in the database when created as a CURRENT
#	2015-07-28 12:18:42

def readHouseData(fileName):
#	global baseDate, logRoot, readList, fieldList, reading
	
	houseData = open(fileName)
	for houseRecord in houseData:
		#print houseRecord
		if houseRecord.find(",")>= 0:
			houseData = houseRecord.split(",")
			#print houseData[0]
			recordDate= houseData[0][0:4]+"-"+houseData[0][4:6]+"-"+houseData[0][6:8] + " " + houseData[1]
			print recordDate
			roomTemp = houseData[2]
			topTankTemp = houseData[17]
			bottomTankTemp = houseData[18]
			askForHeating = houseData[19]
			askForHotWater = houseData[20]
			roomStatOn = houseData[21]
			tankStatOn = houseData[22]
			boilerOn = houseData[23]
			solarPower = houseData[11]
			houseTotal = houseData[10]
			waterHeating = houseData[13]
			sendHeatingData(recordDate, roomTemp, topTankTemp, bottomTankTemp, askForHeating, askForHotWater, roomStatOn, tankStatOn, boilerOn, solarPower, houseTotal, waterHeating)
			  
	return(0)
# roomTemp, topTankTemp, bottomTankTemp, askForHeating, askForHotWater, roomStatOn, tankStatOn, boilerOn)
#print 'Number of arguments:', len(sys.argv), 'arguments.'
#print 'Argument List:', str(sys.argv)


#if len(sys.argv) > 1:
	
#	readHouseData(sys.argv[1])
#else:
#	readHouseData("./testHouseData.csv")

#sendHeatingData("2000-08-06 21:18:42", 18, 65, 21, 1,1,0,1,1,2,3,4)

print "Testing Temperature Measurement"
sendTemperatureMeasurement(0,20,"Test")

print "Testing Power measurement"
sendPowerMeasurement(0, 20, 5, 5)
