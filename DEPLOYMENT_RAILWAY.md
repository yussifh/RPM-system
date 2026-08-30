# Deployment Guide — Railway (MySQL PaaS)

This guide deploys the AI-Integrated Remote Patient Monitoring System on
<a href="https://railway.app" target="_blank">Railway</a> using its managed
**MySQL** plugin plus a container built from the included `Dockerfile`.

Production architecture:

```
Browser ── HTTPS (https://yourapp.up.railway.app)
            │
            ▼
    Streamlit App (Docker container)
            │  internal network
            ▼
    Railway MySQL (managed plugin)
```

The trained ML models ship inside the git repo (they are small), so the
container works immediately — no training step on the server.

---

## Prerequisites

- The repo (this folder) pushed to a **GitHub** repo (or the Railway CLI).
- A **Railway** account (free in the 15-day trial, then ~$5/mo).
- MySQL client tooling to run the one-time DB initialization:
  - `py -3.11 scripts/init_production_db.py` (Python, no `mysql` CLI needed) — **recommended**

---

## Step 1 — Push the code to GitHub

```bash
cd rpm-system
git add .
git commit -m "Production deployment (Docker, DB init, docs)"
git branch -M main
git remote add origin https://github.com/<YOU>/rpm-system.git
git push -u origin main
```

> The local `.env` (with secrets) is **excluded** — `.gitignore` covers `.env`
> and `.dockerignore` prevents it entering the image. Verify with
> `git ls-files | findstr env` (should show nothing matching `.env`).

---

## Step 2 — Create the project + MySQL on Railway

