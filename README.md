# Hackathon Big Data & AI
## Official Challenge: *F1 Social Analytics Engine: extraction, integration and sentiment analysis from the Monaco GP 2025*
### Group: *Parthenopean Paddock Labs*

<img src="https://github.com/user-attachments/assets/e2e09ad7-e84d-4111-8f43-45fdc40c4a24" alt="Team Icon PPL" width="200"/>

## Table of Contents

* [Project Structure](#project-structure)
* [Key Features](#key-features)
* [Setup & Installation](#setup--installation)
* [Scraping](#scraping)
    * [Execution](#execution)
    * [Module Description](#module-description)
    * [Data Output](#data-output)
* [Sentiment Analysis](#sentiment-analysis)

## Project Structure
The project is organized using the following directory structure:
```
HACKATON2025/
├── data/               # Output CSV files
├── reports/            # Generated reports
├── src/                # Source code
│   ├── ingestion/      # Scripts to start scraping
│   │   ├── menuScraping.py
│   │   └── ...
│   ├── sentiment/      # Scripts for sentiment analysis
│   │   └── README.md
│   └── utils/          # Utility modules (scrapers, Redis, etc.)
│       ├── scraperReddit.py
│       ├── scraperYoutube.py
│       ├── utilsMenu.py
│       ├── utilsReddit.py
│       ├── utilsRedis.py
│       ├── utilsYoutube.py
│       └── ...
├── venv/               # Python virtual environment
└── .env                # Environment variables file (credentials)
```

## Key Features
- **Multi-Platform Scraping**: Collects data from:
    - Reddit (posts and comments)
    - YouTube (video comments)
- **Flexible Scraping Configuration**: Allows the user to specify:
    - Platforms to scrape.
    - Search topics/queries.
    - Number of posts/videos and comments to collect.
    - Scraping frequency
- **Data Storage**:
    - Saves data in CSV format in the data/ directory, handling duplicates.
    - Saves data in Redis as native JSON objects, including a nested structure for Reddit posts and comments.
- **Duplicate Prevention**: Uses Redis sets to track already processed content and avoid re-collecting it.

## Setup & Installation
1. **Clone the Repository**
    ``` Bash
    git clone < >
    cd HACKATON2025
    ```
2. **Create and Activate the Virtual Environment**
   ``` Bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ``` Bash
   pip install -r requirements.txt
   ```
4. **Configure Credentials**: Create a `.env` file in the root directory and add the following variables:
   ``` Code snippet
   # Reddit
   CLIENT_ID='YOUR_REDDIT_CLIENT_ID'
   CLIENT_SECRET='YOUR_REDDIT_CLIENT_SECRET'
   USER_AGENT='YOUR_USER_AGENT'

   # YouTube
   YOUTUBE_API_KEY='YOUR_YOUTUBE_API_KEY'

   # Redis
   REDIS_HOST='YOUR_REDIS_HOST_ID'
   REDIS_PORT='YOUR_PORT_ID'
   REDIS_USERNAME='YOUR_REDIS_USERNAME_ID'
   REDIS_PASSWORD='YOUR_REDIS_PASSWORD_ID'

   # Gemini
   GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
   ```
Ensure a Redis instance is running and accessible
## Scraping
### Execution
To start scraping, run the `menuScraping.py` script from the root directory, specifying which scrapers to launch as command-line arguments.

**Example**: To start both the Reddit and YouTube scrapers:
``` Bash
python -m src.ingestion.menuScraping reddit youtube
```
You will then be guided by interactive prompts to enter the configuration details for each selected scraper (topics, limits, frequency).

### Module Description
- `src/ingestion/menuScraping.py`: Main entry point. Handles command-line arguments and starts the interactive menu.
- `src/utils/utilsMenu.py`: Manages user interaction for configuration and launches the scraping processes.
- `src/utils/scraperReddit.py`: Contains the main loop for continuous scraping from Reddit.
- `src/utils/scraperYoutube.py`: Contains the main loop for continuous scraping from YouTube.
- `src/utils/utilsReddit.py`: Implements the specific logic for scraping from Reddit (using `praw`), data cleaning, and sending to Redis/CSV.
- `src/utils/utilsYoutube.py`: Implements the specific logic for scraping from YouTube (using `googleapiclient`), data cleaning, and sending to Redis/CSV.
- `src/utils/utilsRedis.py`: Handles all interactions with the Redis database, including connection, data saving, and duplicate checking.

### Data Output
- **CSV**: CSV files are saved in `data/` directory, named like `reddit_data_SUBREDDIT_NAME.csv` and `youtube_data_QUERY.csv`. These files are updated, and duplicates are removed with each scraping cycle.
- **Redis**: Data is saved in Redis using specific keys (e.g., `reddit:json:POST_ID`, `youtube:json:COMMENT_ID`). The IDs of processed posts/comments are stored in Redis sets to prevent reprocessing.

## Sentiment Analysis

