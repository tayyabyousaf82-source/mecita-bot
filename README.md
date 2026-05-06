# CitaMonitor Bot — Railway Deployment

## Problem Fix
Railway error `Script start.sh not found` fixed with:
- `railway.json` — tells Railway how to start the bot
- `nixpacks.toml` — build configuration
- `Procfile` — fallback start command

---

## Deploy on Railway (Step by Step)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "CitaMonitor bot"
git remote add origin https://github.com/YOUR_USERNAME/citamonitor-bot.git
git push -u origin main
```

### Step 2 — Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Select your repository

### Step 3 — Add Environment Variables
In Railway dashboard → your service → **Variables** tab, add:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `ADMIN_TELEGRAM_ID` | Your Telegram user ID |
| `DATABASE_URL` | (optional) PostgreSQL connection string |
| `REDIS_URL` | (optional) Redis connection string |

### Step 4 — Add Database (Optional)
1. In Railway project → **New** → **Database** → **PostgreSQL**
2. Railway auto-sets `DATABASE_URL` variable

### Step 5 — Deploy
Railway auto-deploys when you push to GitHub.

---

## Get Your Telegram User ID
Message [@userinfobot](https://t.me/userinfobot) — it replies with your ID.

## Get Bot Token
Message [@BotFather](https://t.me/BotFather) → `/newbot`

---

## Bot Commands
- `/start` — Start the bot
- `/nueva_cita` — Create monitoring alert
- `/mis_citas` — View your alerts
- `/ayuda` — Help
