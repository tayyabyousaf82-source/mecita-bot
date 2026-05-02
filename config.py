import os

# Railway Variables tab mein yeh set karein
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]

DB_PATH = "mecita.db"
BOOKING_URL = "https://icp.administracionelectronica.gob.es/icpplustieb/index.html"
MAX_RETRIES = 3
RETRY_DELAY = 5
HEADLESS = True
