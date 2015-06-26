#!/usr/bin/python

#Scott Swindell
#6/25/2013

import time
import socket
import sys
import time
import ephem
from lxml import html
import requests

class satellite:
	"""Class to get position and velocities of 
	a satellite based on catelog number. The TLE
	is grabbed from the celestrak web site. All 
	astrometry calculations are done using pyephem."""
	
	def __init__(self, catnum, obs):
		self.sat = self.getSat( catnum )#ephem tle object
		self.obs = obs
		
	def getSat( self, catnum ):
		#Grab the tle of a satellite from celestrak.com based on catelog number
		page = requests.get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={0}".format(catnum))
		tree = html.fromstring(page.text)
		tle = tree.xpath('//pre')[0].text.split('\n')
		line0 = tle[1]
		line1 = tle[2]
		line2 = tle[3]
		#print tle
		return ephem.readtle( line0, line1, line2 )
		
	def precess_now_2000(self, ranow, decnow):
		#Precess back to epoch 2000
		#Author: Ben Weiner
		coo = ephem.Equatorial(ranow, decnow, epoch=ephem.now())
		coo2 = ephem.Equatorial(coo, epoch='2000')
		return coo2.ra, coo2.dec
	
	
	def position(self, ephemTime ):
		
		self.obs.date = ephemTime
		self.sat.compute(self.obs)
		
		ra2000, dec2000 = self.precess_now_2000( self.sat.ra, self.sat.dec)
		
		return ra2000, dec2000, self.sat.alt, self.sat.az
		
	def velocity(self, ephemTime):
		"""Velocities are interpolated from two positions a second 
		apart. This is not the best way to obtain ra and dec bias rate
		of a satellite. There is velocity information within the TLE
		but pyephem seems not to utilize that. 
		"""
		
		ra_0, dec_0, alt_0, az_0 = self.position( self.sat, ephemTime ) #position now
		ra_1, dec_1, alt_1, az_1, = self.position( self.sat, ephemTime + ephem.second )#position 1 second into the future
		
		#grab position change and convert to arc seconds
		#Becsue our time difference is one second
		#out these values are actually bias rates in 
		#arc seconds per second. 
		biasRA = (ra_1 - ra_0)*3600
		biasDec = (dec_1 - dec_0)*3600
		return biasRA, biasDec

class bigelow_sat( satellite ):
	def __init__(self, catnum):
		obs = ephem.Observer()
		obs.lon = '-110:44:04.3'
		obs.lat = '32:24:59.3'
		obs.elevation = 2510
		
		satellite.__init__( self, catnum, obs )
		
	

if __name__ == "__main__":

	#this will snippet will grab calculate
	#the position of the ISS and send the 
	#61 inch telescope to that position. 
	#It will not track if you want to track
	#you can create a loop.

	#satellite class to track ISS
	theSat = bigelow_sat(25544)
	
	
	#telcom socket stuff
	HOST = "10.30.3.42"
	PORT= 5750
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout( 0.5 )
	s.connect((HOST, PORT))
	
	
	#if you want to track the satellite
	#make a while loop here. 
	
	#grab UT from TCS
	s.send("BIG61 TCS 123 REQUEST UT \r\n")
	ut = s.recv( 128 ).replace("BIG61 TCS 123 ", '')
	
	
	#ephem style date with UT from TCS
	date = "{0}/{1}/{2} {ut}".format(*time.gmtime(), ut=ut)
	
	#compute equatorial coordinates of satellite
	ra,dec,alt,az = theSat.position(ephemTime = date)
	
	print ra, dec
	
	alter coordinates to make it acceptable for TCS (no colons)
	ra,dec = str(ra).replace(':','') ,str(dec).replace(':', '')
	
	
	
	#send coordinates to tcs
	s.send( "BIG61 TCS 123 NEXTRA\r\n".format( ra )
	print s.recv(128)
	s.send( "BIG61 TCS 123 NEXTRA\r\n".format( dec )
	print s.recv(128)
	

	#make the move. This is commented out 
	#Because I don't want anyone accidentally 
	#moving the scope. 
	#s.send("BIG61 TCS 123 MOVNEXT\r\n")
	
	
	
	
	
