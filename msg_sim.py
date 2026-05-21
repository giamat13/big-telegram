"""  
msg_sim.py - סימולציה של הודעה נכנסת לבדיקת המערכת
מדמה הודעה שמגיעה ומפעיל את לוגיקת בדיקת העכבר והצפצופים
"""

import json
import sys
import asyncio
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"

# ייבוא הפונקציות מ-main.py
sys.path.insert(0, str(SCRIPT_DIR))
from main import save_message, beep_if_user_present, load_config

def simulate_message():
    cfg = load_config()
    
    sender_name = "Test User (סימולציה)"
    sender_id = 999999
    text = f"זוהי הודעת בדיקה מסימולציה - {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"\n🔔 מדמה הודעה נכנסת...")
    print(f"   שולח: {sender_name}")
    print(f"   תוכן: {text}\n")
    
    # שמור הודעה
    save_message(cfg, sender_name, sender_id, text)
    print("✅ הודעה נשמרה\n")
    
    # הפעל בדיקת עכבר + צפצופים
    print("🔍 מתחיל בדיקת נוכחות משתמש (עכבר)...")
    print("   זוז את העכבר כדי לבדוק שהצפצופים מתחילים")
    print("   או השאר אותו במקום כדי לבדוק שהצפצופים מתבטלים\n")
    
    beep_if_user_present(cfg)
    
    # המתן מספיק זמן לבדיקה + צפצופים
    import time
    time.sleep(20)
    print("\n✅ סימולציה הסתיימה (לחץ Ctrl+C אם הצפצופים ממשיכים)")

if __name__ == "__main__":
    simulate_message()
