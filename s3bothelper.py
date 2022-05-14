import boto3
import logging
import random
import os
from bothelper import bothelper

class s3bothelper(bothelper):

    def __init__(self, signal, bucket, themesFolder = "themes/", destination = "/tmp/ed209"):
        self.s3 = boto3.client('s3')
        self.signal = signal
        self.bucket = bucket
        self.themes = []
        self.themes_folder = themesFolder
        self.filelists = {}
        self.dest = destination
        self.function_list = []
        for item in dir(__class__):
            if not item.startswith("_") and not item.endswith('Handler'):
                self.function_list.append(item)
        self._updateThemes()

    def _getFileList(self, prefix):
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
        file_list = []
        for page in pages:
            for obj in page['Contents']:
                file_list.append(obj['Key'])
        self.filelists[prefix] = file_list

    def _updateThemes(self):
        self.themes = []
        for o in self.s3.list_objects(Bucket=self.bucket, Prefix=self.themes_folder, Delimiter='/').get('CommonPrefixes'):
            self.themes.append(o.get('Prefix').replace(self.themes_folder, '')[:-1])
        logging.debug(self.themes)

    def _getRandomImage(self, theme = None, moveAfter=False):
        prefix = f"themes/{theme}/" if theme else "outbox/"
        if not prefix in self.filelists:
            self._getFileList(prefix)
        image = random.choice(self.filelists[prefix])
        destination = f"{self.dest}/{image.replace(prefix,'')}"
        if not os.path.exists(self.dest): os.mkdir(self.dest) 
        self.s3.download_file(self.bucket, image, destination)

        if moveAfter:
            self.s3.copy_object(Bucket=self.bucket, CopySource=f"{self.bucket}/{image}", Key=f"{image.replace(prefix,'sent/')}")
            self.s3.delete_object(Bucket=self.bucket, Key=image)
            self._getFileList(prefix).remove(image)
        return destination
        # print(image)

    # def _universalReply(self, timestamp, sender, groupID, message, attachments = []):
    #     self.signal.sendReadReceipt(sender, [timestamp])
    #     if groupID:
    #         self.signal.sendGroupMessage(message, attachments, groupID)
    #     else:
    #         self.signal.sendMessage(message, attachments, [sender])

    def show_themes(self, timestamp, sender, groupID, message, attachments):
        self._updateThemes()
        response = f"Avilable themes: {', '.join(self.themes)}"
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