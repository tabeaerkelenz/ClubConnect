#!/usr/bin/env bash
set -euo pipefail

# ================== CONFIG ==================
BASE_URL="${BASE_URL:-http://localhost:8000}"
JQ_BIN="${JQ_BIN:-jq}"

TS="${TS:-$(date +%s)}"
COACH_EMAIL="${COACH_EMAIL:-coach+$TS@example.com}"   ; COACH_PASS="coachpass"
MEMBER1_EMAIL="${MEMBER1_EMAIL:-alice+$TS@example.com}" ; MEMBER1_PASS="alicepass"
MEMBER2_EMAIL="${MEMBER2_EMAIL:-bob+$TS@example.com}"   ; MEMBER2_PASS="bobpass12"

CLUB_NAME="Berlin Sparks"
GROUP_NAME="U18 Women Basketball"
PLAN_NAME="Offseason 2025"
PERSONAL_PLAN_NAME="Alice Personal Plan"
SESSION_NAME="Conditioning Kickoff"
EX1_NAME="Burpees"
EX2_NAME="Bodyweight Squats"


# --- write .demo_env on exit (even on errors) ---
write_demo_env() {
  cat > .demo_env <<EOF
export BASE_URL="${BASE_URL:-}"
export COACH_EMAIL="${COACH_EMAIL:-}"
export MEMBER1_EMAIL="${MEMBER1_EMAIL:-}"
export MEMBER2_EMAIL="${MEMBER2_EMAIL:-}"
export COACH_TOKEN="${COACH_TOKEN:-}"
export MEMBER1_TOKEN="${MEMBER1_TOKEN:-}"
export MEMBER2_TOKEN="${MEMBER2_TOKEN:-}"
export CLUB_ID="${CLUB_ID:-}"
export GROUP_ID="${GROUP_ID:-}"
export PLAN_ID="${PLAN_ID:-}"
export SESSION_ID="${SESSION_ID:-}"
export COACH_PASS="${COACH_PASS:-}"
export MEMBER1_PASS="${MEMBER1_PASS:-}"
export MEMBER2_PASS="${MEMBER2_PASS:-}"
EOF
  echo "Wrote .demo_env (run: source .demo_env)"
}
trap write_demo_env EXIT


# ================== HELPERS ==================
color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
title() { color "1;36" "▶ $*"; }
ok()    { color "1;32" "✔ $*"; }
info()  { color "0;33" "• $*"; }
die()   { color "1;31" "✖ $*"; exit 1; }

command -v "$JQ_BIN" >/dev/null || die "Please install jq (brew install jq / apt install jq)."

api() {
  # $1=METHOD $2=PATH [$3=TOKEN]
  local method="$1" path="$2" token="${3:-}"
  if [[ -t 0 ]]; then
    curl -sS -X "$method" "${BASE_URL}${path}" \
      -H "Accept: application/json" -H "Content-Type: application/json" \
      ${token:+ -H "Authorization: Bearer $token"}
  else
    curl -sS -X "$method" "${BASE_URL}${path}" \
      -H "Accept: application/json" -H "Content-Type: application/json" \
      ${token:+ -H "Authorization: Bearer $token"} \
      --data-binary @-
  fi
}

# Cross-platform ISO8601 UTC builders (GNU date or BSD date)
iso_plus() { # $1=days $2=HH:MM
  local d="$1" hm="$2"
  if date -u -d "now" '+%Y' >/dev/null 2>&1; then
    # GNU date
    date -u -d "+${d} day ${hm}" +'%Y-%m-%dT%H:%M:%SZ'
  else
    # BSD date (macOS)
    local H="${hm%%:*}" M="${hm##*:}"
    date -u -v+"${d}"d -v"${H}"H -v"${M}"M -v0S +'%Y-%m-%dT%H:%M:%SZ'
  fi
}

