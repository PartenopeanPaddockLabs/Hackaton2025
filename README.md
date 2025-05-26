# Hackathon Big Data & AI
## Official Challenge: *F1 Social Analytics Engine: extraction, integration and sentiment analysis from the Monaco GP 2025*
### Group: *Parthenopean Paddock Labs*
- **Boccarossa Antonio - a.boccarossa@studenti.unina.it**
- **Brunello Francesco - f.brunello@studenti.unina.it**
- **Bruno Vincenzo Luigi - vincenzol.bruno@studenti.unina.it**
- **Cangiano Salvatore - salva.cangiano@studenti.unina.it**

<img src="https://github.com/user-attachments/assets/e2e09ad7-e84d-4111-8f43-45fdc40c4a24" alt="Team Icon PPL" width="200"/>


## Table of Contents

- [Hackathon Big Data \& AI](#hackathon-big-data--ai)
  - [Official Challenge: *F1 Social Analytics Engine: extraction, integration and sentiment analysis from the Monaco GP 2025*](#official-challenge-f1-social-analytics-engine-extraction-integration-and-sentiment-analysis-from-the-monaco-gp-2025)
    - [Group: *Parthenopean Paddock Labs*](#group-parthenopean-paddock-labs)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Key Features](#key-features)
  - [Architecture](#architecture)
  - [Setup \& Installation](#setup--installation)
  - [Scraping](#scraping)
    - [Execution](#execution)
    - [Module Description](#module-description)
    - [Data Output](#data-output)
  - [Sentiment Analysis](#sentiment-analysis)
    - [Workflow](#workflow)
    - [Execution](#execution-1)
    - [Output](#output)

## Project Structure
The project is organized using the following directory structure:
```
HACKATON2025/
├── data/               # Output CSV files
├── reports/            # Generated reports
├── src/                # Source code
│   ├── ingestion/      # Script to start scraping
│   │   ├── menuScraping.py
│   │   └── ...
│   ├── sentiment/      # Script for sentiment analysis
│   │   ├── sentiment.py
│   │   └── ...
│   │
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
- **Persistent Storage**: Stores processed data and sentiment results in **MongoDB** for long-term access and future analysis.
- **Duplicate Prevention**: Uses Redis sets to track already processed content and avoid re-collecting it.
- **Automated Reporting**: Generates visual reports (charts, word clouds) and textual summaries using Matplotlib and Gemini.

## Architecture
Here is a visual representation of our project's architecture:
![architettura_new2 drawio](https://github.com/user-attachments/assets/2950b8cf-09a3-4ca8-87dd-c87eccd91710)


## Setup & Installation
1. **Clone the Repository**
    ``` Bash
    git clone https://github.com/PartenopeanPaddockLabs/Hackaton2025.git
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

   # MongoDB
   MONGO_CONNECTION_STRING='YOUR_MONGODB_CONNECTION_STRING'
   ```
Ensure a Redis instance and MongoDB instance (local or Atlas) are running and accessible.

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

This section details the core analysis component of the F1 Social Analytics Engine. It processes the data collected from Redis, applies sentiment analysis using different models, and generates insightful reports.

The sentiment analysis module acts as a **consumer process**. It continuously monitors the Redis database for new data entries (posts and comments) fetched by the scraping scripts. Once data is available, it processes it, assigns a sentiment score, and, upon user interruption, generates a comprehensive set of visual and textual reports.

### Workflow
1. **Polling Redis:** The script continuously scans the Redis database every 5 minutes for keys matching the patterns `reddit:json *` and `youtube:json*`.
2. **Data Processing:**
   - For **YouTube** keys, it extracts the comment text.
   - For **Reddit** keys, it extracts the main post text and concatenates it with all its associated comments to preserve context.
3. **Sentiment Assignment:**
   - YouTube texts are passed to the **Hugging Face** model.
   - Reddit combined texts are sent to **Gemini** API.
   - Both models return a sentiment from: "Very Negative", "Negative", "Neutral", "Positive", "Very Positive".
4.  **Saving to MongoDB:** The original data, along with its calculated sentiment score and a timestamp, is saved as a document in the MongoDB collection.
5.  **Data Cleanup:** If the data is successfully saved to MongoDB, its key is deleted from Redis.
4. **Report Generation (on `Ctrl+C`):** When the user stops the script:
   - It aggregates all collected sentiment data.
   - It generates and saves `.png` files for:
     - Sentiment distribution bar charts (per platform).
     - Sentiment distibution pie charts (per platform).
     - Word clouds for each sentiment category (per platform).
   - It sends the bar and pie charts as images to **Gemini (Multimodal)** to obtain a final textual analysis based on the visual data.
   - The textual analysis is printed to the console.

### Execution
To run the sentiment analysis consumer, ensure your `.env` file is correctly configured (especially `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, and `GEMINI_API_KEY`) and that your scraping scripts are running and populating Redis. 

1.  Make sure your virtual environment is activated:
    ```bash
    source venv/bin/activate  # Or venv\Scripts\activate on Windows
    ```
2.  Run the consumer script:
    ```bash
    # if you are in the root path
    python src/sentiment/sentiment.py
    ```
3.  The script will start polling Redis and saving to MongoDB. Let it run for as long as you want to process data.
4.  To stop the script and trigger the report generation, press `Ctrl+C` in your terminal.

### Output
The primary outputs are:
- **Image Files (.png):** Several chart and word cloud images.
- **Console Output:** Real-time processing logs and the final textual analysis generated by Gemini.
- **MongoDB Database:** The primary persistent output, containing all processed data with sentiment scores.


