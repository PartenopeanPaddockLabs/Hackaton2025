import re
import praw
from praw.models import MoreComments
import pandas as pd
from datetime import datetime
import pytz
import emoji as em
import os
from src.utils.utilsRedis import sendDataRedditToRedis, checkRedditPostAlreadyElaborated
from src.utils.utilsYoutube import save_data_to_csv


def scrape_reddit_posts_and_comments(subreddit_name, post_limit=10, comment_limit=20, reddit=None):   
    """
    Scrapes posts and their top-level comments from a specified Reddit subreddit.
    It collects data for both posts and comments, handles text cleaning,
    checks for already processed posts using Redis, and prepares data
    for storage in Redis (with nested comments) and for a Pandas DataFrame (flat structure).

    Args:
        subreddit_name (str): The name of the subreddit to scrape (e.g., 'python').
        post_limit (int): The maximum number of hot posts to retrieve.
        comment_limit (int): The maximum number of top-level comments to retrieve per post.
        reddit (praw.Reddit): An initialized PRAW Reddit instance for API interaction.

    Returns:
        pandas.DataFrame: A DataFrame containing scraped post and comment data,
                          where each post and comment is a separate row.
    """
    collected_data = []
    observation_time = datetime.now(pytz.utc).isoformat()

    print(f"\nScraping subreddit: r/{subreddit_name}...")

    subreddit = reddit.subreddit(subreddit_name)

    # Cycling posts
    for post in subreddit.hot(limit=post_limit):
        post_url = f"https://www.reddit.com{post.permalink}"
        publish_date_iso = datetime.utcfromtimestamp(post.created_utc).replace(tzinfo=pytz.utc).isoformat()

        # Checking if the post was already elaborated
        post_content_id = f"reddit_post_{post.id}"
        if checkRedditPostAlreadyElaborated(post_content_id, subreddit_name):
            print(f"Skipping already processed post: {post_content_id}")
            continue

        #Post body cleaning
        cleanedPostText=cleanText(post,True)

        # Building json for reddit post
        post_data = {
            'content_id': f"reddit_post_{post.id}",
            'observation_time': observation_time,
            'user': str(post.author),
            'user_location': None,
            'social_media': 'Reddit',
            'publish_date': publish_date_iso,
            'geo_location': None,
            'comment_raw_text': cleanedPostText,
            'emoji': em.distinct_emoji_list(post.selftext),
            'reference_post_url': post_url,
            'like_count': post.score,
            'reply_count': post.num_comments,
            'repost_count': 0,
            'quote_count': 0,
            'bookmark_count': 0,
            'content_type': 'post'
        }
        collected_data.append(post_data)

        # Principal Comments
        post.comments.replace_more(limit=0)
        comment_counter = 0

        comments = []

        # Cycling comments
        for comment in post.comments:
            if comment_counter >= comment_limit:
                break
            publish_date_iso = datetime.utcfromtimestamp(comment.created_utc).replace(tzinfo=pytz.utc).isoformat()

            # Comment body cleaning
            cleanedCommentText=cleanText(comment,False)

            # Building json for reddit comments of the post
            comment_data = {
                'content_id': f"reddit_comm_{comment.id}",
                'observation_time': observation_time,
                'user': str(comment.author),
                'user_location': None,
                'social_media': 'Reddit',
                'publish_date': publish_date_iso,
                'geo_location': None,
                'comment_raw_text': cleanedCommentText,
                'emoji': em.distinct_emoji_list(comment.body),
                'reference_post_url': post_url,
                'like_count': comment.score,
                'reply_count': 0,  # Reddit does not provide direct reply count for each comment
                'repost_count': 0,
                'quote_count': 0,
                'bookmark_count': 0,
                'content_type': 'commento'
            }
            collected_data.append(comment_data)
            comment_counter += 1
            comments.append(comment_data)

        # Copy to send post with innested comments
        post_data_for_redis = post_data.copy()
        post_data_for_redis['comments'] = comments #Aggiungiamo la lista di commenti

        # Send each post to redis
        sendDataRedditToRedis(post_data_for_redis, subreddit_name)

    print(f"\nScraping completato. Totale elementi raccolti: {len(collected_data)}")
    return pd.DataFrame(collected_data) 


def cleanText(text, isPost):
    """
    Cleans the raw text content of a Reddit post or comment.
    It removes URLs and replaces multiple newlines with single spaces.

    Args:
        text (praw.models.Submission or praw.models.Comment): The PRAW object
                                                              representing a post or comment.
        isPost (bool): True if the text belongs to a post (uses `selftext`),
                       False if it belongs to a comment (uses `body`).

    Returns:
        str: The cleaned text content.
    """

    # In this case, is a Post
    if isPost == True: 
        postText = text.selftext.strip() if text.selftext != None else " "
    
    # In this case, is a Comment
    else: 
        postText =  text.body.strip() if text.body != None else " "

    # Regex for urls
    postText = re.sub(r'https?://\S+', '', postText)
    cleanedPostText = re.sub(r'\n+', ' ', postText)
    return cleanedPostText


# --- Output ---
def data_to_csv(df_reddit, subreddit_to_scrape):
    """
    Saves the collected Reddit DataFrame to a CSV file.
    It also prints a preview and dimensions of the DataFrame.

    Args:
        df_reddit (pandas.DataFrame): The DataFrame containing Reddit post and comment data.
        subreddit_to_scrape (str): The name of the subreddit, used for naming the output CSV file.
    """
    print("\n--- Reddit Data Preview ---")
    print(df_reddit.head())
    print(f"\nReddit DataFrame Dimensions: {df_reddit.shape}")

    path = "data"
    file_name = f"reddit_data_{subreddit_to_scrape}.csv"
    file_path=os.path.join(path, file_name)
    df = df_reddit.drop_duplicates(subset=['content_id'], keep='first')
    save_data_to_csv(df, file_path)
    #df.to_csv(file_name, index=False)
    print(f"\nReddit data saved to: {file_name}")




