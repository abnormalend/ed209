import configparser
import json
import logging
import random
import os
from pyjokes import get_joke
from schedule import every, repeat, run_pending
# import redditbot
import s3bothelper


class signalbot():

    def __init__(self, signal, configPath):

        # Load our settings from the file
        self.signal = signal
        self.config = configparser.ConfigParser()
        self.configPath = configPath    # hold onto this so we can save back to the file.
        self.config.read(configPath)  #'/home/ubuntu/ed209/config.ini'
        self.owner = self.config['admin']['owner']                  # Has access to the root functions
        self.admins = json.loads(self.config['admin']['bot_admins'])    # Has access to the admin level funtions
        self.blacklist = json.loads(self.config['admin']['blacklist'])  # ignore these people
        self.function_list = []
        self.admin_function_list = []
        self.root_function_list = []
        # self.reddit = redditbot.redditbot()
        self.s3 = s3bothelper.s3bothelper(self.config['s3']['bucket'],self.config['s3']['themes'] , self.config['s3']['destination'])
        self._botFunctions()


# Cleanup and refresh stuff
    @repeat(every().day.at("00:30"))
    def _clean_temp(self):
        os.system(f"sudo find {self.config['s3']['destination']} -type f -atime +{self.config['s3']['cleaningage']} -delete")


# Internal functions

    def _botFunctions(self):
        for item in dir(signalbot):
            if not item.startswith("_") and not item.endswith('Handler') and not item.startswith('admin') and not item.startswith('root'):
                self.function_list.append(item)
            elif not item.startswith("_") and not item.endswith('Handler') and item.startswith('admin'):
                self.admin_function_list.append(item)
            elif not item.startswith("_") and not item.endswith('Handler') and item.startswith('root'):
                self.root_function_list.append(item)

    def _universalReply(self, timestamp, sender, groupID, message, attachments = []):
        self.signal.sendReadReceipt(sender, [timestamp])
        if groupID:
            self.signal.sendGroupMessage(message, attachments, groupID)
        else:
            self.signal.sendMessage(message, attachments, [sender])

    def _saveConfig(self):
        """Save settings to the config file."""
        with open(self.configPath, 'w') as configfile:
            self.config.write(configfile)
        return True

    def _validatePhoneNumber(self, number):
        return len(number) == 12 and number[0] == "+" and number[1:].isnumeric()

    def _updateLists(self):
        """ This function syncs the dicts with the config entries and saves them out"""
        self.config['admin']['bot_admins'] = json.dumps(self.admins)
        self.config['admin']['blacklist'] = json.dumps(self.blacklist)
        self._saveConfig()
    
    def _modify_list(self, timestamp, sender, groupID, message, attachments, my_list_item, my_list, my_action = 'add'):
        if my_action not in ['add', 'del']:
            logging.error(f"Invalid action given {my_action}")
            return f"Invalid action given {my_action}"
        if not self._validatePhoneNumber(my_list_item):
            return f"Failed to validate {my_list_item}, is it a valid phone number with country code?"

        if my_action == 'del' and my_list_item not in my_list:
            return f"Cannot remove {my_list_item} because it is not in the list"

        if my_action == 'add': my_list.append(my_list_item)
        elif my_action == 'del': my_list.remove(my_list_item)
        self._updateLists()
        return  f"success"

    def _noMatchFound(self, timestamp, sender, groupID, message, attachments):
        response = "Were you talking to me? I don't understand that command.  Run /help for a list of available commands."
        self._universalReply(timestamp, sender, groupID, response)

    def _blacklistHandler(self, timestamp, sender, groupID, message, attachments):
        self._universalReply(timestamp, sender, groupID, "", [random.choice(json.loads(self.config['blacklist']['images']))])


# Handler functions, messages and cron

    def cronHandler(self):
        run_pending()
        return True


    def messageHandler(self, timestamp, sender, groupID, message, attachments):
        found = False
        logging.debug(f"sender: {sender}, group: {groupID}, message: {message}")
        if len(message) > 0 and message[0] == '/':  # If a message doesn't start with / we don't care and quit
            if sender not in self.blacklist:
                for item in self.function_list:
                    if message[1:].startswith(item):
                        getattr(self, item)(timestamp, sender, groupID, message, attachments)
                        found = True
                        break
                
                # Admin only functions
                if sender in self.admins or sender == self.owner:
                    for item in self.admin_function_list:
                        if message[1:].startswith(item): 
                            getattr(self, item)(timestamp, sender, groupID, message, attachments)
                            found = True
                            break

                # Root only functions
                if sender == self.owner:
                    for item in self.root_function_list:
                        if message[1:].startswith(item): 
                            getattr(self, item)(timestamp, sender, groupID, message, attachments)
                            found = True
                            break
            else:
                self._blacklistHandler(timestamp, sender, groupID, message, attachments)
                found = True

            # We made it all the way to the end and didn't find anything, better do our no match function
            if not found:
                self._noMatchFound(timestamp, sender, groupID, message, attachments)

