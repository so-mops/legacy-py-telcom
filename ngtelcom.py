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
#import wiringpi2
import time
import os
import subprocess
import socket
import sys
import time
import ephem
from telescope import telescope;tel = telescope("10.30.5.69")

#Get config data and initialize a few things



	

class ngClient( Client ):

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
			ALL = {}
			ALL.update(tel.reqALL())
			XALL.update(tel.reqXALL())
			
			resp="{motion} {ra} {dec} {ha} {lst} {alt} {az} {secz} {epoch} {jd} 1 {dome} {ut} 180.0\r\n".format(**ALL)
			
			self.client.send(resp)

		else:
			print "request was ", reqStr
			
			
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
			
		
		if word[0] == 'RADECGUIDE':
			dra, ddec = float(word[1]), float(word[2])
			tel.comSTEPRA(dra)
			tel.comSTEPDEC(ddec)
			
		return self.client.send( "{0} {1} {2} {3}\r\n".format(cfgDict['OBSID'], cfgDict['SYSID'], refNum, returnVal) )
			
		
	


		

		

	

	

if __name__ == "__main__":
	
	
	
	print "starting server"
	
	s = Server( 5750, handler=ngClient )
	s.run()
	
