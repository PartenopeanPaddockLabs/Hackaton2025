
from dotenv import load_dotenv
from src.utils.utilsReddit import scrape_reddit_posts_and_comments, data_to_csv
import os 
import praw
import time

load_dotenv()

# --- Reddit credentials ---
reddit = praw.Reddit(
    client_id=os.getenv('CLIENT_ID'), #ID APPLICATION GITHUB
    client_secret=os.getenv('CLIENT_SECRET'), #SECRET KEY
    user_agent=os.getenv('USER_AGENT') #STRING
)

# --- Scraping function ---
def startScraping(subreddit_name, max_posts, max_comments_per_post, frequency):
    while True:
        df_reddit = scrape_reddit_posts_and_comments(subreddit_name, max_posts, max_comments_per_post, reddit)
        data_to_csv(df_reddit, subreddit_name)

        time.sleep(frequency)

