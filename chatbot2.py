

import streamlit as st
from dotenv import load_dotenv
import os
import uuid
from pymongo import MongoClient
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from schema_builder import get_schema_context
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import Field, SecretStr
from typing import Optional
from langchain_openai import ChatOpenAI


# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("ServiceAccountKey.json")
    firebase_admin.initialize_app(cred)

db_store = firestore.client()

# --- Firestore Functions ---
def save_to_firestore(chat_id, chat_data):
    chat_data["username"] = st.session_state.username
    db_store.collection("chats").document(chat_id).set(chat_data)

def get_from_firestore(chat_id):
    doc = db_store.collection("chats").document(chat_id).get()
    if doc.exists:
        data = doc.to_dict()
        return {"id": chat_id, "messages": data.get("messages", [])}
    else:
        return {"id": chat_id, "messages": []}

def get_all_chats_for_user(username):
    all_chats = []
    docs = db_store.collection("chats").where("username", "==", username).stream()
    for doc in docs:
        data = doc.to_dict()
        all_chats.append({
            "id": doc.id,
            "messages": data.get("messages", [])
        })
    return all_chats

# --- Load environment and MongoDB ---
load_dotenv()
class ChatOpenRouter(ChatOpenAI):
    openai_api_key: Optional[SecretStr] = Field(
        alias="api_key", default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )

    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"openai_api_key": "OPENROUTER_API_KEY"}

    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        openai_api_key = openai_api_key or os.environ.get("OPENROUTER_API_KEY")
        super().__init__(base_url="https://openrouter.ai/api/v1", openai_api_key=openai_api_key, **kwargs)

# --- Instantiate OpenRouter model ---
llm = ChatOpenRouter(model_name="deepseek/deepseek-r1-0528:free")
mongo_url = os.getenv("MONGODB_URL")
client = MongoClient(mongo_url)
db = client['dealership_db']


# --- Prompt Setup ---
sql_prompt = PromptTemplate(
    input_variables=["context", "query", "schema_context"],
    template="""
You are an expert SQL assistant. Write a correct SQL query for the given database schema.
{schema_context}

Previous conversation context (user and bot history for this session):
{context}

For the following user request, output ONLY the SQL query, nothing else.

User Request: "{query}"
SQL:
"""
)
data_prompt = PromptTemplate(
    input_variables=["query", "schema_context"],
    template="""
You are an expert SQL assistant. Write a correct SQL query for the given database schema.
{schema_context}

For the following user request, output ONLY the SQL query, nothing else.

User Request: "{query}"
SQL:
"""
)


# llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, max_retries=2)

# --- Helpers ---
def build_context_from_history(messages):
    context = ""
    for m in messages[-8:]:
        prefix = "User:" if m["role"] == "user" else "Bot:"
        context += f"{prefix} {m['content']}\n"
    return context.strip()

def handle_query(query, chat_history):
    schema_context=get_schema_context(query)
    print(f"{schema_context} ...........")
    context = build_context_from_history(chat_history)
    sql_query = llm.invoke(sql_prompt.format(context=context, query=query,schema_context=schema_context))
    return sql_query.content if hasattr(sql_query, "content") else str(sql_query)

def handle_query_databot(query):
    schema_context=get_schema_context(query)
    print(f"{schema_context} ...........")
    sql_query = llm.invoke(data_prompt.format(query=query,schema_context=schema_context))
    return sql_query.content if hasattr(sql_query, "content") else str(sql_query)

def login_screen():
    st.markdown("""
    <div style="text-align:center; margin-top:120px">
        <h2 style='color:#d2e8ff'>🧠 Tata Dealership SQL Bot Login</h2>
        <p style='color:#8bbbe8'>Login to continue.</p>
    </div>
    """, unsafe_allow_html=True)
    username = st.text_input("Username", key="login_user")
    login_btn = st.button("Login", key="login_btn")
    if login_btn and username:
        st.session_state.username = username
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

