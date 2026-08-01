#!/bin/sh
# Validate the self-hosted Docker Compose stack.
#
#   sh deployment/check-selfhost.sh
#   CHECK_PUBLIC=true sh deployment/check-selfhost.sh
#
# Contains no secrets. Exits nonzero if any required check fails.
set -eu

LOCAL_BASE="${LOCAL_BASE:-http://127.0.0.1:8081}"
PUBLIC_BASE="${PUBLIC_BASE:-https://vsepr.hungntt.me}"
CHECK_PUBLIC="${CHECK_PUBLIC:-false}"

failures=0

# Requests a URL and reports pass/fail without aborting, so one broken endpoint
# still lets the remaining checks run and be reported together.
check() {
  label="$1"
  url="$2"
  required="$3" # "required" or "optional"

  printf '%-46s' "$label"
  if curl --fail --silent --show-error --max-time 10 -o /dev/null "$url" 2>/dev/null; then
    echo "PASS"
    return 0
  fi

  if [ "$required" = "optional" ]; then
    echo "WARN (optional)"
    return 0
  fi

  echo "FAIL  <- $url"
  failures=$((failures + 1))
}

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required but not installed." >&2
  exit 1
fi

echo "Checking local stack at $LOCAL_BASE"
echo "-------------------------------------------------------"

# Frontend nginx is serving.
check "frontend health (/healthz)" "$LOCAL_BASE/healthz" required

# Backend reachable through the nginx /api/ proxy. This is the important one:
# it proves nginx -> backend:8000 works and the URI prefix is preserved.
check "backend via nginx (/api/v1/health)" "$LOCAL_BASE/api/v1/health" required

# SPA shell is served, so React Router deep links resolve.
check "SPA shell (/)" "$LOCAL_BASE/" required

# Unknown route must fall through to index.html rather than 404.
check "SPA fallback (/some/deep/route)" "$LOCAL_BASE/some/deep/route" required

if [ "$CHECK_PUBLIC" = "true" ]; then
  echo
  echo "Checking public site at $PUBLIC_BASE"
  echo "-------------------------------------------------------"
  echo "(requires a real tunnel token in .env and a live cloudflared container)"
  check "public backend (/api/v1/health)" "$PUBLIC_BASE/api/v1/health" required
  check "public frontend (/)" "$PUBLIC_BASE/" required
else
  echo
  echo "Public checks skipped. Enable with: CHECK_PUBLIC=true sh $0"
fi

# Advisory: backend port 8000 must not be published on the host. A successful
# connection here means the compose port mapping was reintroduced.
echo
echo "Port exposure"
echo "-------------------------------------------------------"
printf '%-46s' "backend :8000 not published"
if curl --fail --silent --max-time 3 -o /dev/null "http://127.0.0.1:8000/api/v1/health" 2>/dev/null; then
  echo "FAIL  <- port 8000 is reachable on the host"
  failures=$((failures + 1))
else
  echo "PASS"
fi

echo
if [ "$failures" -gt 0 ]; then
  echo "$failures check(s) failed."
  exit 1
fi
echo "All required checks passed."
