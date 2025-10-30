# SSO Provider (FastAPI)

Endpoints:
- GET /login (page) and POST /login (form) → returns SSO token (JSON if Accept: application/json) and sets session
- GET /home (page) → requires session
- POST /logout → clears session, revokes token if provided via Authorization or cookie
- POST /validate_token → validates SSO token (signature, exp, revoked)

Run locally:
1) Create MySQL database `sso_provider` and ensure credentials match spec (root/w23452345, localhost:3306)
2) Install deps: `pip install -r requirements.txt`
3) Start: `uvicorn app.main:app --reload`
4) Seed a user: `curl -X POST http://localhost:8000/setup_seed`
5) Open http://localhost:8000/login

Run with Docker Compose:
1) Build and start: `docker compose up -d --build`
2) Wait for app healthcheck to pass, then seed a user:
   `curl -X POST http://localhost:8000/setup_seed`
3) Open http://localhost:8000/login

Notes:
- The app container uses environment variables defined in docker-compose.yml (DB_HOST=db, etc.).
- To customize cookies or DB credentials, edit docker-compose.yml or provide an .env file and reference it via `env_file`.
- For dev hot-reload, mount the repo into the container and adjust CMD to use `--reload`.

Config via env:
- DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- SESSION_SECRET_KEY, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRES_MINUTES

Notes:
- This PoC uses HS256 for SSO token signing with a shared secret (JWT_SECRET_KEY). For production, prefer RS256 + JWKS.
- Tables are auto-created on startup.
