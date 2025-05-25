import redis
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone # Per la deprecation warning

# Carica le variabili d'ambiente
load_dotenv()

# --- Configurazione Redis ------
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_username = os.getenv("REDIS_USERNAME", "default")
redis_password = os.getenv("REDIS_PASSWORD", "fzkLaeEt7D4yqo9xH6RonOyXAedAJNYm")
#redis_username = "default"
#redis_password = "fzkLaeEt7D4yqo9xH6RonOyXAedAJNYm"
redis_db = int(os.getenv("REDIS_DB", 0))

print(f"DEBUG: REDIS_HOST={redis_host}")
print(f"DEBUG: REDIS_PORT={redis_port}")
print(f"DEBUG: REDIS_USERNAME={redis_username}")
print(f"DEBUG: REDIS_PASSWORD={redis_password}") # Stampa con cautela, non in produzione!
print(f"DEBUG: REDIS_DB={redis_db}")

# Nome della Redis Stream da cui consumeremo
REDDIT_STREAM_NAME = "reddit_data_stream"
# Nome del Consumer Group. Tutti i consumatori che fanno parte di questo gruppo
# collaboreranno per processare i messaggi della stream.
CONSUMER_GROUP_NAME = "sentiment_analysis_group"
# Nome di questo specifico consumatore all'interno del gruppo.
# Può essere dinamico se hai più istanze.
CONSUMER_NAME = "consumer_instance_1"

# --- Connessione a Redis ------
try:
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username,
        password=redis_password,
        decode_responses=True # Decodifica automaticamente le risposte da byte a stringhe
    )
    r.ping()
    print(f"Consumatore: Connesso a Redis su {redis_host}:{redis_port}, DB {redis_db}")
except redis.exceptions.ConnectionError as e:
    print(f"Consumatore: Errore di connessione a Redis: {e}.")
    print("Assicurati che il server Redis sia in esecuzione e accessibile. Esco.")
    exit(1) # Esci se non riusciamo a connetterci
except Exception as e:
    print(f"Consumatore: Errore generico durante la connessione a Redis: {e}")
    exit(1)

# --- Inizializzazione del Consumer Group ---
# XGROUP CREATE stream_name group_name ID (crea il gruppo se non esiste)
# Il '$' significa iniziare a leggere solo i nuovi messaggi che arrivano dopo la creazione del gruppo.
# Se vuoi leggere tutti i messaggi esistenti, usa '0'.
try:
    r.xgroup_create(REDDIT_STREAM_NAME, CONSUMER_GROUP_NAME, id='0', mkstream=True)
    print(f"Consumatore: Consumer Group '{CONSUMER_GROUP_NAME}' creato o già esistente.")
except redis.exceptions.ResponseError as e:
    # Se il gruppo esiste già, riceveremo un errore, che possiamo ignorare.
    if "BUSYGROUP" in str(e):
        print(f"Consumatore: Consumer Group '{CONSUMER_GROUP_NAME}' esiste già. Connessione al gruppo.")
    else:
        print(f"Consumatore: Errore nella creazione/connessione del Consumer Group: {e}")
        exit(1)

# --- Funzione per processare un singolo messaggio ---
def process_message(message_id, message_data):
    """
    Simula l'analisi del sentiment e salva i dati.
    """
    print(f"\n--- Processando Messaggio ID: {message_id} ---")
    
    # I dati letti dalla stream sono dizionari, ma i valori che erano liste/dizionari
    # sono ora stringhe JSON e vanno decodificati.
    processed_data = {}
    for key, value in message_data.items():
        try:
            # Tenta di decodificare come JSON, altrimenti usa il valore così com'è.
            processed_data[key] = json.loads(value)
        except json.JSONDecodeError:
            processed_data[key] = value
        except TypeError: # Gestisce il caso in cui value sia None o non una stringa
            processed_data[key] = value

    print(f"Tipo di Contenuto: {processed_data.get('content_type')}")
    print(f"Utente: {processed_data.get('user')}")
    print(f"Testo: {processed_data.get('comment_raw_text')[:100]}...") # Prime 100 car.
    print(f"Emoji: {processed_data.get('emoji')}")
    
    # --- SIMULAZIONE ANALISI SENTIMENT ---
    # Qui potresti integrare la tua logica di analisi del sentiment
    sentiment_score = 0.5 # Esempio di score
    sentiment_label = "neutro" # Esempio di label

    # Aggiungi i risultati dell'analisi al dizionario
    processed_data['sentiment_score'] = sentiment_score
    processed_data['sentiment_label'] = sentiment_label

    print(f"Sentiment Score: {sentiment_score}")
    print(f"Sentiment Label: {sentiment_label}")

    # --- SALVATAGGIO DEI DATI (Simulato) ---
    # In un'applicazione reale, qui salveresti processed_data in un database
    # come PostgreSQL, MongoDB, un data warehouse, ecc.
    print(f"Simulazione salvataggio nel database finale...")
    
    # Aggiornamento per evitare DeprecationWarning
    # publish_date_iso = datetime.utcfromtimestamp(int(processed_data['publish_date'])).replace(tzinfo=pytz.utc).isoformat()
    # Se publish_date è già una stringa ISO, non serve convertirla di nuovo.
    # Se fosse un timestamp numerico:
    # publish_date_obj = datetime.fromtimestamp(float(processed_data['publish_date']), tz=timezone.utc)
    # print(f"Data di Pubblicazione: {publish_date_obj.isoformat()}")

    print("Messaggio processato con successo.")


# --- Ciclo di Consumo ---
def start_consuming():
    print(f"\nConsumatore: In attesa di messaggi sulla stream '{REDDIT_STREAM_NAME}'...")
    last_id = '0' # Per iniziare a leggere da inizio stream (o '$' per nuovi messaggi)
    
    while True:
        try:
            # XREADGROUP GROUP group_name consumer_name COUNT count BLOCK milliseconds STREAMS stream_name ID
            # Blocca per un massimo di 1000ms (1 secondo) se non ci sono messaggi.
            # Questo evita un polling continuo della CPU.
            messages = r.xreadgroup(
                groupname=CONSUMER_GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={REDDIT_STREAM_NAME: '>'}, # '>' indica che vogliamo solo i nuovi messaggi non ancora processati
                count=10, # Leggiamo fino a 10 messaggi alla volta
                block=1000 # Blocca per 1000ms se non ci sono messaggi
            )

            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        process_message(message_id, message_data)
                        
                        # --- RICONOSCIMENTO (ACK) DEL MESSAGGIO ---
                        # XACK stream_name group_name ID
                        # Questo dice a Redis: "Ho processato questo messaggio, non darmelo più".
                        r.xack(REDDIT_STREAM_NAME, CONSUMER_GROUP_NAME, message_id)
                        print(f"Consumatore: Messaggio ID {message_id} riconosciuto (ACK).")
            else:
                print("Consumatore: Nessun nuovo messaggio. In attesa...")

        except redis.exceptions.ConnectionError as e:
            print(f"Consumatore: Disconnesso da Redis. Riprovo in 5 secondi... Errore: {e}")
            time.sleep(5) # Attendiamo prima di riprovare
        except Exception as e:
            print(f"Consumatore: Errore durante il consumo dei messaggi: {e}")
            # Potresti aggiungere qui una logica per gestire messaggi "malformati" o in errore
            # Ad esempio, spostarli in una "dead letter queue" o registrare l'errore.
            time.sleep(1) # Breve pausa per evitare loop infiniti su errori
            

if __name__ == "__main__":
    import time # Importa time per la pausa
    start_consuming()