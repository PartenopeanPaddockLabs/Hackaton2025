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

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_USERNAME = os.getenv('REDIS_USERNAME')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MONGO_URI = os.getenv('MONGO_CONNECION_STRING')


if not all([REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, GEMINI_API_KEY]):
    print("Errore: Una o più variabili d'ambiente non sono state trovate.")
    print("Assicurati di aver creato un file .env corretto.")
    exit(1)

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        decode_responses=False
    )
    r.ping()
    print("Connesso a Redis nel cloud con successo!")
except redis.exceptions.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    print("Assicurati che l'host, la porta e la password siano corretti e che il server Redis sia accessibile.")
    exit(1)

REDDIT_KEY_PATTERN = 'reddit:json *'
YOUTUBE_KEY_PATTERN = 'youtube:json*'
POLLING_KEY_PATTERNS = [REDDIT_KEY_PATTERN, YOUTUBE_KEY_PATTERN]
polling_interval_seconds = 300 #ogni 5 minuti il server prova a fetchare dati

try:
    client_mongo = MongoClient(MONGO_URI)
    db = client_mongo['F1Hackathon']
    collection = db['SocialData']
    client_mongo.admin.command('ping')
    print("Connesso a MongoDB con successo!")
except Exception as e:
    print(f"Errore di connessione a MongoDB: {e}")
    print("Assicurati che l'URI di connessione sia corretto e che il server MongoDB sia accessibile.")
    exit(1)


hf_model_name = "tabularisai/multilingual-sentiment-analysis"
hf_tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
hf_model = AutoModelForSequenceClassification.from_pretrained(hf_model_name)

ordered_sentiments = ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"]

def predict_sentiment_youtube(text):
    if not text:
        print("Nessun testo fornito per l'analisi del sentiment.")
        return []
    inputs = hf_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = hf_model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
    return [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]

def predict_sentiment_reddit(text):
    if not text or not text.strip():
        return "Neutral" # O un altro valore di default in caso di testo vuoto

    query = f"""Analizza il sentiment complessivo del seguente testo, che include un post di Reddit e i suoi commenti.
    Rispondi UNICAMENTE con una delle seguenti etichette, senza ulteriori spiegazioni o testo aggiuntivo:
    "Very Negative", "Negative", "Neutral", "Positive", "Very Positive".

    Testo da analizzare:
    {text}
    """

    try:
        # Usa la variabile api_key caricata dall'ambiente
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"contents": [{"parts": [{"text": query}]}]})
        )
        res.raise_for_status()
        output = res.json()

        response_text = output.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()

        for sentiment_label in ordered_sentiments:
            if sentiment_label in response_text:
                return sentiment_label

        print(f"Avviso: Gemini ha risposto inaspettatamente '{response_text}'. Assegnato 'Neutral'.")
        return "Neutral"

    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta Gemini: {e}")
        return "Neutral"
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing JSON della risposta Gemini: {e}")
        print(f"Risposta raw: {res.text if 'res' in locals() else 'N/A'}")
        return "Neutral"
    except Exception as e:
        print(f"Errore generico durante la previsione sentiment di Gemini: {e}")
        return "Neutral"

