"""XChat Login Dialog — Modern Dark Theme with Host/Join mode"""

import os, tkinter as tk
from tkinter import ttk
from typing import Optional

T = {
    "bg": "#1e1f22", "panel": "#2b2d31", "input_bg": "#383a40",
    "text": "#dbdee1", "muted": "#949ba4", "white": "#ffffff",
    "accent": "#5865f2", "accent_hov": "#4752c4", "red": "#f23f42",
    "green": "#23a55a",
}

class LoginDialog:
    def __init__(self, parent=None):
        self.parent = parent; self.result: Optional[str] = None
        self.mode = "host"  # "host" or "join"
        self.target_ip = "127.0.0.1"
        self.target_port = "1112"
        self.owns_root = parent is None

        self.dialog = tk.Tk() if self.owns_root else tk.Toplevel(parent)
        self.dialog.title("XChat — Login")
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
        self.dialog.configure(bg=T["bg"])
        self.dialog.geometry("400x570")
        self.dialog.attributes("-topmost", True)
        self.dialog.update_idletasks(); self.dialog.deiconify(); self.dialog.lift()
        sw, sh = self.dialog.winfo_screenwidth(), self.dialog.winfo_screenheight()
        self.dialog.geometry(f"400x570+{(sw-400)//2}+{(sh-570)//2}")

        if not self.owns_root:
            self.dialog.transient(parent)
        self.dialog.grab_set(); self.dialog.focus_force()
        self._build()

    def _build(self):
        f = tk.Frame(self.dialog, bg=T["bg"], padx=28, pady=24)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="💬", font=("Segoe UI", 34), bg=T["bg"]).pack(pady=(0,0))
        tk.Label(f, text="XChat", font=("Segoe UI", 20, "bold"),
                 fg=T["white"], bg=T["bg"]).pack()
        tk.Label(f, text="Distributed Intelligent Chat",
                 font=("Segoe UI", 8), fg=T["muted"], bg=T["bg"]).pack(pady=(0,14))

        # ── Mode selection ──
        mf = tk.LabelFrame(f, text="  CONNECTION MODE  ", font=("Segoe UI", 8, "bold"),
                           fg=T["muted"], bg=T["bg"], relief="solid", bd=1, padx=8, pady=6)
        mf.pack(fill="x", pady=(0,10))

        self.mode_var = tk.StringVar(value="host")
        tk.Radiobutton(mf, text="🏠  Host  —  Start server on my computer",
                       variable=self.mode_var, value="host", font=("Segoe UI", 10),
                       fg=T["text"], bg=T["bg"], selectcolor=T["panel"],
                       activebackground=T["bg"], activeforeground=T["white"],
                       anchor="w", padx=4, pady=2,
                       command=self._on_mode).pack(fill="x")
        tk.Radiobutton(mf, text="🔗  Join  —  Connect to friend's server",
                       variable=self.mode_var, value="join", font=("Segoe UI", 10),
                       fg=T["text"], bg=T["bg"], selectcolor=T["panel"],
                       activebackground=T["bg"], activeforeground=T["white"],
                       anchor="w", padx=4, pady=2,
                       command=self._on_mode).pack(fill="x")

        # ── Join fields (hidden initially) ──
        self.join_frame = tk.Frame(f, bg=T["bg"])

        tk.Label(self.join_frame, text="Server IP", font=("Segoe UI", 8, "bold"),
                 fg=T["muted"], bg=T["bg"]).pack(anchor="w")
        ipf = tk.Frame(self.join_frame, bg=T["bg"]); ipf.pack(fill="x", pady=(2,6))
        self.ip_entry = tk.Entry(ipf, font=("Segoe UI", 10), bg=T["input_bg"], fg=T["text"],
                                 insertbackground=T["text"], relief="flat", bd=8)
        self.ip_entry.pack(side="left", fill="x", expand=True)
        self.ip_entry.insert(0, "127.0.0.1")
        tk.Label(ipf, text=" : ", font=("Segoe UI", 10), fg=T["muted"], bg=T["bg"]).pack(side="left")
        self.port_entry = tk.Entry(ipf, font=("Segoe UI", 10), bg=T["input_bg"], fg=T["text"],
                                    insertbackground=T["text"], relief="flat", bd=8, width=6)
        self.port_entry.pack(side="left")
        self.port_entry.insert(0, "1112")

        # ── Username ──
        tk.Label(f, text="USERNAME", font=("Segoe UI", 8, "bold"),
                 fg=T["muted"], bg=T["bg"]).pack(anchor="w", pady=(6, 0))
        self.ue = tk.Entry(f, font=("Segoe UI", 11), bg=T["input_bg"], fg=T["text"],
                           insertbackground=T["text"], relief="flat", bd=10)
        self.ue.pack(fill="x", pady=(3,10)); self.ue.focus_set()
        self.ue.bind("<Return>", lambda e: self._ok())

        # ── Persona ──
        tk.Label(f, text="BOT PERSONA  (optional)", font=("Segoe UI", 8, "bold"),
                 fg=T["muted"], bg=T["bg"]).pack(anchor="w")

        pf = tk.Frame(f, bg=T["input_bg"], padx=4, pady=4)
        pf.pack(fill="x", pady=(3,10))

        self.pv = tk.StringVar(value="helpful")
        for txt, val in [("😊  Helpful","helpful"),("🎭  Humorous","humorous"),
                         ("💼  Serious","serious"),("🎨  Creative","creative"),
                         ("📚  Advisor","advisor")]:
            tk.Radiobutton(pf, text=txt, variable=self.pv, value=val,
                           font=("Segoe UI", 10), fg=T["text"], bg=T["input_bg"],
                           selectcolor=T["panel"], activebackground=T["input_bg"],
                           activeforeground=T["white"], anchor="w", padx=6, pady=2
                           ).pack(fill="x")

        self.sl = tk.Label(f, text="", font=("Segoe UI", 9), fg=T["red"], bg=T["bg"])
        self.sl.pack(pady=(0,10))

        bf = tk.Frame(f, bg=T["bg"]); bf.pack(fill="x")
        tk.Button(bf, text="Cancel", command=self._cancel, font=("Segoe UI", 10),
                  bg=T["input_bg"], fg=T["text"], relief="flat", padx=16, pady=6).pack(side="right", padx=(6,0))
        tk.Button(bf, text="🚀  Connect", command=self._ok, font=("Segoe UI", 10, "bold"),
                  bg=T["accent"], fg=T["white"], relief="flat", padx=16, pady=6).pack(side="right")

    def _on_mode(self):
        if self.mode_var.get() == "join":
            self.join_frame.pack(fill="x", before=self.sl)
        else:
            self.join_frame.pack_forget()

    def _ok(self):
        u = self.ue.get().strip()
        if not u: self.sl.config(text="Enter a username"); return
        if len(u)<2: self.sl.config(text="At least 2 characters"); return
        if len(u)>20: self.sl.config(text="Max 20 characters"); return
        if not all(c.isalnum() or c=="_" for c in u):
            self.sl.config(text="Letters, numbers, underscores only"); return
        self.mode = self.mode_var.get()
        self.target_ip = self.ip_entry.get().strip() or "127.0.0.1"
        self.target_port = self.port_entry.get().strip() or "1112"
        self.result = u; self.dialog.destroy(); self.dialog.quit()

    def _cancel(self):
        self.result = None; self.dialog.destroy(); self.dialog.quit()

    def get_username(self): return self.result
    def get_persona(self): return self.pv.get()


def show_login_dialog(parent) -> tuple:
    """Returns (username, persona, mode, target_ip, target_port)"""
    d = LoginDialog(parent); d.dialog.mainloop()
    u, p = d.get_username(), d.get_persona()
    if d.owns_root:
        try: d.dialog.destroy()
        except: pass
    return u, p, d.mode, d.target_ip, d.target_port
