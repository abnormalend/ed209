
class bothelper():

    def __init__(self, signal, config):
        self.signal = signal
        self.config = config
        self.function_list = []
        for item in dir(__class__):
            if not item.startswith("_") and not item.endswith('Handler'):
                self.function_list.append(item)

    def _universalReply(self, timestamp, sender, groupID, message, attachments = []):
        self.signal.sendReadReceipt(sender, [timestamp])
        if groupID:
            self.signal.sendGroupMessage(message, attachments, groupID)
        else:
            self.signal.sendMessage(message, attachments, [sender])

    def _saveConfig(self):
        """Save settings to the config file."""
        with open(self.config['self']['path'], 'w') as configfile:
            self.config.write(configfile)
        return True