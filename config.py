import os

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS    = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip()]
WEB_PORT     = int(os.environ.get("PORT", 8080))
WEB_HOST     = "0.0.0.0"
WEB_URL      = os.environ.get("WEB_URL", "https://your-app.railway.app")
DB_PATH      = "mecita.db"
CAPTCHA_API_KEY = os.environ.get("CAPTCHA_API_KEY", "")
BOOKING_URL  = "https://icp.administracionelectronica.gob.es/icpplustieb/index.html"
HEADLESS     = True
MAX_RETRIES  = 999
RETRY_DELAY  = 300
