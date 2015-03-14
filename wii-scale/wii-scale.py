# Author: Andreas Älveborn
# URL: https://github.com/aelveborn/Wii-Scale
#
# This file is part of Wii-Scale
#
# ----------------------------------------------------------------------------
#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Andreas Älveborn
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/python

import wiiboard
import pygame
import time
import sys

from bluetooth import *
from socketIO_client import SocketIO, LoggingNamespace


# Global
sleep = True
sensitivity = 30 #kg

port = 8080
server = "localhost"


class CalculateWeight:
	def formatWeight(self, weight):
		return round(weight, 1)

	def weight(self, data):
		i = 0
		total = 0
		for i in range(len(data)):
			total += data[i]
		total = total / len(data)
		return self.formatWeight(total)


class WebSocketIO:
	def __init__(self):
		self.socketIO = SocketIO(server, port, LoggingNamespace)
		self.socketIO.on('sleep', self.receive_sleep)

	def wait(self):
		self.socketIO.wait(seconds = 1)

	def send_status(self, status):
		self.socketIO.emit('status', {'status': status})

	def send_weight(self, totalWeight):
		self.socketIO.emit('weight', {'totalWeight': totalWeight})

	# Accepts True or False as argument
	def receive_sleep(self, *args):
		global sleep
		if isinstance(args[0], bool):
			sleep = args[0]


def main():
	global sleep
	print "Wii-Scale started"

	calculate = CalculateWeight()
	socket = WebSocketIO()
	pygame.init()

	# Scale	
	running = True
	while(running):

		if sleep:
			socket.wait()
			continue

		# Re initialize each run due to bug in wiiboard
		board = wiiboard.Wiiboard()
		socket.send_status("SYNC")

		# Connect to balance board
		address = board.discover()
		board.connect(address)

		if address != None:			

			#Flash lights
			time.sleep(0.1)
			board.setLight(True)

			#Measure weight
			socket.send_status("READY")

			i = 0
			done = False
			total = []
			firstStep = True
			skipReadings = 80

			while(not done):
				time.sleep(0.05)

				for event in pygame.event.get():
					if event.type == wiiboard.WIIBOARD_MASS:
						if event.mass.totalWeight > sensitivity:

							if firstStep:
								firstStep = False
								socket.send_status("MEASURING")

							# Skips the first readings when the user steps on the balance board
							skipReadings -= 1
							if(skipReadings < 0):
								total.append(event.mass.totalWeight)
								socket.send_weight(calculate.weight(total))

						if event.mass.totalWeight <= sensitivity and not firstStep:
							done = True
						
						if event.type == wiiboard.WIIBOARD_BUTTON_RELEASE:
							done = True

		# Done
		sleep = True
		socket.send_status("SLEEP")

		# Disconnect
		board.disconnect()

	# Clean up
	pygame.quit()


if __name__ == "__main__":
	main()