import logging
import random
import requests
from slugify import slugify
import mimetypes
from bothelper import bothelper

class redditbothelper(bothelper):

    def __init__(self, signal, config):
        self.signal = signal
        self.config = config
        self.function_list = []
        self.reddit_modes = ["top", "controversial", "best", "hot", "new", "rising"]
        self.supported_extensions = ["jpg", "gif", "mp4"]
        for item in dir(__class__):
            if not item.startswith("_") and not item.endswith('Handler'):
                self.function_list.append(item)

    def _getPosts(self, subreddit, listing = 'hot', timeframe = 'day', limit = 10 , random_mode = False):
        valid_timeframes = ["hour", "day", "week", "month", "year", "all"]
        valid_listings = ["top", "controversial", "best", "hot", "new", "rising"]

        if random_mode:
            timeframe = random.choice(valid_timeframes)
            listing = random.choice(valid_listings)

        if timeframe not in valid_timeframes:
            logging.error(f"invalid timeframe: {timeframe}, must be one of {', '.join(valid_timeframes)}")
            return False
        if listing not in valid_listings:
            logging.error(f"Invalid listing: {listing}, must be one of {', '.join(valid_listings)}")

        try:
            base_url = f'https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}&t={timeframe}'
            request = requests.get(base_url, headers = {'User-agent': 'ed209'})
        except:
            print('An Error Occured')
        return request.json()['data']['children']

    def _filterPosts(self, posts):
        """Go through a list of posts and remove any that aren't suitable for our purposes"""
        goodPosts = []
        for post in posts:
            logging.info(post['data']['title'])
            if post['data']['is_self']:
                logging.info('skipping because of selfpost')
                continue
            if post['data']['over_18'] and not self.config['reddit'].getboolean('allow_nsfw'):
                logging.info('skipping because nfsw content not allowed')
                continue
            if post['data']['url'].split('.')[-1] not in self.supported_extensions:
                logging.info('skipping because of unsupported extension')
                continue
            logging.info("Post Accepted")
            goodPosts.append(post)
        return goodPosts

    def _getRandomPost(self, subreddit):
        posts = self._getPosts(subreddit, random_mode=True)
        posts = self._filterPosts(posts)
        if not posts:
            return False, None    #No matches, quit now
        randompost = random.choice(posts)['data']
        logging.info(randompost.get('title'))
        logging.info(randompost.get('url'))
        logging.info(randompost.get('url_overridden_by_dest'))
        return randompost['title'], self._downloadRedditFile(randompost['url'], randompost['title'])

    def _downloadRedditFile(self, url, title):
        r = requests.get(url, allow_redirects=True)
        native_extensions = [".jpg",".gif",".mp4"]
        convert_extensions = [".webm"]
        ext = None
        for one_ext in native_extensions:
            if url.endswith(one_ext):
                ext = one_ext

        destination = f"{self.config['reddit']['destination']}/{slugify(title)}{ext if ext else mimetypes.guess_extension(r.headers['content-type'])}"
        open(destination, 'wb').write(r.content)
        return destination

    def reddit(self, timestamp, sender, groupID, message, attachments):
        options = message.split()
        match len(options):
            case 1:     # Random mode, default subreddit
                title, file = self._getRandomPost(self.config['reddit']['default_subreddit'])
            case 2:     # We have either a mode or a subreddit, need to figure out which
                if options[1] in self.reddit_modes:
                   logging.warning("non-random mode not made yet")
                   title = "non-random mode not made yet"
                   file = self.config['images']['techdiff']
                else:
                     title, file = self._getRandomPost(options[1])
            case 3:
                logging.warning("non-random mode not made yet")
                title = "non-random mode not made yet"
                file = self.config['images']['techdiff']
        # subreddit = message[14:].strip()
        # title, file = self._getRandomPost(subreddit if subreddit else self.config['reddit']['default_subreddit'])
        if title and file:
            self._universalReply(timestamp, sender, groupID, title, [file])
        else:
            self._universalReply(timestamp, sender, groupID, "Sorry, nothing found. This could be due to an invalid subreddit, or one of the settings for file types or content filters.")