# ================== AUTH ==================
create_user() {
  local email="$1" pass="$2" name="$3"
  api POST "/users" <<<"{
    \"email\": \"$email\",
    \"password\": \"$pass\",
    \"name\": \"$name\"
  }" >/dev/null || true  # ignore conflict if already exists
}

login() {
  local email="$1" pass="$2"
  local resp token
  resp=$(curl -sS -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=$email" \
    --data-urlencode "password=$pass")
  token=$(echo "$resp" | jq -r '.access_token // .token // .jwt // empty')
  if [[ -z "$token" || "$token" == "null" ]]; then
    echo "Login failed for $email. Raw response:" >&2
    echo "$resp" >&2
    exit 1
  fi
  printf '%s' "$token"
}

me_id() {
  local token="$1" resp
  resp=$(curl -sS "$BASE_URL/auth/me" -H "Authorization: Bearer $token")
  echo "$resp" | jq -er '.id' 2>/dev/null || { echo "$resp" >&2; exit 1; }
}

# ================== FLOW ==================
title "Health check (optional)"
api GET "/healthz" | $JQ_BIN -r . 2>/dev/null || info "healthz not JSON (ok)"

title "Create 3 users"
create_user "$COACH_EMAIL"  "$COACH_PASS"  "Coach Carla"
create_user "$MEMBER1_EMAIL" "$MEMBER1_PASS" "Alice A."
create_user "$MEMBER2_EMAIL" "$MEMBER2_PASS" "Bob B."
ok "Users ensured"

title "Login all users"
COACH_TOKEN="$(login "$COACH_EMAIL" "$COACH_PASS")"
MEMBER1_TOKEN="$(login "$MEMBER1_EMAIL" "$MEMBER1_PASS")"
MEMBER2_TOKEN="$(login "$MEMBER2_EMAIL" "$MEMBER2_PASS")"
ok "Got JWTs"

title "Resolve user IDs with GET /auth/me"
COACH_ID="$(me_id "$COACH_TOKEN")"
ALICE_ID="$(me_id "$MEMBER1_TOKEN")"
BOB_ID="$(me_id "$MEMBER2_TOKEN")"
info "Coach=$COACH_ID, Alice=$ALICE_ID, Bob=$BOB_ID"

# ---- Clubs ----
title "Coach creates a club"
CLUB_ID="$(
  api POST "/clubs" "$COACH_TOKEN" <<<"{
    \"name\": \"$CLUB_NAME\",
    \"description\": \"High-tempo, fundamentals-first\"
  }" | $JQ_BIN -r '.id'
)"
ok "Club '$CLUB_NAME' → id=$CLUB_ID"

title "List/Search clubs (public)"
api GET "/clubs" | $JQ_BIN -r '.[0:3] | .[]? | [.id,.name] | @tsv' || true

title "My clubs (coach)"
api GET "/clubs/mine" "$COACH_TOKEN" | $JQ_BIN -r '.[] | [.id,.name] | @tsv'

# ---- Club memberships ----
title "Coach adds club memberships by email"
api POST "/clubs/${CLUB_ID}/memberships" "$COACH_TOKEN" <<<"{
  \"email\":\"$MEMBER1_EMAIL\", \"role\":\"member\"
}" | $JQ_BIN -r '.id' >/dev/null
api POST "/clubs/${CLUB_ID}/memberships" "$COACH_TOKEN" <<<"{
  \"email\":\"$MEMBER2_EMAIL\", \"role\":\"member\"
}" | $JQ_BIN -r '.id' >/dev/null
ok "Alice & Bob added"

title "List club memberships"
MEMBERSHIPS_JSON="$(api GET "/clubs/${CLUB_ID}/memberships" "$COACH_TOKEN")"
echo "$MEMBERSHIPS_JSON" | $JQ_BIN -r '.[] | [.id,.user_id,.role] | @tsv' || echo "$MEMBERSHIPS_JSON"

