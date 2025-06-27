# 🧠 Tata Dealership SQL Bot

A Streamlit-based intelligent chatbot that converts **natural language dealership queries** into **SQL** and enables users to analyze dealership data stored in MongoDB. It leverages powerful LLMs (like DeepSeek via OpenRouter) to interpret user queries and return accurate SQL statements, which are then executed using DuckDB.

---

## 🚀 Features

- 🔍 **Natural Language to SQL**: Ask questions like “Show top 5 dealers in Maharashtra with highest discount” and receive SQL query results.
- 📊 **MongoDB Integration**: Reads dealership data dynamically from MongoDB collections.
- 🧠 **LLM-Powered SQL Translation**: Uses `deepseek/deepseek-r1-0528:free` model from OpenRouter.
- ⚙️ **DuckDB Engine**: Executes SQL on in-memory DataFrames quickly and efficiently.
- 🧾 **Multi-State Querying**: Supports state-specific queries like Odisha, Gujarat, Punjab, etc.
- 💬 **Persistent Chat Storage**: Chat logs are saved using Google Firestore per user session.
- 👤 **Login System**: Each user logs in and sees only their chat history.
- 💡 **Live UI**: Powered by Streamlit, featuring a clean, dark-themed UI with scrollable history.

---

## 📚 Libraries Used

| Library           | Purpose                                                                |
|-------------------|------------------------------------------------------------------------|
| `streamlit`       | Build interactive web UI.                                              |
| `pymongo`         | Connect to and query MongoDB collections.                              |
| `duckdb`          | Execute SQL on Pandas DataFrames.                                      |
| `firebase_admin`  | Integrate with Google Firestore to store chat sessions.                |
| `langchain`       | Prompt templating and LLM interaction.                                 |
| `langchain-openai`| Adapter to work with OpenRouter (for DeepSeek model).                  |
| `dotenv`          | Securely load environment variables.                                   |
| `uuid`            | Generate unique IDs for chats.                                         |
| `re`              | Regular expression handling (e.g., cleaning malformed SQL).            |
| `pydantic`        | Strong typing and secret field validation.                             |

---

## 🤖 LLM Used

- **Model**: `deepseek/deepseek-r1-0528:free`
- **Provider**: [OpenRouter](https://openrouter.ai/)
- **Free Usage**:
  - You can register on OpenRouter to get a limited free quota.
  - After creating an account, generate an API key and store it in `.env` file as:
    ```
    OPENROUTER_API_KEY=your_openrouter_api_key
    ```
  - This key is used by `ChatOpenAI` client via the `ChatOpenRouter` subclass to connect seamlessly.
Context Length: 164,000 tokens

Max Output Tokens: 164,000 tokens

Latency: approximately 2.75 seconds

Throughput: approximately 38.44 tokens per second

Cost: Free (accessed via OpenRouter)

Location: US-based (includes fallback providers)

Uptime: High availability with fallback routing


---

## 🔥 Firestore Usage

- Stores chats in a `chats` collection.
- Each document contains a `username`, `messages` list, and unique chat `ID`.
- Messages are persisted across sessions, so you can resume conversations later.
- Setup:
  - Go to [Firebase Console](https://console.firebase.google.com/)
  - Create a project > Firestore DB > Generate a new private key (JSON)
  - Download the key and place it in your root directory as:  
    ```
    ServiceAccountKey.json
    ```

---

## 📂 Folder Structure

schema_builder.py # Builds schema context from MongoDB
├── chatbot2.py # Main Streamlit application
├── ServiceAccountKey.json # Firestore admin SDK credentials
├── .env # Contains MongoDB URL and OpenRouter key
├── requirements.txt # Python dependencies
├── README.md # You're reading this!



---

## 🛠️ How to Run This Project

1. **Clone the repo**
   ```bash
   git clone https://github.com/aditya2004-blip/tata-dealership-sql-bot.git
   

2.python -m venv env
source env/bin/activate   # or .\env\Scripts\activate on Windows

3. pip install -r requirements.txt

4.OPENROUTER_API_KEY=your_openrouter_api_key
MONGODB_URL=your_mongodb_connection_string

5.python load_data.py


6.streamlit run app.py

