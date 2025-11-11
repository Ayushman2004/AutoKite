# AutoKite
AutoKite is an AI-driven email client designed to make your inbox lighter and smarter. It automatically summarizes and categorizes your emails using context-aware AI, helping you focus on what truly matters.

---

## 🚀 Features

- 🧠 **AI Summarization:** Automatically summarizes long or complex emails using local LLMs via **Ollama**.  
- 🗂️ **Smart Categorization:** Organizes emails into relevant categories based on content and context.  
- 💾 **Vector Storage:** Uses **ChromaDB** to store and query semantic email embeddings efficiently.  
- 🔐 **Local Privacy:** All processing runs locally through your virtual environment — no external cloud APIs needed.  
- 🌐 **Streamlit Interface:** Intuitive and interactive web UI for viewing, summarizing, and managing emails.  

---


## 🧩 Tech Stack

| Component        | Description |
|------------------|-------------|
| **Python**       | Core backend logic |
| **Streamlit**    | Web interface for visualization |
| **Ollama**       | Local AI inference engine |
| **ChromaDB**     | Vector database for contextual storage |
| **IMAP-Tools**   | Email fetching via IMAP |
| **BeautifulSoup4 / lxml** | Email content parsing |
| **Pydantic**     | Data validation and models |
| **dotenv**       | Environment variable management |

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Ayushman2004/AutoKite.git
cd AutoKite
```

### 2️⃣ Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate     # On macOS/Linux
venv\Scripts\activate        # On Windows
```

### 3️⃣ Install ChromaDB and Dependencies
```bash
pip install chromadb
pip install -r requirements.txt
```

### 4️⃣ Install and run Ollama

Ollama is used for running local LLMs (like Llama 3, Mistral, etc.).
Download and install it from: https://ollama.ai

After installation, pull your preferred model:

```bash
ollama pull phi3.5
```

### 5️⃣ Run application
```bash
streamlit run app.py
```


---

## ⚙️ Environment Variables

```bash
GMAIL_EMAIL=#####
GMAIL_APP_PASSWORD=#####

# Ollama Configuration
OLLAMA_MODEL=phi3.5
OLLAMA_HOST=#####

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=#####
```



