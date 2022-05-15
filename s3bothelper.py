import boto3
import logging
import random
import os
from bothelper import bothelper

class s3bothelper(bothelper):

    def __init__(self, signal, config):
        self.s3 = boto3.client('s3')
        self.signal = signal
        self.config = config
        self.bucket = self.config['s3']['bucket']
        self.subdirs = []
        self.basedir= self.config['s3']['basedir']
        self.filelists = {}
        self.dest = self.config['s3']['destination']
        self.function_list = []
        for item in dir(__class__):
            if not item.startswith("_") and not item.endswith('Handler'):
                self.function_list.append(item)
        self._updateSubdirs()

    def _getFileList(self, prefix):
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
        file_list = []
        for page in pages:
            for obj in page['Contents']:
                file_list.append(obj['Key'])
        self.filelists[prefix] = file_list

    def _updateSubdirs(self):
        """Get a list of subdirectories inside the basedir, build a list of them"""
        self.subdirs = []   # Erase the current subdirs so we don't double up anything
        for o in self.s3.list_objects(Bucket=self.bucket, Prefix=self.basedir, Delimiter='/').get('CommonPrefixes'):
            self.subdirs.append(o.get('Prefix').replace(self.basedir, '')[:-1])
        logging.debug(self.subdirs)

    def _getRandomImage(self, subdir = None, moveAfter=False):
        prefix = f"{self.basedir}{subdir}" if subdir else self.config['s3']['default_path']
        if not prefix in self.filelists:
            self._getFileList(prefix)
        image = random.choice(self.filelists[prefix])
        destination = f"{self.dest}/{image.replace(prefix,'')}"
        if not os.path.exists(self.dest): os.mkdir(self.dest) 
        self.s3.download_file(self.bucket, image, destination)

        if moveAfter:
            self.s3.copy_object(Bucket=self.bucket, CopySource=f"{self.bucket}/{image}", Key=f"{image.replace(prefix,self.config['s3']['move_after_dest'])}")
            self.s3.delete_object(Bucket=self.bucket, Key=image)
            self._getFileList(prefix).remove(image)
        return destination

    def show_subdirs(self, timestamp, sender, groupID, message, attachments):
        self._updateSubdirs()
        nl = '\n'
        response = f"Avilable subdirs:{nl}{nl.join(self.subdirs)}"
        if self.config['s3']['selected_subdir']:
            response = response + f"{nl}{nl}Selected subdir: {self.config['s3']['selected_subdir']}"
        self._universalReply(timestamp, sender, groupID, response)

    # def show_active_subdir(self, timestamp, sender, groupID, message, attachments):
    #     response = f"Current subdir: {self.config['s3']['selected_subdir']}"
    #     self._universalReply(timestamp, sender, groupID, response)

    def set_subdir(self, timestamp, sender, groupID, message, attachments):
        new_subdir= message.split()[1]
        self.config['s3']['selected_subdir'] = new_subdir
        self._saveConfig()
        self.show_subdirs( timestamp, sender, groupID, message, attachments)

    def send_pic(self, timestamp, sender, groupID, message, attachments):
        reqd_subdir = message.split()[1] if len(message.split()) > 1 else None
        subdir = reqd_subdir if reqd_subdir in self.subdirs else None
        file = self._getRandomImage(subdir, True if groupID else False)
        self._universalReply(timestamp, sender, groupID, "", [file])