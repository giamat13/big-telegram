"""
show_message.py – מציג הודעות ממתינות שהגיעו ממעקב Telegram.
מציג כל הודעה בגדול על המסך עם אפשרות לסמן כ"נראה".

הרץ: python show_message.py
"""

import json
import sys
import os
import platform
from pathlib import Path
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:
    print("❌ חסר tkinter. ב-Linux הרץ: sudo apt-get install python3-tk")
    sys.exit(1)

SCRIPT_DIR  = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"


def load_config():
    if not CONFIG_PATH.exists():
        return {"messages_file": "pending_messages.json"}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_messages(msg_file: Path):
    if not msg_file.exists():
        return []
    try:
        with open(msg_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_messages(msg_file: Path, messages: list):
    with open(msg_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# ─── חלון הצגת הודעה ──────────────────────────────────────────────────────────
class MessageViewer:
    def __init__(self, root: tk.Tk, messages: list, msg_file: Path):
        self.root      = root
        self.messages  = messages          # כל ההודעות
        self.unseen    = [m for m in messages if not m.get("seen")]
        self.msg_file  = msg_file
        self.index     = 0

        self._setup_window()
        self._build_ui()
        self._show_current()

    # ── הגדרות חלון ────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("📨 הודעות ממתינות")
        self.root.configure(bg="#0a0a1a")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.bind("<Escape>", lambda e: self._close())
        self.root.bind("<Return>", lambda e: self._mark_seen_and_next())
        self.root.bind("<Right>", lambda e: self._next())
        self.root.bind("<Left>",  lambda e: self._prev())

    # ── בניית ממשק ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        # רקע שכבה
        self.canvas = tk.Canvas(self.root, bg="#0a0a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # מסגרת מרכזית
        frame = tk.Frame(self.root, bg="#12122a",
                         highlightbackground="#3a3aff",
                         highlightthickness=3,
                         bd=0)
        frame.place(relx=0.5, rely=0.5, anchor="center",
                    width=min(sw - 120, 1200), height=min(sh - 120, 780))

        # כותרת
        self.lbl_title = tk.Label(frame,
            text="",
            bg="#12122a", fg="#7b7bff",
            font=("Segoe UI", 18, "bold"),
            wraplength=min(sw - 200, 1100),
            justify="center")
        self.lbl_title.pack(pady=(40, 10))

        # שם שולח
        self.lbl_sender = tk.Label(frame,
            text="",
            bg="#12122a", fg="#ffffff",
            font=("Segoe UI", 38, "bold"),
            wraplength=min(sw - 200, 1100),
            justify="center")
        self.lbl_sender.pack(pady=(0, 20))

        # גוף ההודעה
        self.lbl_msg = tk.Label(frame,
            text="",
            bg="#12122a", fg="#e8e8ff",
            font=("Segoe UI", 30),
            wraplength=min(sw - 200, 1100),
            justify="center")
        self.lbl_msg.pack(pady=20, padx=40, expand=True)

        # זמן
        self.lbl_time = tk.Label(frame,
            text="",
            bg="#12122a", fg="#555599",
            font=("Segoe UI", 14))
        self.lbl_time.pack(pady=(0, 20))

        # מונה
        self.lbl_counter = tk.Label(frame,
            text="",
            bg="#12122a", fg="#4444aa",
            font=("Segoe UI", 13))
        self.lbl_counter.pack()

        # כפתורים
        btn_frame = tk.Frame(frame, bg="#12122a")
        btn_frame.pack(pady=30)

        btn_style = {
            "font": ("Segoe UI", 16, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 30, "pady": 12,
            "bd": 0,
        }

        self.btn_seen = tk.Button(btn_frame,
            text="✅  סמן כנראה (Enter)",
            bg="#1e6b1e", fg="white",
            activebackground="#2a8a2a", activeforeground="white",
            command=self._mark_seen_and_next,
            **btn_style)
        self.btn_seen.pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame,
            text="⬅  הקודם",
            bg="#1a1a4a", fg="white",
            activebackground="#2a2a6a", activeforeground="white",
            command=self._prev,
            **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame,
            text="➡  הבא",
            bg="#1a1a4a", fg="white",
            activebackground="#2a2a6a", activeforeground="white",
            command=self._next,
            **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame,
            text="✔  סמן הכל כנראה",
            bg="#4a1a1a", fg="white",
            activebackground="#6a2a2a", activeforeground="white",
            command=self._mark_all_seen,
            **btn_style).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame,
            text="✖  סגור (Esc)",
            bg="#2a0000", fg="#ff6666",
            activebackground="#3a0000", activeforeground="#ff9999",
            command=self._close,
            **btn_style).pack(side=tk.LEFT, padx=10)

        # רמז מקשים
        tk.Label(frame,
            text="← → ניווט  |  Enter = סמן כנראה  |  Esc = סגור",
            bg="#12122a", fg="#333366",
            font=("Segoe UI", 11)).pack(pady=(0, 10))

    # ── עדכון תצוגה ────────────────────────────────────────────────────────────
    def _show_current(self):
        if not self.unseen:
            self.lbl_title.config(text="🎉 אין הודעות חדשות")
            self.lbl_sender.config(text="")
            self.lbl_msg.config(text="כל ההודעות נראו.")
            self.lbl_time.config(text="")
            self.lbl_counter.config(text="")
            self.btn_seen.config(state=tk.DISABLED)
            print("✅ כל ההודעות נקראו - הצפצופים אמורים להיעצר")
            return

        msg = self.unseen[self.index]

        try:
            dt  = datetime.fromisoformat(msg["timestamp"])
            ts  = dt.strftime("%d/%m/%Y  %H:%M:%S")
        except Exception:
            ts = msg.get("timestamp", "")

        seen_mark = ""
        self.lbl_title.config(text=f"📨 הודעה חדשה מטלגרם {seen_mark}")
        self.lbl_sender.config(text=f"👤 {msg.get('sender_name', '?')}")
        self.lbl_msg.config(text=msg.get("text", ""))
        self.lbl_time.config(text=f"🕐 {ts}")
        self.lbl_counter.config(
            text=f"הודעה {self.index + 1} מתוך {len(self.unseen)} לא-נראות")
        self.btn_seen.config(state=tk.NORMAL)
        print(f"💬 מציג הודעה {self.index + 1}/{len(self.unseen)} מ-{msg.get('sender_name', '?')}")

    # ── פעולות ─────────────────────────────────────────────────────────────────
    def _mark_seen_and_next(self):
        if not self.unseen:
            return
        msg = self.unseen[self.index]
        # סמן כנראה במערך המקורי
        for m in self.messages:
            if (m.get("timestamp") == msg.get("timestamp") and
                    m.get("sender_id") == msg.get("sender_id")):
                m["seen"] = True
                break
        save_messages(self.msg_file, self.messages)
        print(f"✅ הודעה סומנה כנראתה מ-{msg.get('sender_name', '?')}")

        self.unseen.pop(self.index)
        if self.unseen:
            self.index = min(self.index, len(self.unseen) - 1)
        self._show_current()

    def _mark_all_seen(self):
        for m in self.messages:
            m["seen"] = True
        save_messages(self.msg_file, self.messages)
        print(f"✅ כל {len(self.unseen)} ההודעות סומנו כנראו")
        self.unseen.clear()
        self.index = 0
        self._show_current()

    def _next(self):
        if self.unseen:
            self.index = (self.index + 1) % len(self.unseen)
            self._show_current()

    def _prev(self):
        if self.unseen:
            self.index = (self.index - 1) % len(self.unseen)
            self._show_current()

    def _close(self):
        self.root.destroy()


# ─── כניסה ────────────────────────────────────────────────────────────────────
def main():
    cfg      = load_config()
    msg_file = SCRIPT_DIR / cfg.get("messages_file", "pending_messages.json")
    messages = load_messages(msg_file)

    unseen_count = sum(1 for m in messages if not m.get("seen"))

    if not messages:
        print("📭 אין הודעות שמורות עדיין.")
        print("   (monitor.py צריך לרוץ ברקע כדי לאסוף הודעות)")
        # הצג בכל זאת חלון נוח
    
    if unseen_count == 0 and messages:
        print("✅ כל ההודעות כבר נראו.")

    print(f"📬 נמצאו {unseen_count} הודעות לא-נראות (סה״כ: {len(messages)})")

    root = tk.Tk()
    app  = MessageViewer(root, messages, msg_file)
    root.mainloop()


if __name__ == "__main__":
    main()
