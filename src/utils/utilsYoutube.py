import pandas as pd
import os
from datetime import datetime
import pytz
from googleapiclient.discovery import build
from src.utils.utilsRedis import sendDataYoutubeToRedis, checkYoutubeCommentAlreadyElaborated
import emoji
import re

def scrape_youtube_comments(api_key, query, limit_videos, limit_comments):
    """Funzione per fare scraping dei commenti da YouTube."""
    
    collected_data = []
    observation_time = datetime.now(pytz.utc).isoformat()
    print(f"\nInizio scraping YouTube con query: '{query}'...")

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=limit_videos,
            type='video'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        print(f"Trovati {len(video_ids)} video.")

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

                for item in comment_response.get('items', []):

                    content_id = f"yt_comm_{item['snippet']['topLevelComment']['id']}"

                    # Check if the comment was already elaborated
                    if checkYoutubeCommentAlreadyElaborated(video_id, content_id):
                        print(f"Youtube comment {content_id} of video {video_id} was already elborated")
                        continue

                    comment = item['snippet']['topLevelComment']['snippet']
                    publish_date_aware = datetime.strptime(comment['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    publish_date_iso = publish_date_aware.isoformat()

                    comment_raw_text = comment.get('textDisplay', '')
                    comment_raw_text = clean_text(comment_raw_text)

                    emojis_found = emoji.distinct_emoji_list(comment_raw_text)
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

                    # Send comment to Redis
                    sendDataYoutubeToRedis(video_id, data)

                    comments_in_video += 1
                print(f"Raccolti {comments_in_video} commenti.")

            except Exception as e:
                print(f"Errore generico estrazione commenti: {e}")

    except Exception as e:
        print(f"Errore generico scraping YouTube: {e}")

    print("\nScraping YouTube completato.")
    return pd.DataFrame(collected_data)

def clean_text(text):
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)  # Rimuove URL
    text = re.sub(r'\s+', ' ', text).strip() # Rimuove spazi multipli e strip
    return text

def save_data_to_csv(df_new, file_path):
    """Controlla che non ci siano duplicati all'interno del DataFrame e lo salva in un file CSV."""

    existing_df = pd.DataFrame()

    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path)
            print(f"File {file_path} esiste già, caricamento dei dati esistenti.")
        except pd.errors.EmptyDataError:
            print(f"File {file_path} è vuoto, si procede con un DataFrame vuoto.")
            existing_df = pd.DataFrame()
        except Exception as e:
            print(f"Errore durante il caricamento del file esistente: {e}")
            existing_df = pd.DataFrame()
    else:
        print(f"File {file_path} non esiste.")

    df = pd.concat([existing_df, df_new], ignore_index=True)

    if 'content_id' in df.columns:
        df = df.drop_duplicates(subset=['content_id'], keep='first')
    else:
        print("Warning: La colonna 'content_id' non esiste, impossibile rimuovere duplicati.")

    try:
        df_to_save = df.copy()
        if 'emoji'in df_to_save.columns:
            df_to_save['emoji'] = df_to_save['emoji'].apply(lambda x: ','.join(x) if isinstance(x, list) else str(x))
        df_to_save.to_csv(file_path, index=False)
        print(f"Dati salvati in {file_path}")
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati: {e}")