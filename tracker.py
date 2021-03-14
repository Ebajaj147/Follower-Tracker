from __future__ import print_function
import time
from datetime import datetime
import os

from twitter import Twitter, OAuth, TwitterHTTPError
from tqdm import tqdm_notebook as tqdm
import pandas as pd
import matplotlib.pyplot as plt

USER_TO_ANALYZE = 'ebajaj147'
OAUTH_TOKEN = ''
OAUTH_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

twitter_connection = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

pbar = tqdm()
pbar.write('Collecting list of Twitter followers for @{}'.format(USER_TO_ANALYZE))

rl_status = twitter_connection.application.rate_limit_status()
if rl_status['resources']['followers']['/followers/ids']['remaining'] <= 0:
    sleep_until = rl_status['resources']['followers']['/followers/ids']['reset']
    sleep_for = int(sleep_until - time.time()) + 10 # wait a little extra time just in case
    if sleep_for > 0:
        pbar.write('Sleeping for {} seconds...'.format(sleep_for))
        time.sleep(sleep_for)
        pbar.write('Awake!')

followers_status = twitter_connection.followers.ids(screen_name=USER_TO_ANALYZE)
followers = followers_status['ids']
next_cursor = followers_status['next_cursor']
pbar.update(len(followers))

while next_cursor != 0:
    rl_status = twitter_connection.application.rate_limit_status()
    if rl_status['resources']['followers']['/followers/ids']['remaining'] <= 0:
        sleep_until = rl_status['resources']['followers']['/followers/ids']['reset']
        sleep_for = int(sleep_until - time.time()) + 10 # wait a little extra time just in case
        if sleep_for > 0:
            pbar.write('Sleeping for {} seconds...'.format(sleep_for))
            time.sleep(sleep_for)
            pbar.write('Awake!')

    followers_status = twitter_connection.followers.ids(screen_name=USER_TO_ANALYZE, cursor=next_cursor)
    # Prevent duplicate Twitter user IDs
    more_followers = [follower for follower in followers_status['ids'] if follower not in followers]
    followers += more_followers
    next_cursor = followers_status['next_cursor']

    pbar.update(len(more_followers))

pbar.close()

pbar = tqdm(total=len(followers))
pbar.write('Collecting join dates of Twitter followers for @{}'.format(USER_TO_ANALYZE))
followers_created = list()

rl_status = twitter_connection.application.rate_limit_status()
remaining_calls = rl_status['resources']['users']['/users/lookup']['remaining']

for base_index in range(0, len(followers), 100):
    if remaining_calls == 50:
        # Update the remaining calls count just in case
        rl_status = twitter_connection.application.rate_limit_status()
        remaining_calls = rl_status['resources']['users']['/users/lookup']['remaining']

    if remaining_calls <= 0:
        sleep_until = rl_status['resources']['users']['/users/lookup']['reset']
        sleep_for = int(sleep_until - time.time()) + 10 # wait a little extra time just in case
        if sleep_for > 0:
            pbar.write('Sleeping for {} seconds...'.format(sleep_for))
            time.sleep(sleep_for)
            pbar.write('Awake!')
            rl_status = twitter_connection.application.rate_limit_status()
            remaining_calls = rl_status['resources']['users']['/users/lookup']['remaining']

    remaining_calls -= 1

    # 100 users per request
    user_info = twitter_connection.users.lookup(user_id=list(followers[base_index:base_index + 100]))
    followers_created += [x['created_at'] for x in user_info]

    pbar.update(len(followers[base_index:base_index + 100]))

pbar.close()
print('Creating Follower Factory visualization for @{}'.format(USER_TO_ANALYZE))

days_since_2006 = [(x.year - 2006) * 365 + x.dayofyear for x in pd.to_datetime(followers_created)]

mpl_style_url = "https://gist.githubusercontent.com/Ebajaj147/cc48510c6e15349b370abcaf4663d6b1/raw/b5e3414109e4e9bf9aa1bf5b944ed0d7e0a4f6b6/twitter.mplstyle"
alpha = 0.1 * min(9, 80000. / len(days_since_2006))
with plt.style.context(mpl_style_url):
    plt.figure(figsize=(9, 12))
    plt.scatter(x=range(len(days_since_2006)), y=days_since_2006[::-1], s=2, alpha=alpha)
    plt.yticks(range(0, 365 * (datetime.today().year + 1 - 2006), 365), range(2006, datetime.today().year + 1))
    plt.xlabel('Follower count for @{}'.format(USER_TO_ANALYZE))
    plt.ylabel('Date follower joined Twitter')
    plt.savefig('{}-follower-factory.png'.format(USER_TO_ANALYZE))

print('Follower Factory visualization saved to {}'.format(os.getcwd()))