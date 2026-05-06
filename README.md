# 🗓 CitaMonitor

**Production-grade SaaS appointment monitoring system for the Spanish ICP government portal.**

Real-time detection · Telegram notifications · Admin dashboard · Fully Dockerized

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx Reverse Proxy                 │
│              (SSL termination, rate limiting)           │
└──────────┬──────────────────┬───────────────────────────┘
           │                  │
    ┌──────▼──────┐    ┌──────▼──────┐
    │  Next.js    │    │   FastAPI   │◄──── WebSocket (admin)
    │  Dashboard  │    │   Backend   │◄──── REST API
    └─────────────┘    └──────┬──────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────▼─────┐  ┌─────▼──────┐ ┌─────▼──────┐
       │ PostgreSQL │  │   Redis    │ │  aiogram   │
       │  Database  │  │  Pub/Sub   │ │ Telegram   │
       └────────────┘  └─────┬──────┘ │    Bot     │
                             │        └────────────┘
                      ┌──────▼──────┐
                      │  Playwright │
                      │   Workers   │
                      │ (×2 default)│
                      └─────────────┘
```

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **Telegram Bot** | FSM-based profile creation: province → trámite → dates → contact info |
| 🎭 **Playwright Engine** | Adaptive polling (10–60s), exponential backoff, screenshot capture |
| 🔐 **OTP System** | Admin-controlled OTP resolution via dashboard or Telegram reply |
| 📊 **Real-time Dashboard** | WebSocket-powered Next.js admin panel |
| 🔔 **Instant Notifications** | Sub-1s Telegram alerts + WebSocket push |
| 🐳 **Fully Dockerized** | docker compose up — everything works |

---

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/yourorg/citamonitor.git
cd citamonitor
cp .env.example .env
```

Edit `.env` with your values:

```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
ADMIN_TELEGRAM_ID=your_telegram_user_id
POSTGRES_PASSWORD=strong_random_password
REDIS_PASSWORD=strong_random_password
SECRET_KEY=64_char_random_string_here
ADMIN_PASSWORD=dashboard_admin_password
```

### 2. Launch

```bash
docker compose up -d
```

### 3. Access

| Service | URL |
|---------|-----|
| Admin Dashboard | http://localhost |
| API Docs | http://localhost/api/docs |
| Telegram Bot | Search your bot on Telegram |

---

## Getting Your Telegram ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It replies with your numeric user ID
3. Set that as `ADMIN_TELEGRAM_ID` in `.env`

## Creating a Bot Token

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the token to `TELEGRAM_BOT_TOKEN`

---

## Services

| Container | Role |
|-----------|------|
| `citamonitor_postgres` | PostgreSQL 16 database |
| `citamonitor_redis` | Redis 7 for pub/sub + FSM storage |
| `citamonitor_backend` | FastAPI + SQLAlchemy + WebSocket server |
| `citamonitor_bot` | aiogram Telegram bot |
| `citamonitor_worker` | Playwright monitoring workers (×2) |
| `citamonitor_frontend` | Next.js admin dashboard |
| `citamonitor_nginx` | Nginx reverse proxy |

---

## User Flow (Telegram Bot)

```
/nueva_cita
    │
    ▼
[1] Select Province    (inline keyboard)
[2] Select Trámite     (inline keyboard)  
[3] Select Oficina     (text or skip)
[4] Date From          (DD/MM/YYYY)
[5] Date To            (DD/MM/YYYY)
[6] Phone numbers      (comma-separated or skip)
[7] Email addresses    (comma-separated or skip)
    │
    ▼
[Summary screen with Edit buttons for each field]
    │
    ▼
[Confirm] → Monitoring job starts immediately
    │
    ▼
Bot notifies user when slot is found 🎉
```

---

## OTP Flow

When the ICP system shows an OTP page:

```
Worker detects OTP page
    │
    ▼
Worker pauses & creates OTP request in DB
    │
    ├──► Admin Telegram: 🔐 OTP REQUIRED alert + screenshot
    └──► Dashboard: Real-time alert in OTP Panel
         │
         ▼
    Admin enters OTP code in dashboard input field
         │
         ▼
    Backend resolves OTP, notifies worker via Redis
         │
         ▼
    Worker enters OTP on page and continues monitoring
```

