import os
from dotenv import load_dotenv
from utilsYoutube import scrape_youtube_comments, save_data_to_csv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("La chiave API di YouTube non è stata trovata nel file .env.")

def start_scraping_youtube(search_query="F1 Monaco GP 2025", max_videos_to_scrape=3, max_comments_per_video_to_scrape=25):
    """
    Funzione per avviare lo scraping dei commenti da YouTube.
    """

    df_youtube = scrape_youtube_comments(API_KEY, search_query, max_videos_to_scrape, max_comments_per_video_to_scrape)

    if not df_youtube.empty:
        print("\n--- Anteprima Dati YouTube ---")
        print(df_youtube.head())
        print(f"\nDimensioni DataFrame YouTube: {df_youtube.shape}")

        output_dir = "../../data"
        file_name = f"youtube_data_{search_query}.csv"
        file_path = os.path.join(output_dir, file_name)

        save_data_to_csv(df_youtube, file_path)
    else:
        print("Nessun dato raccolto da YouTube.")

