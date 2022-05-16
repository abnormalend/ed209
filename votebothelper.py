from os import times
from time import time
from bothelper import bothelper
from slugify import slugify
import logging

class votebothelper(bothelper):

    def __init__(self, signal, config):
        self.signal = signal
        self.config = config
        self.votes = {}
        self.function_list = []
        for item in dir(__class__):
            if not item.startswith("_") and not item.endswith('Handler'):
                self.function_list.append(item)

    def vote_create(self, timestamp, sender, groupID, message, attachments):
        vote_message = message.split()
        if len(vote_message) <= 1:
            response = "Usage: /vote_create Sentence about whatever this vote is for"
            self._universalReply(timestamp, sender, groupID, response)
        else:
            vote_body = ' '.join(vote_message[1:])
            vote_id = slugify(vote_body)
            logging.info(f"vote_id: {vote_id}")
            logging.info(f"vote_body: {vote_body}")
            if vote_id in self.votes:
                response = "Vote already exists, please create a new vote"
                self._universalReply(timestamp, sender, groupID, response)
            else:
                self.votes[vote_id] = {}
                response = f"Vote created, vote_id is {vote_id}"
                self._universalReply(timestamp, sender, groupID, response)
    
    def vote(self, timestamp, sender, groupID, message, attachments):
        vote_message = message.split()
        if len(vote_message) <= 2:
            response = "Usage: /vote voteID Whatever choice you're voting for"
            self._universalReply(timestamp, sender, groupID, response)
        else:
            vote_id = vote_message[1]
            choice_body = ' '.join(vote_message[2:])
            logging.info(f"vote_id: {vote_id}")
            logging.info(f"choice_body: {' '.join(choice_body)}")
            if self.votes[vote_id].get(choice_body):
                self.votes[vote_id][choice_body] += 1
            else:
                self.votes[vote_id][choice_body] = 1
            response = "Vote Recorded"
            self._universalReply(timestamp, sender, groupID, response)

    def vote_list(self, timestamp, sender, groupID, message, attachments):
        nl = "\n"
        response = f"Vote IDs:{nl}"
        for key, value in self.votes.items():
            logging.info(f'key: {key}')
            logging.info(f'value: {value}')
            response += f"{key}{nl}"
        self._universalReply(timestamp, sender, groupID, response)

    def vote_results(self, timestamp, sender, groupID, message, attachments):
        vote_message = message.split()
        if len(vote_message) <= 1:
            response = "Usage: /vote_results voteID"
            # self._universalReply(timestamp, sender, groupID, response)
        else:
            vote_id = vote_message[1]
            nl = "\n"
            response = f"{vote_id}:{nl}"

            for key, value in self.votes[vote_id].items():
                response += f"{key}: {value}{nl}"
        self._universalReply(timestamp, sender, groupID, response)