---

## Monitoring Engine

The Playwright worker implements:

- **Adaptive polling**: 30–60s normally, 10–25s in high-activity mode
- **Random jitter**: ±2s on every interval to avoid detection patterns  
- **Exponential backoff**: Backs off on errors (2^n seconds, max 5 min)
- **Slot detection**: Checks DOM for `.cita-disponible`, calendar tables, hidden changes
- **Screenshot capture**: Saves proof of availability immediately on detection

**STRICT RULES (always enforced):**
- ❌ No CAPTCHA bypass
- ❌ No security circumvention  
- ❌ No aggressive rate violations
- ✅ Respects server response patterns

---

## Admin Dashboard Pages

| Page | Path | Features |
|------|------|---------|
| Overview | `/dashboard` | Stats cards, activity chart, health, recent jobs |
| Jobs | `/dashboard/jobs` | All jobs, filter by status, stop/restart controls, screenshot viewer |
| OTP Panel | `/dashboard/otp` | Real-time OTP alerts, inline code input, auto-notification |
| Users | `/dashboard/users` | User list, search, ban/unban |
| Logs | `/dashboard/logs` | Live log stream, filter by source/level, terminal UI |

---

## Production VPS Deployment

### Prerequisites

```bash
# Ubuntu 22.04+
apt update && apt install -y docker.io docker-compose-plugin
systemctl enable --now docker
```

### Deploy

```bash
bash scripts/deploy.sh
```

### Enable HTTPS (Let's Encrypt)

```bash
apt install certbot
certbot certonly --standalone -d yourdomain.com
# Then uncomment HTTPS block in nginx/nginx.conf
# Update NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL in .env
docker compose restart nginx
```

### Scale Workers

```yaml
# docker-compose.yml
worker:
  deploy:
    replicas: 4  # Increase as needed
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather |
| `ADMIN_TELEGRAM_ID` | ✅ | Your numeric Telegram user ID |
| `POSTGRES_PASSWORD` | ✅ | Strong random password |
| `REDIS_PASSWORD` | ✅ | Strong random password |
| `SECRET_KEY` | ✅ | 64+ char random string for JWT |
| `ADMIN_PASSWORD` | ✅ | Dashboard login password |
| `POLL_INTERVAL_NORMAL_MIN` | ❌ | Default: 30 (seconds) |
| `POLL_INTERVAL_NORMAL_MAX` | ❌ | Default: 60 (seconds) |
| `POLL_INTERVAL_HIGH_MIN` | ❌ | Default: 10 (seconds) |
| `POLL_INTERVAL_HIGH_MAX` | ❌ | Default: 25 (seconds) |
| `MAX_CONCURRENT_WORKERS` | ❌ | Default: 5 |
| `FIREBASE_PROJECT_ID` | ❌ | For mobile push notifications |

---

## Database Schema

```
users
  ├── id, telegram_id, username, first_name, last_name
  ├── is_active, is_banned, created_at, last_seen
  └── → profiles, jobs, otp_requests

profiles
  ├── user_id (FK), province_code/name, tramite_code/name
  ├── oficina_code/name, date_from, date_to
  ├── phones[], emails[], certificates[] (JSON)
  └── is_active, created_at

monitoring_jobs
  ├── user_id (FK), profile_id (FK)
  ├── status: queued|searching|found|stopped|error|paused
  ├── check_count, last_check_at, found_at
  └── screenshot_path, error_message, error_count

otp_requests
  ├── user_id (FK), job_id (FK)
  ├── status: pending|resolved|expired
  ├── screenshot_path, context_data
  └── otp_value, resolved_by, resolved_at

logs
  ├── job_id (FK, nullable)
  ├── level: debug|info|warning|error
  ├── source: playwright|bot|system|worker
  └── message, extra (JSON), created_at

notifications
  ├── user_id, job_id (FK, nullable)
  ├── channel: telegram|websocket|firebase
  └── event_type, payload (JSON), sent, error
```

---

## License

MIT — free to use, modify, and deploy.

---

## Disclaimer

This tool monitors publicly accessible appointment pages only. It does not:
- Bypass CAPTCHA or security measures
- Automate booking or form submission
- Circumvent rate limits or access controls

Use responsibly and in accordance with the terms of service of the monitored portal.
