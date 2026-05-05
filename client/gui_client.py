"""
Main GUI Client for Distributed Intelligent Chat System.

Features:
- Full duplex message display (sent/received) ✅
- Bug fix: system_msg reset after display ✅
- Real-time message reception via background thread ✅
- Emoji support ✅
- Login interface ✅
- AI Bot integration with persona selection ✅
- Sentiment analysis with emoji indicators ✅
- Chat summary command (/summary) ✅
- AI image generation command (/aipic) ✅
- Group chat with @Bot trigger ✅
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import queue
import json
import time
from typing import Optional, Dict, List

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config.settings as cfg
from client.chat_client import ChatClient
from client.login_dialog import show_login_dialog
from bot.ai_bot import AIBot, get_bot, reset_bot
from bot.sentiment_analyzer import get_analyzer
from bot.summary_generator import SummaryGenerator


class GUIChatClient:
    """Main GUI chat client with all features."""
    
    def __init__(self, username: str, persona: str = "helpful"):
        self.username = username
        self.persona = persona
        
        # Network client
        self.client: Optional[ChatClient] = None
        self.connected = False
        
        # Bot instance
        self.bot: Optional[AIBot] = None
        self.bot_enabled = True
        self.chat_history: List[str] = []  # For summary feature
        
        # Sentiment analyzer
        self.sentiment_analyzer = get_analyzer()
        
        # Message queue for thread-safe GUI updates
        self.gui_queue = queue.Queue()
        
        # === BUG FIX: Explicitly initialize system_msg to empty string ===
        # This prevents the known bug where messages repeat because system_msg 
        # was not reset after display
        self.system_msg = ""
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title(f"ICDS Chat - {username}")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Setup styles and UI
        self._setup_styles()
        self._setup_ui()
        
        # Connect to server
        self._connect_to_server()
        
        # Start GUI update loop
        self._start_gui_update_loop()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Configure message styles and colors."""
        self.colors = {
            'sent': cfg.COLOR_SENT,        # Blue for sent messages
            'received': cfg.COLOR_RECEIVED, # Gray for received
            'bot': cfg.COLOR_BOT,          # Purple for bot
            'system': cfg.COLOR_SYSTEM,     # Dark gray for system
            'bg': '#ffffff',
            'entry_bg': '#f8f9fa'
        }
        
        # Font configurations
        self.fonts = {
            'message': ('Arial', 10),
            'system': ('Arial', 9, 'italic'),
            'entry': ('Arial', 11)
        }
    
    def _setup_ui(self):
        """Build the complete GUI interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === 1. Connection Status Bar ===
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_indicator = tk.Label(
            status_frame, text="●", font=('Arial', 12),
            foreground='gray'
        )
        self.status_indicator.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(status_frame, text="Connecting...")
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bot status
        self.bot_status_label = ttk.Label(
            status_frame, text="🤖 Bot: Active", 
            foreground=cfg.COLOR_BOT
        )
        self.bot_status_label.pack(side=tk.RIGHT)
        
        # === 2. Chat Display Area (Core Feature) ===
        chat_frame = ttk.LabelFrame(main_frame, text="Chat History", padding="5")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            state='disabled',
            wrap='word',
            font=self.fonts['message'],
            bg=self.colors['bg']
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different message types
        # ✅ Bidirectional message display configuration
        self.chat_display.tag_config('sent', justify='right', foreground=self.colors['sent'])
        self.chat_display.tag_config('received', justify='left', foreground=self.colors['received'])
        self.chat_display.tag_config('bot', justify='left', foreground=self.colors['bot'], font=('Arial', 10, 'italic'))
        self.chat_display.tag_config('system', justify='center', foreground=self.colors['system'], font=self.fonts['system'])
        self.chat_display.tag_config('emoji', justify='left', font=('Arial', 12))
        
        # === 3. Input Area ===
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.message_entry = ttk.Entry(
            input_frame,
            font=self.fonts['entry']
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        
        send_btn = tk.Button(
            input_frame,
            text="Send 📤",
            command=self._send_message,
            bg='#007acc',
            fg='white',
            relief='flat',
            padx=15,
            pady=5
        )
        send_btn.pack(side=tk.RIGHT)
        
        # === 4. Emoji Quick Insert (Bonus Feature) ===
        emoji_frame = ttk.Frame(main_frame)
        emoji_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(emoji_frame, text="Quick Emojis:").pack(side=tk.LEFT, padx=(0, 5))
        
        emojis = ["😊", "👍", "🎉", "🤔", "❓", "✨", "👋", "❤️"]
        for emoji in emojis:
            btn = tk.Button(
                emoji_frame,
                text=emoji,
                width=2,
                command=lambda e=emoji: self._insert_emoji(e),
                relief='flat',
                font=('Arial', 12)
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # === 5. Control Buttons ===
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X)
        
        # User list button
        users_btn = tk.Button(
            control_frame,
            text="👥 Users",
            command=self._show_users,
            relief='flat',
            padx=10
        )
        users_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Bot persona selector
        ttk.Label(control_frame, text="Bot Persona:").pack(side=tk.LEFT, padx=(15, 5))
        
        self.persona_var = tk.StringVar(value=self.persona)
        persona_combo = ttk.Combobox(
            control_frame,
            textvariable=self.persona_var,
            values=["helpful", "humorous", "serious", "creative", "advisor"],
            width=12,
            state='readonly'
        )
        persona_combo.pack(side=tk.LEFT)
        persona_combo.bind('<<ComboboxSelected>>', self._change_persona)
        
        # Toggle bot button
        self.bot_toggle_btn = tk.Button(
            control_frame,
            text="🤖 Bot: ON",
            command=self._toggle_bot,
            relief='flat',
            padx=10,
            bg='#e8f5e9'
        )
        self.bot_toggle_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Help button
        help_btn = tk.Button(
            control_frame,
            text="❓ Help",
            command=self._show_help,
            relief='flat',
            padx=10
        )
        help_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Exit button
        exit_btn = tk.Button(
            control_frame,
            text="🚪 Exit",
            command=self._on_close,
            relief='flat',
            padx=10,
            bg='#ffebee'
        )
        exit_btn.pack(side=tk.RIGHT)
    
    def _connect_to_server(self):
        """Initialize connection to chat server."""
        self.client = ChatClient(self.username)
        self.client.on_connected = self._on_connected
        self.client.on_disconnected = self._on_disconnected
        self.client.on_message_received = self._on_message_received
        
        if self.client.connect():
            if self.client.login():
                self._display_system("Connected to server!")
            else:
                self._display_system("Login failed. Username may be taken.")
        else:
            self._display_system("Failed to connect to server. Make sure server is running.")
    
    def _on_connected(self):
        """Callback when connected to server."""
        self.connected = True
        self.status_indicator.config(foreground='green')
        self.status_label.config(text=f"Connected as {self.username}")
        
        # Initialize bot
        reset_bot()  # Reset any existing bot
        self.bot = get_bot(persona=self.persona)
        
        self._display_system(f"Welcome, {self.username}! Type /help for commands.")
    
    def _on_disconnected(self):
        """Callback when disconnected from server."""
        self.connected = False
        self.status_indicator.config(foreground='red')
        self.status_label.config(text="Disconnected")
        self._display_system("Disconnected from server.")
    
    def _on_message_received(self, msg_data: dict):
        """
        Callback when message received from server.
        Runs in background thread - must queue to main thread.
        """
        # Queue the message for main thread processing
        self.gui_queue.put(msg_data)
    
    def _start_gui_update_loop(self):
        """Start periodic GUI update loop (runs in main thread)."""
        self._process_gui_queue()
    
    def _process_gui_queue(self):
        """
        Process queued messages from network thread.
        ✅ This ensures all GUI updates happen in main thread.
        """
        try:
            while True:
                msg_data = self.gui_queue.get_nowait()
                self._handle_received_message(msg_data)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_gui_queue)
    
    def _handle_received_message(self, msg_data: dict):
        """Process a received message (in main thread)."""
        action = msg_data.get('action', '')
        
        if action == 'exchange':
            sender = msg_data.get('from', 'Unknown')
            content = msg_data.get('message', '')
            
            # Skip own messages (already displayed when sent)
            if sender == self.username:
                return
            
            # Store in history for summary
            self.chat_history.append(f"{sender}: {content}")

            # Treat bot-formatted messages as bot output for all clients.
            # This keeps the bot bubble style while still using normal server broadcast.
            if content.startswith("🤖 Bot:"):
                self._display_message(f"{sender} {content}", tag='bot')
                return
            
            # Analyze sentiment and display with emoji
            sentiment = self.sentiment_analyzer.analyze(content)
            self._display_message(
                f"{sender}: {content}",
                tag='received',
                emoji=sentiment['emoji']
            )
        
        elif action == 'login':
            status = msg_data.get('status', '')
            if status == 'ok':
                pass  # Already handled
            elif status == 'duplicate':
                self._display_system("Login failed: Username already taken")
        
        elif action == 'list':
            results = msg_data.get('results', '')
            self._display_system(f"Online Users:\n{results}")
        
        elif action == 'time':
            result = msg_data.get('results', '')
            self._display_system(f"Server Time: {result}")
        
        elif action == 'search':
            results = msg_data.get('results', '')
            self._display_system(f"Search Results:\n{results}")
        
        elif action == 'connect':
            status = msg_data.get('status', '')
            from_user = msg_data.get('from', '')
            if status == 'request':
                self._display_system(f"Connection request from {from_user}")
            elif status == 'success':
                self._display_system(f"Connected with {from_user}")
        
        elif action == 'bot_response':
            response = msg_data.get('content', '')
            original_sender = msg_data.get('original_sender', '')
            if original_sender:
                self._display_message(f"🤖 Bot: {response}", tag='bot')
            else:
                self._display_message(f"🤖 Bot: {response}", tag='bot')
        
        elif action == 'disconnect':
            self._display_system("Peer disconnected")
    
    def _should_bot_respond(self, content: str, sender: str) -> bool:
        """
        Check if bot should respond to this message.
        ✅ Group chat feature: Only respond to @Bot or keywords.
        """
        if sender == "Bot":  # Don't respond to other bots
            return False
        
        content_lower = content.lower()
        
        # Check for @Bot mention
        if '@bot' in content_lower or '@Bot' in content:
            return True
        
        # Check for specific keywords (avoid spam)
        trigger_keywords = ['help', 'bot', 'ai', 'question', 'please']
        if any(keyword in content_lower for keyword in trigger_keywords):
            return True
        
        return False
    
    def _schedule_bot_response(self, user_content: str, sender: str):
        """Schedule bot response to avoid blocking GUI."""
        def respond():
            # Generate response
            response = self.bot.chat(user_content)
            
            # Add bot response to history
            bot_entry = f"🤖 Bot: {response}"
            self.chat_history.append(bot_entry)

            # Broadcast bot response through server so every client can see it.
            if self.connected and self.client:
                self.client.send_message(bot_entry, broadcast=True)
            
            # Queue display in main thread
            self.gui_queue.put({
                'action': 'bot_response',
                'content': response,
                'original_sender': sender,
                'original_content': user_content
            })
        
        # Run in background thread
        thread = threading.Thread(target=respond, daemon=True)
        thread.start()
    
    def _display_message(self, text: str, tag: str = 'received', emoji: str = ''):
        """
        Display a message in the chat window.
        ✅ Thread-safe: Must be called from main thread.
        """
        def _insert():
            self.chat_display.config(state='normal')
            
            # Add emoji prefix if provided
            if emoji:
                full_text = f"{emoji} {text}\n"
            else:
                full_text = f"{text}\n"
            
            self.chat_display.insert(tk.END, full_text, tag)
            self.chat_display.config(state='disabled')
            self.chat_display.see(tk.END)  # Auto-scroll to bottom
        
        # Ensure execution in main thread
        if threading.current_thread() is threading.main_thread():
            _insert()
        else:
            self.root.after(0, _insert)
    
    def _display_system(self, text: str):
        """Display system message (centered, gray)."""
        # ✅ BUG FIX: Explicitly clear system_msg before and after display
        # This fixes the known bug where messages repeat
        self.system_msg = ""
        
        def _insert():
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"\n{text}\n", 'system')
            self.chat_display.config(state='disabled')
            self.chat_display.see(tk.END)
            
            # ✅ BUG FIX: Reset system_msg after display
            # This is the critical fix for the repeat message bug
            self.system_msg = ""
        
        if threading.current_thread() is threading.main_thread():
            _insert()
        else:
            self.root.after(0, _insert)
    
    def _insert_emoji(self, emoji: str):
        """Insert emoji at cursor position in input field."""
        self.message_entry.insert(tk.INSERT, emoji + " ")
        self.message_entry.focus_set()
    
    def _send_message(self):
        """Send message to server."""
        content = self.message_entry.get().strip()
        
        if not content:
            return
        
        # Clear input
        self.message_entry.delete(0, tk.END)
        
        # Check for special commands
        if content.startswith('/'):
            self._handle_command(content)
            return
        
        # Send to server
        if self.connected and self.client:
            self.client.send_message(content, broadcast=True)
        
        # ✅ Display own message (right-aligned, blue)
        self._display_message(f"{self.username}: {content}", tag='sent')
        
        # Store in history
        self.chat_history.append(f"{self.username}: {content}")

        # Trigger local bot response for the sender's own @Bot mentions/keywords
        if self.bot_enabled and self._should_bot_respond(content, self.username):
            self._schedule_bot_response(content, self.username)
    
    def _handle_command(self, command: str):
        """Handle special commands."""
        # Extract command name (handle both /cmd arg and /cmd: arg formats)
        cmd = command.lower().split()[0].rstrip(':')
        
        if cmd == '/help':
            self._show_help()
        
        elif cmd == '/summary':
            self._generate_summary()
        
        elif cmd == '/aipic':
            # AI image generation command
            if self.bot:
                response = self.bot.chat(command)
                self._display_message(f"🤖 Bot: {response}", tag='bot')
                self.chat_history.append(f"🤖 Bot: {response}")
        
        elif cmd == '/persona':
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                new_persona = parts[1].lower()
                if self.bot and self.bot.set_persona(new_persona):
                    self.persona_var.set(new_persona)
                    self._display_system(f"Bot persona changed to: {new_persona}")
                else:
                    self._display_system(f"Unknown persona: {new_persona}")
        
        elif cmd == '/clear':
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')
            self._display_system("Chat cleared.")
        
        elif cmd == '/users':
            if self.client:
                self.client.list_users()
        
        elif cmd == '/time':
            if self.client:
                self.client.get_time()
        
        elif cmd == '/quit' or cmd == '/exit':
            self._on_close()
        
        else:
            self._display_system(f"Unknown command: {cmd}. Type /help for available commands.")
    
    def _generate_summary(self):
        """Generate summary of recent chat history."""
        if not self.chat_history:
            self._display_system("No chat history to summarize.")
            return
        
        generator = SummaryGenerator(llm_client=self.bot if self.bot.ollama_available else None)
        summary = generator.generate(self.chat_history)
        
        self._display_system(summary)
    
    def _show_users(self):
        """Show list of online users."""
        if self.client:
            self.client.list_users()
    
    def _change_persona(self, event=None):
        """Change bot persona based on selection."""
        new_persona = self.persona_var.get()
        if self.bot:
            self.bot.set_persona(new_persona)
            self._display_system(f"Bot persona changed to: {new_persona}")
    
    def _toggle_bot(self):
        """Toggle bot on/off."""
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_toggle_btn.config(text="🤖 Bot: ON", bg='#e8f5e9')
            self.bot_status_label.config(text="🤖 Bot: Active")
            self._display_system("Bot enabled. Mention @Bot to interact.")
        else:
            self.bot_toggle_btn.config(text="🤖 Bot: OFF", bg='#ffebee')
            self.bot_status_label.config(text="🤖 Bot: Inactive")
            self._display_system("Bot disabled.")
    
    def _show_help(self):
        """Show help dialog."""
        help_text = """