# ---- Groups ----
title "Coach creates a group"
GROUP_ID="$(
  api POST "/clubs/${CLUB_ID}/groups" "$COACH_TOKEN" <<<"{
    \"name\": \"$GROUP_NAME\",
    \"description\": \"Under-18 Women Team\"
  }" | $JQ_BIN -r '.id'
)"
ok "Group '$GROUP_NAME' → id=$GROUP_ID"

title "Add group members (by user_id)"
api POST "/clubs/${CLUB_ID}/groups/${GROUP_ID}/memberships" "$COACH_TOKEN" <<<"{
  \"user_id\": $ALICE_ID, \"role\": \"member\"
}" | $JQ_BIN -r '.id' >/dev/null
api POST "/clubs/${CLUB_ID}/groups/${GROUP_ID}/memberships" "$COACH_TOKEN" <<<"{
  \"user_id\": $BOB_ID, \"role\": \"member\"
}" | $JQ_BIN -r '.id' >/dev/null
ok "Alice & Bob added to group"

title "List group members"
api GET "/clubs/${CLUB_ID}/groups/${GROUP_ID}/memberships" "$COACH_TOKEN" \
  | $JQ_BIN -r '.[] | [.user_id,.role] | @tsv'

# ---- Member views ----
title "Member (Alice) — my clubs & groups"
api GET "/clubs/mine" "$MEMBER1_TOKEN" | $JQ_BIN -r '.[] | [.id,.name] | @tsv'
api GET "/clubs/${CLUB_ID}/groups" "$MEMBER1_TOKEN" | $JQ_BIN -r '.[] | [.id,.name] | @tsv'

# ---- Plans (club) ----
title "Coach creates a club plan"
PLAN_ID="$(
  api POST "/clubs/${CLUB_ID}/plans" "$COACH_TOKEN" <<<"{
    \"name\":\"$PLAN_NAME\",
    \"plan_type\":\"club\",
    \"description\":\"Build base conditioning\"
  }" | $JQ_BIN -r '.id'
)"
ok "Plan '$PLAN_NAME' → id=$PLAN_ID"

title "Coach adds exercises to the plan"
post_ex() {
  local name="$1" desc="$2"
  local resp code
  resp=$(curl -sS -w '\n%{http_code}' -X POST \
    "$BASE_URL/clubs/$CLUB_ID/plans/$PLAN_ID/exercises" \
    -H "Authorization: Bearer $COACH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\",\"description\":\"$desc\"}")
  code="${resp##*$'\n'}"
  [[ "$code" -lt 400 ]] || die "Create exercise failed ($code): ${resp%$'\n'*}"
}
post_ex "$EX1_NAME" "demo"
post_ex "$EX2_NAME" "demo"
ok "Exercises created"

# ---- Sessions for plan ----
START_TS="$(iso_plus 1 '18:00')"
END_TS="$(iso_plus 1 '19:30')"
title "Coach creates a session"
SESSION_ID="$(
  api POST "/clubs/${CLUB_ID}/plans/${PLAN_ID}/sessions" "$COACH_TOKEN" <<<"{
    \"name\":\"$SESSION_NAME\",
    \"location\":\"Campus Gym\",
    \"starts_at\":\"$START_TS\",
    \"ends_at\":\"$END_TS\",
    \"note\":\"Bring water\"
  }" | $JQ_BIN -r '.id'
)"
ok "Session '$SESSION_NAME' → id=$SESSION_ID"

title "List sessions"
api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}/sessions" "$COACH_TOKEN" \
  | $JQ_BIN -r '.[] | [.id,.name,.starts_at,.ends_at] | @tsv'

# ---- Plan assignments (group + specific user) ----
title "Assign plan to group"
api POST "/clubs/${CLUB_ID}/plans/${PLAN_ID}/assignees" "$COACH_TOKEN" <<<"{
  \"group_id\": $GROUP_ID
}" | $JQ_BIN -r '.id' >/dev/null

