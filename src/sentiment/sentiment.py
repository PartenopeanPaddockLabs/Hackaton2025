import requests, json, re
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from collections import Counter
import base64
import redis
import time
import os
from dotenv import load_dotenv
from redis.commands.json.path import Path
from wordcloud import WordCloud, STOPWORDS
import nltk
from nltk.corpus import stopwords
from pymongo import MongoClient

#loading of environment variables
load_dotenv()

#Redis Cloud environment variables
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_USERNAME = os.getenv('REDIS_USERNAME')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MONGO_URI = os.getenv('MONGO_CONNECION_STRING')

#Check if all required environment variables are loaded
if not all([REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, GEMINI_API_KEY]):
    print("Error: One or more environment variables were not found.")
    print("Make sure you have created a proper .env file.")
    exit(1)

try:
    #Initialization of Redis Cloud structure with environment variables
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        decode_responses=False
    )
    r.ping() #connection attempt
    print("Connection to Redis in the cloud successfully!")
except redis.exceptions.ConnectionError as e:
    print(f"Redis connection error: {e}")
    print("Make sure the host, port, and password are correct and that the Redis server is accessible.")
    exit(1)

#Pattern storage for Reddit posts and YouTube comments in order to optimize search
REDDIT_KEY_PATTERN = 'reddit:json *'
YOUTUBE_KEY_PATTERN = 'youtube:json*'
#this vector is used by the server to poll itself of incoming elements on Redis that have those patterns
POLLING_KEY_PATTERNS = [REDDIT_KEY_PATTERN, YOUTUBE_KEY_PATTERN]
polling_interval_seconds = 300 #this interval (in seconds) indicates how often the server tries to retrieve data from Redis (in this case, every 5 minutes)

try:
    #MongoDB setup and connection
    client_mongo = MongoClient(MONGO_URI)
    db = client_mongo['F1Hackathon']
    collection = db['SocialData']
    client_mongo.admin.command('ping')
    print("Connection to MongoDB successfull!")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    print("Make sure that the connection URI is correct and that the MongoDB server is accessible.")
    exit(1)


hf_model_name = "tabularisai/multilingual-sentiment-analysis" #here we define the model's name we will use for the sentiment analysis on YouTube
hf_tokenizer = AutoTokenizer.from_pretrained(hf_model_name) #Tokenizer definition: it's useful to convert the human-readbile text into a numeric format
hf_model = AutoModelForSequenceClassification.from_pretrained(hf_model_name) #load the model

# Defines the ordered sentiment labels for clarity
ordered_sentiments = ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"]

def predict_sentiment_youtube(text):
    # Handles cases where no text is provided for sentiment analysis.
    if not text:
        print("No text provided for sentiment analysis.")
        return []
    # Tokenizes the input text, converting it into a format the model can understand.
    # 'return_tensors="pt"' specifies PyTorch tensors.
    # 'truncation=True' truncates text if it exceeds the model's max length.
    # 'padding=True' pads shorter texts to the max length.
    # 'max_length=512' sets the maximum token length.
    inputs = hf_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    # Performs model inference without calculating gradients, which saves memory and speeds up prediction
    with torch.no_grad():
        outputs = hf_model(**inputs)
    # Converts the raw model outputs (logits) into probabilities using the softmax function.
    # Softmax ensures the scores sum to 1, interpretable as probabilities for each sentiment class.
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    # Maps the numerical class indices returned by the model to human-readable sentiment labels
    sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
    return [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]

