import os
from dotenv import load_dotenv
import redis
from redis.commands.json.path import Path


load_dotenv()

#-- Configuration
redis_host = os.getenv("REDIS_HOST", 'localhost')
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_username = os.getenv("REDIS_USERNAME", "default")
redis_password = os.getenv("REDIS_PASSWORD", None)
redis_db = int(os.getenv("REDIS_DB", 0))

processed_ids_key_prefix = "processed_reddit_ids" #per tenere traccia di quelli gia' inviati
processed_ids_key_prefix_y = "processed_youtube_ids"

# Connessione a Redis

try:
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username, # Aggiunto il parametro username
        password=redis_password,
        decode_responses=True # Mantiene le risposte in stringhe Python, utile
    )
    r.ping() # Verifica la connessione
    print(f"Connesso a Redis su {redis_host}:{redis_port}, DB {redis_db}")

    
except redis.exceptions.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}. Assicurati che il server Redis sia in esecuzione e accessibile.")
    print("Controlla host, porta, username e password nel tuo file .env.")
    r = None # Imposta r a None per gestire l'assenza di connessione
except Exception as e:
    print(f"Errore generico durante la connessione a Redis: {e}")
    r = None


def sendDataRedditToRedis(post_data, subreddit_name):
    if r:
        try:
            processed_ids_key=f"{processed_ids_key_prefix}:{subreddit_name}"
            r.json().set(f"reddit:json {post_data['content_id']}", Path.root_path(), post_data)
            r.sadd(processed_ids_key, *[post_data['content_id']])
            print(f"Post {post_data['content_id']} salvato come JSON nativo in Redis.")
        except Exception as e:
            print(f"Errore nell'invio del post a Redis con RedisJSON: {e}")

def checkRedditPostAlreadyElaborated(post_content_id, subreddit_name):
    if r:
        try:
                processed_ids_key = f"{processed_ids_key_prefix}:{subreddit_name}"
                if r.sismember(processed_ids_key, post_content_id):
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error checking post id already elaborated: {e}")
            return False
        
def sendDataYoutubeToRedis(video_id, comment_data):
    if r: 
        try:
            processed_ids_key = f"{processed_ids_key_prefix_y}:{video_id}"
            r.json().set(f"youtube:json{comment_data['content_id']}", Path.root_path(), comment_data)
            r.sadd(processed_ids_key, *[comment_data['content_id']])
            print(f"Youtube Comment {comment_data['content_id']} saved as native Json in Redis.")
        except Exception as e:
            print(f"Error sending comment to Redis: {e}")

def checkYoutubeCommentAlreadyElaborated(video_id, comment_id):
    if r:
        try:
                processed_ids_key = f"{processed_ids_key_prefix_y}:{video_id}"
                if r.sismember(processed_ids_key, comment_id):
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error checking post id already elaborated: {e}")
            return False