def generate_report(texts_for_wordcloud, sentiments_for_report, source_type="General"):

    if not sentiments_for_report:
        print(f"Nessun dato di sentiment per generare il report {source_type}.")
        return

    labels = [f"Item {i+1}" for i in range(len(sentiments_for_report))]
    sentiment_to_index = {s: i for i, s in enumerate(ordered_sentiments)}
    y_values = [sentiment_to_index.get(s, 2) for s in sentiments_for_report]

    plt.figure(figsize=(max(10, len(sentiments_for_report) * 0.8), 8))
    colors = ["darkred", "red", "gray", "lightgreen", "green"]
    bar_colors = [colors[sentiment_to_index.get(s, 2)] for s in sentiments_for_report]

    bars = plt.bar(labels, y_values, color=bar_colors)
    plt.yticks(ticks=range(len(ordered_sentiments)), labels=ordered_sentiments)
    plt.title(f"Sentiment Classificato per Contenuti ({source_type})")
    plt.ylabel("Sentiment")
    plt.xlabel(f"Contenuto {source_type}")
    plt.xticks(rotation=45, ha='right', fontsize=8)

    for bar, sentiment in zip(bars, sentiments_for_report):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), sentiment, ha='center', va='bottom', fontsize=7)

    plt.tight_layout()
    plt.savefig(f"sentiment_class_bar_chart_{source_type}.png")
    # plt.show()
    plt.close()

    sentiment_counts = Counter(sentiments_for_report)
    pie_colors_map = {s: colors[sentiment_to_index.get(s, 2)] for s in sentiment_counts.keys()}
    pie_colors = [pie_colors_map[s] for s in sentiment_counts.keys()]


    plt.figure(figsize=(6, 6))
    plt.pie(sentiment_counts.values(), labels=sentiment_counts.keys(), autopct='%1.1f%%', colors=pie_colors)
    plt.title(f"Distribuzione del Sentiment ({source_type})")
    plt.savefig(f"sentiment_pie_chart_{source_type}.png")
    # plt.show()
    plt.close()

    my_stopwords = set(STOPWORDS)
    my_stopwords.update(stopwords.words('english'))
    my_stopwords.update(stopwords.words('italian'))
    my_stopwords.update(stopwords.words('french'))
    my_stopwords.update(stopwords.words('spanish'))
    my_stopwords.update(stopwords.words('german'))
    my_stopwords.update(stopwords.words('portuguese'))

    custom_stopwords = {"post", "comment", "reddit", "youtube", "video", "watch", "link", "https", "http"}
    my_stopwords.update(custom_stopwords)

    all_texts_map = {}
    for t, s in zip(texts_for_wordcloud, sentiments_for_report):
        if s not in all_texts_map:
            all_texts_map[s] = []
        all_texts_map[s].append(t)

    for sentiment in ordered_sentiments:
        if sentiment in all_texts_map:
            text_concat_for_wc = " ".join(all_texts_map[sentiment])
            if not text_concat_for_wc.strip():
                continue
            wc = WordCloud(width=600, height=400, background_color='white', stopwords=my_stopwords).generate(text_concat_for_wc)
            plt.figure(figsize=(6, 4))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title(f"Word Cloud - {sentiment} ({source_type})")
            plt.savefig(f"wordcloud_{sentiment}_{source_type}.png")
            # plt.show()
            plt.close()

def summarizationGemini(source_type="General"):

    bar_chart_path = f"sentiment_class_bar_chart_{source_type}.png"
    pie_chart_path = f"sentiment_pie_chart_{source_type}.png"

    try:
        with open(bar_chart_path, "rb") as istogramma_sentiment:
            istogramma_sentiment_base64 = base64.b64encode(istogramma_sentiment.read()).decode('utf-8')
        with open(pie_chart_path, "rb") as torta_sentiment:
            torta_sentiment_base64 = base64.b64encode(torta_sentiment.read()).decode('utf-8')

        query = f"""
            Ti fornirò due grafici (a barre e a torta) che mostrano i risultati di un'analisi del sentiment sui contenuti {source_type} relativi al GP di Monaco 2025.
            Il tuo compito è analizzare **esclusivamente** questi grafici e produrre un'analisi **descrittiva e fattuale** dei risultati.
            Il riassunto deve includere:

            1.  **Distribuzione Generale:** Descrivi come si distribuiscono i sentiment (molto negativo, negativo, neutro, positivo, molto positivo), indicando le proporzioni percentuali visibili nel grafico a torta.
            2.  **Sentiment Dominante:** Identifica chiaramente qual è il sentiment più comune e quale il meno comune.
            3.  **Tendenze e Picchi:** Basandoti sul grafico a barre (se applicabile) e sulla torta, evidenzia se ci sono picchi significativi (ad esempio, una predominanza schiacciante di un sentiment o una presenza notevole dei sentimenti estremi 'Very Positive' o 'Very Negative').
            4.  **Insight Fattuali:** Riporta qualsiasi osservazione oggettiva che puoi dedurre **direttamente** dai grafici, senza fare ipotesi esterne o dare consigli. Ad esempio: "Si osserva una polarizzazione se i sentimenti estremi sono alti" oppure "La maggioranza dei contenuti genera reazioni neutrali".

            **IMPORTANTE:** Non includere NESSUN suggerimento, NESSUNA raccomandazione, NESSUN consiglio di marketing o comunicazione e NESSUN piano d'azione. La tua risposta deve essere **solo** un'analisi oggettiva di ciò che i grafici mostrano.
            """
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
        response_extracted_words = output.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        res_new = response_extracted_words.replace("```json", "").replace("```", "")
        print(f"\n--- Riassunto Gemini per {source_type} ---")
        print(res_new)
        print(f"--- Fine Riassunto Gemini per {source_type} ---\n")
    except FileNotFoundError:
        print(f"Errore: File grafici non trovati per {source_type}. Assicurati che i report siano stati generati prima di chiamare Gemini.")
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta Gemini per la summarization: {e}")
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing JSON della risposta Gemini per la summarization: {e}")
    except Exception as e:
        print(f"Errore generico durante la summarization Gemini per {source_type}: {e}")

