import requests
import logging
import random
from slugify import slugify
import mimetypes

class redditbot():

    def __init__(self, tempdir = "/tmp/ed209"):
        print("foo")
        self.tempdir = tempdir

    def getPosts(self, subreddit, listing = 'hot', timeframe = 'day', limit = 10 , random_mode = False):
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

    def getRandomPost(self, subreddit):
        posts = self.getPosts(subreddit, random_mode=True)
        randompost = random.choice(posts)['data']
        logging.debug(randompost['title'])
        logging.debug(randompost['url_overridden_by_dest'])
        return randompost['title'], self.downloadRedditFile(randompost['url_overridden_by_dest'], randompost['title'])

    def downloadRedditFile(self, url, title):
        r = requests.get(url, allow_redirects=True)
        destination = f"{self.tempdir}/{slugify(title)}{mimetypes.guess_extension(r.headers['content-type'])}"
        open(destination, 'wb').write(r.content)
        return destination




# temp stuff for testing delete when done

# reddit = redditbot()

# print(reddit.getRandomPost('pics'))

# posts[0]['data']['url_overridden_by_dest']
# posts[0]['data']['title']