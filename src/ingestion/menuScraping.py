import sys
from src.utils.utilsMenu import run_scraper, get_reddit_config, get_youtube_config

scrapers = ['reddit', 'youtube']

def startMenu():
    if len(sys.argv) <= 1:
        print("❌ Specifica almeno uno scraper come argomento!")
        print("Esempio: python script.py reddit youtube")
        sys.exit(1)
    
    selected_scrapers = sys.argv[1:]
    
    configs = []
    for scraper in selected_scrapers:
        if scraper not in scrapers:
            print(f"❌ Scraper non valido: {scraper}")
            continue
        if scraper == 'reddit':
            config = get_reddit_config()
        elif scraper == 'youtube':
            config = get_youtube_config()

        
        configs.append(config)

    # Simula l'avvio dei processi
    for config in configs:
        run_scraper(config)

if __name__ == '__main__':
    startMenu()
