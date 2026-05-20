"""
monitor.py – רץ ברקע ומנטר הודעות טלגרם מאנשי קשר מוגדרים.
כשמגיעה הודעה: מצפצף + שומר להצגה מאוחרת.

התקנה:
    pip install telethon

הגדרה ראשונה:
    1. לך ל https://my.telegram.org → App configuration
    2. צור App → קבל api_id ו-api_hash
    3. הכנס אותם ב-config.json
    4. הרץ: python monitor.py (בפעם הראשונה ישאל על מספר טלפון + קוד)
"""

import asyncio
import json
import os
import sys
import platform
import threading
import time
import subprocess
from datetime import datetime
from pathlib import Path

# ─── הגדרות ביפ ───────────────────────────────────────────────────────────────
BEEP_FREQUENCY  = 1000   # Hz
BEEP_DURATION   = 200    # מילישניות
BEEP_INTERVAL   = 0.4    # שניות בין ביפ לביפ
BEEP_CHECK_READ = 5.0    # שניות בין בדיקות אם נקרא

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import User
except ImportError:
    print("❌ חסרה ספרייה. הרץ: pip install telethon")
    sys.exit(1)

# ─── טעינת קונפיג ─────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"

def load_config():
    if not CONFIG_PATH.exists():
        print(f"❌ לא נמצא config.json ב: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_message(cfg, sender_name: str, sender_id: int, text: str):
    """שומר הודעה לקובץ JSON לצפייה מאוחרת."""
    msg_file = SCRIPT_DIR / cfg["messages_file"]
    
    messages = []
    if msg_file.exists():
        try:
            with open(msg_file, encoding="utf-8") as f:
                messages = json.load(f)
        except Exception:
            messages = []
    
    messages.append({
        "timestamp": datetime.now().isoformat(),
        "sender_name": sender_name,
        "sender_id": sender_id,
        "text": text,
        "seen": False
    })
    
    with open(msg_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# ─── צפצוף ────────────────────────────────────────────────────────────────────
def _all_messages_read(cfg) -> bool:
    """מחזיר True אם כל ההודעות בקובץ נקראו."""
    msg_file = SCRIPT_DIR / cfg["messages_file"]
    if not msg_file.exists():
        return True
    try:
        with open(msg_file, encoding="utf-8") as f:
            messages = json.load(f)
        return all(m.get("seen", False) for m in messages)
    except Exception:
        return True


def beep_until_read(cfg):
    """מצפצף ברציפות, בודק כל 5 שניות אם ההודעות נקראו."""
    def _loop():
        last_check = 0
        while True:
            now = time.time()
            if now - last_check >= BEEP_CHECK_READ:
                if _all_messages_read(cfg):
                    return
                last_check = now
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(BEEP_FREQUENCY, BEEP_DURATION)
            elif platform.system() == "Darwin":
                os.system("osascript -e 'beep'")
            else:
                ret = os.system(f"beep -f {BEEP_FREQUENCY} -l {BEEP_DURATION} 2>/dev/null")
                if ret != 0:
                    os.system("paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null")
            time.sleep(BEEP_INTERVAL)

    threading.Thread(target=_loop, daemon=True).start()

# ─── האזנה ל-F8 ───────────────────────────────────────────────────────────────
def start_hotkey_listener():
    """מאזין ל-F8 גלובלית (ללא Admin) ופותח את show_message.py."""
    try:
        from pynput import keyboard as pynput_kb
    except ImportError:
        print("⚠️  ספריית pynput לא מותקנת – F8 לא יעבוד.")
        print("   הרץ: pip install pynput")
        return

    show_script = SCRIPT_DIR / "show_message.py"
    F8 = pynput_kb.Key.f8

    def on_press(key):
        if key == F8:
            print("\n🖥️  [F8] פותח show_message.py...")
            subprocess.Popen(
                [sys.executable, str(show_script)],
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )

    listener = pynput_kb.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    print("⌨️  לחץ F8 בכל עת כדי לפתוח את show_message.py\n")

# ─── לוגיקה ראשית ─────────────────────────────────────────────────────────────
async def main():
    cfg = load_config()
    
    if cfg["api_id"] == "YOUR_API_ID":
        print("❌ יש להגדיר api_id ו-api_hash ב-config.json")
        print("   לך ל: https://my.telegram.org → API development tools")
        sys.exit(1)
    
    watched_raw = [str(c).lower().strip() for c in cfg.get("watched_contacts", [])]
    session     = SCRIPT_DIR / cfg.get("session_name", "telegram_monitor")
    
    start_hotkey_listener()
    print(f"🚀 מנטר Telegram...")
    print(f"📋 אנשי קשר למעקב: {', '.join(watched_raw)}")
    print(f"📁 הודעות ישמרו ב: {SCRIPT_DIR / cfg['messages_file']}")
    print("   (הרץ show_message.py כדי לראות הודעות ממתינות)\n")
    
    client = TelegramClient(str(session), int(cfg["api_id"]), cfg["api_hash"])
    
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        sender = await event.get_sender()
        if not isinstance(sender, User):
            return
        
        # בנה מזהים לבדיקה: username, phone, שם מלא, first name
        identifiers = set()
        if sender.username:
            identifiers.add(sender.username.lower())
        if sender.phone:
            identifiers.add(sender.phone.strip())
            identifiers.add("+" + sender.phone.strip())
        
        first = (sender.first_name or "").strip()
        last  = (sender.last_name  or "").strip()
        full  = f"{first} {last}".strip().lower()
        if first: identifiers.add(first.lower())
        if full:  identifiers.add(full)
        
        # האם השולח ברשימת המעקב?
        match = any(w in identifiers for w in watched_raw)
        if not match:
            return
        
        sender_name = full if full else (sender.username or str(sender.id))
        text        = event.raw_text or "[הודעה ללא טקסט]"
        
        print(f"\n🔔 [{datetime.now().strftime('%H:%M:%S')}] הודעה מ-{sender_name}:")
        print(f"   {text[:120]}{'...' if len(text) > 120 else ''}")
        
        # שמור + צפצף
        save_message(cfg, sender_name, sender.id, text)
        beep_until_read(cfg)
    
    await client.start()
    print("✅ מחובר לטלגרם. ממתין להודעות... (Ctrl+C לעצירה)\n")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 הסתיים.")