def predict_sentiment_reddit(text):
    if not text or not text.strip():
        return "Neutral" #Or another default value in case of empty text
    #queries to Gemini to perform sentiment analysis with the same sentiment classes used for YouTube
    query = f"""Analizza il sentiment complessivo del seguente testo, che include un post di Reddit e i suoi commenti.
    Rispondi UNICAMENTE con una delle seguenti etichette, senza ulteriori spiegazioni o testo aggiuntivo:
    "Very Negative", "Negative", "Neutral", "Positive", "Very Positive".

    Testo da analizzare:
    {text}
    """

    try:
        #request via POST to Gemini in which the query is passed
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"contents": [{"parts": [{"text": query}]}]})
        )
        res.raise_for_status() #This line checks if the request was successful
        output = res.json() #This line parses the JSON response from the API and stores it in the output variable 

        # Extract the text response from the Gemini output, handling potential missing keys
        response_text = output.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()

        # Check if the Gemini response contains one of the expected sentiment labels 
        for sentiment_label in ordered_sentiments:
            if sentiment_label in response_text:
                return sentiment_label

        print(f"Notice: Gemini unexpectedly answered '{response_text}'. Assigned 'Neutral'.")
        return "Neutral"

    except requests.exceptions.RequestException as e:
        print(f"Gemini error request: {e}")
        return "Neutral"
    except json.JSONDecodeError as e:
        print(f"Error in JSON parsing of Gemini response: {e}")
        print(f"Raw response: {res.text if 'res' in locals() else 'N/A'}")
        return "Neutral"
    except Exception as e:
        print(f"Generic error during Gemini sentiment prediction: {e}")
        return "Neutral"

def generate_report(texts_for_wordcloud, sentiments_for_report, source_type="General"):
    """
    Generates sentiment analysis reports including bar charts, pie charts, and word clouds.
    
    Args:
        source_type (str): The type of content (e.g., "YouTube", "Reddit") for naming files and titles.
    """
    if not sentiments_for_report:
        print(f"No sentiment data to generate the report {source_type}.")
        return
    #Prepare data for the bar chart
    labels = [f"Item {i+1}" for i in range(len(sentiments_for_report))]
    sentiment_to_index = {s: i for i, s in enumerate(ordered_sentiments)}
    y_values = [sentiment_to_index.get(s, 2) for s in sentiments_for_report]

    # Define colors for sentiment categories
    plt.figure(figsize=(max(10, len(sentiments_for_report) * 0.8), 8)) # Dynamic figure size
    colors = ["darkred", "red", "gray", "lightgreen", "green"]
    bar_colors = [colors[sentiment_to_index.get(s, 2)] for s in sentiments_for_report]

    # Generate Sentiment Bar Chart
    bars = plt.bar(labels, y_values, color=bar_colors)
    plt.yticks(ticks=range(len(ordered_sentiments)), labels=ordered_sentiments)# Set y-axis ticks and labels
    plt.title(f"Sentiment ranked by Content ({source_type})")
    plt.ylabel("Sentiment")
    plt.xlabel(f"Content {source_type}")
    plt.xticks(rotation=45, ha='right', fontsize=8) #Rotate x-axis labels for readability

    # Add sentiment labels on top of the bars
    for bar, sentiment in zip(bars, sentiments_for_report):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), sentiment, ha='center', va='bottom', fontsize=7)

    plt.tight_layout()# Adjust layout to prevent labels from overlapping
    plt.savefig(f"sentiment_class_bar_chart_{source_type}.png")
    plt.close() # Close the plot to free up memory

    # Generate Sentiment Pie Chart
    sentiment_counts = Counter(sentiments_for_report) # Count occurrences of each sentiment
    pie_colors_map = {s: colors[sentiment_to_index.get(s, 2)] for s in sentiment_counts.keys()}
    pie_colors = [pie_colors_map[s] for s in sentiment_counts.keys()]


    plt.figure(figsize=(6, 6))
    plt.pie(sentiment_counts.values(), labels=sentiment_counts.keys(), autopct='%1.1f%%', colors=pie_colors)
    plt.title(f"Distribuzione del Sentiment ({source_type})")
    plt.savefig(f"sentiment_pie_chart_{source_type}.png")
    plt.close()

    # Prepare stopwords for Word Clouds
    my_stopwords = set(STOPWORDS) # Default English stopwords
    # Add stopwords from NLTK for multiple languages
    my_stopwords.update(stopwords.words('english'))
    my_stopwords.update(stopwords.words('italian'))
    my_stopwords.update(stopwords.words('french'))
    my_stopwords.update(stopwords.words('spanish'))
    my_stopwords.update(stopwords.words('german'))
    my_stopwords.update(stopwords.words('portuguese'))

    # Add custom stopwords relevant to the context
    custom_stopwords = {"post", "comment", "reddit", "youtube", "video", "watch", "link", "https", "http"}
    my_stopwords.update(custom_stopwords)

    # Group texts by sentiment for individual word clouds
    all_texts_map = {}
    for t, s in zip(texts_for_wordcloud, sentiments_for_report):
        if s not in all_texts_map:
            all_texts_map[s] = []
        all_texts_map[s].append(t)

    # Generate Word Clouds for each sentiment category
    for sentiment in ordered_sentiments:
        if sentiment in all_texts_map:
            text_concat_for_wc = " ".join(all_texts_map[sentiment])
            if not text_concat_for_wc.strip(): # Skip if no text for this sentiment
                continue
            # Create a WordCloud object
            wc = WordCloud(width=600, height=400, background_color='white', stopwords=my_stopwords).generate(text_concat_for_wc)
            plt.figure(figsize=(6, 4))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title(f"Word Cloud - {sentiment} ({source_type})")
            plt.savefig(f"wordcloud_{sentiment}_{source_type}.png")
            # plt.show()
            plt.close()

