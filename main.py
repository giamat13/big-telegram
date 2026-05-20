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
def beep(frequency: int, duration_ms: int, repeat: int):
    """מנגן צפצוף – עובד על Windows, macOS, Linux."""
    def _beep():
        for i in range(repeat):
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(frequency, duration_ms)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"osascript -e 'beep {repeat}'")
                return  # osascript כבר מטפל בחזרה
            else:  # Linux
                # נסה beep, אם לא קיים – השתמש ב-speaker-test
                ret = os.system(f"beep -f {frequency} -l {duration_ms} 2>/dev/null")
                if ret != 0:
                    os.system(f"python3 -c \""
                              f"import subprocess; subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'], "
                              f"capture_output=True)\"")
            if i < repeat - 1:
                time.sleep(0.3)
    
    t = threading.Thread(target=_beep, daemon=True)
    t.start()

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
    beep_cfg    = cfg.get("beep", {"frequency": 1000, "duration_ms": 500, "repeat": 3})
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
        beep(beep_cfg["frequency"], beep_cfg["duration_ms"], beep_cfg["repeat"])
    
    await client.start()
    print("✅ מחובר לטלגרם. ממתין להודעות... (Ctrl+C לעצירה)\n")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 הסתיים.")
