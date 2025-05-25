
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

# --- Scraping Reddit function ---
def startScrapingReddit(subreddit_name, max_posts, max_comments_per_post, frequency):
    """
    Continuously scrapes Reddit posts and comments from a specified subreddit.
    It fetches data, saves it to a CSV, and then pauses for a defined interval
    before repeating the process.

    Args:
        subreddit_name (str): The name of the subreddit to scrape (e.g., 'python').
        max_posts (int): Maximum number of hot posts to retrieve.
        max_comments_per_post (int): Maximum top-level comments per post.
        frequency (int): Time in seconds to wait between scraping cycles.
    """
    while True:
        # Scrape data and get a DataFrame from collected Reddit posts and comments
        df_reddit = scrape_reddit_posts_and_comments(subreddit_name, max_posts, max_comments_per_post, reddit)
        data_to_csv(df_reddit, subreddit_name)
        time.sleep(frequency)

