"""
XChat — Modern Distributed Chat Client

Features:
- Auto-start local server (works in EXE and script mode)
- Beautiful modern dark UI with Discord-inspired design
- API Key settings panel (SiliconFlow)
- Chat bubbles, Bot integration, sentiment analysis
"""

import os, sys, subprocess, socket, time, threading, queue, json
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config.settings as cfg
from client.chat_client import ChatClient
from client.login_dialog import show_login_dialog
from bot.ai_bot import AIBot, get_bot, reset_bot
from bot.sentiment_analyzer import get_analyzer
from bot.summary_generator import SummaryGenerator

# ═══════════════════════════════════════════════════════
#  THEME — Discord / Slack inspired dark palette
# ═══════════════════════════════════════════════════════
T = {
    "bg":         "#1e1f22",
    "sidebar":    "#2b2d31",
    "topbar":     "#2b2d31",
    "input_bg":   "#383a40",
    "chat_bg":    "#1e1f22",
    "bubble_me":  "#5865f2",
    "bubble_you": "#3f4147",
    "bubble_bot": "#8b5cf6",
    "text":       "#dbdee1",
    "muted":      "#949ba4",
    "white":      "#ffffff",
    "accent":     "#5865f2",
    "accent_hov": "#4752c4",
    "green":      "#23a55a",
    "red":        "#f23f42",
    "yellow":     "#f0b232",
    "border":     "#3f4147",
}