1. Log in at <a href="https://railway.app" target="_blank">railway.app</a> → **New Project**.
2. Choose the **MySQL** template (Railway's managed MySQL plugin).
   - You will get a *template service* group: one app placeholder + the MySQL DB.
3. In the MySQL service → **Variables** tab, note the generated values for:
   `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`.
4. Enable **Public Network** on the MySQL service (Settings → Networking).
   Record the public `HOST:PORT` — you'll use it once for DB initialization
   (the app itself will use the internal host).

---

## Step 3 — Deploy the app service

1. In your Railway project, click **New → Service → Deploy from GitHub repo**.
   - Connect GitHub, select your `rpm-system` repo, and make sure **Dockerfile**
     is picked as the build type (Railway detects it automatically).
2. While it builds, set the app's **Variables** (see Step 4).

---

## Step 4 — Service environment variables

Railway lets you reference a plugin's variables with `${{ MYSQLHOST }}`.

| Variable | Value | Notes |
|---|---|---|
| `DB_HOST` | `${{ MYSQLHOST }}` | internal MySQL host |
| `DB_PORT` | `${{ MYSQLPORT }}` | 3306 typical |
| `DB_NAME` | `${{ MYSQLDATABASE }}` | default is `railway` |
| `DB_USER` | `${{ MYSQLUSER }}` | |
| `DB_PASSWORD` | `${{ MYSQLPASSWORD }}` | |
| `APP_ENV` | `production` | |
| `APP_SECRET_KEY` | a long random string | e.g. `py -c "import secrets;print(secrets.token_hex(32))"` |
| `BCRYPT_ROUNDS` | `12` | optional |
| `SESSION_EXPIRY_MINUTES` | `60` | optional |

No `.env` file is needed — `app/core/config.py` reads these environment
variables, and the container starts with:

```
python -m streamlit run app/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0
```

> `python -m streamlit` (not bare `streamlit`) is required: with a plain
> `streamlit run app/main.py` the script dir (`/app/app`) becomes
> `sys.path[0]`, so `from app.core... import` fails inside the container.
> `$PORT` is injected by Railway (the Dockerfile handles it).

---

## Step 5 — Initialize the database (ONE TIME)

With the MySQL plugin's **public** `HOST:PORT` and its credentials:

```bash
cd rpm-system
py -3.11 scripts/init_production_db.py \
    --host <PUBLIC-MYSQL-HOST> \
    --port <PUBLIC-MYSQL-PORT> \
    --user <MYSQLUSER> \
    --password <MYSQLPASSWORD> \
    --name <MYSQLDATABASE>
```

What it does (all idempotent-ish, safe to re-run on a fresh DB):

1. Creates the target database if needed (`utf8mb4`).
2. Disables FK checks, then applies `database/schema.sql` (drops + creates
   all 21 tables) and re-enables the checks. FK checks are turned off so
   leftover/pre-existing tables (e.g. a template's `addresses` table with a
   FK to `users`) can't block the DROPs.
3. Seeds demo accounts **only if the `users` table is empty**:
   `admin@rpm.com/admin1234 · doctor@rpm.com/doctor1234 · patient@rpm.com/patient1234`.
4. Creates the extra tables (`doctor_ratings`, `teleconsultations`,
   `system_settings`).

> Run it ONCE against the fresh Railway DB. Do **not** run it against the
> production DB repeatedly — `schema.sql` DROPs all tables.

---

## Step 6 — Open the app

1. In the app service → **Settings → Networking**, click **Generate Domain**.
   Railway issues a free `https://<your-app>.up.railway.app` with a valid TLS
   certificate automatically.
2. Visit it, log in with a demo account, and check:
   - Patient Dashboard → **Submit Reading** (uses the ML models) ✓
   - **Teleconsultation** → the embedded Jitsi room loads ✓
3. Recommended: enable the service **health check** with path
   `/_stcore/health` (Streamlit's built-in endpoint) so Railway restarts the
   app if it becomes unhealthy.

---

## Deployed status (this project)

- **URL:** <a href="https://rpm-system-production.up.railway.app" target="_blank">https://rpm-system-production.up.railway.app</a>
- **GitHub:** `https://github.com/yussifh/RPM-system` (branch `main`)
- **Railway project:** `artistic-victory` · service `rpm-system` (Dockerfile) + managed MySQL
- DB initialized (21 tables + demo accounts). Login verified with `patient@rpm.com`.
- **Health check enabled** on the service: path `/_stcore/health` (Streamlit's
  built-in endpoint) — confirmed 200 `ok`. Railway pings it for readiness and
  restarts the app if it stops answering.

### Health check / service settings (Infrastructure as Code)

Railway now prefers **IaC** (`.railway/railway.ts`) over `railway.json`
(Config as Code is deprecated, works until 2026-12-01). The service settings
in this repo live in `.railway/railway.ts`:

```
npm install   # installs the `railway` SDK (devDependency)
# Windows: the SDK must find the real CLI binary on process.env._ :
#   $env:_ = "C:\Users\<you>\AppData\Roaming\npm\node_modules\@railway\cli\bin\railway.exe"
railway config plan    # review (must show "0 to destroy")
railway config apply --yes
```

`.railway/` contains live secrets (DB password, APP_SECRET_KEY) and is
**gitignored** — never commit it. After cloning, recreate it with
`railway config migrate` and re-apply.

---

## Updating the deployed app

- **Auto-deploy (recommended):** in the Railway dashboard, open the `rpm-system`
  service → **Settings** → connect your GitHub repo, then set
  **Automatically Deploy → All pushes** (this requires installing the Railway
  GitHub App once). After that, every push to `main` rebuilds and redeploys.
- **Manual (no dashboard):** push to `main`, then run
  `railway redeploy --service rpm-system --from-source --yes` to pull the
  latest commit and redeploy. (CLI-added services don't receive push webhooks
  until you connect GitHub in the dashboard.)

---

## Alternative: Railway CLI (no GitHub)

```bash
# npm i -g @railway/cli
railway login
railway link
railway up
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Missing required environment variable: 'DB_PASSWORD'` | App env vars not set — re-check Step 4 values. |
| `Cannot connect to MySQL server` | Confirm `DB_HOST` uses `${{ MYSQLHOST }}` (internal), not the public host. |
| Blank screen / old look | Streamlit caches the app's theme in the tab — hard refresh (Ctrl+Shift+R). |
| Teleconsultation video doesn't connect | Jitsi runs client-side from the browser — both users need internet (and ideally the same network). Not a server issue. |
| ML pages crash (`no attribute multi_class`) | Only if models are missing from the image — confirm `app/ml/trained_models/*.joblib` are committed (they are un-ignored now). |
| Deploy shows Nixpacks instead of Docker | In Service settings set **Builder → Dockerfile**. |

---

## Security reminders

- Never put `APP_SECRET_KEY` or DB credentials in code or the repo — use the
  service Variables.
- Rotate the admin password after initial login.
- This is an academic demonstration, not a certified medical device (see README).