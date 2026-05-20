# 📨 Telegram Alert Monitor

מערכת Python לניטור הודעות Telegram מאנשי קשר מסוימים.
- **monitor.py** – רץ ברקע, מאזין להודעות, מצפצף כשמגיע משהו
- **show_message.py** – מציג בגדול על המסך את כל ההודעות שהתקבלו
- **config.json** – כל ההגדרות

---

## ⚙️ הגדרה ראשונית

### שלב 1 – קבל API מטלגרם
1. לך ל: https://my.telegram.org/auth
2. התחבר עם מספר הטלפון שלך
3. לחץ **"API development tools"**
4. צור אפליקציה חדשה (שם + תיאור כלשהם)
5. קבל `api_id` ו-`api_hash`

### שלב 2 – ערוך config.json
```json
{
    "api_id": "12345678",           ← ה-api_id שלך
    "api_hash": "abcdef1234...",    ← ה-api_hash שלך
    "watched_contacts": [
        "username_של_האיש_קשר",    ← ה-@ של הטלגרם (בלי @)
        "+972501234567"             ← או מספר טלפון
    ],
    "beep": {
        "frequency": 1000,          ← תדירות הצפצוף (Hz)
        "duration_ms": 500,         ← אורך כל צפצוף (מילישניות)
        "repeat": 3                 ← כמה פעמים לצפצף
    }
}
```

**watched_contacts** – אפשר לרשום:
- שם משתמש: `"john_doe"` (בלי @)
- מספר טלפון: `"+972501234567"`
- שם פרטי: `"יוסי"` (פחות מדויק)

### שלב 3 – התקן תלויות
```bash
pip install telethon
```

---

## 🚀 הפעלה

### הרצה ידנית
```bash
# טרמינל 1 – הניטור (יישאר פתוח ברקע)
python monitor.py

# בפעם הראשונה יבקש:
# - מספר טלפון (עם קידומת מדינה: +972...)
# - קוד אימות שיגיע לטלגרם שלך
# - סיסמת 2FA אם מוגדרת

# טרמינל 2 – כשרוצים לראות הודעות
python show_message.py
```

### הרצה בסטארטאפ (Windows)
1. לחץ `Win+R` → הקלד `shell:startup`
2. צור קובץ `telegram_monitor.bat`:
```bat
@echo off
cd /d "C:\path\to\telegram_alert"
python monitor.py
```
3. גרור אותו לתיקיית ה-Startup

### הרצה בסטארטאפ (macOS)
```bash
# הוסף ל-~/.zshrc או צור LaunchAgent
# או פשוט הרץ בטרמינל ברקע:
nohup python monitor.py &
```

---

## 🖥️ ממשק show_message.py

| מקש | פעולה |
|-----|-------|
| `Enter` | סמן הודעה כנראה + עבור לבאה |
| `→` | הודעה הבאה |
| `←` | הודעה הקודמת |
| `Esc` | סגור |

כפתור **"סמן הכל כנראה"** – מנקה את כל ההודעות בבת אחת.

---

## 🗂️ קבצים שנוצרים

- `telegram_monitor.session` – קובץ הסשן של Telethon (שמור! זה ה"זיכרון" של ההתחברות)
- `pending_messages.json` – ההודעות שנשמרו ממתינות לצפייה

---

## 🔔 צפצוף

| מערכת | שיטה |
|-------|------|
| Windows | `winsound.Beep` (מובנה, ללא תלויות) |
| macOS | `osascript beep` |
| Linux | `beep` או `paplay` (freedesktop sounds) |

ב-Linux אם לא שומעים: `sudo apt-get install beep`