ICDS Chat Commands:

Basic:
  /help - Show this help
  /users - List online users
  /time - Show server time
  /clear - Clear chat display
  /quit - Exit application

AI Bot Features:
  @Bot <message> - Chat with AI bot
  /persona <name> - Change bot persona
  /summary - Summarize recent chat
  /aipic: <desc> - Generate AI image

Bot Personas:
  helpful, humorous, serious, creative, advisor

Tips:
  • Use emoji buttons for quick insertion
  • Bot only responds to @Bot mentions
  • Sentiment analysis shows emoji indicators
"""
        messagebox.showinfo("Help", help_text)
    
    def _on_close(self):
        """Handle application close."""
        if self.client:
            self.client.disconnect()
        
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    # Check for display only on Linux/Unix systems
    if sys.platform.startswith('linux'):
        if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
            print('[ERROR] No graphical display available. GUI client requires X11/Wayland.')
            print('Set $DISPLAY or $WAYLAND_DISPLAY, or use a terminal-based client instead.')
            return

    try:
        print("[INFO] 启动 GUI 客户端...")
        sys.stdout.flush()
        print("[INFO] 创建登录对话框...")
        sys.stdout.flush()
        
        # Show login dialog
        print("[INFO] 等待用户登录...")
        sys.stdout.flush()
        username, persona = show_login_dialog(None)
        
        if username:
            print(f"[INFO] 用户登录: {username}, 角色: {persona}")
            sys.stdout.flush()
            
            # Start main application
            app = GUIChatClient(username=username, persona=persona)
            app.run()
        else:
            print("登录已取消")
            sys.stdout.flush()
    
    except Exception as e:
        print(f"[ERROR] 程序崩溃: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()


if __name__ == "__main__":
    main()
