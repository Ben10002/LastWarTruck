# LKW Bot Platform

Multi-User Bot-Plattform für automatisierten LKW-Bot mit Abo-System.

## Projektstruktur

```
lkw_bot_platform/
├── app.py                          # Hauptanwendung (Flask)
├── config.py                       # Konfiguration
├── requirements.txt                # Python Dependencies
├── .env.example                    # Environment Template
├── models/                         # Datenbank-Models
│   ├── user.py                     # User Model
│   ├── subscription.py             # Abo & License Keys
│   └── bot_config.py               # Bot-Einstellungen & Logs
├── routes/                         # Flask Blueprints
│   ├── auth.py                     # Login/Register (TODO)
│   ├── admin.py                    # Admin Dashboard (TODO)
│   ├── dashboard.py                # User Dashboard (TODO)
│   └── bot.py                      # Bot Steuerung (TODO)
├── bot_manager/                    # Bot Logic
│   ├── lkw_bot.py                  # LKW Bot (TODO)
│   └── bot_controller.py           # Multi-User Management (TODO)
├── templates/                      # HTML Templates
└── static/                         # CSS/JS
```

## Features

### ✅ Schritt 1: Fundament (FERTIG)
- [x] Projektstruktur
- [x] Datenbank-Models (User, Subscription, Keys, BotConfig, Timer, Logs)
- [x] Basis-Konfiguration
- [x] Flask App Setup

### ⏳ Schritt 2: Authentifizierung (TODO)
- [ ] Login-System
- [ ] Registrierung
- [ ] Session-Management
- [ ] Templates

### ⏳ Schritt 3: Admin-Bereich (TODO)
- [ ] Admin-Dashboard
- [ ] Key-Generator
- [ ] User-Management
- [ ] Wartungsmodus

### ⏳ Schritt 4: User-Dashboard (TODO)
- [ ] Persönliches Dashboard
- [ ] Abo-Status
- [ ] Bot-Konfiguration

### ⏳ Schritt 5: Bot-Integration (TODO)
- [ ] Multi-User Bot-Controller
- [ ] Bot Start/Stop
- [ ] Timer-Persistenz
- [ ] Log-Anzeige

### ⏳ Schritt 6: Deployment (TODO)
- [ ] VPS Setup
- [ ] Nginx/Apache
- [ ] Systemd Service

## Installation

### 1. Repository klonen / Dateien hochladen

### 2. Virtual Environment erstellen
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Environment konfigurieren
```bash
cp .env.example .env
# .env editieren und SECRET_KEY ändern!
```

### 5. Datenbank initialisieren
```bash
python app.py
# Erstellt lkw_bot.db und Admin-User
```

### 6. Anwendung starten
```bash
python app.py
```

Öffne Browser: `http://localhost:5000`

## Standard Admin-Login
```
E-Mail: admin@lkwbot.de
Passwort: admin123
```
**⚠️ WICHTIG: Ändere das Admin-Passwort sofort nach dem ersten Login!**

## Datenbank-Schema

### Users
- E-Mail, Passwort, Admin-Status, Aktiv-Status

### Subscriptions
- User-ID, Ablaufdatum, Erstellungsdatum

### LicenseKeys
- Key-Code, Laufzeit, Eingelöst-Status, Ersteller

### BotConfigs
- SSH-Daten (VMOSCloud), Screen-Settings, Bot-Einstellungen

### BotTimers
- Timer-Name, Nächster Run, Interval, Aktiv-Status

### BotLogs
- Log-Type, Nachricht, Zeitstempel

## Nächste Schritte

**Schritt 2:** Authentifizierung implementieren
- Login/Register Routes
- WTForms für Formulare
- Templates erstellen

## Technologien

- **Backend:** Flask 3.0
- **Database:** SQLAlchemy (SQLite/PostgreSQL)
- **Auth:** Flask-Login
- **Frontend:** Bootstrap 5 + Vanilla JS (geplant)
- **Bot:** OpenCV, Tesseract, Paramiko

## Lizenz

Privates Projekt - Alle Rechte vorbehalten