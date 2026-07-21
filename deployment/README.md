# Deployment

Docker Compose is the complete runnable deployment configuration for this repository. It builds non-root FastAPI and multi-stage nginx frontend images, health-checks both services, proxies /api/v1, and persists anonymous study JSONL in a named volume.

    cp .env.example .env
    # set TEACHER_EXPORT_TOKEN
    docker compose config
    docker compose build
    docker compose up -d

Open http://localhost:8080 and verify /api/v1/health through the same origin. No public deployment is claimed.

render.yaml is a provider blueprint that still requires real service URLs, CORS origin, token, and optional secrets in the provider dashboard. railway.json describes the backend service only. Never put secrets in these checked-in files.

TLS should terminate at the hosting platform or an operator-configured proxy. deployment/nginx.conf is an HTTP internal reverse-proxy example; add a real domain and certificate management outside this repository.
