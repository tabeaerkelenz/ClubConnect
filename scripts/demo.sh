#!/usr/bin/env bash
set -euo pipefail

# ====== CONFIG ======
BASE_URL="${BASE_URL:-https://clubconnect-0r4z.onrender.com}"
COACH_NAME="Coach Carla"
ATHLETE_NAME="Athlete Alex"
TS="$(date +%s)"
COACH_EMAIL="coach_${TS}@example.com"
ATHLETE_EMAIL="athlete_${TS}@example.com"
PASSWORD="Password123"

# Dependencies: jq
if ! command -v jq >/dev/null 2>&1; then
  echo "This script needs 'jq'. Install via: brew install jq  (macOS) or apt-get install jq"
  exit 1
fi

echo "=== ClubConnect API Demo ==="
echo "Base URL: $BASE_URL"
echo

# Helper: pretty curl
curl_json() {
  local method="$1"; shift
  local url="$1"; shift
  local data="${1:-}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" "$url" \
      -H "Content-Type: application/json" \
      -d "$data"
  else
    curl -sS -X "$method" "$url"
  fi
}

auth_curl_json() {
  local method="$1"; shift
  local url="$1"; shift
  local token="$1"; shift
  local data="${1:-}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" "$url" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "$data"
  else
    curl -sS -X "$method" "$url" \
      -H "Authorization: Bearer $token"
  fi
}

# ====== 1) SIGNUP two users ======
echo "-> Creating coach user..."
coach_resp="$(curl_json POST "$BASE_URL/users" "$(jq -n --arg n "$COACH_NAME" --arg e "$COACH_EMAIL" --arg p "$PASSWORD" '{name:$n, email:$e, password:$p}')" )"
echo "$coach_resp" | jq .
coach_id="$(echo "$coach_resp" | jq -r '.id // .user.id // empty')"
echo "coach_id=${coach_id}"

echo "-> Creating athlete user..."
athlete_resp="$(curl_json POST "$BASE_URL/users" "$(jq -n --arg n "$ATHLETE_NAME" --arg e "$ATHLETE_EMAIL" --arg p "$PASSWORD" '{name:$n, email:$e, password:$p}')" )"
echo "$athlete_resp" | jq .
athlete_id="$(echo "$athlete_resp" | jq -r '.id // .user.id // empty')"
echo "athlete_id=${athlete_id}"
echo

# ====== 2) LOGIN (OAuth2 Password flow typical) ======
# Common FastAPI pattern: POST /auth/login with form data -> { access_token, token_type }
echo "-> Logging in as coach..."
coach_login="$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$COACH_EMAIL&password=$PASSWORD")"
echo "$coach_login" | jq .
coach_token="$(echo "$coach_login" | jq -r '.access_token // empty')"
if [[ -z "$coach_token" ]]; then
  echo "Login might be at /token instead. Trying /token ..."
  coach_login="$(curl -sS -X POST "$BASE_URL/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$COACH_EMAIL&password=$PASSWORD")"
  echo "$coach_login" | jq .
  coach_token="$(echo "$coach_login" | jq -r '.access_token // empty')"
fi
[[ -n "$coach_token" ]] || { echo "ERROR: Could not obtain coach JWT token."; exit 1; }

echo "-> /auth/me (coach)"
auth_curl_json GET "$BASE_URL/auth/me" "$coach_token" | jq .
echo

# ====== 3) CREATE CLUB (as coach) ======
echo "-> Creating club..."
club_name="Masterschool Fitness Club $TS"
club_resp="$(auth_curl_json POST "$BASE_URL/clubs" "$coach_token" "$(jq -n --arg name "$club_name" --arg desc "Demo club created from script" '{name:$name, description:$desc}')" )"
echo "$club_resp" | jq .
club_id="$(echo "$club_resp" | jq -r '.id // .club.id // empty')"
[[ -n "$club_id" ]] || { echo "ERROR: Could not parse club_id."; exit 1; }
echo "club_id=${club_id}"
echo

# ====== 4) (OPTIONAL) ADD MEMBERSHIP (athlete joins club) ======
# Adjust path/body if your project differs (e.g. /clubs/{club_id}/memberships).
echo "-> Adding athlete as club member (role='athlete')..."
membership_body="$(jq -n --arg uid "${athlete_id:-0}" --arg cid "$club_id" --arg role "athlete" '{user_id:($uid|tonumber), club_id:($cid|tonumber), role:$role}')"