def process_message(message_data):
    """
    Elabora un singolo messaggio da Redis e restituisce il testo combinato/originale,
    il sentiment calcolato e la lista di testi raw per le WordCloud.
    """

    content_id = message_data.get('content_id', 'Unknown ID')
    social_media_type = message_data.get('social_media', 'Unknown')
    print(f"\nInizio elaborazione per: {content_id} da {social_media_type}")

    combined_text_for_sentiment = ""
    texts_for_wordcloud_current_item = []

    if social_media_type == 'YouTube':
        comment_text = message_data.get('comment_raw_text', '')
        if comment_text and isinstance(comment_text, str) and comment_text.strip():
            combined_text_for_sentiment = comment_text
            texts_for_wordcloud_current_item.append(comment_text)
            print(f"Estratto testo YouTube: '{comment_text[:100]}...'")
            sentiment_result = predict_sentiment_youtube([combined_text_for_sentiment])[0]
        else:
            print(f"Nessun testo valido trovato per il commento YouTube {content_id}.")
            return None, None, None

    elif social_media_type == 'Reddit':
        post_text = message_data.get('comment_raw_text', '')
        if post_text and isinstance(post_text, str) and post_text.strip():
            combined_text_for_sentiment += post_text
            texts_for_wordcloud_current_item.append(post_text)
            print(f"Estratto testo Post Reddit: '{post_text[:100]}...'")

        comments = message_data.get('comments', [])
        for comment in comments:
            comment_text = comment.get('comment_raw_text', '')
            if comment_text and isinstance(comment_text, str) and comment_text.strip():
                combined_text_for_sentiment += " commento:" + comment_text
                texts_for_wordcloud_current_item.append(comment_text)
                print(f"Estratto testo Commento Reddit: '{comment_text[:100]}...'")

        if not combined_text_for_sentiment.strip():
            print(f"Nessun testo valido (post o commenti) trovato per l'elemento Reddit {content_id}.")
            return None, None, None
        print(f"Testo combinato Reddit (post+commenti): '{combined_text_for_sentiment[:200]}...'")
        sentiment_result = predict_sentiment_reddit(combined_text_for_sentiment)

    else:
        print(f"Tipo di social media '{social_media_type}' non riconosciuto per {content_id}.")
        return None, None, None

    return combined_text_for_sentiment, sentiment_result, texts_for_wordcloud_current_item

