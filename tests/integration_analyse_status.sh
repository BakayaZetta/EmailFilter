#!/usr/bin/env bash
set -euo pipefail

# Usage: ./tests/integration_analyse_status.sh [base_url]
BASE_URL="${1:-http://localhost:6969}"

TMP_EML="$(mktemp)"
trap 'rm -f "$TMP_EML"' EXIT

cat > "$TMP_EML" <<'EOF'
From: sender@example.com
To: receiver@example.com
Subject: Integration scan status test
Date: Tue, 10 Mar 2026 17:00:00 +0000
Message-ID: <integration-scan-status@example.com>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

Integration test payload.
EOF

response="$(curl -sS -m 20 -X POST "$BASE_URL/analyse/" -F "file=@$TMP_EML" -F "uploader_email=integration@example.com")"

request_id="$(printf '%s' "$response" | sed -n 's/.*"request_id":"\([^"]*\)".*/\1/p')"
if [[ -z "$request_id" ]]; then
  request_id="$(printf '%s' "$response" | sed -n 's/.*"request_id": "\([^"]*\)".*/\1/p')"
fi

if [[ -z "$request_id" ]]; then
  echo "ERROR: Could not parse request_id from response: $response"
  exit 1
fi

for i in $(seq 1 40); do
  status_json="$(curl -sS -m 10 "$BASE_URL/analyse/status/$request_id")"

  if printf '%s' "$status_json" | grep -Eq '"status"\s*:\s*"finished"'; then
    echo "PASS: analyse job reached finished state ($request_id)"
    exit 0
  fi

  if printf '%s' "$status_json" | grep -Eq '"status"\s*:\s*"failed"'; then
    echo "FAIL: analyse job entered failed state ($request_id): $status_json"
    exit 2
  fi

  sleep 1
done

echo "FAIL: analyse job did not reach a terminal state in time ($request_id)"
exit 3
