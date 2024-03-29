#front 2
#right 1
import os
import math
import time
import numpy as np
import csv
import matplotlib.pyplot as plt
import serial

# Leap of faith
d0 = 50

flag = 0
ack = 101

POWER_OFFSET = 80 

#RSSI Values
P0 = 0
P1 = 0
P2 = 0

delta_x = 0
delta_y = 0
theta = 0
dist = 0
lamda = 1
dmax = 120


ser = serial.Serial("/dev/ttyACM0", 38400)

fwd = "0 50\n"
rev = "0 -50\n"
turn90p = "90 0\n"
turn90n = "-90 0\n"
motionCmd = ""
 
def sendMotionCmd(data):
	global flag, ack
	while(ser.inWaiting() == 0):
		if(flag == 0): 
			time.sleep(0.5)
			ser.write(data)
			flag = 1

	data_read = ser.readline()
	   
	if(int(data_read) == ack):
		#print data_read
		flag = 0

def getRSSI():
	sum = 0	
	for i in range(0, 20):
		cmd = "iwconfig wlan0 | grep -i --color quality | grep -i --color signal"

		data = os.popen(cmd).read()

		
		link_quality = ''
		signal_strength = ''	
		link_quality = data[23:25]
		signal_strength = data[43:46]

		rssi_dBm = int(signal_strength)
		quality = int(link_quality)
		rssi_dB = rssi_dBm - 30

		freq = 2437
			
		#distance = math.pow(10.0, (27.55 - (20*math.log10(freq)) + math.fabs(rssi_dBm))/20.0)

		#data_to_write =  "wlan0: RSSI = " + str(rssi_dBm) + " dBm"

		#print data_to_write

		sum = sum + rssi_dBm

	rssi_dBm = sum/20
			
	return rssi_dBm

def analyse():
	global delta_x, delta_y, theta, dist, lamda, motionCmd, dmax
	delta_y = P1 - P0
	delta_x = P2 - P0

	if(delta_x != 0 and delta_y != 0):
		lamda = -15*(math.pow(10, (-3)*(P0+POWER_OFFSET)/(2.5*10)) - 5*math.pow(10, (-2)*(P0+POWER_OFFSET)/(2.5*10)))
		#lamda = dmax/(math.pow(delta_x,2), math.pow(delta_y,2))
	else:
		lamda = 1

	theta = math.ceil(math.degrees((math.atan2(delta_y, delta_x))))
	dist = math.ceil(lamda * math.sqrt(math.pow(delta_x,2), math.pow(delta_y,2)))

	print "Delta_y :" + str(delta_y) + "Delta_x :" + str(delta_x) + "lamda :" + str(lamda) + "Theta :" + str(theta) + "Dist :" + str(dist)

	motionCmd = str(theta) + " " + str(dist) + "\n"
	#print motionCmd

	sendMotionCmd(motionCmd)

def perpProbe():
	global P0, P1, P2
	P0 = getRSSI()
	if(P0 < -25):
		sendMotionCmd(fwd)
		P1 = getRSSI()
		sendMotionCmd(rev)
		sendMotionCmd(turn90p)
		sendMotionCmd(fwd)
		P2 = getRSSI()
		sendMotionCmd(rev) + "dBm  "
		print "P0 :" + str(P0) + " dBm  " + "P1 :" + str(P1) + " dBm  " + "P0 :" + str(P2)  + " dBm"
		analyse()
 

def NSEWProbe():
	P = getRSSI()
	sendMotionCmd("0 100\n")
	PN = getRSSI()
	sendMotionCmd("0 -100\n")
	P = P + getRSSI()
	sendMotionCmd("0 -100\n")
	PS = getRSSI()
	sendMotionCmd("0 100\n")
	P = P + getRSSI()
	sendMotionCmd("90 0\n")
	sendMotionCmd("0 100\n")
	PE = getRSSI()
	sendMotionCmd("0 -100\n")
	P = P + getRSSI()
	sendMotionCmd("0 -100\n")
	PW = getRSSI()
	sendMotionCmd("0 100\n")
	P = P + getRSSI()
	sendMotionCmd("-90 0\n")
	P0 = int(P/5)

	deltaN = PN - P0
	deltaS = PS - P0
	deltaE = PE - P0
	deltaW = PW - P0

	deltaMax = max(deltaN, deltaS, deltaE, deltaW)

	print "NSEWProbe :" + "P0: " + str(P0) + "  " + "PN: " + str(PN) + "  " + "PS: " + str(PS) + "  " + "PE: " + str(PE) + "  " + "PW: " + str(PW) + "  " + "deltaMax :" + str(deltaMax)
	

	if(deltaMax == deltaN):
		pass
	elif(deltaMax == deltaE):
		sendMotionCmd("90 0\n")
	elif(deltaMax == deltaS):
		sendMotionCmd("180 0\n")
	elif(deltaMax == deltaW):
		sendMotionCmd("-90 0\n")

    return P0, deltaMax

def optDist(P, delta):
    moveDist = 200
	while(moveDist > 15):
		lamda = -15*(math.pow(10, (-3)*(P+POWER_OFFSET)/(2.5*10)) - 5*math.pow(10, (-2)*(P+POWER_OFFSET)/(2.5*10)))

		moveDist = lamda * delta	

		dataWrite = "0 " + str(moveDist) + "\n"

		print "optDist :" + "lamda :" + str(lamda) + "  " + "moveDist :" + str(moveDist)

		sendMotionCmd(dataWrite)

		Pnew = getRSSI()
		delta = Pnew - P
		P = Pnew

	if(P > -30):
		return 1
	else:
		return 0

def FBProbe():
	P = getRSSI()
	sendMotionCmd("0 100\n")
	PF = getRSSI()
	sendMotionCmd("0 -100\n")
	P = P + getRSSI()
	sendMotionCmd("0 -100\n")
	PB = getRSSI()
	sendMotionCmd("0 100\n")
	P = P + getRSSI()
	P0 = P/3

	deltaF = PF - P0
	deltaB = PB - P0
   
	deltaMax = max(deltaF, deltaB)

	print "FBProbe :" + "P0: " + str(P0) + "  " + "PF: " + str(PF) + "  " + "PB: " + str(PB) + "  " + "deltaMax :" + str(deltaMax)

	if(deltaMax == deltaF):
		pass
	elif(deltaMax == deltaB):
		sendMotionCmd("180 0\n")

	return P0, deltaMax



P, delta = NSEWProbe()
Out1 = optDist(P, delta)

if (Out1 == 1):
	pass
else:
	sendMotionCmd("90 0\n")
	P, delta = FBProbe()
	Out2 = optDist(P, delta)
	if(Out2 == 1):
		pass
	else: 
		print "Couldnot optimize!! Go fuck urself"
	
		

