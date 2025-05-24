# 📁 src/

Benvenuto nella cartella `src/`, il cuore del progetto! Qui si trova tutto il codice sorgente, organizzato in tre sezioni principali:

---

## 📦 `ingestion/`
Contiene il codice per la **raccolta, normalizzazione e integrazione dei dati** provenienti dai social media.

### Cosa metterci:
- Script per scraping o accesso API (es. Twitter/X, Reddit, YouTube, Instagram, ecc.)
- Parser e trasformatori per portare i dati allo **schema comune**
- Pulizia e validazione dei dati

📤 **Output atteso:** un file `.csv`, `.parquet` o database normalizzato da salvare nella cartella `data/` (fuori da `src/`), contenente il dataset integrato, o caricato su Google Drive (per file superiori ad 80 MB).

---

## 💬 `sentiment/`
Contiene gli strumenti per la **sentiment analysis**.

### Cosa metterci:
- Modelli di analisi classici (TextBlob, VADER, scikit-learn, ecc.)
- Pipeline o script per usare modelli LLM
- Analisi geografica e temporale del sentiment
- Generazione di grafici o visualizzazioni (da salvare in `reports/`)

📤 **Output atteso:** file di analisi, immagini, grafici, documenti da salvare in `reports/`.

---

## 🛠️ `utils/`
Contiene utility e funzioni condivise tra ingestion e sentiment.

### Cosa metterci:
- Funzioni di logging
- Helpers per timestamp, parsing geolocalizzazione, caricamento file, ecc.

---

### 📁 Dove vanno i file generati?
- 🔄 Tutti i datataset con schema comune in output alla parte di ingestion (con size inferiori ad 80 MB) vanno salvati nella cartella **`data/`** (che si trova nella root del progetto, fuori da `src/`).
- 📊 Visualizzazioni o report finali possono essere messi nella una cartella **`reports/`**.

---

### ✅ Best Practice
- Mantieni il codice modulare e ben documentato 🧼
- Evita duplicazioni tra ingestion e sentiment 👯
- Se usi Jupyter Notebook, puoi metterli in una cartella `notebooks/` nella rispettive folder di ingestion, sentiment

Buon lavoro, esploratori del dato! 🚀
