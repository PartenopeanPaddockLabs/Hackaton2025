import pandas as pd
import os
from datetime import datetime
import pytz
from googleapiclient.discovery import build
from src.utils.utilsRedis import sendDataYoutubeToRedis, checkYoutubeCommentAlreadyElaborated
import emoji
import re

def scrape_youtube_comments(api_key, query, limit_videos, limit_comments):
    """
    Scrapes comments from YouTube videos based on a search query.
    It fetches video IDs, then retrieves comments for each video,
    cleans the text, checks for already processed comments using Redis,
    and prepares data for storage in a Pandas DataFrame and for Redis.

    Args:
        api_key (str): Your YouTube Data API key.
        query (str): The search term to find relevant YouTube videos.
        limit_videos (int): The maximum number of videos to search for.
        limit_comments (int): The maximum number of top-level comments to retrieve per video.

    Returns:
        pandas.DataFrame: A DataFrame containing the scraped YouTube comment data.
    """
    collected_data = []
    observation_time = datetime.now(pytz.utc).isoformat()
    print(f"\nStarting YouTube scraping with query: '{query}'...")

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=limit_videos,
            type='video'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        print(f"Found {len(video_ids)} videos.")

        # Cycling videos
        for video_id in video_ids:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            comments_in_video = 0
            try:
                comment_response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=limit_comments,
                    textFormat='plainText'
                ).execute()

                # Cycling video comments
                for item in comment_response.get('items', []):

                    content_id = f"yt_comm_{item['snippet']['topLevelComment']['id']}"

                    # Checking if the comment was already elaborated
                    if checkYoutubeCommentAlreadyElaborated(video_id, content_id):
                        print(f"Youtube comment {content_id} of video {video_id} was already elborated")
                        continue

                    comment = item['snippet']['topLevelComment']['snippet']
                    publish_date_aware = datetime.strptime(comment['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    publish_date_iso = publish_date_aware.isoformat()

                    # Extracting comments raw text
                    comment_raw_text = comment.get('textDisplay', '')
                    comment_raw_text = clean_text(comment_raw_text)

                    emojis_found = emoji.distinct_emoji_list(comment_raw_text)
                    
                    # Building json for youtube comment
                    data = {
                        'content_id': content_id,
                        'observation_time': observation_time,
                        'user': comment['authorDisplayName'],
                        'user_location': None,
                        'social_media': 'YouTube',
                        'publish_date': publish_date_iso,
                        'geo_location': None,
                        'comment_raw_text': comment_raw_text,
                        'emoji': emojis_found,
                        'reference_post_url': video_url,
                        'like_count': comment['likeCount'],
                        'reply_count': item['snippet']['totalReplyCount'],
                        'repost_count': 0,
                        'quote_count': 0,
                        'bookmark_count': 0,
                        'content_type': 'commento'
                    }
                    collected_data.append(data)

                    # Sending comments to Redis
                    sendDataYoutubeToRedis(video_id, data)

                    comments_in_video += 1
                print(f"Collected {comments_in_video} comments.")

            except Exception as e:
                print(f"Generic error extracting comments: {e}")

    except Exception as e:
        print(f"Generic YouTube scraping error: {e}")

    print("\nYoutube scraping completed.")
    return pd.DataFrame(collected_data)

def clean_text(text):
    """
    Cleans the raw text content by removing URLs and normalizing whitespace.

    Args:
        text (str): The input string to be cleaned.

    Returns:
        str: The cleaned text.
    """
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)  # Removes URLs
    text = re.sub(r'\s+', ' ', text).strip() # Removes multiple spaces and strips
    return text

def save_data_to_csv(df_new, file_path):
    """
    Checks for duplicates within the DataFrame, concatenates with existing data
    if the file exists, and saves the combined DataFrame to a CSV file.

    Args:
        df_new (pandas.DataFrame): The new DataFrame containing data to be saved.
        file_path (str): The full path to the CSV file where data will be saved.
    """
    existing_df = pd.DataFrame()

    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path)
            print(f"File {file_path} already exists, loading existing data.")
        except pd.errors.EmptyDataError:
            print(f"File {file_path} is empty, proceeding with an empty DataFrame.")
            existing_df = pd.DataFrame()
        except Exception as e:
            print(f"Error loading existing file: {e}")
            existing_df = pd.DataFrame()
    else:
        print(f"File {file_path} does not exist.")

    df = pd.concat([existing_df, df_new], ignore_index=True)

    if 'content_id' in df.columns:
        df = df.drop_duplicates(subset=['content_id'], keep='first')
    else:
        print("Warning: 'content_id' column does not exist, unable to remove duplicates.")

    try:
        df_to_save = df.copy()
        if 'emoji'in df_to_save.columns:
            df_to_save['emoji'] = df_to_save['emoji'].apply(lambda x: ','.join(x) if isinstance(x, list) else str(x))
        df_to_save.to_csv(file_path, index=False)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"Error saving data: {e}")