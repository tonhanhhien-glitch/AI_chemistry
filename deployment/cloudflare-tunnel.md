# Self-hosting VSEPR-AI with Cloudflare Tunnel

Runs the whole application on your own machine and publishes it at
<https://vsepr.parxyz.sarl> through a Cloudflare Tunnel. Nothing is deployed to
Render, Railway, Vercel, Netlify, or AWS.

## Architecture

```
Browser ──> https://vsepr.parxyz.sarl
              │
              ▼
        Cloudflare edge (TLS terminates here)
              │  outbound-only tunnel
              ▼
        cloudflared container
              │  http://frontend:80
              ▼
        frontend (nginx)  ──/api/ ──>  backend:8000  (FastAPI)
              │
              └── React SPA
```

Single origin: the SPA and the API share the hostname
`vsepr.parxyz.sarl`. There is no separate public backend hostname, and the
browser never talks to port 8000.

Port exposure:

| Service     | Host port           | Reachable from |
| ----------- | ------------------- | -------------- |
| backend     | none (`expose` only)| other containers only |
| frontend    | `127.0.0.1:8081`    | this machine only |
| cloudflared | none                | nothing inbound |

No router port forwarding, no static public IP, and no inbound firewall rules
are needed. `cloudflared` dials *out* to Cloudflare and traffic returns over
that connection.

## 1. Create the tunnel (manual, in the Cloudflare dashboard)

### Change the domain of an existing deployment

For an existing tunnel, keep the current connector and token. In the Cloudflare
dashboard, open that tunnel's **Published application routes** and add:

- Subdomain: `vsepr`
- Domain: `parxyz.sarl`
- Service: `http://frontend:80` (type **HTTP**)

The `parxyz.sarl` zone must be active in the same Cloudflare account as the
tunnel. Confirm the proxied `vsepr` CNAME points to
`<TUNNEL-UUID>.cfargotunnel.com` in that zone. Cloudflare normally creates it when
you save the route. A DNS record alone does not configure the tunnel route.

Update the existing root `.env` to use
`CORS_ORIGINS=https://vsepr.parxyz.sarl,http://localhost:8081`, then apply it:

```sh
docker compose up -d --no-deps backend
CHECK_PUBLIC=true sh deployment/check-selfhost.sh
```

The frontend uses relative `/api/v1` URLs, so no frontend rebuild is needed.
After the new hostname passes the public checks, remove the old published
application route and DNS record if you no longer want that hostname served.
If the new zone belongs to a different Cloudflare account, create a tunnel in
that account and replace `CLOUDFLARE_TUNNEL_TOKEN` in the root `.env`, then run
`docker compose up -d --no-deps cloudflared` as well.

