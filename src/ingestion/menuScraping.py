import sys
from src.utils.utilsMenu import run_scraper, get_reddit_config, get_youtube_config

# List of possible scraper to inserto into the terminal
scrapers = ['reddit', 'youtube']

def startMenu():
    """
    This function serves as the main entry point for the scraping application.
    It parses command-line arguments to determine which scrapers to run (e.g., 'reddit', 'youtube').
    For each selected scraper, it retrieves the necessary configuration and then
    initiates the scraping process. It handles invalid scraper selections and
    provides usage instructions if no scrapers are specified.
    """
    if len(sys.argv) <= 1:
        print("❌ Please specify at least one scraper as an argument!")
        print("Example: python -m src.ingestion.menuScraping reddit youtube")
        sys.exit(1)
    
    # Collecting scrapers from args
    selected_scrapers = sys.argv[1:]
    
    # Buidling configs for scrapers
    configs = []
    for scraper in selected_scrapers:
        if scraper not in scrapers:
            print(f"❌ Not valid Scraper: {scraper}")
            continue
        if scraper == 'reddit':
            config = get_reddit_config()
        elif scraper == 'youtube':
            config = get_youtube_config()
     
        configs.append(config)

    # Run scrapers
    for config in configs:
        run_scraper(config)

if __name__ == '__main__':
    startMenu()
