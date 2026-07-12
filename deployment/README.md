# Deployment Task Checklist

## Backend Deployment

- [ ] Create production `backend/.env` from `backend/.env.example`.
- [ ] Add Anthropic API key securely.
- [ ] Configure CORS domain.
- [ ] Build Docker image (`backend/Dockerfile`).
- [ ] Run backend container.
- [ ] Test `/health`.
- [ ] Test `/api/v1/analyze`.
- [ ] Add HTTPS (see `nginx.conf`).
- [ ] Add logging.
- [ ] Add error monitoring.

## Frontend Deployment

- [ ] Create production `frontend/.env` from `frontend/.env.example`.
- [ ] Set backend API URL (`VITE_API_BASE_URL`).
- [ ] Build frontend (`npm run build`).
- [ ] Deploy to hosting service.
- [ ] Test home page.
- [ ] Test molecule analysis page.
- [ ] Test 3D viewer.
- [ ] Test mobile view.

## Full Production Validation

- [ ] Run full backend test set.
- [ ] Validate all curated molecules.
- [ ] Ask chemistry expert to review outputs.
- [ ] Check AI explanations for hallucinations.
- [ ] Check mobile compatibility.
- [ ] Check text display.
- [ ] Check performance.
- [ ] Check browser compatibility.

## Infra Files in This Folder

- [ ] Fill in `nginx.conf` (server_name, TLS certs, upstream addresses).
- [ ] Fill in `backend.env.example` / `frontend.env.example` with the real production keys/URLs (never commit actual secrets).
- [ ] Decide hosting provider and complete either `render.yaml` or `railway.json` (or replace with the chosen provider's config).
- [ ] Write `deploy_notes.md` with the concrete step-by-step deploy process once the provider is chosen.
