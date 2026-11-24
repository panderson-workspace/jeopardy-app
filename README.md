# Analytics Jeopardy
 
A live, browser-based Jeopardy game built with **Streamlit** (UI) and **Google Sheets** (database). Built to run inside a Teams/Zoom call: the host screenshares the board, players join from any device with a public URL and buzz in from their phones.
 
---
 
## Architecture
 
| Layer | Tool |
|---|---|
| UI / app server | Streamlit (`app.py`) |
| Database | Google Sheets via `gspread` + service account |
| Hosting | Streamlit Community Cloud (auto-redeploys on every push to GitHub) |
| Version control | Git + GitHub |
 
---
 
## Setup
 
### 1. Google Sheet
 
Create a Google Sheet with these four tabs. Header names must match exactly (lowercase, no leading/trailing spaces).
 
**`Players`**
 
| name | score |
|---|---|
 
**`GameState`** (labels in column A, values in column B)
 
| A | B |
|---|---|
| active_question_id | *(blank)* |
| buzzer_locked | FALSE |
| first_buzzer | *(blank)* |
| show_answer | FALSE |
 
**`JeopardyContent`**
 
| id | category | value | question | answer | used |
|---|---|---|---|---|---|
 
- `id` must be unique per row (1, 2, 3...).
- `value` is numeric (100, 200, 300, 400).
- Leave `used` blank. The app writes `TRUE` when a question is played.
- The app expects values of 100-400 per category to render cleanly on the board.
**`BuzzerLog`**
 
| timestamp | player_name | question_id | status |
|---|---|---|---|
 
`question_id` matches `id` in `JeopardyContent`, so you can audit buzz order per question directly in the Sheet. `status` is `FIRST` or `LATE`.
 
### 2. Google Cloud service account
 
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project.
2. Enable **Google Sheets API** and **Google Drive API**.
3. **IAM & Admin → Service Accounts** → create one → **Keys → Add Key → JSON**. Download the file.
4. Copy the `client_email` from the JSON and **share your Sheet with that email as Editor**.
### 3. Local project
 
```bash
mkdir jeopardy-app && cd jeopardy-app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install streamlit gspread google-auth
```
 
Project structure:
 
```
jeopardy-app/
├── app.py
├── requirements.txt
└── .streamlit/
    ├── config.toml
    └── secrets.toml     # local only, never commit
```
 
**`requirements.txt`** — write this by hand. Do **not** use `pip freeze` from an Anaconda environment; it embeds local file paths and breaks the cloud build.
 
```
streamlit
gspread
google-auth
```
 
**`.streamlit/config.toml`** — do **not** hardcode a local IP; it breaks cloud deployment.
 
```toml
[server]
headless = true
port = 8501
```
 
**`.streamlit/secrets.toml`** — values come from the downloaded service account JSON, plus your own host password and Sheet ID.
 
```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
 
[app]
host_password = "choose-a-host-password"
spreadsheet_key = "YOUR_SHEET_ID"
```
 
- `spreadsheet_key` is the string in the Sheet URL between `/d/` and `/edit`.
- Keep `private_key` on one line with the `\n` characters intact.
- Add `.streamlit/secrets.toml` to `.gitignore`.
### 4. Run locally (optional)
 
```bash
streamlit run app.py
```
 
### 5. Deploy to Streamlit Cloud
 
1. Push the repo to GitHub (private repos work).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with the same GitHub account.
3. **New app** → select repo, branch `main`, main file `app.py`, and optionally a custom URL.
4. **Settings → Secrets** → paste the full contents of your local `secrets.toml` → Save.
5. Deploy. Every `git push` redeploys automatically in about 60-90 seconds.
Share the resulting `*.streamlit.app` URL with participants.
 
---
 
## Caching and API limits
 
The Google Sheets API free tier allows **60 read requests per minute per project**. Without caching, every player's browser would hit the Sheet independently and exceed that quickly (20 players polling every 3 seconds = ~400 reads/min).
 
The app avoids this with **server-side shared caching** (`@st.cache_data`). The cache lives in the Streamlit server's memory and is shared across all connected users, so the Sheet is read once per window regardless of how many people are connected.
 
| Data | Cache TTL | Notes |
|---|---|---|
| Game state (active question, buzzer, answer toggle) | 3 sec | Read via a single `batch_get` of B1:B4 |
| Players / scores | 5 sec | Cleared immediately when points are applied |
| Questions (JeopardyContent) | 300 sec | Cleared when a question is marked used |
 
Other protections:
- Caches are manually cleared after every write (buzz, score change, question select) so reads reflect the latest state.
- `safe_read()` retries up to 3 times on `429` rate-limit errors instead of crashing.
- The Sheet connection itself is cached with `@st.cache_resource`.
**How polling works:** a `@st.fragment(run_every=3)` re-renders only the question/buzzer area every 3 seconds on each player's screen. With the shared cache, that costs roughly **20 Sheet reads per minute total**, independent of player count.
 
