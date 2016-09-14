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
while 1:#wait for the telescope to come on line
	try:

		from telescope import telescope;tel = telescope("10.30.5.69", "BIG61")
		time.sleep(1.0)
		break
	except Exception:
		time.sleep(30)
	
from astro.angles import RA_angle, Dec_angle
import math
import re
from scottSock import scottSock
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
		print "instantiating Client {0} {1}".format( client, address )
		self.laddress = address
		self.running = 1

	def run(self):
		self.running = 1
		msg_tot = ""
		while self.running:
			try:
				data = self.client.recv(self.size)
				print data
				
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
				if inWords[0] == "BIG61" and inWords[1] == "TCS":
					
					try:
						refNum = int( inWords[2] )
					except(ValueError):
						self.client.send("Missing Reference Number")
						self.client.close()
						self.running = 0
						break	
						
				else:
					
					self.client.send("BAD")
					self.client.close()
					self.running = 0
					break
				
				#Check for exceptions caused by bad input or bad parse
				try:
					req_or_com = inWords[3]
				except Exception as prob:
					self.client.send( 'error=%s value=%s \n'%( prob, data ) )
					self.client.close()
					self.running = 0
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
				self.running = 0
				
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
			
		
		if "ALL" in reqstr:
			ALL = {}
			ALL.update(tel.reqALL())
			ALL.update(tel.reqXALL())
			ALL.update({'ut':tel.reqTIME()})

			ALL["motion"] = int(ALL["motion"])
			ALL["ra"] = ALL["ra"].replace(":","")
			ALL["dec"] = ALL["dec"].replace(":","")
			ALL["dome"] = tel.reqDOME()["az"]
			for key in [ "alt", "az", "secz", "jd", "dome" ]:
				ALL[key] = float(ALL[key])
			for key, val in ALL.iteritems():
				try:
					ALL[key] = val.strip()
				except (ValueError, AttributeError):
					pass
			      #BIG61 TCS 1 0  212629.68 +321422.8  +00:00:00 21:26:31  90.0  180.0 1.00                2000.0  2457275.731741 1 1    
			resp="BIG61 TCS {refNum} {motion}  {ra} {dec}  {ha} {lst}  {alt:04.1f}  {az:05.1f} {secz:05.2f}                {epoch}  {jd:09.1f} 180.5 {dome:05.1f}                  180.0 \r\n".format(refNum=refNum, **ALL)
			#print ALL
			#print resp
			#self.client.send(resp)

		elif "MOTION" in reqstr:
			mot = int( tel.request('motion') )
			
			if mot == 4:
				resp = "BIG61 TCS {0} 0\r\n".format(refNum )
			else:
				resp = "BIG61 TCS {0} {1}\r\n".format(refNum, mot )

		else:
			print "shit! request was ", reqstr
			resp = ""
		
		self.client.send(resp)
			
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
		
		for ii in range(len(comlist)):
			while comlist[ii].endswith('\r') or comlist[ii].endswith('\n'):
				comlist[ii] = comlist[ii][:-1]
				
		print comlist
		
		if comlist[0] == 'RADECGUIDE':
			dra, ddec = float(comlist[1]), float(comlist[2])
			print dra, ddec
			tel.comSTEPRA(dra/math.cos(tel.reqDEC()))
			tel.comSTEPDEC(ddec)
			soc_guide(dra, ddec)
			#log_guide( dra, ddec )
			
		
		elif comlist[0] == 'NEXTRA':
			if len( comlist ) == 3:
				rapm = float( comlist[2] )
			else:
				rapm = 0.0
			tel.comNEXTPOS( str2ra(comlist[1]), Dec_Angle(tel.reqXDEC()['next']), tel.request("DISEPOCH").strip(), 0.0, 0.0 )
		
			
		elif comlist[0] == 'NEXTDEC':
			if len( comlist ) == 3:
				rapm = float( comlist[2] )
			else:
				rapm = 0.0
			tel.comNEXTPOS( RA_Angle(tel.reqXRA()['next']), str2dec(comlist[1]), tel.request("DISEPOCH").strip(), 0.0, 0.0 )
			
		elif comlist[0] == 'MOVNEXT':
			tel.comMOVNEXT()
		elif comlist[0] == "SHUTDOWN":
			self.running = 0
			self.client.close()
		
		else:
			print "SHIT"
		return self.client.send( "{0} {1} {2} {3}\r\n".format("BIG61", "TCS", refNum, "OK") )
			
		
	


def str2ra(angle_str):
	return RA_angle("{0}:{1}:{2}".format(angle_str[0:2], angle_str[2:4], angle_str[4:] ) )

def str2dec( angle_str ):
	return RA_angle("{0}:{1}:{2}".format(angle_str[0:3], angle_str[3:5], angle_str[5:] ) )
	
def log_guide( dra, ddec  ):
	f=open("guide.dat", 'a')
	f.write( "{0} {1} {1}\n".format(time.time(), dra, ddec) )
	f.close()
	

def soc_guide(dra, ddec):
	try:
		s=scottSock( '10.30.1.1', 5749 )
		s.talk( "{0} {1}\n".format(dra, ddec) )
		print dra, ddec
		s.close()
	except Exception as err:
		pass

	return
	

if __name__ == "__main__":
	
	
	
	print "starting server"
	try:
		s = Server( 5750, handler=ngClient )
		s.run()
	except(Exception):
		print "Closing server"
		s.server.close()
	
