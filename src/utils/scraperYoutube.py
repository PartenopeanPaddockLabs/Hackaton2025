import os
from dotenv import load_dotenv
from src.utils.utilsYoutube import scrape_youtube_comments, save_data_to_csv
import time

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("La chiave API di YouTube non è stata trovata nel file .env.")

def start_scraping_youtube(search_query="F1 Monaco GP 2025", max_videos_to_scrape=3, max_comments_per_video_to_scrape=25, frequency=10):
    """
    Continuously scrapes YouTube comments based on a search query.
    It retrieves comments from multiple videos, saves the data to a CSV file,
    and then pauses before performing the next scraping cycle.

    Args:
        search_query (str): The search term to find relevant YouTube videos.
        max_videos_to_scrape (int): The maximum number of videos to scrape comments from per cycle.
        max_comments_per_video_to_scrape (int): The maximum number of comments to retrieve per video.
        frequency (int): The time in seconds to wait between scraping cycles.
    """
    while True:
        df_youtube = scrape_youtube_comments(API_KEY, search_query, max_videos_to_scrape, max_comments_per_video_to_scrape)

        if not df_youtube.empty:
            print("\n--- Youtube Data Preview ---")
            print(df_youtube.head())
            print(f"\nYouTube DataFrame Dimensions: {df_youtube.shape}")

            output_dir = "data"
            file_name = f"youtube_data_{search_query}.csv"
            file_path = os.path.join(output_dir, file_name)

            save_data_to_csv(df_youtube, file_path)
        else:
            print("No data collected from YouTube")
        
        time.sleep(frequency)