# Try common routes in order:
mem_resp="$(auth_curl_json POST "$BASE_URL/memberships" "$coach_token" "$membership_body" || true)"
if [[ -z "$mem_resp" || "$mem_resp" == "null" || "$(echo "$mem_resp" | jq -r '.detail? // empty')" != "" ]]; then
  echo "   Fallback: trying /clubs/$club_id/memberships ..."
  mem_resp="$(auth_curl_json POST "$BASE_URL/clubs/$club_id/memberships" "$coach_token" "$(jq -n --arg uid "${athlete_id:-0}" --arg role "athlete" '{user_id:($uid|tonumber), role:$role}')" || true)"
fi
echo "${mem_resp:-{}}" | jq .
echo

# ====== 5) CREATE PLAN under the club ======
echo "-> Creating plan..."
plan_resp="$(auth_curl_json POST "$BASE_URL/clubs/$club_id/plans" "$coach_token" "$(jq -n '{name:"September Conditioning", plan_type:"club", description:"Demo plan via script"}')" )"
echo "$plan_resp" | jq .
plan_id="$(echo "$plan_resp" | jq -r '.id // .plan.id // empty')"
[[ -n "$plan_id" ]] || { echo "ERROR: Could not parse plan_id."; exit 1; }
echo "plan_id=${plan_id}"
echo

# ====== 6) (OPTIONAL) ASSIGN PLAN to athlete ======
# If your project uses plan assignments separately:
# Try /plan_assignments or /plans/{plan_id}/assignments
echo "-> (Optional) Assign plan to athlete (if route exists)..."
assign_payload="$(jq -n --arg pid "$plan_id" --arg uid "${athlete_id:-0}" '{plan_id:($pid|tonumber), user_id:($uid|tonumber), role:"athlete"}')"
assign_resp="$(auth_curl_json POST "$BASE_URL/plan_assignments" "$coach_token" "$assign_payload" || true)"
if [[ -z "$assign_resp" || "$assign_resp" == "null" || "$(echo "$assign_resp" | jq -r '.detail? // empty')" != "" ]]; then
  echo "   Fallback: trying /plans/$plan_id/assignments ..."
  assign_resp="$(auth_curl_json POST "$BASE_URL/plans/$plan_id/assignments" "$coach_token" "$(jq -n --arg uid "${athlete_id:-0}" '{user_id:($uid|tonumber), role:"athlete"}')" || true)"
fi
echo "${assign_resp:-{}}" | jq .
echo

# ====== 7) CREATE SESSION under the plan ======
echo "-> Creating session..."
# Example ISO times; adjust fields to your schema (e.g. start_time/end_time or datetime)
session_body="$(jq -n '{
  date: (now | todate),
  start_time: "18:00",
  end_time: "19:00",
  location: "Campus Gym",
  note: "Intro session from demo script"
}')"

session_resp="$(auth_curl_json POST "$BASE_URL/clubs/$club_id/plans/$plan_id/sessions" "$coach_token" "$session_body" )"
echo "$session_resp" | jq .
session_id="$(echo "$session_resp" | jq -r '.id // .session.id // empty')"
echo "session_id=${session_id:-unknown}"
echo

# ====== 8) LIST THINGS BACK ======
echo "-> Listing clubs..."
auth_curl_json GET "$BASE_URL/clubs" "$coach_token" | jq '.[-5:]'

echo "-> Listing plans for club..."
auth_curl_json GET "$BASE_URL/clubs/$club_id/plans" "$coach_token" | jq '.[-5:]'

echo "-> Listing sessions for plan..."
auth_curl_json GET "$BASE_URL/clubs/$club_id/plans/$plan_id/sessions" "$coach_token" | jq '.[-5:]'

echo
echo "=== Done. You can explore more at: $BASE_URL/docs ==="

# TO RUN:
# cd ClubConnect
# chmod +x scripts/demo.sh
# ./scripts/demo.sh

# or against local:
# BASE_URL="http://localhost:8000" ./scripts/demo.sh