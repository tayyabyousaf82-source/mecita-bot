# config.py — MiCitaBot Configuration
# ⚠️ IMPORTANT: Fill in your values below before running the bot

# ── Bot Token ─────────────────────────────────────────────────────────────────
# Get from @BotFather on Telegram
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ── Admin Telegram User IDs ───────────────────────────────────────────────────
# Add your Telegram user ID (get it from @userinfobot)
# You can add multiple admins: [123456789, 987654321]
ADMIN_IDS = [
    123456789,  # <-- Replace with your Telegram user ID
]

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = "mecita.db"

# ── Booking Settings ──────────────────────────────────────────────────────────
# Website URL for appointment booking
BOOKING_URL = "https://icp.administracionelectronica.gob.es/icpplustieb/index.html"

# Max retries if no appointment slots available
MAX_RETRIES = 3

# Wait seconds between retries
RETRY_DELAY = 5

# Headless browser (True = invisible, False = show browser window for debugging)
HEADLESS = True