if __name__ == "__main__":
    print(f"Consumatore avviato. Ricerca di chiavi JSON con pattern: {', '.join(POLLING_KEY_PATTERNS)}...")

    final_youtube_sentiments_data = []
    final_reddit_sentiments_data = []
    all_youtube_raw_texts_for_wc = []
    all_reddit_raw_texts_for_wc = []

    try:
        while True:
            total_processed_keys_in_cycle = 0
            for pattern in POLLING_KEY_PATTERNS:
                cursor = 0
                keys_to_process = []
                while True:
                    cursor, keys = r.scan(cursor, match=pattern, count=50)
                    keys_to_process.extend(keys)
                    if cursor == 0:
                        break

                if keys_to_process:
                    print(f"\nTrovate {len(keys_to_process)} chiavi JSON per il pattern '{pattern}' da elaborare.")
                    for key_bytes in keys_to_process:
                        key = key_bytes.decode('utf-8')
                        try:
                            # Usa r.json().get() correttamente
                            message_data = r.json().get(key) # Non serve Path.root_path() qui

                            if message_data:
                                combined_text, sentiment_val, raw_texts_for_wc_current_item = process_message(message_data)

                                if combined_text is not None and sentiment_val is not None:

                                    if client_mongo:
                                        try:
                                            message_data['sentiment'] = sentiment_val

                                            collection.insert_one(message_data)
                                            print(f"Documento {message_data.get('content_id')} salvato su MongoDB.")

                                        except Exception as mongo_error:
                                            print(f"Errore durante il salvataggio su MongoDB: {mongo_error}. Il dato non sarà eliminato da Redis.")
                                            continue
                                    else:
                                        print("Connessione a MongoDB non disponibile. Salto salvataggio.")
                                        continue


                                    social_media_type = message_data.get('social_media', 'Unknown')
                                    if social_media_type == "YouTube":
                                        final_youtube_sentiments_data.append(sentiment_val)
                                        all_youtube_raw_texts_for_wc.extend(raw_texts_for_wc_current_item)
                                    elif social_media_type == "Reddit":
                                        final_reddit_sentiments_data.append(sentiment_val)
                                        all_reddit_raw_texts_for_wc.extend(raw_texts_for_wc_current_item)

                                    r.delete(key)
                                    total_processed_keys_in_cycle += 1
                                    print(f"Chiave '{key}' eliminata dopo l'elaborazione.")
                                else:
                                    print(f"Nessun dato valido estratto per la chiave '{key}'. Potrebbe essere eliminata se vuota o non valida.")

                            else:
                                print(f"Chiave '{key}' vuota o non trovata durante il GET. Eliminazione...")
                                r.delete(key)
                                total_processed_keys_in_cycle += 1


                        except redis.exceptions.ResponseError as re:
                            print(f"Errore Redis (prob. non è JSON) per la chiave '{key}': {re}. La chiave non sarà eliminata.")
                        except json.JSONDecodeError:
                            print(f"Errore nel parsing JSON per la chiave '{key}'. Contenuto non valido. Chiave non eliminata.")
                        except Exception as e:
                            print(f"Errore durante l'elaborazione o eliminazione della chiave '{key}': {e}. Chiave non eliminata.")
                else:
                    print(f"Nessuna chiave con pattern '{pattern}' trovata in questo ciclo.")

            if total_processed_keys_in_cycle == 0:
                print(f"Nessun nuovo messaggio elaborato in questo ciclo. Pausa di {polling_interval_seconds} secondi...")
                time.sleep(polling_interval_seconds)
            else:
                print(f"\nCiclo completato. Elaborati {total_processed_keys_in_cycle} messaggi totali.")
                print("In attesa del prossimo ciclo...")
                time.sleep(5) # Piccola pausa prima di scansionare di nuovo


    except KeyboardInterrupt:
        print("\nConsumatore interrotto dall'utente.")
        print("\nGenerazione dei report finali...")

        if final_youtube_sentiments_data:
            print("\nGenerazione report finale e summarization per Youtube...")
            generate_report(all_youtube_raw_texts_for_wc, final_youtube_sentiments_data, "YouTube")
            summarizationGemini("YouTube")
        else:
            print("Nessun dato YouTube elaborato per generare il report finale.")

        if final_reddit_sentiments_data:
            print("\nGenerazione report finale e summarization per Reddit...")
            generate_report(all_reddit_raw_texts_for_wc, final_reddit_sentiments_data, "Reddit")
            summarizationGemini("Reddit")
        else:
            print("Nessun dato Reddit elaborato per generare il report finale.")

    except Exception as e:
        print(f"Errore inaspettato nel loop principale: {e}")
    finally:
        print("Consumatore terminato.")