title "Assign plan to Alice"
api POST "/clubs/${CLUB_ID}/plans/${PLAN_ID}/assignees" "$COACH_TOKEN" <<<"{
  \"user_id\": $ALICE_ID
}" | $JQ_BIN -r '.id' >/dev/null
ok "Assignments done"

title "Member (Alice) — plans assigned to me"
api GET "/clubs/${CLUB_ID}/plans/mine" "$MEMBER1_TOKEN" \
  | $JQ_BIN -r '.[] | [.id,.name,.plan_type] | @tsv'

title "Member (Alice) — plan overview (assigned)"
# core fields
api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}" "$MEMBER1_TOKEN" | $JQ_BIN -r '.name, .plan_type'

# counts via list endpoints (members can view assigned plans)
EX_COUNT=$(api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}/exercises" "$MEMBER1_TOKEN" \
  | $JQ_BIN 'if type=="array" then length else (.items // [] | length) end')

SESS_COUNT=$(api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}/sessions" "$MEMBER1_TOKEN" \
  | $JQ_BIN 'if type=="array" then length else (.items // [] | length) end')

echo "exercises=$EX_COUNT  sessions=$SESS_COUNT"

# (optional) tiny previews
api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}/exercises" "$MEMBER1_TOKEN" \
  | $JQ_BIN -r 'if type=="array" then . else .items // [] end | [.[0].name, .[1].name] | map(select(.)) | join(", ") as $n | if ($n|length)>0 then "e.g. " + $n else empty end'
api GET "/clubs/${CLUB_ID}/plans/${PLAN_ID}/sessions" "$MEMBER1_TOKEN" \
  | $JQ_BIN -r 'if type=="array" then . else .items // [] end | .[0] | select(.) | [.id,.name] | @tsv'

# ---- Attendance (note: attendance routes are by club+session, no plan_id) ----
title "Coach marks attendance for session"
api POST "/clubs/${CLUB_ID}/sessions/${SESSION_ID}/attendances?user_id=${ALICE_ID}" "$COACH_TOKEN" <<<'{"status":"present"}' >/dev/null
api POST "/clubs/${CLUB_ID}/sessions/${SESSION_ID}/attendances?user_id=${BOB_ID}"   "$COACH_TOKEN" <<<'{"status":"absent"}'  >/dev/null
ok "Attendance recorded"

title "List attendances for session"
api GET "/clubs/${CLUB_ID}/sessions/${SESSION_ID}/attendances" "$COACH_TOKEN" \
  | $JQ_BIN -r '(if type=="array" then . else .items // .attendances // [] end)
                | if length==0 then "— none —" else .[] | [.id,.user_id,.status] | @tsv end'

# ---- Member personal plan (no sessions; just exercises) ----
title "Alice creates a personal plan"
ALICE_PERSONAL_PLAN_ID="$(
  api POST "/clubs/${CLUB_ID}/plans" "$MEMBER1_TOKEN" <<<"{
    \"name\":\"$PERSONAL_PLAN_NAME\",
    \"plan_type\":\"personal\",
    \"description\":\"My own off-day workouts\"
  }" | $JQ_BIN -r '.id'
)"
ok "Alice personal plan → id=$ALICE_PERSONAL_PLAN_ID"

title "Alice adds exercises to her personal plan"
api POST "/clubs/${CLUB_ID}/plans/${ALICE_PERSONAL_PLAN_ID}/exercises" "$MEMBER1_TOKEN" <<<"{
  \"name\":\"Plank\", \"description\":\"Core stability\", \"sets\":3, \"reps\":60
}" | $JQ_BIN -r '.id' >/dev/null

title "DONE"
echo "Club:          $CLUB_ID"
echo "Group:         $GROUP_ID"
echo "Plan (club):   $PLAN_ID"
echo "Session:       $SESSION_ID"
echo "Alice plan:    $ALICE_PERSONAL_PLAN_ID"