def summarizationGemini(source_type="General"):
    """
    Generates a summary of the sentiment analysis reports using the Google Gemini Vision API,
    by sending the generated charts as images.
    
    Args:
        source_type (str): The type of content (e.g., "YouTube", "Reddit") for summary context.
    """
    bar_chart_path = f"sentiment_class_bar_chart_{source_type}.png"
    pie_chart_path = f"sentiment_pie_chart_{source_type}.png"

    try:
        # Encode the generated chart images to base64 for sending to Gemini API
        with open(bar_chart_path, "rb") as istogramma_sentiment:
            istogramma_sentiment_base64 = base64.b64encode(istogramma_sentiment.read()).decode('utf-8')
        with open(pie_chart_path, "rb") as torta_sentiment:
            torta_sentiment_base64 = base64.b64encode(torta_sentiment.read()).decode('utf-8')
        # Define the query for Gemini to summarize the charts
        query = f"""
            Ti fornirò due grafici (a barre e a torta) che mostrano i risultati di un'analisi del sentiment sui contenuti {source_type} relativi al GP di Monaco 2025.
            Il tuo compito è analizzare **esclusivamente** questi grafici e produrre un'analisi **descrittiva e fattuale** dei risultati.
            Il riassunto deve includere:

            1.  **Distribuzione Generale:** Descrivi come si distribuiscono i sentiment (molto negativo, negativo, neutro, positivo, molto positivo), indicando le proporzioni percentuali visibili nel grafico a torta.
            2.  **Sentiment Dominante:** Identifica chiaramente qual è il sentiment più comune e quale il meno comune.
            3.  **Tendenze e Picchi:** Basandoti sul grafico a barre (se applicabile) e sulla torta, evidenzia se ci sono picchi significativi (ad esempio, una predominanza schiacciante di un sentiment o una presenza notevole dei sentimenti estremi 'Very Positive' o 'Very Negative').
            4.  **Insight Fattuali:** Riporta qualsiasi osservazione oggettiva che puoi dedurre **direttamente** dai grafici, senza fare ipotesi esterne o dare consigli. Ad esempio: "Si osserva una polarizzazione se i sentimenti estremi sono alti" oppure "La maggioranza dei contenuti genera reazioni neutrali".

            **IMPORTANTE:** Non includere NESSUN suggerimento, NESSUNA raccomandazione, NESSUN consiglio di marketing o comunicazione e NESSUN piano d'azione. La tua risposta deve essere **solo** un'analisi oggettiva di ciò che i grafici mostrano. La lingua deve essere inglese.
            """
        # Send the request to Gemini Vision API with the query and image data
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"contents": [{"parts": [
                {"text": query},
                {"inline_data": {"mime_type": "image/png", "data": istogramma_sentiment_base64}},
                {"inline_data": {"mime_type": "image/png", "data": torta_sentiment_base64}}
            ]}]})
        )
        res.raise_for_status()
        output = res.json()
        # Extract the summary text from Gemini's response and clean up markdown
        response_extracted_words = output.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        res_new = response_extracted_words.replace("```json", "").replace("```", "")
        print(f"\n--- Gemini summary for {source_type} ---")
        print(res_new)
        print(f"--- End Gemini summary for {source_type} ---\n")
    except FileNotFoundError:
        print(f"Error: Graphics files not found for {source_type}. Make sure reports have been generated before calling Gemini.")
    except requests.exceptions.RequestException as e:
        print(f"Gemini request error for summarization: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Gemini response for summarization: {e}")
    except Exception as e:
        print(f"Generic error during Gemini summarization for {source_type}: {e}")