# Unrestricted functions

    def eightball(self, timestamp, sender, groupID, message, attachments):
        responses = ['It is Certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']
        self._universalReply(timestamp, sender, groupID, '8ball: ' + random.choice(responses))

    def send_joke(self, timestamp, sender, groupID, message, attachments):
        piclist = [self.config['send_joke']['image']]
        response = get_joke()
        self._universalReply(timestamp, sender, groupID, response, piclist)

    def help(self, timestamp, sender, groupID, message, attachments):
        nl = '\n'
        response = f"Commands:{nl}{nl.join(self.function_list)} {nl}{nl}Admin Commands:{nl}{nl.join(self.admin_function_list)}{nl}{nl}Root Commands:{nl}{nl.join(self.root_function_list)}"
        self._universalReply(timestamp, sender, groupID, response)

    def show_admins(self, timestamp, sender, groupID, message, attachments):
        response = f"Admin users are: {', '.join(self.admins + [self.owner])}"
        self._universalReply(timestamp, sender, groupID, response)

    def show_blacklist(self, timestamp, sender, groupID, message, attachments):
        response = f"Blacklisted users are: {', '.join(self.blacklist)}"
        self._universalReply(timestamp, sender, groupID, response)

    def show_themes(self, timestamp, sender, groupID, message, attachments):
        self.s3.updateThemes()
        response = f"Avilable themes: {', '.join(self.s3.themes)}"
        self._universalReply(timestamp, sender, groupID, response)

    def show_active_theme(self, timestamp, sender, groupID, message, attachments):
        response = f"Current theme: {self.config['humpday']['selected_theme']}"
        self._universalReply(timestamp, sender, groupID, response)

    def set_theme(self, timestamp, sender, groupID, message, attachments):
        new_theme = message[10:].strip()
        self.config['humpday']['selected_theme'] = new_theme
        self._saveConfig()
        self.show_active_theme( timestamp, sender, groupID, message, attachments)

    def send_nudes(self, timestamp, sender, groupID, message, attachments):
        theme = message[11:].strip()
        theme = theme if theme in self.s3.themes else None

        file = self.s3.getRandomImage(theme, True if groupID else False)
        self._universalReply(timestamp, sender, groupID, "", [file])

    def echo(self, timestamp, sender, groupID, message, attachments):
        self._universalReply(timestamp, sender, groupID, message[5:].strip())

    def drunkpost(self, timestamp, sender, groupID, message, attachments):
        self._universalReply(timestamp, sender, groupID, "coming soon...")

    def boldtest(self, timestamp, sender, groupID, message, attachments):
        self._universalReply(timestamp, sender, groupID, "𝐛𝐨𝐥𝐝 𝐭𝐞𝐱𝐭 𝕓𝕠𝕝𝕕 𝕥𝕖𝕩𝕥 𝗯𝗼𝗹𝗱 𝘁𝗲𝘅𝘁")
### ADMIN FUNCTIONS

    def admin_add_blacklist(self, timestamp, sender, groupID, message, attachments):
        response = self._modify_list(timestamp, sender, groupID, message, attachments, message[20:].strip(), self.blacklist)
        self._universalReply(timestamp, sender, groupID, response)

    def admin_del_blacklist(self, timestamp, sender, groupID, message, attachments):
        response = self._modify_list(timestamp, sender, groupID, message, attachments, message[20:].strip(), self.blacklist, 'del')
        self._universalReply(timestamp, sender, groupID, response)


### ROOT FUNCTIONS

    def root_add_admin(self, timestamp, sender, groupID, message, attachments):
        response = self._modify_list(timestamp, sender, groupID, message, attachments, message[15:].strip(), self.admins)
        self._universalReply(timestamp, sender, groupID, response)

    def root_del_admin(self, timestamp, sender, groupID, message, attachments):
        response = self._modify_list(timestamp, sender, groupID, message, attachments, message[15:].strip(), self.admins, 'del')
        self._universalReply(timestamp, sender, groupID, response)