
# Instructions for using python telcom server #

## Dependencies ##

To run ngtelcom.py or telcom.py you will need:
 - python 2.7, It would be fairly easy to make it compatible
    with python 3+. 
 - git -- sudo apt-get install git
 - python-pip sudo apt-get install python-pip

with pip install psutil and pytz
```bash
sudo pip install psutil
sudo pip install pytz
```
also you will need some scott python libraries you can get by typing
```bash


git clone user@mogit.as.arizona.edu:/mnt/git/telescope/py-utils/py-server
git clone user@mogit.as.arizona.edu:/mnt/git/telescope/py-utils/telescope
git clone user@mogit.as.arizona.edu:/mnt/git/telescope/py-utils/py-astro/astro
```

To install the cloned libraries above, simply enter each repo directory and type 

```bash
sudo python setup.py
```

## Installing ngtelcom ##


### Installing as an upstart service ###
Edit the upstart service file ngtelcom 
to make sure Path files are consistent.

I have been using /home/scott/git-clones/legacy-py-telcom 
but obviously this won't work if you don't have access to /home/scott. 


copy the upstart service file to /etc/init.d

and type 
```bash
sudo update-rc.d ngtelcom defaults
```

ngtelcom should start at boot time

to run it imediately

```bash
sudo service ngtelcom start
```
 

## installing telcom (for legacy tcs) ##
Follow the instructions above but replace
ngtelcom with telcom. 

The telcom version also requires a config file
which is a JSON encoded values. It should be fairly
obvious to the user how to change the necessary values 
to suit your needs. 
