import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Analytics Jeopardy", layout="wide")

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Mobile responsiveness */
@media (max-width: 768px) {
    .score-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    .board-wrap {
        padding: 12px !important;
    }
    .cat-header {
        font-size: 10px !important;
        padding: 6px 4px !important;
        min-height: 36px !important;
    }
    div[data-testid="stButton"] button {
        font-size: 13px !important;
        padding: 10px 0 !important;
    }
}
/* Page background */
[data-testid="stAppViewContainer"] {
    background-color: #f5f0eb;
}
[data-testid="stHeader"] {
    background-color: #241a10;
}
/* Top accent bar */
[data-testid="stAppViewContainer"]::before {
    content: '';
    display: block;
    height: 4px;
    background: #b85c38;
    width: 100%;
}
/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #3d2e18;
}
[data-testid="stSidebar"] * {
    color: #edf5e6 !important;
}
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
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #4a6038 !important;
}
/* Main text */
h1, h2, h3 { color: #241a10 !important; }
p, label { color: #3d2e18 !important; }
/* Section labels */
.section-label {
    font-size: 11px;
    font-weight: 600;
    color: #8b6a50;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
/* Score cards */
.score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px;
    margin-bottom: 20px;
}
.score-card {
    background: #3d2e18;
    border-radius: 10px;
    padding: 12px 14px;
}
.score-card.leader {
    border: 2px solid #b85c38;
}
.score-name {
    font-size: 11px;
    color: #b8d4a8;
    margin-bottom: 4px;
}
.score-val {
    font-size: 24px;
    font-weight: 600;
    color: #edf5e6;
}
.leader-tag {
    font-size: 9px;
    color: #b85c38;
    font-weight: 600;
    margin-left: 4px;
}
/* Answer banner */
.answer-banner {
    background: #fdeae0;
    border: 1.5px solid #e8a880;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
.answer-label {
    font-size: 10px;
    color: #b85c38;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.answer-text {
    font-size: 15px;
    color: #3a1a08;
    font-weight: 500;
}
.burgundy-pill {
    background: #8b2040;
    color: #fde8ef;
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 500;
    margin-left: 8px;
    vertical-align: middle;
}
/* Buzzer area */
.buzzer-area {
    background: #fff8f2;
    border: 1.5px solid #e8c4a0;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    font-size: 14px;
    color: #5a3a20;
    font-weight: 500;
}
.buzzer-highlight {
    color: #8b2040;
    font-weight: 600;
}
/* Buzz button */
div[data-testid="stButton"] button[kind="primary"],
.buzz-btn div[data-testid="stButton"] button {
    background-color: #5a7a4a !important;
    color: #edf5e6 !important;
    border: none !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 20px !important;
    border-radius: 10px !important;
    width: 100% !important;
}
/* Board */
.board-wrap {
    background: #241a10;
    border-radius: 14px;
    padding: 20px;
    margin-top: 8px;
}
.board-label {
    color: #b8d4a8;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 14px;
}
.cat-header {
    background: #3d2e18;
    color: #b8d4a8;
    text-align: center;
    font-weight: 600;
    font-size: 13px;
    border-radius: 8px;
    padding: 10px 6px;
    margin-bottom: 8px;
    min-height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
}
div[data-testid="stButton"] button {
    background-color: #5a7a4a !important;
    color: #edf5e6 !important;
    border: none !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 16px 0 !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    transition: background-color 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    background-color: #4a6038 !important;
}
div[data-testid="stButton"] button:disabled {
    background-color: #2d3d24 !important;
    color: #4a6038 !important;
    cursor: not-allowed !important;
}
/* Divider */
hr {
    border-color: #e8c4a0 !important;
    margin: 16px 0 !important;
}
/* Player pill in header */
.player-pill {
    display: inline-block;
    background: #b85c38;
    color: #fff8f0;
    font-size: 12px;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 500;
    margin-bottom: 16px;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    [data-testid="stSidebar"] {
        width: 220px !important;
        min-width: 220px !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        [data-testid="stMainBlockContainer"] {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
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
def get_players():
    ws = get_sheet("Players")
    return ws.get_all_records()

def add_or_get_player(name):
    ws = get_sheet("Players")
    records = ws.get_all_records()
    if name not in [r["name"] for r in records]:
        ws.append_row([name, 0])
    return get_players()

def update_score(name, delta):
    ws = get_sheet("Players")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if r["name"] == name:
            ws.update_cell(i + 2, 2, r["score"] + delta)
            break

def read_game_state():
    try:
        ws = get_sheet("GameState")
        return {
            "active_question_id": ws.acell("B1").value,
            "buzzer_locked":      ws.acell("B2").value,
            "first_buzzer":       ws.acell("B3").value,
            "show_answer":        ws.acell("B4").value,
        }
    except Exception:
        return {
            "active_question_id": "",
            "buzzer_locked": "FALSE",
            "first_buzzer": "",
            "show_answer": "FALSE",
        }

def write_game_state(key, value):
    ws = get_sheet("GameState")
    cell_map = {
        "active_question_id": "B1",
        "buzzer_locked":      "B2",
        "first_buzzer":       "B3",
        "show_answer":        "B4",
    }
    ws.update_acell(cell_map[key], value)

def reset_buzzer():
    write_game_state("buzzer_locked", "FALSE")
    write_game_state("first_buzzer", "")
    write_game_state("show_answer", "FALSE")

def buzz_in(player_name, question_id):
    state = read_game_state()
    if state["buzzer_locked"] == "TRUE":
        log_ws = get_sheet("BuzzerLog")
        log_ws.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), player_name, question_id, "LATE"])
        return False
    write_game_state("buzzer_locked", "TRUE")
    write_game_state("first_buzzer", player_name)
    log_ws = get_sheet("BuzzerLog")
    log_ws.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), player_name, question_id, "FIRST"])
    return True