def process_message(message_data):
    """
    Processes a single message (JSON data) retrieved from Redis.
    Extracts text, determines social media type, performs sentiment analysis,
    and returns the combined text, calculated sentiment, and raw texts for word clouds.
    
    Args:
        message_data (dictionary): The JSON data representing a social media post/comment. 
    """
    content_id = message_data.get('content_id', 'Unknown ID')
    social_media_type = message_data.get('social_media', 'Unknown')
    print(f"\nStart processing for: {content_id} from {social_media_type}")

    combined_text_for_sentiment = "" # Stores text combined for sentiment analysis (e.g., Reddit post + comments)
    texts_for_wordcloud_current_item = []# Stores individual raw texts for detailed word clouds

    if social_media_type == 'YouTube':
        # For YouTube, the primary text is typically the comment itself
        comment_text = message_data.get('comment_raw_text', '')
        if comment_text and isinstance(comment_text, str) and comment_text.strip():
            combined_text_for_sentiment = comment_text
            texts_for_wordcloud_current_item.append(comment_text)
            print(f"YouTube text extracted: '{comment_text[:100]}...'")
            # Call the Hugging Face model for YouTube sentiment
            sentiment_result = predict_sentiment_youtube([combined_text_for_sentiment])[0]
        else:
            print(f"No valid text found for YouTube commentary {content_id}.")
            return None, None, None # Return None if no text to process

    elif social_media_type == 'Reddit':
        # For Reddit, 'comment_raw_text' often refers to the main post text
        post_text = message_data.get('comment_raw_text', '')
        if post_text and isinstance(post_text, str) and post_text.strip():
            combined_text_for_sentiment += post_text
            texts_for_wordcloud_current_item.append(post_text)
            print(f"Reddit post text extracted: '{post_text[:100]}...'")

        # Process nested comments for Reddit posts
        comments = message_data.get('comments', [])
        for comment in comments:
            comment_text = comment.get('comment_raw_text', '')
            if comment_text and isinstance(comment_text, str) and comment_text.strip():
                # Concatenate comments to the main text for overall sentiment analysis
                combined_text_for_sentiment += " commento:" + comment_text
                texts_for_wordcloud_current_item.append(comment_text)
                print(f"Reddit comment text extracted: '{comment_text[:100]}...'")

        if not combined_text_for_sentiment.strip():
            print(f"No valid text (posts or comments) found for Reddit element {content_id}.")
            return None, None, None # Return None if no text to process for Reddit
        print(f"Reddit combined text (post+comments): '{combined_text_for_sentiment[:200]}...'")
        # Call the Gemini model for Reddit sentiment, as it handles longer, combined texts
        sentiment_result = predict_sentiment_reddit(combined_text_for_sentiment)

    else:
        # Handle unrecognized social media types
        print(f"Social media type '{social_media_type}' not recognized for {content_id}.")
        return None, None, None

    return combined_text_for_sentiment, sentiment_result, texts_for_wordcloud_current_item

# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"Consumatore avviato. Ricerca di chiavi JSON con pattern: {', '.join(POLLING_KEY_PATTERNS)}...")

    # Initialize lists to store processed sentiment data and raw texts
    # These lists will accumulate data across multiple polling cycles
    final_youtube_sentiments_data = []
    final_reddit_sentiments_data = []
    all_youtube_raw_texts_for_wc = []
    all_reddit_raw_texts_for_wc = []

    try:
        # The main consumer loop, designed to run indefinitely until interrupted
        while True:
            total_processed_keys_in_cycle = 0 # Counter for keys processed in the current polling cycle
            # Iterate through each defined key pattern (e.g., 'reddit:json*', 'youtube:json*')
            for pattern in POLLING_KEY_PATTERNS: 
                cursor = 0 # Initialize the cursor for the Redis SCAN command
                keys_to_process = [] # List to store keys found in the current scan iteration
                while True:
                    cursor, keys = r.scan(cursor, match=pattern, count=50) # Fetch up to 50 keys at a time
                    keys_to_process.extend(keys) # Add found keys to the list
                    if cursor == 0: # If the cursor returns to 0, it means the scan is complete
                        break

                if keys_to_process:
                    print(f"\nFound {len(keys_to_process)} JSON keys for pattern '{pattern}' to elaborate.")
                    for key_bytes in keys_to_process:
                        key = key_bytes.decode('utf-8') # Decode the key from bytes to a UTF-8 string
                        try:
                            # Retrieve the JSON data associated with the key
                            message_data = r.json().get(key)

                            if message_data:
                                # Process the retrieved message data using the helper function
                                combined_text, sentiment_val, raw_texts_for_wc_current_item = process_message(message_data)

                                if combined_text is not None and sentiment_val is not None:
                                    # If processing was successful, categorize and store the results
                                    if client_mongo:
                                        try:
                                            message_data['sentiment'] = sentiment_val #store the sentiment classification as part of the element

                                            collection.insert_one(message_data) #insert the document into the db
                                            print(f"Document {message_data.get('content_id')} saved on MongoDB.")

                                        except Exception as mongo_error:
                                            print(f"MongoDB saving error: {mongo_error}. The element will not be removed from Redis.")
                                            continue
                                    else:
                                        print("Connection to MongoDB not available. Skip saving.")
                                        continue
                                    # If processing was successful, categorize and store the results
                                    social_media_type = message_data.get('social_media', 'Unknown')
                                    if social_media_type == "YouTube":
                                        final_youtube_sentiments_data.append(sentiment_val)
                                        all_youtube_raw_texts_for_wc.extend(raw_texts_for_wc_current_item)
                                    elif social_media_type == "Reddit":
                                        final_reddit_sentiments_data.append(sentiment_val)
                                        all_reddit_raw_texts_for_wc.extend(raw_texts_for_wc_current_item)

                                    r.delete(key) # Delete the key from Redis after successful processing
                                    total_processed_keys_in_cycle += 1
                                    print(f"Key '{key}' deleted after elaboration.")
                                else:
                                    print(f"No valid data extracted for the key '{key}'. It could be deleted if empty or not valid.")
                            else:
                                print(f"Key '{key}' empty or not found during the GET. Deleting...")
                                r.delete(key) # Delete empty or non-existent keys to clean up
                                total_processed_keys_in_cycle += 1


                        except redis.exceptions.ResponseError as re:
                            print(f"Redis error (likely not JSON) for key '{key}': {re}. The key will not be deleted.")
                        except json.JSONDecodeError:
                            print(f"JSON parsing error for key '{key}'. Invalid content. Key not deleted.")
                        except Exception as e:
                            print(f"Error during processing or deletion of key '{key}': {e}. Key not deleted.")
                else:
                    print(f"No keys with pattern '{pattern}' found in this cycle.")
            
            # --- Polling Logic ---
            # If no new messages were processed in the current cycle, pause for the longer polling interval.
            if total_processed_keys_in_cycle == 0:
                print(f"No new messages processed in this cycle. {polling_interval_seconds} seconds pause...")
                time.sleep(polling_interval_seconds)
            else:
                print(f"\nCycle completed. {total_processed_keys_in_cycle} total messages processed.")
                print("Waiting for next cycle...")
                time.sleep(5) # Short break before re-scanning


    except KeyboardInterrupt:
        # Handle graceful shutdown when the user interrupts the script
        print("\nConsumer halted by user.")
        print("\nFinal reports generating...")

        # Generate and summarize reports for YouTube data if any was collected
        if final_youtube_sentiments_data:
            print("\nFinal report generation and summarization for YouTube...")
            generate_report(all_youtube_raw_texts_for_wc, final_youtube_sentiments_data, "YouTube")
            summarizationGemini("YouTube")
        else:
            print("No YouTube data processed to generate the final report.")

        # Generate and summarize reports for Reddit data if any was collected
        if final_reddit_sentiments_data:
            print("\nFinal report generation and summarization for Reddit...")
            generate_report(all_reddit_raw_texts_for_wc, final_reddit_sentiments_data, "Reddit")
            summarizationGemini("Reddit")
        else:
            print("No Reddit data processed to generate the final report.")

    except Exception as e:
        print(f"Unexpected error within main loop: {e}")
    finally:
        print("Consumer terminated.")
