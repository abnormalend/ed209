# ed209
Python signal bot that uses dbus


# bothelpers

Bot helpers are a specific type of module that can easily be integrated into the main bot.  There are some key requirements to making a bot helper.
- Based on bothelper class, this will have standard functions that can be reused (currently just universal reply)
- bothelpers are enabled by a boolean in the settings file
- adding a new bothelper is done by a conditional block at the end of signalbot __init__ that checks if the boolean is enabled for the new bothelper, and imports the module and creates the object.
- See s3bothelper as a working example.