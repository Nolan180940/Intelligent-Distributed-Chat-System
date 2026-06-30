# Constants for the Distributed Intelligent Chat System

# Network settings
CHAT_IP = '127.0.0.1'
CHAT_PORT = 1112
SERVER = (CHAT_IP, CHAT_PORT)

# Protocol settings
SIZE_SPEC = 5  # Size specification length for message framing
CHAT_WAIT = 0.2  # Wait time between chat iterations

# Client states
S_OFFLINE = 0
S_CONNECTED = 1
S_LOGGEDIN = 2
S_CHATTING = 3

# Bot settings
BOT_NAME = "Bot"
BOT_TRIGGER_KEYWORDS = ["@Bot", "@bot", "BOT", "bot"]
DEFAULT_BOT_PERSONA = "helpful"

# Ollama API settings (local fallback)
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "phi3:mini"

# SiliconFlow API settings (primary AI provider)
# These are also loaded from .env via python-dotenv
SILICONFLOW_API_KEY = "EMPTY"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Menu options
MENU = """
++++ Choose one of the following commands
    time: calendar time in the system
    who: to find out who else are there
    c _peer_: to connect to the _peer_ and chat
    ? _term_: to search your chat logs where _term_ appears
    p _#_: to get number <#> sonnet
    /summary: get a summary of recent chat history
    /aipic: <description> generate AI image (simulated)
    q: to leave the chat system
"""

# Emoji mappings for sentiment
SENTIMENT_EMOJIS = {
    'positive': '😊',
    'neutral': '😐',
    'negative': '😡'
}

# GUI colors
COLOR_SENT = '#0066cc'      # Blue for sent messages
COLOR_RECEIVED = '#333333'  # Gray for received messages
COLOR_BOT = '#9933cc'       # Purple for bot messages
COLOR_SYSTEM = '#666666'    # Dark gray for system messages