### Capacity
 
- **Estimated comfortable capacity: ~20-30 simultaneous players** on Streamlit Community Cloud (free tier) and the free Sheets quota.
- Reads are effectively flat (~20/min). The remaining constraint is **writes** (buzz attempts, score updates), which are not cached. Each buzz attempt is a live read plus a write and a log append.
- This is an estimate from the architecture, not a formal load test. Run a dry run with several simultaneous buzzers before any live session.
- To lower API usage further, raise the fragment `run_every` and the game state `ttl` to 4-5 seconds. Players will see updates 1-2 seconds later.
---
 
## Operating the game as host
 
**Before the session**
1. Open the app URL ~5 minutes early. Free-tier apps sleep when idle and a brief "waking up" message (including a `connection refused` health check line in the logs) is normal.
2. Clear old rows from `Players` and `BuzzerLog`, and clear the `used` column in `JeopardyContent`.
3. Confirm `GameState` B2 = `FALSE`, B4 = `FALSE`, and B1/B3 are blank.
4. Post the URL in the meeting chat.
**Joining**
- Everyone, including you, enters a name on the lobby screen. Players can join at any point mid-game and start at 0 points.
- Open the sidebar and enter the **host password**. A `HOST` badge appears, the sidebar controls unlock, and the board becomes clickable. Players never see host controls and never get a buzz-in-disabled board.
**Running a question**
 
| Step | Action |
|---|---|
| 1 | Click a point value on the board. The question is written to the Sheet, the buzzer resets, and the tile is marked used. |
| 2 | Within ~3 seconds the question appears on every player's screen and the buzz button is live. |
| 3 | First player to buzz locks the buzzer. Everyone sees who buzzed first. Late buzzes get "Oops, too slow!" and are logged as `LATE`. |
| 4 | Call on the first buzzer. **Sidebar → Award / Deduct Points** → select player, enter points (negative to deduct), **Apply Points**. |
| 5 | If they're wrong: **Reset Buzzer** reopens buzzing, or check **Show Buzz Order** (or the `BuzzerLog` tab filtered by `question_id`) to call on the second responder. |
| 6 | **Toggle Reveal Answer** to show the answer banner on all screens. |
| 7 | Click the next question (auto-resets the buzzer), or use **Clear Active Question** to blank the question and reset. |
 
**Sidebar controls**
- **Reset Buzzer** — reopens the buzzer and hides the answer; use for accidental buzzes or wrong answers.
- **Award / Deduct Points** — manual scoring per player.
- **Toggle Reveal Answer** — show or hide the answer for everyone.
- **Clear Active Question** — clears the question and resets the buzzer.
- **Show Buzz Order** — lists buzzes for the current question in order.
**Nothing resets automatically.** The buzzer only resets when you click a new question, Reset Buzzer, or Clear Active Question.
 
---
 
## Known limitations
 
- **Buzz fairness is not fully atomic.** `buzz_in` reads the lock state, then writes. Two buzzes landing within the same fraction of a second could both pass the check. The `BuzzerLog` timestamps (second-level resolution) let you verify order manually.
- **Up to ~3 second visual lag.** The buzz button disables on other players' screens on their next refresh; clicks in that window are still rejected at the Sheet level.
- **Scoreboard and board tiles refresh on full page rerun**, not on the 3-second fragment. A player's view of scores and used tiles updates when their page reruns (for example after they buzz or refresh), not instantly after you award points.
- **Scoreboard shows the top 3 players** by default. Change `sorted_players[:3]` in `app.py` to show more.
- **Local testing vs. cloud:** if you add a `[browser] serverAddress` IP to `config.toml` for local testing, remove it before pushing, or the cloud deploy will fail.
- **Host auth is a single shared password** stored in secrets. Suitable for internal sessions, not for sensitive data.
---
 
## Troubleshooting
 
| Symptom | Fix |
|---|---|
| `429 Quota exceeded` error | Wait ~60 seconds. Raise cache TTLs / `run_every`. Avoid rapid manual refreshing. |
| Cloud build fails on `requirements.txt` | Replace with the clean 3-line version above. |
| Cloud app crashes with `connection refused` on startup | Remove any hardcoded IP from `.streamlit/config.toml`. |
| `KeyError: 'category'` (or similar) | A Sheet header has a stray space or wrong name. |
| `st.secrets has no key` | Secrets not saved in Streamlit Cloud settings, or section names don't match. |
| Host kicked back to lobby | Make sure the host password persists via `st.session_state.host_pw` (already in the code). |
 
