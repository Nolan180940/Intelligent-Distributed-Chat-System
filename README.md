# Intelligent Distributed Chat System

## 📌 Project Overview

本项目是一个基于 Python Socket 和 Tkinter GUI 的分布式智能聊天系统。系统实现了实时双向消息显示、AI 机器人集成（支持 Ollama phi3:mini 模型）、情感分析、聊天摘要和 AI 绘图等核心功能。通过模块化设计和线程安全的消息处理机制，确保了 GUI 界面流畅不卡顿，同时提供了完整的 Bonus 功能支持。

**技术栈：** Python 3.8+、Tkinter、Socket、Threading、Ollama API、TextBlob

**解决的问题：** 传统命令行聊天工具缺乏友好的图形界面和智能化交互体验，本项目通过集成 AI 机器人和情感分析，提供更智能、更人性化的聊天体验。



## 🚀 Quick Start

### Prerequisites

```bash
# 1. Python 3.8+
python --version

# 2. Ollama installed + model downloaded
ollama pull phi3:mini

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download TextBlob corpora (for sentiment analysis)
python -m textblob.download_corpora
```

### Step-by-Step Launch

```bash
# Terminal 1: Start server
python server/chat_server.py

# Terminal 2: Start client A
python client/gui_client.py
# → Login with username "Alice"

# Terminal 3: Start client B (or bot)
python client/gui_client.py  
# → Login with username "Bob" or "Bot"

# Test basic chat:
# Alice sends "Hello" → Bob sees it → Bob replies → Alice sees reply
```

### Testing Features

```bash
# 1. Sentiment Analysis:
# Send "I am so happy today!" → Should show 😊 next to message

# 2. Chat Summary:
# Type "/summary" in chat → Should return brief summary of last 10 messages

# 3. Group Chat @Bot:
# In group chat, send "@Bot tell me a joke" → Bot should reply in group

# 4. AI Image (simulated):
# Type "/aipic: a cute cat" → Should show placeholder image + log message
```

---

## 🐛 Known Issues & Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama connection refused | Run `ollama serve` first, check `http://localhost:11434` |
| TextBlob returns None | Run `python -m textblob.download_corpora` |
| GUI freezes on send | Ensure message receiving runs in `threading.Thread(daemon=True)` |
| Emoji shows as □□ | Install emoji font or use fallback text |
| No graphical display | Set `$DISPLAY` environment variable or use X11 forwarding |

---

## 📁 Project Structure

```
Intelligent Distributed Chat System/
├── server/
│   └── chat_server.py      # Socket server with group chat support
├── client/
│   ├── gui_client.py       # Main GUI client (Tkinter)
│   ├── chat_client.py      # Base client logic
│   └── login_dialog.py     # Login popup
├── bot/
│   ├── ai_bot.py           # Ollama API wrapper + context management
│   ├── sentiment_analyzer.py # TextBlob-based emotion detection
│   └── summary_generator.py  # Chat history summarization
├── utils/
│   └── chat_utils.py       # Helper functions
├── config/
│   └── settings.py         # Ollama endpoint, model name, etc.
├── requirements.txt
├── test_all_features.py    # Automated test script
└── README.md               # This file
```

---

## 💬 Usage Guide

### Basic Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/users` | List online users |
| `/time` | Show server time |
| `/clear` | Clear chat display |
| `/quit` | Exit application |

### AI Bot Commands

| Command | Description |
|---------|-------------|
| `@Bot hello` | Chat with AI (must mention @Bot) |
| `/persona <name>` | Change bot personality |
| `/summary` | Summarize recent chat |
| `/aipic: sunset` | Generate AI image (simulated) |

### Bot Personas

- `helpful` - Friendly and assistive
- `humorous` - Witty and funny
- `serious` - Professional and formal
- `creative` - Imaginative responses
- `advisor` - Academic guidance

---

## 🔧 Configuration

Edit `config/settings.py` to customize:

```python
CHAT_IP = '127.0.0.1'           # Server address
CHAT_PORT = 1112                # Server port
OLLAMA_HOST = "http://localhost:11434"  # Ollama API
OLLAMA_MODEL = "phi3:mini"      # AI model
```

---

### Thread-Safe GUI Updates

All GUI updates go through the main thread:

```python
if threading.current_thread() is threading.main_thread():
    _insert()
else:
    self.root.after(0, _insert)
```

### Ollama Fallback Handling

When Ollama is unavailable, the bot gracefully degrades:

```python
if self.ollama_available:
    response = self._chat_with_ollama(user_message)
else:
    response = self._fallback_response(user_message)
```

---

## 📄 License

MIT License - For educational purposes only

---

## Liability Waiver

This project is for educational purposes only, we won't hold responsibility if anyone clones the repository and makes any updates on it.
