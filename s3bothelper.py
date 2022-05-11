import boto3
import logging
import random
import os

class s3bothelper():

    def __init__(self, bucket, themesFolder = "themes/", destination = "/tmp/ed209"):
        self.s3 = boto3.client('s3')
        self.bucket = bucket
        self.themes = []
        self.themes_folder = themesFolder
        self.filelists = {}
        self.dest = destination
        self.updateThemes()

    def _getFileList(self, prefix):
        
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
        file_list = []
        for page in pages:
            for obj in page['Contents']:
                file_list.append(obj['Key'])
        self.filelists[prefix] = file_list

    def updateThemes(self):
        self.themes = []
        for o in self.s3.list_objects(Bucket=self.bucket, Prefix=self.themes_folder, Delimiter='/').get('CommonPrefixes'):
            self.themes.append(o.get('Prefix').replace(self.themes_folder, '')[:-1])
        logging.debug(self.themes)

    def getRandomImage(self, theme = None, moveAfter=False):
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
