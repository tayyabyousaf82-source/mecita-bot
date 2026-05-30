# Extranjería Notify Bot — Setup Guide

## 1. Create your Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → copy your **BOT_TOKEN**
3. Send `/setcommands` to BotFather, select your bot, paste:
   ```
   start - Iniciar robot
   estado_cuenta - Consultar estado cuenta
   contratar_suscripcion - Contratar suscripción PRO
   agregar_aviso - Añadir aviso
   borrar_aviso - Borrar aviso
   estadisticas - Estadísticas de trámites abiertos
   terms - Términos y condiciones
   help - Ayuda
   ```

## 2. Install on your server (Linux VPS)

```bash
# Clone/copy files to server
mkdir extranjeria_bot && cd extranjeria_bot

# Install Python dependencies
pip install -r requirements.txt

# Set your bot token
export BOT_TOKEN="your_token_here"

# Run the bot
python bot.py
```

## 3. Run as a service (auto-restart)

Create `/etc/systemd/system/extranjeria-bot.service`:

```ini
[Unit]
Description=Extranjeria Notify Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/extranjeria_bot
Environment=BOT_TOKEN=your_token_here
ExecStart=/usr/bin/python3 /home/ubuntu/extranjeria_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable extranjeria-bot
sudo systemctl start extranjeria-bot
sudo systemctl status extranjeria-bot
```

## 4. How it works

- Users send `/agregar_aviso` → select Provincia → Trámite → Oficina
- Bot saves the subscription in SQLite database
- Background task checks Cita Previa website every 60 seconds
- When a slot is detected → Telegram notification is sent immediately
- Notification includes: Provincia, Trámite, Oficina, Date, Time, Link

## 5. Free vs PRO

- **Free**: max 3 subscriptions per user
- **PRO**: unlimited (set manually via `/contratar_suscripcion`)
- To grant PRO manually: open `extranjeria.db` and set `is_pro=1` for the user

## 6. Database

SQLite file `extranjeria.db` is created automatically.
Tables: `users`, `subscriptions`, `availability_log`

## Notes

- The availability checker uses the real Cita Previa website
- Extend `check_availability()` in bot.py with BeautifulSoup HTML parsing
  for production-grade slot detection (install: `pip install beautifulsoup4`)
- CHECK_INTERVAL defaults to 60 seconds (change at top of bot.py)
