# From the TLE and observatory location, find ra, dec, and az, alt

# Currently, the coords being returned seem correct in az, alt
# import numpy as np
import ephem
import sys
from lxml import html
import requests
import os
import time
from telescope import telescope
import socket

POSFLAG = False
VELFLAG = False
WAITFLAG = True
from angles import RA_angle, Dec_angle, Deg10


LOCS = {
	"tucson"	:ephem.Observer(),
	'bigelow':ephem.Observer(),
	"bok"		:ephem.Observer(),
}

LOCS["tucson"].lat = "32:13:18"
LOCS["tucson"].lon = "-110:55:32"
LOCS["tucson"].elevation = 806

LOCS["bigelow"].lon = '-110:44:04.3'
LOCS["bigelow"].lat = '32:24:59.3'
LOCS["bigelow"].elevation = 2510



def getSat(catnum):
	#Grab the tle of a satellite from celestrak.com based on catel
	page = requests.get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={0}".format(catnum))
	tree = html.fromstring(page.text)
	tle = tree.xpath('//pre')[0].text.split('\n')
	line0 = tle[1]
	line1 = tle[2]
	line2 = tle[3]
	#print tle
	return ephem.readtle(line0, line1, line2)
	
	
# and off in ra, dec - turns out for satellites the ra, dec is in
# current epoch rather than J2000, see
# http://rhodesmill.org/pyephem/radec.html
# For satellites, I want apparent topocentric position, but pyephem
# always puts this in epoch-of-date, so need to precess it back to
# 2000 for entering into a TCS.

def compute_radec(tle, obs_location):
	radtodeg = 180.0 / ephem.pi
	
	tle.compute(obs_location)


	
	tnow = ephem.now()
	ra, dec = tle.ra, tle.dec
	alt,az = tle.alt, tle.az
	ra2000, dec2000 = precess_now_2000(tle.ra, tle.dec)
	ra2000, dec2000 = precess_now_2000(tle.ra, tle.dec)

        
	return ra2000, dec2000, float(alt)*radtodeg, float(az)*radtodeg
    
def precess_now_2000(ranow, decnow):
	coo = ephem.Equatorial(ranow, decnow, epoch=ephem.now())
	coo2 = ephem.Equatorial(coo, epoch='2000')
	return coo2.ra, coo2.dec

def curPos(sat, obs=LOCS["tucson"] ):
	obs.date = ephem_time_from_tcs()
	sat.compute(obs)
	ra2000, dec2000 = precess_now_2000(sat.ra, sat.dec)
	return ra2000, dec2000, sat.alt, sat.az

def posNowPlus( sat, obs=LOCS["tucson"], secs=ephem.second )
	obs.date = ephem_time_from_tcs() + ephem.second
	sat.compute(obs)
	ra2000, dec2000 = precess_now_2000(sat.ra, sat.dec)
	
	return ra2000, dec2000, sat.alt, sat.az
	
def ephem_time_from_tcs():
	ut = outval['UT'] #get Time from TCS
	date = time.gmtime()
	year, month, day = date[0], date[1], date[2]
	
	
	return ephem.date("{0}/{1}/{2} {3}".format(year, month, day, ut))


def trackSat( sat )
	while TRACKFLAG:
		if POSFLAG:
			ra,dec,alt,az = curPos(sat)
			#print Deg10(float(alt)),  Deg10(float(az))
			#tel.comELAZ(Deg10(float(alt)),  Deg10(float(az)))
			
		elif VELFLAG:
			ra_0, dec_0, alt_0, az_0 = curPos( sat ) #position now
			ra_1, dec_1, alt_1, az_1, = posNowPlus( sat )#position 1 second into the future
			
			#grab position change and convert to arc seconds
			#Becsue our time difference is one second
			#out these values are actually bias rates in 
			#arc seconds per second. 
			biasRA = (ra_1 - ra_0)*3600
			biasDec = (dec_1 - dec_0)*3600
			
			
			
		

	
			

sat = getSat( int(sys.argv[1]) )
tnow = ephem.now()
a=0
tel = telescope("qnxtcs")
while(1):	
	ra,dec,alt,az = curPos(sat, tel=tel)
	print Deg10(float(alt)),  Deg10(float(az))
	tel.comELAZ(Deg10(float(alt)),  Deg10(float(az)))
	

	


