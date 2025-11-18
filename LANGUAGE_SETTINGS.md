# Language Settings

## 🌍 Platform Language: **ENGLISH ONLY**

All UI elements, messages, logs, and documentation are in **English**.

## Language Configuration

### Default Bot Language
The bot supports two languages for in-game operations:
- `en` - English (default)
- `de` - German

This is set per user in their `BotConfig`:
```python
language = db.Column(db.String(2), default='en')
```

### Admin Email
Default admin email is set to `.com` domain:
- Default: `admin@lkwbot.com`
- Change in `config.py` or `.env` file

## All English Elements

### ✅ Backend (Python)
- All docstrings
- All comments  
- All log messages
- All error messages
- All model descriptions

### ✅ Frontend (HTML/JS)
- All UI text
- All buttons
- All labels
- All form fields
- All alerts/notifications