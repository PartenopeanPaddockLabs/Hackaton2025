import re
import praw
from praw.models import MoreComments
import pandas as pd
from datetime import datetime
import pytz
import emoji as em


def scrape_reddit_posts_and_comments(subreddit_name, post_limit=10, comment_limit=20, reddit=None):
    collected_data = []
    observation_time = datetime.now(pytz.utc).isoformat()

    print(f"\nScraping subreddit: r/{subreddit_name}...")

    subreddit = reddit.subreddit(subreddit_name)

    for post in subreddit.hot(limit=post_limit):
        post_url = f"https://www.reddit.com{post.permalink}"
        publish_date_iso = datetime.utcfromtimestamp(post.created_utc).replace(tzinfo=pytz.utc).isoformat()

        #Post body cleaning
        cleanedPostText=cleanText(post,True)


        post_data = {
            'content_id': f"reddit_post_{post.id}",
            'observation_time': observation_time,
            'user': str(post.author),
            'user_location': None,
            'social_media': 'Reddit',
            'publish_date': publish_date_iso,
            'geo_location': None,
            'raw_text': cleanedPostText,
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

        # Commenti principali
        post.comments.replace_more(limit=0)
        comment_counter = 0


        for comment in post.comments:
            if comment_counter >= comment_limit:
                break
            publish_date_iso = datetime.utcfromtimestamp(comment.created_utc).replace(tzinfo=pytz.utc).isoformat()

            #Comment body cleaning
            cleanedCommentText=cleanText(comment,False)

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
                'reply_count': 0,  # Reddit non offre conteggio diretto delle risposte per ogni commento
                'repost_count': 0,
                'quote_count': 0,
                'bookmark_count': 0,
                'content_type': 'commento'
            }
            collected_data.append(comment_data)
            comment_counter += 1

    print(f"\nScraping completato. Totale elementi raccolti: {len(collected_data)}")
    return pd.DataFrame(collected_data)


def cleanText(text, isPost):
    if isPost == True: #In this case, is a Post
        postText = text.selftext.strip() if text.selftext != None else " "
    else: #In this case, is a Comment
        postText =  text.body.strip() if text.body != None else " "

    postText = re.sub(r'https?://\S+', '', postText)
    cleanedPostText = re.sub(r'\n+', ' ', postText)
    return cleanedPostText


# --- Output ---
def data_to_csv(df_reddit, subreddit_to_scrape):
  print("\n--- Anteprima Dati Reddit ---")
  print(df_reddit.head())
  print(f"\nDimensioni DataFrame Reddit: {df_reddit.shape}")

  file_name = f"reddit_data_{subreddit_to_scrape}.csv"
  df = df_reddit.drop_duplicates(subset=['content_id'], keep='first')
  df.to_csv(file_name, index=False)
  print(f"\nDati Reddit salvati in: {file_name}")


def sendDataToRedis():
    pass