class APISettingsDialog:
    """Settings dialog for API key."""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("API Settings")
        self.dialog.geometry("460x340")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=T["sidebar"])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self._build()

    def _build(self):
        f = tk.Frame(self.dialog, bg=T["sidebar"], padx=24, pady=20)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="🤖 AI Bot Settings", font=("Segoe UI", 13, "bold"),
                 fg=T["text"], bg=T["sidebar"]).pack(anchor="w", pady=(0, 6))
        tk.Label(f, text="Enter API key to enable Bot. Chat works without it.",
                 font=("Segoe UI", 9), fg=T["muted"], bg=T["sidebar"]).pack(anchor="w", pady=(0, 14))

        tk.Label(f, text="SiliconFlow API Key", font=("Segoe UI", 9),
                 fg=T["muted"], bg=T["sidebar"]).pack(anchor="w")
        kf = tk.Frame(f, bg=T["sidebar"]); kf.pack(fill="x", pady=(3, 10))

        self.kv = tk.StringVar(value=os.getenv("SILICONFLOW_API_KEY", ""))
        self.ke = tk.Entry(kf, textvariable=self.kv, show="•", font=("Segoe UI", 10),
                           bg=T["input_bg"], fg=T["text"], insertbackground=T["text"],
                           relief="flat", bd=8)
        self.ke.pack(side="left", fill="x", expand=True)
        self._showing = False
        tk.Button(kf, text="👁", width=3, font=("Segoe UI", 9),
                  bg=T["input_bg"], fg=T["muted"], relief="flat", bd=0,
                  command=self._toggle).pack(side="right", padx=(4, 0))

        tk.Label(f, text="Model", font=("Segoe UI", 9), fg=T["muted"], bg=T["sidebar"]).pack(anchor="w")
        self.mv = tk.StringVar(value=os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct"))
        cb = ttk.Combobox(f, textvariable=self.mv, state="readonly", font=("Segoe UI", 10),
                          values=["Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-14B-Instruct",
                                  "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1"])
        cb.pack(fill="x", pady=(3, 8))

        self.st = tk.Label(f, text="", font=("Segoe UI", 9), bg=T["sidebar"])
        self.st.pack(anchor="w", pady=(2, 14))

        bf = tk.Frame(f, bg=T["sidebar"]); bf.pack(fill="x")
        tk.Button(bf, text="Cancel", command=self.dialog.destroy, font=("Segoe UI", 10),
                  bg=T["input_bg"], fg=T["text"], relief="flat", padx=16, pady=5).pack(side="right", padx=(6, 0))
        tk.Button(bf, text="Save & Apply", command=self._save, font=("Segoe UI", 10, "bold"),
                  bg=T["accent"], fg=T["white"], relief="flat", padx=16, pady=5).pack(side="right")

        tk.Label(f, text="Get free key at cloud.siliconflow.cn", font=("Segoe UI", 8),
                 fg=T["accent"], bg=T["sidebar"], cursor="hand2").pack(side="left", pady=(6, 0))

    def _toggle(self):
        self._showing = not self._showing
        self.ke.config(show="" if self._showing else "•")

    def _save(self):
        k = self.kv.get().strip()
        if k and k != "sk-your-siliconflow-key-here":
            os.environ["SILICONFLOW_API_KEY"] = k
            os.environ["SILICONFLOW_MODEL"] = self.mv.get()
            self.st.config(text="✅ Saved! Bot will use SiliconFlow.", fg=T["green"])
            self.dialog.after(1000, self.dialog.destroy)
        else:
            self.st.config(text="⚠️ Please enter a valid API key", fg=T["red"])


# ═══════════════════════════════════════════════════════
#  MAIN CHAT CLIENT
# ═══════════════════════════════════════════════════════
class XChatClient:
    def __init__(self, username: str, persona: str = "helpful",
                 mode: str = "host", host: str = "127.0.0.1", port: int = 1112):
        self.username = username
        self.persona = persona
        self.mode = mode
        self.host = host
        self.port = port
        self.client: Optional[ChatClient] = None
        self.connected = False
        self.bot: Optional[AIBot] = None
        self.chat_history: List[str] = []
        self.analyzer = get_analyzer()
        self.gui_queue = queue.Queue()

        self.root = tk.Tk()
        self.root.title(f"XChat — {username}")
        self.root.geometry("900x680")
        self.root.minsize(700, 480)
        self.root.configure(bg=T["bg"])

        self._build_ui()
        self._start_server()
        self._connect()
        self._poll()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    # ── Server ──────────────────────────────────────────
    def _start_server(self):
        """Start local server only in Host mode."""
        if self.mode != "host":
            self._sysmsg(f"🔗 Joining {self.host}:{self.port}...")
            return

        if self._server_alive(self.host, self.port):
            return

        self._sysmsg("⏳ Starting server...")
        try:
            # Set config to match before starting server
            cfg.CHAT_IP = self.host
            cfg.CHAT_PORT = self.port
            cfg.SERVER = (self.host, self.port)

            from server.chat_server import Server
            def _run():
                srv = Server()
                srv.run()
            t = threading.Thread(target=_run, daemon=True)
            t.start()

            for _ in range(30):
                time.sleep(0.1)
                if self._server_alive(self.host, self.port):
                    self._sysmsg(f"✅ Server ready on {self.host}:{self.port}")
                    return
            self._sysmsg("⚠️  Server starting slowly...")
        except Exception as e:
            self._sysmsg(f"❌ Server start failed: {e}")

    def _server_alive(self, host=None, port=None):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            ok = s.connect_ex((host or cfg.CHAT_IP, port or cfg.CHAT_PORT)) == 0
            s.close()
            return ok
        except:
            return False

    # ── UI ──────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        tb = tk.Frame(self.root, bg=T["topbar"], height=44)
        tb.pack(fill="x"); tb.pack_propagate(False)

        tk.Label(tb, text="💬  XChat", font=("Segoe UI", 12, "bold"),
                 fg=T["white"], bg=T["topbar"]).pack(side="left", padx=14, pady=8)

        self._dot = tk.Label(tb, text="●", font=("Segoe UI", 9), fg=T["yellow"], bg=T["topbar"])
        self._dot.pack(side="left")

        self._st = tk.Label(tb, text=" Connecting...", font=("Segoe UI", 9),
                            fg=T["muted"], bg=T["topbar"])
        self._st.pack(side="left", padx=(2, 0))

        self._bstat = tk.Label(tb, text="🤖 Bot: OFF", font=("Segoe UI", 9),
                               fg=T["muted"], bg=T["topbar"])
        self._bstat.pack(side="right", padx=(0, 8), pady=10)

        tk.Button(tb, text="⚙", font=("Segoe UI", 13), bg=T["topbar"], fg=T["muted"],
                  relief="flat", bd=0, activebackground=T["topbar"],
                  command=self._settings).pack(side="right", padx=(0, 2), pady=6)

        # Main area: sidebar + chat
        body = tk.Frame(self.root, bg=T["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar
        sb = tk.Frame(body, bg=T["sidebar"], width=180)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)

        tk.Label(sb, text="ONLINE", font=("Segoe UI", 8, "bold"),
                 fg=T["muted"], bg=T["sidebar"]).pack(anchor="w", padx=12, pady=(14, 6))
        self._ulist = tk.Text(sb, font=("Segoe UI", 10), bg=T["sidebar"], fg=T["text"],
                              relief="flat", bd=0, padx=12, pady=4, state="disabled",
                              cursor="arrow", height=20)
        self._ulist.pack(fill="both", expand=True)

        tk.Label(sb, text="", font=("Segoe UI", 8), fg=T["muted"], bg=T["sidebar"]).pack(pady=(0, 4))

        # Chat area
        cr = tk.Frame(body, bg=T["chat_bg"])
        cr.pack(side="left", fill="both", expand=True)

        self._chat = tk.Text(cr, state="disabled", wrap="word", font=("Segoe UI", 10),
                             bg=T["chat_bg"], fg=T["text"], relief="flat", bd=0,
                             padx=14, pady=10, selectbackground=T["accent"], cursor="arrow")
        self._chat.pack(fill="both", expand=True)

        # Tags
        self._chat.tag_config("me", foreground=T["white"], background=T["bubble_me"],
                               lmargin1=100, lmargin2=100, rmargin=16,
                               spacing1=6, spacing3=6, font=("Segoe UI", 10), wrap="word")
        self._chat.tag_config("you", foreground=T["text"], background=T["bubble_you"],
                               lmargin1=16, lmargin2=16, rmargin=100,
                               spacing1=6, spacing3=6, font=("Segoe UI", 10), wrap="word")
        self._chat.tag_config("bot", foreground=T["white"], background=T["bubble_bot"],
                               lmargin1=16, lmargin2=16, rmargin=100,
                               spacing1=6, spacing3=6, font=("Segoe UI", 10, "italic"), wrap="word")
        self._chat.tag_config("sys", foreground=T["muted"], justify="center",
                               spacing1=4, spacing3=4, font=("Segoe UI", 8))

        # Bottom bar
        bb = tk.Frame(self.root, bg=T["input_bg"], padx=12, pady=8)
        bb.pack(fill="x")

        for em in ["😊","👍","🎉","🤔","❤️","👋","🔥","💡"]:
            tk.Button(bb, text=em, width=2, font=("Segoe UI", 13), bg=T["input_bg"],
                      fg=T["text"], relief="flat", bd=0, activebackground=T["sidebar"],
                      command=lambda e=em: self._emoji(e)).pack(side="left", padx=1)

        self._entry = tk.Entry(bb, font=("Segoe UI", 11), bg=T["chat_bg"], fg=T["text"],
                                insertbackground=T["text"], relief="flat", bd=8)
        self._entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._entry.bind("<Return>", lambda e: self._send())
        self._entry.focus_set()

        tk.Button(bb, text="Send  ➤", font=("Segoe UI", 10, "bold"), bg=T["accent"],
                  fg=T["white"], relief="flat", padx=18, pady=7,
                  activebackground=T["accent_hov"], command=self._send).pack(side="right", padx=(6, 0))

    # ── Connection ──────────────────────────────────────
    def _connect(self):
        self.client = ChatClient(self.username, host=self.host, port=self.port)
        self.client.on_connected = self._on_conn
        self.client.on_disconnected = self._on_disc
        self.client.on_message_received = self._on_msg
        if self.client.connect() and self.client.login():
            pass
        else:
            self._sysmsg(f"❌ Cannot reach {self.host}:{self.port}. Is the host running?")

    def _on_conn(self):
        self.connected = True
        self._dot.config(fg=T["green"])
        mode_label = "🏠 Host" if self.mode == "host" else f"🔗 {self.host}"
        self._st.config(text=f" {self.username}  |  {mode_label}")
        reset_bot(); self.bot = get_bot(persona=self.persona)
        self._update_bot()
        self._sysmsg(f"👋 Welcome, {self.username}! ({mode_label})")

    def _on_disc(self):
        self.connected = False
        self._dot.config(fg=T["red"])
        self._st.config(text=" Disconnected")

    def _update_bot(self):
        if self.bot and self.bot.siliconflow_available:
            self._bstat.config(text="🤖 Bot: ON", fg=T["green"])
        elif self.bot and self.bot.ollama_available:
            self._bstat.config(text="🤖 Bot: Local", fg=T["yellow"])
        else:
            self._bstat.config(text="🤖 Bot: OFF", fg=T["muted"])

    # ── Messages ────────────────────────────────────────
    def _on_msg(self, d): self.gui_queue.put(d)

    def _poll(self):
        try:
            while True: self._handle(self.gui_queue.get_nowait())
        except queue.Empty: pass
        self.root.after(100, self._poll)

    def _handle(self, d):
        a = d.get("action","")
        if a == "exchange":
            s, c = d.get("from",""), d.get("message","")
            if s == self.username: return
            self.chat_history.append(f"{s}: {c}")
            if c.startswith("🤖 Bot:"):
                self._show(f"{s} {c}", "bot")
            else:
                em = self.analyzer.analyze(c)["emoji"]
                self._show(f"{s}: {c}", "you", em)
        elif a == "bot_response":
            self._show(f"🤖 Bot: {d.get('content','')}", "bot")
        elif a in ("list","time","search"):
            r = d.get("results","")
            self._sysmsg({"list":"👥 Online","time":"🕐 Time","search":"🔍"}.get(a,"")+f"\n{r}")

    def _send(self):
        c = self._entry.get().strip()
        if not c: return
        self._entry.delete(0, "end")
        if c.startswith("/"):
            self._cmd(c); return
        if self.connected and self.client:
            self.client.send_message(c, broadcast=True)
        self._show(f"{self.username}: {c}", "me")
        self.chat_history.append(f"{self.username}: {c}")
        if self.bot and self._should_bot(c):
            self._bot_reply(c)

    def _should_bot(self, c):
        return c.lower().startswith("@bot") or "@bot" in c.lower()

    def _bot_reply(self, uc):
        def r():
            resp = self.bot.chat(uc)
            be = f"🤖 Bot: {resp}"
            self.chat_history.append(be)
            if self.connected and self.client:
                self.client.send_message(be, broadcast=True)
            self.gui_queue.put({"action":"bot_response","content":resp})
        threading.Thread(target=r, daemon=True).start()

    def _cmd(self, c):
        cmd = c.lower().split()[0].rstrip(":")
        if cmd == "/help":
            messagebox.showinfo("XChat Help",
                "Commands:\n"
                "  /users   — List online users\n"
                "  /time    — Server time\n"
                "  /clear   — Clear chat\n"
                "  /summary — AI summary\n"
                "  /aipic   — Generate image\n"
                "  /persona — Change bot style\n"
                "  /settings— API key\n"
                "  @Bot ... — Talk to AI")
        elif cmd == "/summary":
            if self.chat_history:
                g = SummaryGenerator(llm_client=self.bot)
                self._sysmsg(g.generate(self.chat_history))
            else:
                self._sysmsg("No chat history yet.")
        elif cmd == "/aipic":
            if self.bot:
                r = self.bot.chat(c); self._show(f"🤖 Bot: {r}", "bot")
                self.chat_history.append(f"🤖 Bot: {r}")
        elif cmd == "/persona":
            p = c.split(maxsplit=1)
            if len(p)>1 and self.bot and self.bot.set_persona(p[1].lower()):
                self._sysmsg(f"🎭 Persona → {p[1].lower()}")
        elif cmd == "/clear":
            self._chat.config(state="normal"); self._chat.delete("1.0","end")
            self._chat.config(state="disabled"); self._sysmsg("🧹 Cleared")
        elif cmd == "/settings": self._settings()
        elif cmd == "/users":
            if self.client: self.client.list_users()
        elif cmd == "/time":
            if self.client: self.client.get_time()
        elif cmd in ("/quit","/exit"): self._close()
        else: self._sysmsg(f"❓ Unknown: {cmd}")

    def _settings(self):
        APISettingsDialog(self.root)
        self.root.after(500, self._reinit_bot)

    def _reinit_bot(self):
        reset_bot(); self.bot = get_bot(persona=self.persona)
        self._update_bot()
        if self.bot.siliconflow_available:
            self._sysmsg("🤖 Bot now powered by SiliconFlow!")
        elif self.bot.ollama_available:
            self._sysmsg("🤖 Bot using local Ollama.")
        else:
            self._sysmsg("ℹ️  Set API key in Settings to enable Bot.")

    # ── Display ─────────────────────────────────────────
    def _show(self, text, tag, emoji=""):
        def ins():
            self._chat.config(state="normal")
            pfx = f"{emoji} " if emoji else ""
            self._chat.insert("end", f"{pfx}{text}\n", tag)
            self._chat.config(state="disabled"); self._chat.see("end")
        if threading.current_thread() is threading.main_thread(): ins()
        else: self.root.after(0, ins)

    def _sysmsg(self, text):
        def ins():
            self._chat.config(state="normal")
            self._chat.insert("end", f"  {text}\n", "sys")
            self._chat.config(state="disabled"); self._chat.see("end")
        if threading.current_thread() is threading.main_thread(): ins()
        else: self.root.after(0, ins)

    def _emoji(self, e):
        self._entry.insert("insert", e+" "); self._entry.focus_set()

    def _close(self):
        if self.client: self.client.disconnect()
        self.root.destroy()

    def run(self): self.root.mainloop()


def main():
    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            print("[ERROR] No display available."); return
    u, p, mode, ip, port = show_login_dialog(None)
    if u:
        try: port = int(port)
        except: port = 1112
        XChatClient(username=u, persona=p, mode=mode, host=ip, port=port).run()


if __name__ == "__main__":
    main()