def get_questions():
    ws = get_sheet("JeopardyContent")
    return ws.get_all_records()

def mark_question_used(question_id):
    ws = get_sheet("JeopardyContent")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if str(r["id"]) == str(question_id):
            ws.update_cell(i + 2, 6, "TRUE")
            break

# ── Session state ──────────────────────────────────────────────────────────────
if "player_name" not in st.session_state:
    st.session_state.player_name = None

# ── Lobby ──────────────────────────────────────────────────────────────────────
if st.session_state.player_name is None:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    .lobby-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
        padding: 20px;
    }
    .lobby-card {
        background: #3d2e18;
        border-radius: 16px;
        padding: 36px 32px;
        width: 100%;
        max-width: 420px;
        margin: 0 auto;
    }
    </style>
    <div class="lobby-wrap">
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

# ── Load questions ─────────────────────────────────────────────────────────────
st.session_state.questions = get_questions()
questions = st.session_state.questions
player_name = st.session_state.player_name

# ── Board structure ────────────────────────────────────────────────────────────
categories = {}
for q in questions:
    cat = q["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(q)

# ── Sidebar host controls ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Host Controls")
    pw = st.text_input("Password", type="password", label_visibility="collapsed",
                       placeholder="Host password...")
    is_host = pw == st.secrets["app"]["host_password"]

    if is_host:
        st.success("Host mode active")
        if st.button("Reset Buzzer", use_container_width=True):
            reset_buzzer()
            st.success("Buzzer reset!")

        st.divider()
        st.markdown("**Award / Deduct Points**")
        all_players = get_players()
        selected_player = st.selectbox("Player", [p["name"] for p in all_players])
        point_delta = st.number_input("Points", value=100, step=100)
        if st.button("Apply Points", use_container_width=True):
            update_score(selected_player, point_delta)
            st.success(f"{point_delta:+d} pts → {selected_player}")

        st.divider()
        if st.button("Toggle Reveal Answer", use_container_width=True):
            state = read_game_state()
            write_game_state("show_answer",
                             "FALSE" if state["show_answer"] == "TRUE" else "TRUE")
    else:
        st.markdown(
            "<div style='color:#b8d4a8;font-size:12px;'>Enter host password above</div>",
            unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_pill = st.columns([6, 1])
with col_title:
    st.markdown("# Analytics Jeopardy")
with col_pill:
    st.markdown(f'<div class="player-pill">Playing as: {player_name}</div>',
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
            <div class="score-val">${p['score']}</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

st.divider()

# ── Buzzer fragment ────────────────────────────────────────────────────────────
@st.fragment(run_every=3)
def buzzer_display():
    state = read_game_state()
    first = state["first_buzzer"]
    locked = state["buzzer_locked"] == "TRUE"
    show_ans = state["show_answer"] == "TRUE"
    active_q = state["active_question_id"]

    if show_ans and active_q:
        matching = [q for q in questions if str(q["id"]) == str(active_q)]
        if matching:
            q = matching[0]
            st.markdown(f"""
            <div class="answer-banner">
                <div class="answer-label">Answer revealed</div>
                <div class="answer-text">{q['answer']}
                    <span class="burgundy-pill">Q{q['id']} · {q['category']} · ${q['value']}</span>
                </div>
            </div>""", unsafe_allow_html=True)

    if locked and first:
        st.markdown(f"""
        <div class="buzzer-area">
            <span style="font-size:18px;">🔔</span>&nbsp;
            <span class="buzzer-highlight">{first}</span>&nbsp;buzzed in first!
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="buzzer-area">
            Buzzer is open — select a question to activate it.
        </div>""", unsafe_allow_html=True)

    if st.button("🔔  BUZZ IN", use_container_width=True):
        if not active_q:
            st.error("No active question — host must select one first.")
        elif locked:
            st.error("Too slow — someone already buzzed!")
        else:
            result = buzz_in(player_name, active_q)
            if result:
                st.success("You buzzed in first!")
            else:
                st.error("Too slow — someone already buzzed!")

buzzer_display()

st.divider()

# ── Game board ─────────────────────────────────────────────────────────────────
st.markdown('<div class="board-wrap">', unsafe_allow_html=True)
st.markdown('<div class="board-label">Game Board</div>', unsafe_allow_html=True)

cat_names = list(categories.keys())
board_cols = st.columns(len(cat_names))

for col_idx, cat in enumerate(cat_names):
    with board_cols[col_idx]:
        st.markdown(f'<div class="cat-header">{cat}</div>', unsafe_allow_html=True)
        for q in sorted(categories[cat], key=lambda x: x["value"]):
            used = str(q.get("used", "")).upper() == "TRUE"
            if used:
                st.button("✓", disabled=True, key=f"q_{q['id']}")
            else:
                if st.button(f"${q['value']}", key=f"q_{q['id']}"):
                    write_game_state("active_question_id", str(q["id"]))
                    write_game_state("buzzer_locked", "FALSE")
                    write_game_state("first_buzzer", "")
                    write_game_state("show_answer", "FALSE")
                    mark_question_used(q["id"])
                    st.session_state.questions = get_questions()
                    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)