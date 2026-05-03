import os

# ── Bot ───────────────────────────────────────────────────────────────────────
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS    = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]

# ── 2Captcha ──────────────────────────────────────────────────────────────────
CAPTCHA_API_KEY = os.environ.get("CAPTCHA_API_KEY", "")

# ── Spanish Phone (for OTP) ───────────────────────────────────────────────────
SPANISH_PHONE = os.environ.get("SPANISH_PHONE", "+34600000000")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = "mecita.db"

# ── Booking ───────────────────────────────────────────────────────────────────
BOOKING_URL  = "https://icp.administracionelectronica.gob.es/icpplustieb/index.html"
MAX_RETRIES  = 999          # 24/7 mode — hamesha try karta rahe
RETRY_DELAY  = 300          # 5 min baad dobara try
HEADLESS     = True

# ── Web Form ──────────────────────────────────────────────────────────────────
WEB_PORT     = int(os.environ.get("PORT", 8080))
WEB_HOST     = "0.0.0.0"
