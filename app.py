import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Analytics Jeopardy", layout="wide", initial_sidebar_state="collapsed")

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
* { box-sizing: border-box; }
[data-testid="stAppViewContainer"] { background-color: #f5f0eb; }
[data-testid="stHeader"] { background-color: #241a10; }
[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
[data-testid="stSidebar"] {
    background-color: #3d2e18;
    width: 240px !important;
    min-width: 240px !important;
}
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stSidebar"] * { color: #edf5e6 !important; }
[data-testid="stSidebar"] input {
    background-color: #241a10 !important;
    color: #edf5e6 !important;
    border-color: #5a7a4a !important;
}
[data-testid="stSidebar"] .stButton button {
    background-color: #5a7a4a !important;
    color: #edf5e6 !important;
    border: none !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton button:hover { background-color: #4a6038 !important; }
h1, h2, h3 { color: #241a10 !important; }
h1 a, h2 a, h3 a { display: none !important; }
p, label { color: #3d2e18 !important; }
hr { border-color: #e8c4a0 !important; margin: 16px 0 !important; }

.section-label {
    font-size: 11px; font-weight: 600; color: #8b6a50;
    letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 8px;
}
.score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px; margin-bottom: 20px;
}
.score-card { background: #3d2e18; border-radius: 10px; padding: 12px 14px; }
.score-card.leader { border: 2px solid #b85c38; }
.score-name { font-size: 11px; color: #b8d4a8; margin-bottom: 4px; }
.score-val { font-size: 24px; font-weight: 600; color: #edf5e6; }
.leader-tag { font-size: 9px; color: #b85c38; font-weight: 600; margin-left: 4px; }

.question-card {
    background: #3d2e18; border-radius: 12px;
    padding: 24px 28px; margin-bottom: 16px;
    border-left: 4px solid #b85c38;
}
.question-category {
    font-size: 10px; color: #b8d4a8; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 8px;
}
.question-value {
    font-size: 12px; color: #b85c38; font-weight: 600; margin-bottom: 12px;
}
.question-text {
    font-size: 18px; color: #edf5e6; font-weight: 500; line-height: 1.5;
}
.answer-banner {
    background: #fdeae0; border: 1.5px solid #e8a880;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 16px;
}
.answer-label {
    font-size: 10px; color: #b85c38; font-weight: 600;
    letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 3px;
}
.answer-text { font-size: 15px; color: #3a1a08; font-weight: 500; }
.burgundy-pill {
    background: #8b2040; color: #fde8ef; font-size: 10px;
    padding: 3px 10px; border-radius: 20px; font-weight: 500;
    margin-left: 8px; vertical-align: middle;
}
.buzzer-area {
    background: #fff8f2; border: 1.5px solid #e8c4a0;
    border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
    font-size: 14px; color: #5a3a20; font-weight: 500;
}
.buzzer-highlight { color: #8b2040; font-weight: 600; }
.waiting-state {
    background: #f0ebe4; border: 1.5px solid #e8c4a0;
    border-radius: 12px; padding: 20px; text-align: center;
    color: #8b6a50; font-size: 14px; margin-bottom: 16px;
}
.board-wrap {
    background: #f5f0eb; border-radius: 14px;
    padding: 20px; margin-top: 8px;
}
.board-label {
    color: #5a7a4a; font-size: 18px; letter-spacing: 1px;
    text-transform: uppercase; font-weight: 700; margin-bottom: 14px;
    text-align: center; width: 100%;
}
.cat-header {
    background: #3d2e18; color: #b8d4a8; text-align: center;
    font-weight: 600; font-size: 13px; border-radius: 8px;
    padding: 10px 6px; margin-bottom: 8px; min-height: 52px;
    display: flex; align-items: center; justify-content: center;
    width: 100%;
}
div[data-testid="stButton"] button {
    background-color: #b8d4a8 !important; color: #241a10 !important;
    border: none !important; font-size: 18px !important;
    font-weight: 700 !important; padding: 16px 0 !important;
    border-radius: 8px !important; width: 100% !important;
    margin-bottom: 6px !important; transition: background-color 0.2s !important;
}
div[data-testid="stButton"] button:hover { background-color: #a0c090 !important; }
div[data-testid="stButton"] button:disabled {
    background-color: #d8e8d0 !important; color: #8aaa80 !important;
}
div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button {
    width: 100% !important;
    min-width: 100% !important;
}
div[data-testid="stVerticalBlock"] div[data-testid="stButton"] {
    width: 100% !important;
}
div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button {
    width: 100% !important;
    display: block !important;
}
[data-testid="stColumn"] {
    padding-left: 4px !important;
    padding-right: 4px !important;
}
[data-testid="stColumn"] > div {
    width: 100% !important;
}
.player-pill {
    display: inline-block; background: #b85c38; color: #fff8f0;
    font-size: 12px; padding: 4px 14px; border-radius: 20px;
    font-weight: 500; margin-bottom: 16px;
}
.host-badge {
    display: inline-block; background: #8b2040; color: #fde8ef;
    font-size: 12px; padding: 4px 14px; border-radius: 20px;
    font-weight: 500; margin-bottom: 16px; margin-left: 8px;
}
.lobby-outer {
    display: flex; justify-content: center; align-items: center;
    min-height: 80vh; width: 100%;
}
.lobby-card {
    background: #3d2e18; border-radius: 16px;
    padding: 36px 32px; width: 100%; max-width: 420px;
}

@media (max-width: 768px) {
    .score-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .board-wrap { padding: 12px !important; }
    .cat-header { font-size: 10px !important; padding: 6px 4px !important; min-height: 36px !important; }
    div[data-testid="stButton"] button { font-size: 13px !important; padding: 10px 0 !important; }
    [data-testid="stMainBlockContainer"] { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    .question-text { font-size: 15px !important; }
}
    [data-testid="stColumn"] {
    padding: 0 4px !important;
    flex: 1 !important;
    min-width: 0 !important;
}
[data-testid="stColumn"] > div:first-child {
    width: 100% !important;
}
div[data-testid="stButton"] {
    width: 100% !important;
}
div[data-testid="stButton"] > button {
    width: 100% !important;
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

@st.cache_resource
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["app"]["spreadsheet_key"])

def get_sheet(tab_name):
    return get_spreadsheet().worksheet(tab_name)

# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def get_players_cached():
    ws = get_sheet("Players")
    return ws.get_all_records()

def get_players():
    return get_players_cached()

def add_or_get_player(name):
    ws = get_sheet("Players")
    records = ws.get_all_records()
    if name not in [r["name"] for r in records]:
        ws.append_row([name, 0])
    get_players_cached.clear()

def update_score(name, delta):
    ws = get_sheet("Players")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if r["name"] == name:
            ws.update_cell(i + 2, 2, r["score"] + delta)
            break
    get_players_cached.clear()

@st.cache_data(ttl=3)
def read_game_state_cached():
    try:
        ws = get_sheet("GameState")
        vals = ws.batch_get(["B1", "B2", "B3", "B4"])
        def safe(v, idx):
            try: return v[idx][0][0]
            except: return ""
        return {
            "active_question_id": safe(vals, 0),
            "buzzer_locked":      safe(vals, 1),
            "first_buzzer":       safe(vals, 2),
            "show_answer":        safe(vals, 3),
        }
    except Exception:
        return {"active_question_id": "", "buzzer_locked": "FALSE",
                "first_buzzer": "", "show_answer": "FALSE"}

def read_game_state():
    return read_game_state_cached()

def write_game_state(key, value):
    ws = get_sheet("GameState")
    cell_map = {
        "active_question_id": "B1", "buzzer_locked": "B2",
        "first_buzzer": "B3", "show_answer": "B4",
    }
    ws.update_acell(cell_map[key], value)
    read_game_state_cached.clear()

def reset_buzzer():
    ws = get_sheet("GameState")
    ws.batch_update([
        {"range": "B2", "values": [["FALSE"]]},
        {"range": "B3", "values": [[""]]},
        {"range": "B4", "values": [["FALSE"]]},
    ])
    read_game_state_cached.clear()

def buzz_in(player_name, question_id):
    try:
        ws = get_sheet("GameState")
        vals = ws.batch_get(["B2", "B3"])
        locked = vals[0][0][0] if vals[0] else "FALSE"
        log_ws = get_sheet("BuzzerLog")
        if locked == "TRUE":
            log_ws.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), player_name, question_id, "LATE"])
            return False
        ws.batch_update([
            {"range": "B2", "values": [["TRUE"]]},
            {"range": "B3", "values": [[player_name]]},
        ])
        log_ws.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), player_name, question_id, "FIRST"])
        read_game_state_cached.clear()
        return True
    except Exception:
        return False

@st.cache_data(ttl=300)
def get_questions_cached():
    ws = get_sheet("JeopardyContent")
    return ws.get_all_records()

def get_questions():
    return get_questions_cached()

def mark_question_used(question_id):
    ws = get_sheet("JeopardyContent")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if str(r["id"]) == str(question_id):
            ws.update_cell(i + 2, 6, "TRUE")
            break
    get_questions_cached.clear()

# ── Session state ──────────────────────────────────────────────────────────────
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "host_pw" not in st.session_state:
    st.session_state.host_pw = ""

# ── Lobby ──────────────────────────────────────────────────────────────────────
if st.session_state.player_name is None:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stMainBlockContainer"] { max-width: 100% !important; padding: 0 !important; }
    </style>
    <div class="lobby-outer">
        <div class="lobby-card">
            <div style="color:#b8d4a8;font-size:11px;letter-spacing:0.8px;
                        text-transform:uppercase;font-weight:600;margin-bottom:6px;">Analytics</div>
            <div style="color:#edf5e6;font-size:28px;font-weight:700;margin-bottom:4px;">Jeopardy</div>
            <div style="height:3px;background:#b85c38;border-radius:2px;
                        margin-bottom:24px;width:48px;"></div>
            <div style="color:#b8d4a8;font-size:13px;">Enter your name to join the game.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    name_input = st.text_input("Your name", label_visibility="collapsed",
                               placeholder="Enter your name...")
    if st.button("Join Game", use_container_width=True) and name_input.strip():
        add_or_get_player(name_input.strip())
        st.session_state.player_name = name_input.strip()
        st.rerun()
    st.stop()

# ── Load data ──────────────────────────────────────────────────────────────────
questions = get_questions()
player_name = st.session_state.player_name

categories = {}
for q in questions:
    cat = q["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(q)

# ── Host check ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Host Controls")
    pw = st.text_input("Password", type="password", label_visibility="collapsed",
                       placeholder="Host password...",
                       value=st.session_state.host_pw)
    if pw:
        st.session_state.host_pw = pw
    is_host = st.session_state.host_pw == st.secrets["app"]["host_password"]

    if is_host:
        st.success("Host mode active")
        if st.button("Reset Buzzer", use_container_width=True):
            reset_buzzer()
            st.success("Buzzer reset!")
        st.divider()
        st.markdown("**Award / Deduct Points**")
        all_players_sidebar = get_players()
        if all_players_sidebar:
            selected_player = st.selectbox("Player", [p["name"] for p in all_players_sidebar])
            point_delta = st.number_input("Points", value=100, step=100)
            if st.button("Apply Points", use_container_width=True):
                update_score(selected_player, point_delta)
                st.success(f"{point_delta:+d} pts → {selected_player}")
        st.divider()
        if st.button("Toggle Reveal Answer", use_container_width=True):
            state = read_game_state()
            write_game_state("show_answer",
                             "FALSE" if state["show_answer"] == "TRUE" else "TRUE")
        st.divider()
        if st.button("Clear Active Question", use_container_width=True):
            write_game_state("active_question_id", "")
            reset_buzzer()
            st.success("Question cleared!")
    else:
        st.markdown("<div style='color:#b8d4a8;font-size:12px;'>Enter host password above</div>",
                    unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_pill = st.columns([6, 1])
with col_title:
    st.markdown("# Analytics Jeopardy")
with col_pill:
    badge = '<div class="host-badge">HOST</div>' if is_host else ""
    st.markdown(f'<div class="player-pill">Playing as: {player_name}</div>{badge}',
                unsafe_allow_html=True)

# ── Scoreboard ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Scoreboard</div>', unsafe_allow_html=True)
all_players = get_players()
if all_players:
    max_score = max(p["score"] for p in all_players)
    cards_html = '<div class="score-grid">'
    for p in all_players:
        is_leader = p["score"] == max_score and max_score > 0
        card_class = "score-card leader" if is_leader else "score-card"
        leader_tag = '<span class="leader-tag">leader</span>' if is_leader else ""
        cards_html += f"""
        <div class="{card_class}">
            <div class="score-name">{p['name']}{leader_tag}</div>
            <div class="score-val">{p['score']} pts</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

st.divider()

# ── Buzzer + question fragment ─────────────────────────────────────────────────
@st.fragment(run_every=3)
def buzzer_display():
    state = read_game_state()
    first = state["first_buzzer"]
    locked = state["buzzer_locked"] == "TRUE"
    show_ans = state["show_answer"] == "TRUE"
    active_q = state["active_question_id"]

    matching = [q for q in questions if str(q["id"]) == str(active_q)] if active_q else []
    current_q = matching[0] if matching else None

    # Current question card
    if current_q:
        st.markdown(f"""
        <div class="question-card">
            <div class="question-category">{current_q['category']}</div>
            <div class="question-value">{current_q['value']} pts</div>
            <div class="question-text">{current_q['question']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="waiting-state">
            Waiting for host to select a question...
        </div>""", unsafe_allow_html=True)

    # Answer banner
    if show_ans and current_q:
        st.markdown(f"""
        <div class="answer-banner">
            <div class="answer-label">Answer revealed</div>
            <div class="answer-text">{current_q['answer']}
                <span class="burgundy-pill">{current_q['category']} · {current_q['value']} pts</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # Buzzer status — only show when a question is active
    if current_q:
        if locked and first:
            st.markdown(f"""
            <div class="buzzer-area">
                🔔&nbsp;<span class="buzzer-highlight">{first}</span>&nbsp;buzzed in first!
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="buzzer-area">
                Buzzer is open!
            </div>""", unsafe_allow_html=True)

    # Buzz button — players only, not host
    if not is_host:
        if st.button("🔔  BUZZ IN", use_container_width=True):
            if not active_q:
                st.error("No active question yet — wait for the host.")
            elif locked:
                st.error("Too slow — someone already buzzed!")
            else:
                result = buzz_in(player_name, active_q)
                if result:
                    st.success("You buzzed in first!")
                else:
                    st.error("Too slow — someone already buzzed!")

buzzer_display()

# ── Game board — HOST ONLY ─────────────────────────────────────────────────────
if is_host:
    st.divider()
    st.markdown('<div class="board-label">GAME BOARD</div>', unsafe_allow_html=True)

    cat_names = list(categories.keys())
    board_cols = st.columns(len(cat_names))

    for col_idx, cat in enumerate(cat_names):
        with board_cols[col_idx]:
            st.markdown(f'<div class="cat-header">{cat}</div>', unsafe_allow_html=True)
            for q in sorted(categories[cat], key=lambda x: x["value"]):
                used = str(q.get("used", "")).upper() == "TRUE"
                if used:
                    st.markdown('<div style="background:#d8e8d0;color:#8aaa80;border-radius:8px;padding:18px 0;text-align:center;font-size:16px;font-weight:700;margin-bottom:6px;width:100%;">✓</div>', unsafe_allow_html=True)
                else:
                    if st.button(f"{q['value']} pts", key=f"q_{q['id']}", use_container_width=True):
                        write_game_state("active_question_id", str(q["id"]))
                        reset_buzzer()
                        mark_question_used(q["id"])
                        st.rerun()