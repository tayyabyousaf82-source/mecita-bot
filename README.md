# 🤖 MiCitaBot (@mecita_bot)
## Complete Setup Guide — اردو + English

---

## 📁 File Structure (Files ka structure)

```
mecita_bot/
├── bot.py          ← Main bot code
├── config.py       ← Settings (TOKEN, ADMIN ID)
├── database.py     ← SQLite database
├── booking.py      ← Auto-booking (Playwright)
├── data.py         ← All 52 Provincias data
├── requirements.txt
└── README.md
```

---

## ⚙️ Step 1: Installation (Install karna)

```bash
# 1. Python packages install karein
pip install -r requirements.txt

# 2. Playwright browsers install karein (ZARURI hai)
playwright install chromium

# 3. System dependencies (Linux/VPS pe)
playwright install-deps
```

---

## 🔑 Step 2: Config Setup (config.py fill karein)

`config.py` file kholen aur yeh 2 cheezein fill karein:

### BOT_TOKEN kahan se milega?
1. Telegram pe **@BotFather** open karein
2. `/newbot` type karein
3. Name: `MiCitaBot`
4. Username: `mecita_bot`
5. BotFather aapko token dega — woh copy karein

### ADMIN_IDS kaise pata karein?
1. Telegram pe **@userinfobot** open karein
2. `/start` karein
3. Aapka User ID dikhega (number hoga jaise `987654321`)

```python
# config.py
BOT_TOKEN = "1234567890:ABCDefGhIJKlmnOPQRstUVwxYZ"   # ← Yahan apna token daalein
ADMIN_IDS = [987654321]                                  # ← Yahan apna User ID daalein
```

---

## ▶️ Step 3: Bot Chalana (Run karna)

```bash
python bot.py
```

Terminal mein yeh dikhe toh bot chal raha hai:
```
INFO - 🤖 MiCitaBot started!
```

---

## 🔐 Admin Approval System (Kaise kaam karta hai)

```
User → /start → Bot ko message aata hai
Bot → Admin ko notification bhejta hai [✅ Aprobar] [❌ Rechazar] buttons ke saath
Admin → Button dabata hai
User → Notification aati hai "✅ Aprobado!" ya "❌ Rechazado"
```

### Admin Commands:
| Command | Kya karta hai |
|---------|---------------|
| `/pending` | Pending users list dikhata hai |
| `/users` | Sab users aur unka status |
| `/help` | Admin help menu |

---

## 📋 User Flow (User kaise use karega)

```
1. /start       → Access request bhejta hai
2. Admin approve karta hai
3. /cita        → Province select karo (52 options)
4.              → Tramite select karo
5.              → Oficina select karo
6.              → Naam likhein
7.              → Apellido likhein
8.              → NIE/Passport likhein
9.              → Fecha nacimiento (DD/MM/YYYY)
10.             → Nacionalidad
11.             → Email
12.             → Telefono
13.             → Summary dikhti hai ✅ Confirm / ✏️ Edit
14.             → Bot automatically website pe cita book karta hai
15.             → Result aata hai (success ya error)
```

---

## 🤖 Auto-Booking Kaise Kaam Karta Hai

Bot **Playwright** use karta hai jo ek invisible browser hai:
1. `icp.administracionelectronica.gob.es` website kholti hai
2. Province, tramite select karta hai
3. Form fill karta hai (NIE, nombre, fecha, email, telefono)
4. Pehli available slot le leta hai
5. Confirmation number save karta hai
6. User ko result bhejta hai

**Agar cita na mile:** Bot 3 baar try karta hai, phir user ko manual link bhejta hai.

---

## 🖥️ VPS/Server Pe Chalana (Background mein)

```bash
# Screen use karein (server band hone pe bhi chale)
screen -S mecitabot
python bot.py
# Ctrl+A phir D dabao — background mein chala jayega

# Ya systemd service banao:
sudo nano /etc/systemd/system/mecitabot.service
```

```ini
[Unit]
Description=MiCitaBot Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/mecita_bot
ExecStart=/usr/bin/python3 /home/ubuntu/mecita_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mecitabot
sudo systemctl start mecitabot
sudo systemctl status mecitabot
```

---

## ❓ Common Errors aur Solution

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: telegram` | `pip install python-telegram-bot==21.6` |
| `playwright._impl._errors.Error` | `playwright install chromium` |
| `Invalid token` | config.py mein token dobara check karein |
| `Chat not found` | Admin ID sahi hai? @userinfobot se check karein |
| Bot respond nahi karta | Token aur internet connection check karein |

---

## 📞 Support

Koi masla ho toh:
- `bot.log` file mein error dekh sakte hain
- `/pending` command se users check karein
