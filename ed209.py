#!/usr/bin/python3

from pydbus import SystemBus
from gi.repository import GLib
import logging
import signalbot

# Setup stuff
bus = SystemBus()           # This is our feed of events from signal
loop = GLib.MainLoop()      # This lets us trigger on the events from signal (and schedule)
signal = bus.get('org.asamk.Signal', '/org/asamk/Signal/_16165281428')  # All our bots brains
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO) # Set up our main logging

mybot = signalbot.signalbot(signal, '/home/ubuntu/ed209/config.ini') # Create our bot, load our settings file

GLib.timeout_add_seconds(30, mybot.cronHandler)             # Run the cron handler every 60 seconds
signal.onMessageReceived = mybot.messageHandler       # Run the message handler every time we get a signal message

if __name__ == '__main__':
    loop.run()