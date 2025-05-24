from src.utils.scraperReddit import startScraping
import multiprocessing as mp

#scraping Youtube...
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

#ADD OTHER CONFIGS HERE!!

def run_scraper(config):
    print(f"\n✅ Avvio scraper {config['scraper']} con configurazione:")
    for k, v in config.items():
        if k != 'scraper':
            print(f"  {k}: {v}") 
        
    if config['scraper']=='reddit':
        p = mp.Process(target=startScraping, args=(config['topic'], config['num_posts'], config['num_comments'], config['frequency']))
    elif config['scraper']=='youtube':
        #youtube
        pass
    p.start()
