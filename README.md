# 🧠 Hackathon Big Data & AI  
## Challenge Ufficiale 🚀  
**"F1 Social Analytics Engine: estrazione, integrazione e sentiment analysis dal GP di Monaco 2025"**

---
## Indice

- [🏁 Obiettivo](#-obiettivo)
- [📥 Fase 1 — Data Ingestion and Dataset Building](#-fase-1---data-ingestion-and-dataset-building)
    - [📇 Schema dataset finale](#-schema-dataset-finale)
- [📥 Fase 2 — Social Analysis](#-fase-2---social-analysis)
    - [🎯 Obiettivo della parte di Social Analysis](#-obiettivo-della-parte-di-social-analysis)
    - [✨ Bonus: Estensione LLM-based - Creazione automatica dei report](#-bonus-estensione-llm-based---generatione-automatica-dei-report)
- [📦 Modalità di consegna](#-modalità-di-consegna)
- [📜 Metriche di Valutazione e Punteggi](#-metriche-di-valutazione-e-punteggi)
- [1️⃣ Inizializzazione progetto](#-inizializzazione-progetto)
- [🕒 Timeline](#-timeline)

---

## 🏁 Obiettivo 

In occasione del Gran Premio di Monaco 2025, uno degli eventi più iconici e seguiti della Formula 1, il vostro compito è progettare e realizzare un sistema intelligente che recupera, integra e analizza post e commenti provenienti dai social media, per comprendere come gli utenti vivono l’evento prima, durante e dopo la gara.

L'obiettivo è cogliere le emozioni, le opinioni e le reazioni degli appassionati di motori sparsi in tutto il mondo, offrendo un quadro dinamico e aggiornato in tempo reale su come il pubblico percepisce i piloti, le scuderie, i momenti salienti e gli episodi controversi della gara. Sarà anche importante profilare il tipo di spettatori e/o di appassionati dell'evento estraendo caratteristiche comuni a gruppi di utenti simili.

Questa sfida ha due anime principali:

- **Data ingestion & dataset building (fondamentale!)**
- **Social analysis avanzata (con o senza LLM)**

---


## 📥 Fase 1 - Data Ingestion and Dataset Building

Progettare e implementare una pipeline di data ingestion che:

- 🔍 Recupera in modo automatico (o semi-automatico) contenuti testuali da diversi social media: Instagram, Facebook, Twitter/X, Reddit, YouTube (ma anche altri non in lista che pensate possano essere significativi). (Le analisi cross-platform sono ben gradite 🤗)

- 🧹 Pulisce, filtra e normalizza i dati testuali, le interazioni e i metadati.

- 📦 Produce un dataset finale conforme a uno schema comune condiviso da tutti i gruppi (vedi sotto).


📜 NOTA
- _Il linguaggio ufficiale è l'Inglese ovviamente, ma i più coraggiosi possono provare a fare analisi multilingua (gestendo anche il Francese ad esempio)_

---

### 📇 Schema dataset finale:

Di seguito lo schema che dovrà seguire il Dataset ottenuto a valle della prima fase.

| Feature           | Descrizione                                                                 | Datatype             | Nullable | Note                                        | Esempio                  |
|-------------------|-----------------------------------------------------------------------------|----------------------|----------|---------------------------------------------|--------------------------|
| content_id        | ID univoco del post o commento                                              | stringa              | No       | es. ID nativo social o hash generato        | fb_post_001              |
| observation_time  | Timestamp di un’osservazione di uno specifico contenuto                     | datetime (ISO 8601)  | No       | formato: YYYY-MM-DDTHH:MM:SSZ                | 2025-05-15T10:00:00Z     |
| user              | ID o nome utente (anonimizzato se necessario)                              | stringa              | No       |                                             | giulia_snap              |
| user_location     | Città/Stato indicati nel profilo dell’utente (se presente)                  | stringa              | Si       |                                             | Nizza                    |
| social_media      | Nome della piattaforma (es. Twitter, Reddit, etc.)                          | stringa              | No       |                                             | Instagram                |
| publish_date      | Timestamp UTC del post/commento                                             | datetime (ISO 8601)  | No       | formato: YYYY-MM-DDTHH:MM:SSZ                | 2025-05-25T19:45:10Z     |
| geo_location      | Coordinate GPS (latitudine, longitudine) del luogo dell’interazione         | tuple(float, float)  | Si       |                                             | (45.4642, 9.1900)        |
| comment_raw_text  | Testo originale del contenuto                                               | stringa              | No       | Se non c’è testo, mettere stringa vuota ""  | Corsa Pazzesca 😬🏎️       |
| emoji             | Emoji utilizzate nel testo                                                  | Lista[stringa]       | Si       |                                             | 😬🏎️                      |
| reference_post_url| Link al post originale (se è una risposta/commento)                        | stringa              | Si       | Deve essere un URL                           | facebook.com/post/123456789 |
| like_count        | Numero di like/upvote                                                       | Intero               | No       | Default 0, non può essere negativo          | 112                      |
| reply_count       | Numero di commenti/risposte ricevute                                       | Intero               | No       | Default 0, non può essere negativo          | 17                       |
| repost_count      | Numero di condivisioni/retweet                                             | Intero               | No       | Default 0, non può essere negativo          | 1                        |
| quote_count       | Quote tweet o repost con commento (se disponibile)                         | Intero               | No       | Default 0, non può essere negativo          | 0                        |
| bookmark_count    | Numero di salvataggi (se disponibile)                                     | Intero               | No       | Default 0, non può essere negativo          | 0                        |
| content_type      | Tipo di contenuto analizzato                                               | stringa              | No       | Valore categorico: "post" o "commento"      | post                     |


📜 NOTA
_E' importante che tutti i dataset rispettino la convenzione riportata sopra, i dataset che non rispettano lo schema saranno penalizzati in fase di valutazione_

---

## 📥 Fase 2 - Social Analysis

Una volta creato un dataset coerente, la sfida si sposta sull'analisi dei risultati. Ecco cosa includere, come strutturare la consegna e cosa valutare.

### 🎯 Obiettivo della Social Analysis

Analizzare i contenuti raccolti (post/commenti) per comprendere come evolve l’umore e la percezione degli utenti nel tempo e nello spazio in relazione al Gran Premio di Monaco 2025, con un focus sulle fasi prima, durante e dopo la gara. Oltretutto raccogliendo le informazioni degli utenti sarà possibile anche definirne i profili e le caratteristiche comuni.

L’analisi può mettere in luce emozioni, attese, reazioni e controversie legate ai piloti, ai team e possibili correlazioni con gli eventi chiave della gara. Sono quindi suggerite tecniche di Sentiment Analysis,
Emotion Analysis, hate speech recognition, ma anche virality pattern recognition, misinformation detection etc.

---

#### ⚙️ Approcci suggeriti

#### 1. Approccio classico (NLP tradizionale)

Utilizzo di tecniche di Natural Language Processing tradizionali, quali:  
- Pre-elaborazione del testo (tokenizzazione, rimozione stopwords, stemming)  
- Rappresentazione con tecniche tipo TF-IDF  
- Classificatori supervisionati (SVM, Naive Bayes, Random Forest)  
- Analizzatori di sentiment già pronti come TextBlob o VAD  

#### 2. Approccio con LLM (Large Language Models)

Sfruttare modelli linguistici di nuova generazione (GPT, LLaMA, Claude, Mistral, ecc.) per:  
- Classificare direttamente il sentiment di ogni contenuto  
- Estendere l’analisi con rilevazione di emozioni, argomenti principali, intensità del sentimento  
- Arricchire dati mancanti (es. dedurre location, riconoscere sarcasmo, ecc.)  

Questi modelli possono essere interrogati tramite prompt ben costruiti per analisi dettagliate su testi brevi, rumorosi o ambigui.

### Alcuni riferimenti utili:

- Emotion recognition
⁠https://huggingface.co/SamLowe/roberta-base-go_emotions
⁠⁠https://huggingface.co/j-hartmann/emotion-english-distilroberta-base

- Hate Speech Recognition
https://huggingface.co/facebook/roberta-hate-speech-dynabench-r4-target

- Sentiment
https://huggingface.co/tabularisai/multilingual-sentiment-analysis

---

### ✨ Bonus: Estensione LLM-based - Generatione automatica dei report

Oltre alla social analysis, è incoraggiato l’uso di LLM e modelli multimodali per:  

- 📊 Generare automaticamente grafici o visualizzazioni dai dati analizzati  
- 🧠 Riassumere in linguaggio naturale i risultati (es. "Nei commenti dalla Francia, il sentiment era positivo prima della gara, ma è calato dopo l’incidente al 35° giro")  

Insomma, la generazione del report finale potrebbe essere eseguita da modelli di Generative AI.

Esempi di strumenti/approcci:  
- GPT-4-Vision, Gemini, Claude 3 per generare visualizzazioni via prompt  
- Plotly + LLM per generare codice Python per grafici  
- Diagrammi, mappe e infografiche sintetiche generate da modelli come DALL·E o Midjourney 


**⚠️ Questa parte è opzionale ma valorizzata nella valutazione, dimostrando originalità e padronanza delle tecnologie LLM.**

---

## 📦 Modalità di consegna

Lista degli artefatti da consegnare:

- Codice sorgente su Repository GitHub + pacchetti necessari (file requirements.txt) + eventuale Documentazione tecnica (link da condividere con gli organizzatori prima della scadenza)
- Dataset generato dall’ingestion (**)
- Documento PDF, Presentazione Powerpoint o qualsiasi altro formato con risultati analisi dell’evento (inclusi eventuali grafici Bonus) all’interno della repository GitHub sotto la folder reports

****Consegna del dataset post-ingestion**: Se il dataset finale supera i limiti di GitHub (es. >80MB per file o >1GB totali) sarà necessario utilizzare il link che vi verrò passato **privatavamente** al quale caricare il file.

---

## 📜 Metriche di Valutazione e Punteggi

Passiamo alla valutazione della vostra soluzione che avverrà attraverso cinque macro-criteri. 

Ogni aspetto tiene conto non solo della qualità tecnica, ma anche della creatività, dell’efficacia dell’analisi e della chiarezza nella comunicazione dei risultati. 
Di seguito la griglia di valutazione dettagliata, il punteggio massimo raggiungibile è di **100**:

| Macro-metrica                        | Punteggio massimo | Dettaglio                                                                 |
|-------------------------------------|-------------------|--------------------------------------------------------------------------|
| 1. Qualità della soluzione          | 30 pts            | Codice pulito e documentato, automazione, modularità, riusabilità                      |
| 2. Creatività della soluzione       | 20 pts            | Idee originali, approcci inediti, uso creativo di tool/LLM              |
| 3. Completezza del dato             | 20 pts            | Aderenza allo schema, qualità e copertura dei dati                      |
| 4. Efficacia dell’analisi di sentiment | 15 pts         | Accuratezza, rilevanza, originalità delle intuizioni                    |
| 5. Output e comunicazione (report, grafici, doc) | 15 pts | Chiarezza, presentazione, comprensibilità per non esperti               |

---

## 1️⃣ Inizializzazione progetto 

Ogni team deve creare una propria repository GitHub a partire da un template ufficiale fornito dall’organizzazione. Tutti i team lavoreranno sulla stessa struttura di base per garantire ordine, coerenza e facilità di valutazione.

### 🚀 Istruzioni per iniziare con il template

Per partecipare all’hackathon, ogni team dovrà creare repository su GitHub a cui sarà adattato il template della competizione, segui questi passaggi per iniziare a lavorare:

1. **Creare la repository personale su GitHub**

   Crea una nuova repository pubblica su un profilo GitHub di riferimento per il team, quindi clona la tua nuova repository in locale e posizionati nella root della stessa.
   
2. **Installare copier**

    copier è lo strumento che ti permette di generare la struttura di progetto dal template. Va quindi installato usando pip:

      ```bash
   pip install copier
      ```
3. **Importare il template**

    All’interno della cartella del progetto (dove hai clonato la repo), esegui il seguente comando:

    ```bash
    copier copy gh:lezzco/sentiment-analysis-hackathon-2025 .
    ```
    Una volta completato avrete il template installato, nelle varie folder esistono dei README.md che vi aiuterrano ad orientarvi (se questa guida principale vi sembra troppo confusionaria)
   
**Adesso avete questo template sulla vostra repository e potete iniziare!**

---
## Altre Info:
- I gruppi dovranno essere composti da almeno 2 persone e massimo 4 persone;
- Il premio finale per il gruppo vincitore sarà un buono Amazon dal valore di 400 euro.
  
## 🕒 Timeline

| Evento                            | Data e Ora                      |
|----------------------------------|----------------------------------|
| ⏳ **Chiusura iscrizioni**        | 🗓️ Venerdì 23 maggio, ore 20:45     |
| 📤 **Consegna progetto**          | 🗓️ Lunedì 26 maggio, ore 21:30      |
| 🎤 **Presentazione risultati**    | 🗓️ Martedì 27 maggio, ore 08:30      |