def format_sidebar_chat_title(ch):
    first_user = next((msg["content"] for msg in ch.get("messages", []) if msg["role"] == "user"), None)
    return (first_user or "New Chat")[:32]

# --- Streamlit UI Config ---
st.set_page_config(page_title="Tata SQL ChatBot", layout="wide")

st.markdown("""
<style>
body, .main, .block-container {
    background-color: #111b2a !important;
}
[data-testid="stSidebar"] {
    background-color: #09213d !important;
    color: #d2e8ff !important;
    width: 355px !important;
    border-right: 2px solid #0066b3;
}
 .block-container { height: 100% !important; }

.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: #111b2a;
    padding: 10px 0 60px 0;
    height: 100%;
}
.chat-message {
    border-radius: 12px;
    padding: 15px 20px;
    max-width: 80%;
    font-size: 1.08rem;
}
.user-message {
    background-color: #1e3854;
    color: #97c3f7;
    align-self: flex-end;
    text-align: right;
    border: 1.5px solid #2994e2;
}
.bot-message {
    background-color: #11294c;
    color: #e7f1fb;
    align-self: flex-start;
    text-align: left;
    border: 1.5px solid #0a66c2;
}
</style>
""", unsafe_allow_html=True)

# --- Login Handling ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    login_screen()

# --- Chat Session Management ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = get_all_chats_for_user(st.session_state.username)

if "active_chat_id" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.active_chat_id = st.session_state.all_chats[0]["id"]
    else:
        new_id = str(uuid.uuid4())
        st.session_state.active_chat_id = new_id
        st.session_state.all_chats = [{"id": new_id, "messages": []}]

def get_active_chat():
    return next((c for c in st.session_state.all_chats if c["id"] == st.session_state.active_chat_id), None)

# --- Sidebar ---
with st.sidebar:
    st.image("images/sidebar_logo.png", width=300)
    st.title("Chats")
    if st.button("\u2795 New Chat"):
        chat_id = str(uuid.uuid4())
        st.session_state.active_chat_id = chat_id
        st.session_state.all_chats.append({"id": chat_id, "messages": []})
        st.rerun()
    for ch in st.session_state.all_chats:
        button_text = format_sidebar_chat_title(ch)
        key = f"chat_{ch['id']}"
        if st.button(f"💬 {button_text}", key=key):
            st.session_state.active_chat_id = ch["id"]
            st.rerun()
    st.markdown("---")
    st.write(f"👤 **User:** {st.session_state.username}")

# --- Chat UI ---
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
    <img src="images/chat_container_logo.png" width="38"/>
    <h2 style="margin:0; color:#d2e8ff; font-weight:700;">Tata Dealership SQL Bot</h2>
</div>
""", unsafe_allow_html=True)

st.caption("Your SQL Copilot for Tata dealership analytics")
chat_container = st.container()
active_chat = get_active_chat()

if active_chat is not None:
    if "messages" not in active_chat:
        active_chat["messages"] = []
    with chat_container:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for msg in active_chat["messages"]:
            css_class = "user-message" if msg["role"] == "user" else "bot-message"
            st.markdown(f"<div class='chat-message {css_class}'>{msg['content']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

query = st.text_input("Type your SQL or dealership question...", key=f"input_field_{st.session_state.active_chat_id}")

if st.button("Send", key=f"send_{st.session_state.active_chat_id}") and query:
    active_chat["messages"].append({"role": "user", "content": query})
    with st.spinner("Thinking..."):
        try:
            answer = handle_query(query, active_chat["messages"])
        except Exception as e:
            answer = f"❌ Error: {str(e)}"
    active_chat["messages"].append({"role": "bot", "content": answer})
    save_to_firestore(st.session_state.active_chat_id, active_chat)
    st.session_state.all_chats = get_all_chats_for_user(st.session_state.username)
    st.rerun()

st.markdown("""
<script>
var chatDiv = window.parent.document.querySelector('.chat-container');
if(chatDiv) chatDiv.scrollTop = chatDiv.scrollHeight;
</script>
""", unsafe_allow_html=True)
