from src.utils.scraperReddit import startScrapingReddit
from src.utils.scraperYoutube import start_scraping_youtube
import multiprocessing as mp


"""
get_reddit_config, takes the config for reddit scraper
"""

def get_reddit_config():
    topic = input("Reddit - Topic to search: ")
    num_posts = int(input("Reddit - Number of posts: "))
    num_comments = int(input("Reddit - Number of comments (for each post): "))
    frequency = int(input("Reddit - Frequency of scraping in seconds: "))
    return {
        'scraper': 'reddit',
        'topic': topic,
        'num_posts': num_posts,
        'num_comments': num_comments,
        'frequency': frequency
    }


"""
get_youtube_config, takes the config for youtube scraper
"""
def get_youtube_config():
    query = input("YouTube - Content to search: ")
    max_videos = int(input("YouTube - Number of video: "))
    max_comments = int(input("YouTube - Number of comments (for each video): "))
    frequency = int(input("YouTube - Frequency of scraping in seconds: "))
    return {
        'scraper': 'youtube',
        'query': query,
        'max_videos': max_videos,
        'max_comments': max_comments,
        'frequency': frequency
    }

"""
run_scraper, this function takes every confing present in configs lits and starts 
a process (running the function startScraping...) for every config.

Args:
    parameteres: configs, is a list of "config" structure a specific dictionary made to initialize the scrapers


"""
def run_scraper(config):
    print(f"\n✅ Avvio scraper {config['scraper']} con configurazione:")
    for k, v in config.items():
        if k != 'scraper':
            print(f"  {k}: {v}") 
        
    if config['scraper']=='reddit':
        p = mp.Process(target=startScrapingReddit, args=(config['topic'], config['num_posts'], config['num_comments'], config['frequency']))
    elif config['scraper']=='youtube':
        p = mp.Process(target=start_scraping_youtube, args=(config['query'], config['max_videos'], config['max_comments'], config['frequency']))
    p.start()
