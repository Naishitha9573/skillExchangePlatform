# Connected learning on SkillSwap

The existing `conversations`, `messages`, `learning_sessions`, `swap_requests`,
`notifications`, and `ratings` remain the source of truth. This upgrade adds no
parallel chat or booking tables. `app/collaboration.py` owns the chat/scheduling
operations and REST router; `app/realtime.py` owns event delivery and call signaling.
Both routers are registered in `app/main.py`.

## Workflow and permissions

1. Discover a skill and propose a swap using one of your offers. Both offered
   listings and learning goals can be the target of a proposal.
2. The receiver accepts; the existing ordered participant-pair conversation is
   created/reused. A pending proposal also permits discussion. Existing direct
   conversations remain usable even without an accepted swap.
3. Messages persist before publication. Each message has a UTC timestamp, optional
   client UUID for idempotent retries, and a nullable read timestamp. The sender is
   always derived from authentication. A read receipt only marks incoming messages
   through the last displayed ID; opening an unrelated notification does not mark
   messages read. Historical conversations are private to their two participants.
4. Book through Learning Sessions. New bookings require an accepted or completed
   swap between the selected users. The UI offers 30/60/90 minutes; the existing API
   range of 15–180 minutes remains supported. Both calendars are checked for overlap.
   SQLite takes a write reservation before checking; PostgreSQL locks participant
   rows in a consistent order. Either participant can reschedule or cancel.
5. The private video room uses the learning session ID, not a new meeting record.
   It opens 15 minutes before the start and closes 60 minutes after the scheduled
   end. The server rechecks ownership, status, and the time window on join and on
   every signaling event. Only one tab/device per participant can occupy a room.
6. Complete a session after its scheduled start. When no other scheduled sessions
   remain for its accepted swap, the swap is also completed. Existing manual swap
   completion remains available. Completed and cancelled sessions cannot reopen.
7. Each participant can submit one review per completed exchange. Completion and
   reviews are participant reports, not independent verification of teaching quality.

## APIs and event contract

Existing `/api/v1/messages`, `/messages/{other_id}`, `/sessions`,
`/sessions/{session_id}`, swaps, ratings, and notification routes remain registered.
`GET /messages/{other_id}` now returns the newest 100 messages in ascending order;
use `before_id` and `limit` (1–100) for older history. Session PATCH accepts the
existing `status` plus optional `scheduled_at`, `duration_minutes`, and `topic`.
Stricter relationship, date, status, and ownership validation intentionally rejects
bookings and mutations that the previous implementation accepted incorrectly.

