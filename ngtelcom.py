#!/usr/bin/env python

"""
A server for pcTCS to handle socket requests/commands
This is a replacement for the original telcom written by 
Dave Harvey.

Author: Scott Swindell
Date: 12/2013
"""


from server import Server, Client
import json
import sys
import threading
import wiringpi2
import time
import os
import subprocess
import socket
import sys
import time
import ephem
from telescope import telescope;tel = telescope("qnxtcs")

#Get config data and initialize a few things
cfgName = sys.argv[1]
cfgDict = json.load( open(cfgName, 'r') )

if cfgDict['hasActivityLight']:
	from blink import blinker

threadLock = threading.Lock()
serialLock = threading.lock()

if cfgDict['hasIIS']:
	wiringpi2.wiringPiSetup()
	wiringpi2.pinMode( 1,2 )

if cfgDict['hasActivityLight']:
	ACT_LIGHT = blinker(26)
	ACT_LIGHT.setState(1)

global outval
outval = []	

global sat_obj = False
	

class legacyClient( Client ):

	##################################################
	"""	Client class to handle socket requests
		or commands. Each time a socket is opened on
		port 5750 the Server class opens this thread
		to handle it. 
				
		"""
	##################################################
	
	def __init__(self,(client,address)):
		Client.__init__(self, (client,address))
		if cfgDict["debug"]: print "instantiating Client {0} {1}".format( client, address )
		self.laddress = address

	def run(self):
		running = 1
		msg_tot = ""
		while running:
			try:
				data = self.client.recv(self.size)
				
			except Exception as e:
				print "error is", e, 'at', time.ctime()
				print "When trying to read from {0}".format(self.laddress)
				print "With Messages: ", msg_tot
				data = False


			
			if data:
				msg_tot+=data
				#if cfgDict['hasActivityLight']:
					#ACT_LIGHT.blink(0.05)
				
				
				if data.endswith( '\n' ): data = data[:-1]#Remove trailing new line
				inWords = data.split( ' ' )
				
				#Check for Harvey's telcom string strucutre
				if inWords[0] == cfgDict['OBSID'] and inWords[1] == cfgDict['SYSID']:
					
					try:
						refNum = int( inWords[2] )
					except(ValueError):
						self.client.send("Missing Reference Number")
						self.client.close()
						running = 0
						break	
						
				else:
					
					self.client.send("BAD")
					self.client.close()
					running = 0
					break
				
				#Check for exceptions caused by bad input or bad parse
				try:
					req_or_com = inWords[3]
				except Exception as prob:
					self.client.send( 'error=%s value=%s \n'%( prob, data ) )
					self.client.close()
					running = 0
					break
				
				#handle requests
				if req_or_com == "REQUEST":
					self.request( refNum, inWords[4] )
          
				elif req_or_com == "NGREQUEST":
					self.ngRequests[inWords[4]]()	
				
				elif req_or_com == "SAT":
					self.sat_com(refNum, inWords[4:])
				
				#Handle commands
				else:
					com = ''
					self.command( inWords[3:], refNum )
             	
			else:
				
				self.client.close()
				running = 0
				
	#Legacy Request
	def request( self, refNum, reqstr ):
		####################################################################
		"""	
		Name: request
		args" refNum, reqStr
		Description: This method handles all the request made
			to telcom eg: BOK TCS 123 REQUEST RA
			in the above example 123 is refNum and 'REQUEST RA'
			is the request string.
			"""
		####################################################################
	
		#Different programs use different key words. (I think)
		extraKeys={"MOTION":"MOT",  "AIRMASS":"SECZ", "ROT":"IIS", }
		
		
		#get rid of any and all new lines or carriage returns
		while (reqstr.endswith("\r") or reqstr.endswith('\n')):
			reqstr = reqstr[:-1]
			
		
		if "ALL" in reqStr:
			ALL = tel.reqALL()
			self.client.send("".format(  ))

	#legacy Command
	def command(self, comlist, refNum ):
	
	#########################################################
		"""	
			Name: command
			args: comlist, refNum
			 
			Description: This method handles all the commands made
				to telcom eg: BOK TCS 123 MOVELAZ 90.0 180.0
				in the above example 123 is refNum and 'MOVELAZ 90.0 180.0'
				is the request string.
		"""
	#########################################################
		
		#construct command string
		comstr = ''
		for word in comlist: 
			comstr+=word+' '
			
		#Get rid of whitespace caused by above parsing
		comstr = comstr[:-1]
			
		#get rid of any newline or carriage returns
		while ( comstr.endswith( "\r" ) or comstr.endswith( '\n' ) ):
			comstr = comstr[:-1]
			
		#Write the command to the serial port
		try:
			with serialLock:
				ser = serial.Serial( gUSBport, 9600 )
				ser.write( comstr+"\r" )
		except Exception as e:
			if cfgDict['debug']: print e
			return self.client.send( "{0} {1} {2} {3}\r\n".format(cfgDict['OBSID'], cfgDict['SYSID'], refNum, "SERIAL_ERROR") )
			
		#Wait half a second and grab the error code from
		#the telem stream
		time.sleep( 0.5 )
		errorCode = outval["ERROR"].upper().strip()
			
		if errorCode != "E": #Command was not understood
				returnVal = "BAD"
		else:#Command was understood
			returnVal = "OK"
		return self.client.send( "{0} {1} {2} {3}\r\n".format(cfgDict['OBSID'], cfgDict['SYSID'], refNum, returnVal) )
			
		
	
	def sat_com(self, com):
		global sat_obj
		
		for index in range( len( com ) ):
			while com[index].endswith("\r")  or com[index].endswith("\n"):
				com[index] = com[index][:-1]
		
		if com[0] == "SATNUM":
			try:
				sat_obj = bigelow_sat(com[1])
				return self.client.send("Acquired TLE\r\n")
			except(Exception):
				return self.client.send("TLE ERROR\r\n")
				
		elif com[0] == "GETPOS":
		
			
			with threadLock:
				ut = outval["UT"]
			if sat_obj != False:
				date = "{0}/{1}/{2} {ut}".format(*time.gmtime(), ut=ut)
				ra,dec,alt,az = sat_obj.position( date )
			
				return self.client.send( "{0} {1} {2} {3}\r\n".format( str(ra), str(dec), str(alt), str(az) ) )
				
			else:
				return self.client.send( "No Satellite recorded, Send SATNUM\r\n" )
				
			
		elif com[0] == "GETBIAS"
			with threadLock:
				if sat_obj != False:
					date = "{0}/{1}/{2} {ut}".format(*time.gmtime(), ut=ut)
					biasRA,biasDec = sat_obj.position( date )
					return self.client.send( "{0} {1} \r\n".format( biasRA, biasDec ) )
				
				else:
					return self.client.send( "No Satellite recorded, Send SATNUM\r\n" )
		
	
	def ngAll(self):
		outstr = ''
		
		for val in outval.itervalues():
			outstr+=val+' '
		return self.client.send( "{0}\n".format(outstr) )

		

		

	

	

if __name__ == "__main__":
	#try:
	ser = get_serial( 9600 )
	ser.start()
	
	
	
	if cfgDict['debug']: print "starting server"
	s = Server( 5750, handler=legacyClient )
	s.run()
	#except Exception as E:
		#s=open("/home/pi/telcom.err", 'a')
		#s.write("++++++++++++++++++++++++++++++++++++++++++++\n")
		#s.write(time.asctime() + "\n")
		#s.write( str( E ) )
		#s.close()
		#ACT_LIGHT.setState( 0 )
		#print E
		#raise Exception(E)
