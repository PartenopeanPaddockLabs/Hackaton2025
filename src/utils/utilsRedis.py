import os
from dotenv import load_dotenv
import redis
from redis.commands.json.path import Path


load_dotenv()

#-- Configuration and connection to Redis --#
redis_host = os.getenv("REDIS_HOST", 'localhost')
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_username = os.getenv("REDIS_USERNAME", "default")
redis_password = os.getenv("REDIS_PASSWORD", None)
redis_db = int(os.getenv("REDIS_DB", 0))

processed_ids_key_prefix = "processed_reddit_ids" 
processed_ids_key_prefix_y = "processed_youtube_ids"


try:
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username, 
        password=redis_password,
        decode_responses=True 
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
#-- Configuration and connection to Redis --#


"""
sendDataRedditToRedis
This function takes the dictionary created and sends it to Redis in a Key-JSON stream. 


Args:
    post_data: the principal structure to send, the document with the principal features of posts and comment scraped 
    subreddit_name: the name of the specific scraped subreddit

"""
def sendDataRedditToRedis(post_data, subreddit_name):
    if r:
        try:
            processed_ids_key=f"{processed_ids_key_prefix}:{subreddit_name}"
            r.json().set(f"reddit:json {post_data['content_id']}", Path.root_path(), post_data)
            r.sadd(processed_ids_key, *[post_data['content_id']])
            print(f"Post {post_data['content_id']} salvato come JSON nativo in Redis.")
        except Exception as e:
            print(f"Errore nell'invio del post a Redis con RedisJSON: {e}")



"""
checkRedditPostAlreadyElaborated
This function checks if the post scraped from Reddit is already scraped or not.


Args:
    post_content_id: the id of the considered post
    subreddit_name: the name of the specific scraped subreddit

"""
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
        

"""
sendDataYoutubeToRedis
This function takes the dictionary created and sends it to Redis in a Key-JSON stream. 

Args:
    video_id: the id of the video considered
    comment_data: the principal structure to send, the document with the principal features of comments scraped

"""
def sendDataYoutubeToRedis(video_id, comment_data):
    if r: 
        try:
            processed_ids_key = f"{processed_ids_key_prefix_y}:{video_id}"
            r.json().set(f"youtube:json{comment_data['content_id']}", Path.root_path(), comment_data)
            r.sadd(processed_ids_key, *[comment_data['content_id']])
            print(f"Youtube Comment {comment_data['content_id']} saved as native Json in Redis.")
        except Exception as e:
            print(f"Error sending comment to Redis: {e}")


"""
checkYoutubeCommentAlreadyElaborated
This function checks if the video scraped from Youtube is already scraped or not.


Args:
    video_id: the id of the considered post
    comment_id: the id of the considered comment 

"""
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