Added endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/conversations` | Own conversations, last messages, unread counts |
| `POST /api/v1/conversations` | Open/reuse a pair conversation with `participant_id` |
| `POST /api/v1/conversations/{id}/read` | Mark incoming messages through `through_id` |
| `GET /api/v1/partners` | Accepted/completed swaps and their partners/topics |
| `GET /api/v1/sessions/{id}` | Own session and call availability |
| `GET /api/v1/sessions/{id}/ice-config` | Authorized STUN/TURN configuration |
| `GET /api/v1/ratings` | Reviews submitted by the current user |
| `GET /api/v1/skills/mine` | Current user's offers/goals without discovery's limit |
| `GET /api/v1/auth/providers` | Google sign-in availability |
| `WS /api/v1/ws` | Authenticated events and signaling |

The socket's first frame, within 10 seconds, must be
`{"type":"auth","token":"<access JWT>"}`. Tokens never appear in WebSocket URLs.
Browser origins must match `CORS_ORIGINS`. Invalid/expired tokens close with `4401`;
disallowed origins use `4403`. Connections are bounded to five per account and
180 incoming events per 10 seconds per connection. Send `ping` every 15 seconds;
the server replies `pong` and closes idle connections after 45 seconds.

Server events: `ready`, `message.created`, `message.ack`, `messages.read`,
`conversations.changed`, `notifications.changed`, `swaps.changed`, `session.updated`,
`call.joined`, `call.waiting`, `call.peer_ready`, `call.peer_left`, `call.closed`,
`call.offer`, `call.answer`, `call.ice`, `error`, and `pong`.

Clients may send `message.send` with `receiver_id`, `body`, and optional UUID
`client_id`. The current UI sends durable messages through the preserved POST
endpoint and receives updates over WebSockets. Both transports use the same
persistence function. REST retries reuse the UUID so a lost response cannot create
duplicate messages or notifications. Reconnect uses bounded exponential backoff,
then refetches persisted messages/counts; read receipts and notifications also sync
across tabs. The bell retains a 30-second fallback only while realtime is unavailable.

Calls send `call.join` with `session_id`, then exchange `call.offer` / `call.answer`
with `description: {type, sdp}` and `call.ice` with an ICE candidate object.
`call.leave` releases the current room. The first participant makes the offer once
the second is ready. Incoming candidates are queued until a remote description is
set. Rejoining rebuilds the peer connection. Leave/unmount closes the peer and stops
every local media track. A scheduling change closes the signaling room and clients
release their media. The server never accepts a user-supplied recipient for signaling.

## Database upgrade

Back up the database before deployment. SQLite startup runs the existing idempotent
additive upgrade. It adds `messages.read_at`, `messages.client_id`, and indexes for
unread queries and per-sender UUID uniqueness. Old message bodies and sessions are
preserved. Pre-upgrade messages are initially marked read because the old system did
not track reads; subsequent unread messages stay unread on future startups.

New PostgreSQL databases use the models normally. For an existing PostgreSQL
deployment, run `backend/migrations/20260912_collaboration.sql` once during release;
SQLite's compatibility migrator intentionally does not execute against PostgreSQL.
The original normalized schema must already be present before applying this migration.

## Deployment

- Run **one Uvicorn worker** for this implementation. Example from `backend`:
  `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --ws-max-size 65536`.
  The event hub and call-room membership live in memory. Multiple workers/replicas
  require a shared event bus **and** room registry; sticky sessions alone do not
  ensure that both partners reach the same worker. A restart is recoverable for chat
  through database history; calls reconnect while both users remain on the page.
- Use an ASGI host with WebSocket upgrade support, HTTPS/WSS, and a proxy idle
  timeout above 60 seconds. Serve the frontend with SPA fallback to `index.html`,
  including `/auth/google/callback` and `/sessions/{id}/call`. Configure exact frontend
  origins in `CORS_ORIGINS`, and build with `VITE_API_URL` pointing to your API.
- Browsers need HTTPS (or localhost) for camera/microphone access. They also need
  user permission. The UI includes denied-permission recovery and audio-only
  fallback when no camera exists. Calls use native browser WebRTC; media flows
  between peers or through your TURN relay and is not recorded by the application.
- STUN alone does **not** guarantee calls across every NAT/firewall. For dependable
  internet calls, deploy coturn and configure `TURN_URLS` and backend-only
  `TURN_SECRET`. Enable coturn's `use-auth-secret` with the same shared secret.
  Example URL format: `turn:turn.example.com:3478?transport=udp,turns:turn.example.com:5349?transport=tcp`.
  The authenticated endpoint mints expiring HMAC credentials, never returns the
  shared secret, and uses `TURN_CREDENTIAL_TTL_SECONDS` (default four hours).
  Open the relay's listener/relay ports according to your coturn configuration.
- Register a Google OAuth web client and its exact redirect URI, such as
  `https://app.example.com/auth/google/callback`. Configure `GOOGLE_CLIENT_ID`,
  `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in backend deployment secrets.
  Google state is verified against both a signed expiry and an HttpOnly browser
  cookie, plus a frontend session-state check. Prefer frontend and API under the
  same site, or proxy `/api` through the frontend host, so browsers that block
  third-party cookies can complete OAuth. Email/password login remains available
  when Google is unconfigured. Set `DEMO_MODE=false` outside demo deployments.
- Put database files on persistent storage. Keep `SECRET_KEY` stable and at least
  32 random characters. Configure edge rate limits for public auth endpoints before
  opening a public service. No `.env` files were changed by this implementation.

Example Nginx locations (merge into an existing HTTPS server block):

```nginx
location /api/v1/ws {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 75s;
}
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
}
location / {
    try_files $uri $uri/ /index.html;
}
```

## Validation

From a working environment, install `backend/requirements-dev.txt`, then run:

```text
python -m pytest backend/tests -q
python -m ruff check backend/app backend/tests --select F
cd frontend
npm run build
```

`python backend/tests/browser_flow.py` launches its own hidden local servers on
8011/5178 and Chrome contexts with synthetic cameras/microphones. It uses an ignored
disposable SQLite database, checks real media in both browsers, and captures desktop
and mobile screenshots under `.artifacts/browser`. It never changes the development
database. Local synthetic-media success does not replace a TURN-equipped test across
two real networks or testing permission prompts on physical mobile devices.

Implementation references: [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/),
[WebRTC signaling and video calling](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Signaling_and_video_calling),
[Google OAuth web-server flow](https://developers.google.com/identity/protocols/oauth2/web-server).
