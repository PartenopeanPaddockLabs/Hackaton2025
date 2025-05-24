import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import pytz
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

def scrape_youtube_comments(api_key, query, limit_videos, limit_comments):
    """Funzione per fare scraping dei commenti da YouTube."""
    collected_data = []
    observation_time = datetime.now(pytz.utc).isoformat()
    print(f"\nInizio scraping YouTube con query: '{query}'...")

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        print(f"Oggetto YouTube creato. Tipo: {type(youtube)}")

        print("Cerco video...")
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
            print(f"  Estraggo commenti dal video: {video_url}...")
            comments_in_video = 0
            try:
                comment_response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=limit_comments,
                    textFormat='plainText'
                ).execute()

                for item in comment_response.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    publish_date_aware = datetime.strptime(comment['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    publish_date_iso = publish_date_aware.isoformat()
                    data = {
                        'content_id': f"yt_comm_{item['snippet']['topLevelComment']['id']}",
                        'observation_time': observation_time,
                        'user': comment['authorDisplayName'],
                        'user_location': None,
                        'social_media': 'YouTube',
                        'publish_date': publish_date_iso,
                        'geo_location': None,
                        'comment_raw_text': comment['textDisplay'],
                        'emoji': [],
                        'reference_post_url': video_url,
                        'like_count': comment['likeCount'],
                        'reply_count': item['snippet']['totalReplyCount'],
                        'repost_count': 0,
                        'quote_count': 0,
                        'bookmark_count': 0,
                        'content_type': 'commento'
                    }
                    collected_data.append(data)
                    comments_in_video += 1
                print(f"    -> Raccolti {comments_in_video} commenti.")

            except Exception as e:
                print(f"    Errore generico estrazione commenti: {e}")

    except Exception as e:
        print(f"Errore generico scraping YouTube: {e}")

    print("\nScraping YouTube completato.")
    return pd.DataFrame(collected_data)

if __name__ == "__main__":
    try:
        if not API_KEY:
            raise ValueError("La chiave API di YouTube non è stata trovata.")

        search_query = "F1 Monaco GP 2025"
        max_videos_to_scrape = 3
        max_comments_per_video_to_scrape = 25

        df_youtube = scrape_youtube_comments(API_KEY, search_query, max_videos_to_scrape, max_comments_per_video_to_scrape)

        if not df_youtube.empty:
            print("\n--- Anteprima Dati YouTube ---")
            print(df_youtube.head())
            print(f"\nDimensioni DataFrame YouTube: {df_youtube.shape}")

            file_name = "youtube_data_monacogp.csv"
            df_youtube.to_csv(file_name, index=False)
            print(f"\nDati YouTube salvati in: {file_name}")
        else:
            print("\nNessun dato raccolto da YouTube.")

    except (FileNotFoundError, ValueError) as e:
        print(f"Errore critico: {e}")
    except Exception as e:
        print(f"Errore imprevisto nell'esecuzione: {e}")