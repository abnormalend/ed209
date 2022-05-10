#!/usr/bin/python3

# from sqlite3 import Timestamp
# from re import T
from pydbus import SystemBus
from gi.repository import GLib
from schedule import every, repeat, run_pending
import random
import logging
import configparser
import json
from pyjokes import get_joke

# Setup stuff
bus = SystemBus()
loop = GLib.MainLoop()
signal = bus.get('org.asamk.Signal', '/org/asamk/Signal/_16165281428')
log_level_info = {'logging.DEBUG': logging.DEBUG, 
                    'logging.INFO': logging.INFO,
                    'logging.WARNING': logging.WARNING,
                    'logging.ERROR': logging.ERROR,
                        }
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

owner=""  #This signal user has access to top level commands
bot_admins=[]  #These signal users have elevated privileges
# admins = bot_admins
# admins.append(owner)
config = configparser.ConfigParser()
config.read('config.ini')
owner = config['admin']['owner']
bot_admins = json.loads(config['admin']['bot_admins'])
logging.getLogger().setLevel(log_level_info.get(config['logging']['loglevel'],logging.ERROR))



# Helper functions
@repeat(every().tuesday.at('17:45'))
def messageOwner():
    signal.sendMessage("new cron test", [], [owner])

# @repeat(every(10).minutes)
# def messageOwner():
#     signal.sendMessage("Testing 123...", [], [owner])


def universalReply(timestamp, sender, groupID, message, attachments = []):
    signal.sendReadReceipt(sender, [timestamp])
    if groupID:
        signal.sendGroupMessage(message, attachments, groupID)
    else:
        signal.sendMessage(message, attachments, [sender])

def loadConfig():
    logging.info("Work in progress")

def saveConfig(timestamp, sender, groupID, message, attachments):
    config['admin']['bot_admins'] = json.dumps(bot_admins)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    universalReply(timestamp, sender, groupID, 'config saved')

# Feature Functions
def eightBall(timestamp, sender, groupID, message, attachments):
    responses = ['It is Certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']
    universalReply(timestamp, sender, groupID, '8ball: ' + random.choice(responses))

def showAdmins(timestamp, sender, groupID, message, attachments):
    response = f"Admin users are: {', '.join(bot_admins + [owner])}"
    universalReply(timestamp, sender, groupID, response)

def sendNudes(timestamp, sender, groupID, message, attachments):
    piclist = ['/home/ubuntu/ed209/images/doge.jpg']
    # response = get_joke()
    response =  ""
    universalReply(timestamp, sender, groupID, response, piclist)

def sendJoke(timestamp, sender, groupID, message, attachments):
    piclist = ['/home/ubuntu/ed209/images/doge.jpg']
    response = get_joke()
    universalReply(timestamp, sender, groupID, response, piclist)

def sendHelp(timestamp, sender, groupID, message, attachments):
    response = """Available commands:
/help
/8ball
/send_joke
/send_nudes
/show_admins

root only:
/add_admin
/del_admin
/save_config

    """
    universalReply(timestamp, sender, groupID, response)

# Admin Functions

def addAdmin(timestamp, sender, groupID, message, attachments):
    new_admin = message[10:].strip()
    if len(new_admin) == 12 and new_admin[0] == "+" and new_admin[1:].isnumeric():
        
        bot_admins.append(new_admin)
        response = f"Adding new admin user: {new_admin}"
        logging.debug(response)
    else:
        response = f"New user did not pass checks, cannot add {new_admin}"
        logging.warning(response)
    universalReply(timestamp, sender, groupID, response)

def delAdmin(timestamp, sender, groupID, message, attachments):
    del_admin = message[10:].strip()
    if len(del_admin) == 12 and del_admin[0] == "+" and del_admin[1:].isnumeric() and del_admin in bot_admins:
        
        bot_admins.remove(del_admin)
        response = f"Removing admin user: {del_admin}"
        logging.debug(response)
    else:
        response = f"New user did not pass checks, cannot remove {del_admin}"
        logging.warning(response)
    universalReply(timestamp, sender, groupID, response)

def messageHandler (timestamp, sender, groupID, message, attachments):
    logging.debug(f"sender: {sender}, group: {groupID}, message: {message}")
    if len(message) > 0 and message[0] == '/':  # If a message doesn't start with / we don't care and quit
    # Each defined function that ed209 can respond to gets set up here.  We use startswith by default but 
    # have the option of doing more complicated matching of the string
        if message[1:].startswith('8ball'):
            eightBall(timestamp, sender, groupID, message, attachments)

        elif message[1:].startswith('show_admins'):
            showAdmins(timestamp, sender, groupID, message, attachments)

        elif message[1:].startswith('send_nudes'):
            sendNudes(timestamp, sender, groupID, message, attachments)

        elif message[1:].startswith('send_joke'):
            sendJoke(timestamp, sender, groupID, message, attachments)       

        elif message[1:].startswith('help'):
            sendHelp(timestamp, sender, groupID, message, attachments)  


        # Root user (owner) functions here
        if sender == owner:
            logging.debug("Owner detected, checking root user functions")
            if message[1:].startswith('echo'):
                universalReply(timestamp, sender, groupID, message[5:])
            elif message[1:].startswith('add_admin'):
                addAdmin(timestamp, sender, groupID, message, attachments)
            elif message[1:].startswith('del_admin'):
                delAdmin(timestamp, sender, groupID, message, attachments)
            elif message[1:].startswith('save_config'):
                saveConfig(timestamp, sender, groupID, message, attachments)
    return

# schedule.every(10).minutes.do(messageOwner)

def cronHandler():
    logging.debug("cron hit")
    run_pending()
    return True


GLib.timeout_add_seconds(60,cronHandler)             # Run the cron handler every 60 seconds
signal.onMessageReceived = messageHandler       # Run the message handler every time we get a signal message

if __name__ == '__main__':
    loop.run()
