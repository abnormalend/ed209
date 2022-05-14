
class bothelper():

    def __init__(self, signal):
        self.signal = signal

    def _universalReply(self, timestamp, sender, groupID, message, attachments = []):
        self.signal.sendReadReceipt(sender, [timestamp])
        if groupID:
            self.signal.sendGroupMessage(message, attachments, groupID)
        else:
            self.signal.sendMessage(message, attachments, [sender])