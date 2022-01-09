#!/usr/bin/env python

#########################
#
# run-fan turns a fan on and off when temperature exceeds temperature
# thresholds.
#
#########################

#########################
#
# run-fan starts automatically using systemd
#
# Create a systemd service file using:
#   $ sudo nano /lib/systemd/system/run-fan.service
#
# with the contents as shown below
# remove # and leading spaces:
#   [Unit]
#   Description=run fan when hot
#   After=meadiacenter.service
#
#   [Service]
#   # If User and Group are not specified as root, then it won't work
#   User=root
#   Group=root
#   Type=simple
#   ExecStart=/usr/bin/python /home/osmc/run-fan.py
#   Restart=Always
#
#   [Install]
#   WantedBy=multi-user.target
#
# end of the run-fan.service
# ctrl-o, ENTER, ctrl-x to save and exit the nano editor
#
# After any changes to /lib/systemd/system/run-fan.service:
#    sudo systemctl daemon-reload
#    sudo systemctl enable run-fan.service
#    sudo reboot
#
# Ensure the run-fan.service in systemd is enabled and running:
#    systemctl list-unit-files | grep enabled
#    systemctl | grep running | grep fan
#    systemctl status run-fan.service -l
#
# If there are any issues with starting the script using systemd, 
# then examine the journal using:
#    sudo journalctl -u run-fan.service
#
#########################

#########################
#
# The original script is from:
#    Author: Edoardo Paolo Scalafiotti <edoardo849@gmail.com>
#    Source: https://hackernoon.com/how-to-control-a-fan-to-cool-the-cpu-of-your-raspberrypi-3313b6e7f92c
#
#########################

#########################
import os
import time
import signal
import sys
import datetime

#########################
sleepTime = 30	# Time to sleep between checking the temperature
                # want to write unbuffered to file
fileLog = open('/home/pi/.octoprint/logs/run-fan.log', 'w+',buffering=1)

#########################
# Log messages should be time stamped
def timeStamp():
    t = time.time()
    s = datetime.datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S - ')
    return s

# Write messages in a standard format
def printMsg(s):
    fileLog.write(timeStamp() + s + "\n")


# Fan class
class Fan(object):
    fanOff = True

    def __init__(self):
        self.fanOff = True

    # Turn the fan on or off
    def setFan(self, temp, on):
        if on:
            printMsg("Turning fan on " + str(temp))
            res = os.popen('uhubctl -l 1-1 -p 2 -a on ').readline()
            printMsg("Result:" + res)

        else:
            printMsg("Turning fan off " + str(temp))
            res = os.popen('uhubctl -l 1-1 -p 2 -a off').readline()
            printMsg("Result:" + res)

        self.fanOff = not on

# Temperature class
class Temperature(object):
    cpuTemperature = 0.0
    startTemperature = 0.0
    stopTemperature = 0.0
    firstrun=True

    def __init__(self):
        # Start temperature in Celsius
        #   Maximum operating temperature of Raspberry Pi 3 is 85C
        #   CPU performance is throttled at 82C
        #   running a CPU at lower temperatures will prolong its life
        self.startTemperature = 60.0

        # Wait until the temperature is M degrees under the Max before shutting off
        self.stopTemperature = self.startTemperature - 5.0

        printMsg("Start fan at: " + str(self.startTemperature))
        printMsg("Stop fan at: " + str(self.stopTemperature))

    def getTemperature(self):
        # need to specify path for vcgencmd
        res = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
        self.cpuTemperature = float((res.replace("temp=","").replace("'C\n","")))

    # Using the CPU's temperature, turn the fan on or off
    def checkTemperature(self, myFan):
        self.getTemperature()
        if self.cpuTemperature > self.startTemperature:
            # need to turn fan on, but only if the fan is off
            if self.firstrun:
                self.firstrun=False
                myFan.setFan(self.cpuTemperature, True)
            if myFan.fanOff:
                myFan.setFan(self.cpuTemperature, True)
        elif self.cpuTemperature <= self.stopTemperature:
            # need to turn fan off, but only if the fan is on
            if self.firstrun:
                self.firstrun=False
                myFan.setFan(self.cpuTemperature, False)
            if not myFan.fanOff:
                myFan.setFan(self.cpuTemperature, False)

#########################
printMsg("Starting: run-fan")
try:
    myFan = Fan()
    myTemp = Temperature()
    while True:
        myTemp.checkTemperature(myFan)

        # Read the temperature every N sec (sleepTime)
        # Turning a device on & off can wear it out
        time.sleep(sleepTime)

except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
    printMsg("keyboard exception occurred")
    fileLog.close()

except Exception as e:
    printMsg("ERROR: an unhandled exception occurred")
    printMsg(repr(e) )
    fileLog.close()