Reference: [Cloudflare Tunnel routing](https://developers.cloudflare.com/tunnel/concepts/routing/).

### Create a tunnel for a new deployment

1. Log in to the Cloudflare dashboard.
2. Go to **Networking → Tunnels**.
3. Click **Create a tunnel**.
4. Choose **Cloudflared** as the connector type — this creates a *remotely
   managed* tunnel whose routing lives in the dashboard.
5. Name the tunnel `vsepr-local` and save.
6. On the connector page, select the **Docker** tab. Cloudflare shows a command
   like:

   ```
   docker run cloudflare/cloudflared:latest tunnel --no-autoupdate run --token <LONG_SECRET_TOKEN>
   ```

7. Copy **only** the value after `--token`. Do not paste it into GitHub, a chat
   assistant, a screenshot, or any tracked file. It goes in `.env` and nowhere
   else. You do not need to run that `docker run` command — Compose runs the
   connector for you.

## 2. Add the published application route

Still inside the tunnel, open **Published application routes** and add a route:

| Field       | Value                |
| ----------- | -------------------- |
| Hostname    | `vsepr.parxyz.sarl`   |
| Service type| `HTTP`               |
| Service URL | `http://frontend:80` |

Use `http://frontend:80`, **not** `http://localhost:8081`. `cloudflared` runs in
its own container, where `localhost` means the cloudflared container itself. The
Compose service name `frontend` resolves to the nginx container over the shared
default network.

## 3. Confirm the DNS route

Go to **DNS → Records** for `parxyz.sarl` and look for:

| Type  | Name    | Target                          | Proxy status |
| ----- | ------- | ------------------------------- | ------------ |
| CNAME | `vsepr` | `<TUNNEL-UUID>.cfargotunnel.com`| Proxied      |

Saving the published application normally creates this record automatically. If
it is missing, add it manually using the tunnel UUID shown on the tunnel page.

If the tunnel is stopped while this DNS record still exists, visitors get
Cloudflare **error 1016 (origin DNS error)**. That means "tunnel is down", not
"DNS is broken".

## 4. Create your local `.env`

```sh
cp .env.example .env
```

Generate the teacher export token:

```sh
openssl rand -hex 32
```

Edit `.env` (`nano .env`) and fill in:

```
CLOUDFLARE_TUNNEL_TOKEN=<the real tunnel token from step 1>
CORS_ORIGINS=https://vsepr.parxyz.sarl,http://localhost:8081
TEACHER_EXPORT_TOKEN=<the openssl output>
OPENROUTER_API_KEY=
OPENROUTER_MODEL=google/gemma-4-31b-it:free
ENABLE_OPENROUTER=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ENABLE_OPENAI=false
ENABLE_PUBCHEM=true
ENABLE_RDKIT=false
```

Do not quote the values — these tokens contain no spaces.

Verify `.env` is ignored before you ever commit:

```sh
git check-ignore -v .env      # must print a .gitignore rule
git status --short             # .env must NOT appear
```

## 5. Start

```sh
docker compose up -d --build
docker compose ps
```

Expected:

```
backend       healthy
frontend      healthy
cloudflared   running
```

`cloudflared` has no healthcheck of its own, so `running` is the healthy state.

Logs:

```sh
docker compose logs -f cloudflared          # look for "Registered tunnel connection"
docker compose logs -f frontend backend
docker compose logs --tail=100 backend frontend
```

`Ctrl+C` stops following the logs; it does not stop the containers.

Beware: `docker compose config` prints the *expanded* token to your terminal.
For a safe structural check use:

```sh
docker compose config --services   # backend, frontend, cloudflared
```

## 6. Test locally

```sh
curl --fail http://127.0.0.1:8081/healthz          # -> ok
curl --fail http://127.0.0.1:8081/api/v1/health     # -> backend JSON
```

Or run the bundled script:

```sh
sh deployment/check-selfhost.sh
```

Then open <http://127.0.0.1:8081> and analyse a molecule such as `CO2`.

Do **not** test the backend at `http://localhost:8000` — port 8000 is
deliberately no longer published. Its absence is the security fix, not a bug.

## 7. Test publicly

```sh
curl --fail https://vsepr.parxyz.sarl/api/v1/health
CHECK_PUBLIC=true sh deployment/check-selfhost.sh
```

Then open <https://vsepr.parxyz.sarl> and check:

- The homepage loads.
- React routes survive a page refresh (deep-link, then F5).
- Molecule analysis works.
- In browser devtools, API calls go to `https://vsepr.parxyz.sarl/api/v1/...`
  and **nothing** is requested from `localhost:8000`.
- The mobile layout works.
- Survey and feedback data survive `docker compose restart`.

## 8. Update

```sh
git pull
docker compose up -d --build
```

## 9. Stop

```sh
docker compose down        # stops containers, KEEPS the study-data volume
```

> **Danger:** `docker compose down -v` also **deletes the `study-data` volume**,
> destroying every survey response, feedback record, and database file. There is
> no undo. Do not use it as part of normal operation. Take a backup first
> (section 11) if you ever genuinely need it.

## 10. Keeping the site up

The site is only reachable while your machine is running. It must:

- stay powered on,
- stay connected to the Internet,
- and be prevented from sleeping.

Disable sleep on Ubuntu / GNOME:

```sh
# Never suspend, even when idle or on the login screen.
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
```

Closing a laptop lid still suspends by default; set
`HandleLidSwitch=ignore` in `/etc/systemd/logind.conf` and run
`sudo systemctl restart systemd-logind` if you host on a laptop.

Start Docker automatically after reboot:

```sh
sudo systemctl enable docker.service containerd.service
```

Every service in `docker-compose.yml` uses `restart: unless-stopped`, so once
the Docker daemon starts at boot, the three containers come back on their own.
`unless-stopped` respects a manual `docker compose stop` — those containers stay
down until you start them again.

Verify after a reboot:

```sh
docker compose ps
sh deployment/check-selfhost.sh
```

## 11. Back up and restore the data volume

All persistent study data lives in the `study-data` Docker volume, mounted at
`/data` in the backend. It is *not* in your Git repository, so it needs its own
backup.

The volume's full name is prefixed with the Compose project name (the directory
name), e.g. `ai_chemistry_study-data`. Confirm it:

```sh
docker volume ls | grep study-data
```

### Back up

```sh
mkdir -p backups
docker run --rm \
  -v ai_chemistry_study-data:/data:ro \
  -v "$PWD/backups":/backup \
  alpine tar czf "/backup/study-data-$(date +%F-%H%M).tar.gz" -C /data .
```

Reads the volume read-only, so it is safe to run while the stack is up. Keep
these archives out of Git — they contain student submissions.

### Restore

Stop the stack first so the backend is not writing during the restore:

```sh
docker compose down
docker run --rm \
  -v ai_chemistry_study-data:/data \
  -v "$PWD/backups":/backup \
  alpine sh -c 'rm -rf /data/* && tar xzf /backup/study-data-YYYY-MM-DD-HHMM.tar.gz -C /data'
docker compose up -d
```

Replace the filename with the archive you want. The `rm -rf /data/*` makes the
restore exact rather than a merge — double-check the archive name before
running it.

## 12. Security notes

- The public student site intentionally has **no login**. Cloudflare Access is
  deliberately *not* configured, because students must reach it without
  authenticating.
- Cloudflare Access remains a good future option for **teacher-only or
  administrative routes** (for example a `/teacher/*` export path) if those are
  ever exposed publicly. Today the teacher export is guarded by
  `TEACHER_EXPORT_TOKEN` instead.
- Rotate the tunnel token from the dashboard if it is ever pasted somewhere it
  should not be; rotating invalidates the old value.
- Nginx proxies only `/api/`. FastAPI's `/docs` and `/openapi.json` sit outside
  that prefix and are therefore not reachable through the tunnel.
